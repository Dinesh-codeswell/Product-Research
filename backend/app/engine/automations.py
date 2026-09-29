"""Automation Engine — Event-Triggered Rules (Baserow-inspired, Baserow-grade boundaries)

When research or SEO pipelines complete, dispatch_event evaluates enabled
AutomationRules. Matching rules fire their action (webhook today; task
creation is reserved for the frontend to render into its board). Read-only
review before mutation: webhooks POST a compact, reviewable JSON payload.
"""
import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_entities import AutomationRule, AutomationLog

logger = logging.getLogger(__name__)

# Event types supported by dispatch_event
SUPPORTED_EVENTS = ("research.completed", "seo.completed")


def _rule_matches(rule: AutomationRule, event_type: str, payload: Dict[str, Any]) -> bool:
    if rule.event_type != event_type:
        return False
    cond = rule.conditions or {}

    if event_type == "research.completed":
        # Optional query substring filter
        q_filter = cond.get("query_contains")
        if q_filter and q_filter.lower() not in (payload.get("query") or "").lower():
            return False
        min_clusters = cond.get("min_clusters")
        if min_clusters is not None and (payload.get("clusters_count") or 0) < min_clusters:
            return False
        # Highest severity across clusters
        max_sev = max((c.get("severity_score") or 0) for c in payload.get("clusters", [])) if payload.get("clusters") else 0
        min_sev = cond.get("min_severity")
        if min_sev is not None and max_sev < float(min_sev):
            return False
    else:  # seo.completed
        score = payload.get("overall_score")
        score_below = cond.get("score_below")
        if score_below is not None and (score or 0) >= float(score_below):
            return False
        score_above = cond.get("score_above")
        if score_above is not None and (score or 0) <= float(score_above):
            return False
        domain_contains = cond.get("domain_contains")
        if domain_contains and domain_contains.lower() not in (payload.get("domain") or ""):
            return False

    return True


def _build_payload(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
        "source": "pulseradar-automation",
    }


async def dispatch_event(db: AsyncSession, event_type: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluates all enabled rules for an event and fires matching actions.

    Never raises: automation failures must not break the pipelines that
    triggered them. Returns the list of fired rule records for logging.
    """
    if event_type not in SUPPORTED_EVENTS:
        return []

    fired: List[Dict[str, Any]] = []
    try:
        res = await db.execute(select(AutomationRule).where(AutomationRule.enabled == True))  # noqa: E712
        rules = res.scalars().all()
    except Exception as e:
        logger.error(f"Automation dispatch could not load rules: {e}")
        return []

    for rule in rules:
        try:
            if not _rule_matches(rule, event_type, data):
                continue

            payload = _build_payload(event_type, data)
            status, error = "FIRED", None

            if rule.action_type == "webhook":
                url = (rule.action_config or {}).get("url")
                if not url:
                    status, error = "FAILED", "Missing webhook URL"
                else:
                    secret = (rule.action_config or {}).get("secret")
                    body = json.dumps(payload, default=str).encode()
                    headers = {"Content-Type": "application/json"}
                    if secret:
                        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
                        headers["X-PulseRadar-Signature"] = f"sha256={sig}"
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            resp = await client.post(url, content=body, headers=headers)
                        if resp.status_code >= 400:
                            status, error = "FAILED", f"Webhook returned HTTP {resp.status_code}"
                    except Exception as we:
                        status, error = "FAILED", f"Webhook error: {type(we).__name__}"

            rule.last_fired_at = datetime.utcnow()
            rule.fire_count += 1
            db.add(AutomationLog(
                rule_id=rule.id,
                event_type=event_type,
                payload=payload,
                status=status,
                error=error,
            ))
            fired.append({"rule_id": rule.id, "rule_name": rule.name, "status": status, "error": error})

        except Exception as re:
            logger.error(f"Automation rule {rule.id} evaluation failed: {re}")

    try:
        await db.commit()
    except Exception as ce:
        logger.error(f"Automation commit failed: {ce}")

    return fired
