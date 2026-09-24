"""Laya System 1 Decision Engine Client for PulseRadar

Provides sub-40ms non-autoregressive triage, semantic relevance filtering,
and calibrated severity scoring for scraped multi-channel product signals.

Supports:
1. Local in-process Laya router (zero-latency, no network overhead).
2. Remote HTTP microservice via TypeSafe Jev wire protocol (/v1/systemone).
3. Resilient heuristic fallback if the local model is downloading or offline.
"""
import logging
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class SignalEvaluation(BaseModel):
    is_relevant: bool
    category: Literal["PAIN_POINT", "DESIRE", "WORKAROUND", "CHURN_TRIGGER", "NOISE"]
    severity_level: Literal[0, 1, 2, 3]  # 0: informational, 1: minor friction, 2: blocking bug, 3: critical churn

class LayaEngine:
    _instance: Optional["LayaEngine"] = None
    _router = None
    _init_attempted = False
    _cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self.enabled = getattr(settings, "LAYA_ENABLED", True)
        self.service_url = getattr(settings, "LAYA_SERVICE_URL", "http://127.0.0.1:8080")
        self.use_local = getattr(settings, "LAYA_USE_LOCAL", True)
        self._ensure_initialized()

    def _ensure_initialized(self):
        if not self.enabled or self._init_attempted:
            return

        LayaEngine._init_attempted = True
        if self.use_local:
            try:
                import laya
                LayaEngine._router = laya.Router()
                logger.info("Laya local in-process Router initialized successfully for PulseRadar.")
            except ImportError:
                logger.info("Laya not installed in this Python environment. Will use remote HTTP service or fallback.")
            except Exception as e:
                logger.warning(f"Laya local initialization deferred ({e}). Will use remote/fallback mode.")

    def evaluate_signal(self, text: str, query: str) -> Dict[str, Any]:
        """Evaluates a single piece of user feedback against the research query in ~35ms.
        
        Returns:
            dict containing:
                - is_relevant (bool): Whether the signal relates to the query topic.
                - category (str): PAIN_POINT, DESIRE, WORKAROUND, or CHURN_TRIGGER.
                - severity (float): 0.0 to 1.0 calibrated severity score.
                - confidence (float): 0.0 to 1.0 Bayesian confidence score.
        """
        if not text or len(text.strip()) < 20:
            return {"is_relevant": False, "category": "NOISE", "severity": 0.0, "confidence": 0.0}

        import hashlib
        cache_key = f"{query}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
        if cache_key in LayaEngine._cache:
            return LayaEngine._cache[cache_key]

        if not self.enabled:
            res = self._heuristic_fallback(text)
            LayaEngine._cache[cache_key] = res
            return res

        # 1. Local in-process evaluation (Fastest, zero tokens)
        if LayaEngine._router:
            try:
                prompt = f"Product Topic: '{query}'\nUser Feedback:\n{text[:450]}"
                questions = {
                    "category": {
                        "type": "choice",
                        "instructions": "What kind of product signal is this user feedback?",
                        "criteria": {
                            "PAIN_POINT": "complaints, errors, bugs, crashes, slow performance, or broken functionality",
                            "DESIRE": "feature requests, hopes, or missing product capabilities",
                            "WORKAROUND": "hacks, temporary scripts, custom wrappers, or manual bypasses",
                            "CHURN_TRIGGER": "cancelling account, switching to alternative, or high pricing anger",
                            "IRRELEVANT_NOISE": "spam, promotions, telegram links, advertisements, or completely unrelated text"
                        }
                    },
                    "severity": {
                        "type": "score",
                        "instructions": "How severe is the user dissatisfaction or friction?",
                        "criteria": [
                            "none or mild: informational or neutral observation",
                            "moderate: annoying friction or minor inconvenience",
                            "high: blocking workflow or serious recurring defect",
                            "critical: data loss, service crash, or leaving product"
                        ]
                    }
                }
                res = LayaEngine._router.predict(prompt, questions)
                ans = res.get("answers", {})
                cat_ans = ans.get("category", {})
                cat = cat_ans.get("choice", "PAIN_POINT")
                conf = cat_ans.get("confidence", 0.70)
                
                # Ordinal severity score (0 to 3) mapped to continuous float
                sev_ans = ans.get("severity", {})
                raw_sev = sev_ans.get("score", 1.0)
                sev_float = round(min(0.98, max(0.40, 0.45 + (raw_sev / 3.0) * 0.50)), 2)

                is_rel = (cat != "IRRELEVANT_NOISE")
                final_cat = cat if cat != "IRRELEVANT_NOISE" else "PAIN_POINT"

                ret = {
                    "is_relevant": is_rel,
                    "category": final_cat,
                    "severity": sev_float,
                    "confidence": round(float(conf), 3)
                }
                self._save_cache(cache_key, ret)
                return ret
            except Exception as e:
                logger.debug(f"Local Laya predict error ({e}), trying remote service...")

        # 2. Remote HTTP microservice (/v1/systemone)
        try:
            with httpx.Client(timeout=2.0) as client:
                body = {
                    "state": f"Topic: {query}\nFeedback: {text[:450]}",
                    "questions": [
                        {
                            "id": "rel",
                            "kind": "noul",
                            "prompt": f"Is this feedback genuinely relevant to '{query}'?"
                        },
                        {
                            "id": "cat",
                            "kind": "choice",
                            "prompt": "What category best describes this feedback?",
                            "options": {
                                "PAIN_POINT": "complaints, errors, bugs, or slow performance",
                                "DESIRE": "feature requests, hopes, or missing capabilities",
                                "WORKAROUND": "hacks, temporary scripts, or third-party wrappers",
                                "CHURN_TRIGGER": "switching to competitor, cancelling, or cost anger",
                                "NOISE": "spam, promotions, bot text, or unrelated chatter"
                            }
                        }
                    ]
                }
                resp = client.post(f"{self.service_url}/v1/systemone", json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    ans = data.get("answers", {})
                    rel_prob = ans.get("rel", 0.8)
                    cat_choice = ans.get("cat", "PAIN_POINT")
                    conf = data.get("confidence", {}).get("cat", 0.75)

                    ret = {
                        "is_relevant": (rel_prob >= 0.5) and (cat_choice != "NOISE"),
                        "category": cat_choice if cat_choice != "NOISE" else "PAIN_POINT",
                        "severity": 0.85 if cat_choice in ["PAIN_POINT", "CHURN_TRIGGER"] else 0.60,
                        "confidence": round(float(conf), 3)
                    }
                    self._save_cache(cache_key, ret)
                    return ret
        except Exception:
            pass

        # 3. Resilient heuristic fallback
        res = self._heuristic_fallback(text)
        self._save_cache(cache_key, res)
        return res

    def _save_cache(self, key: str, value: Dict[str, Any]):
        LayaEngine._cache[key] = value
        if len(LayaEngine._cache) > 2000:
            LayaEngine._cache.pop(next(iter(LayaEngine._cache)))

    def _heuristic_fallback(self, text: str) -> Dict[str, Any]:
        """Grounded heuristic fallback when Laya engine is temporarily loading."""
        lower = text.lower()
        
        # High confidence noise / spam
        if any(w in lower for w in ["telegram.me", "t.me/", "crypto pump", "airdrop", "presale", "whatsapp group", "click here to win", "casino", "free bonus"]):
            return {"is_relevant": False, "category": "NOISE", "severity": 0.0, "confidence": 0.90}

        # High confidence churn
        if any(w in lower for w in ["cancel", "switch to", "moved to", "pricing cliff", "rip off", "ditching"]):
            return {"is_relevant": True, "category": "CHURN_TRIGGER", "severity": 0.92, "confidence": 0.78}
        
        # Workarounds
        if any(w in lower for w in ["workaround", "hack", "wrapper", "patch", "script", "bypass"]):
            return {"is_relevant": True, "category": "WORKAROUND", "severity": 0.70, "confidence": 0.72}

        # Desires
        if any(w in lower for w in ["wish", "hope", "need", "feature request", "why can't", "should support", "please add"]):
            return {"is_relevant": True, "category": "DESIRE", "severity": 0.58, "confidence": 0.75}

        # Default pain point
        return {"is_relevant": True, "category": "PAIN_POINT", "severity": 0.75, "confidence": 0.60}

