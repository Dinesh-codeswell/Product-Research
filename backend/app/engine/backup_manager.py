"""Backup Manager (borg-inspired: dedup-friendly snapshot, rotate, restore)

Protects the two irreplaceable data stores:
  - pulseradar.db            (SQLAlchemy sessions, clusters, watchlists, automations)
  - data/transcripts_cache.sqlite3 (cached YouTube transcripts)

Design principles borrowed from BorgBackup:
  * Snapshots are immutable once written (write-temp-then-rename).
  * Rotation keeps the last N snapshots per target (default 10).
  * Manifests record sizes + SHA-256 so integrity is verifiable after copy.
  * SQLite files are safely copied via sqlite3 backup API (consistent even
    while the app is writing), falling back to a plain byte copy.

Snapshots live in `backend/data/backups/<name>/` so the whole folder can
itself be synced or zipped off-site.
"""
import hashlib
import logging
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent   # backend/
DATA_DIR = BACKEND_DIR / "data"
BACKUP_ROOT = DATA_DIR / "backups"

# Relative targets: name -> path candidates (first existing wins)
DEFAULT_TARGETS: Dict[str, List[str]] = {
    "pulseradar_db": ["pulseradar.db"],
    "transcripts_cache": ["data/transcripts_cache.sqlite3"],
}

MAX_SNAPSHOTS_DEFAULT = 10


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _safe_copy_sqlite(src: Path, dst: Path) -> None:
    """Consistent copy of a live SQLite file via the backup API."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp")
    try:
        src_conn = sqlite3.connect(str(src))
        dst_conn = sqlite3.connect(str(tmp))
        with dst_conn:
            src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
    except sqlite3.Error:
        # Non-SQLite or locked: fall back to byte copy
        shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def create_backup(name: str, note: str = "") -> Dict[str, Any]:
    """Creates a timestamped snapshot of all known targets. Returns a manifest."""
    name = name.strip() or "manual"
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    snap_id = f"{ts}_{name}"
    snap_dir = BACKUP_ROOT / snap_id
    snap_dir.mkdir(parents=True, exist_ok=True)

    files: List[Dict[str, Any]] = []
    for target, rel_candidates in DEFAULT_TARGETS.items():
        src: Optional[Path] = None
        for rel in rel_candidates:
            p = BACKEND_DIR / rel
            if p.exists():
                src = p
                break
        if not src:
            files.append({"target": target, "status": "missing", "path": None})
            continue
        dst = snap_dir / src.name
        try:
            if src.suffix in (".db", ".sqlite", ".sqlite3"):
                _safe_copy_sqlite(src, dst)
            else:
                shutil.copy2(src, dst)
            files.append({
                "target": target,
                "status": "ok",
                "path": src.name,
                "size_bytes": dst.stat().st_size,
                "sha256": _sha256(dst),
            })
        except Exception as e:  # noqa: BLE001 — one bad file must not abort the rest
            logger.warning(f"Backup of {target} failed: {e}")
            files.append({"target": target, "status": "error", "path": str(src), "error": str(e)})

    ok_count = sum(1 for f in files if f.get("status") == "ok")
    manifest = {
        "snapshot_id": snap_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "name": name,
        "note": note,
        "file_count": ok_count,
        "total_bytes": sum(f.get("size_bytes", 0) for f in files if f.get("status") == "ok"),
        "files": files,
    }

    # Write manifest atomically
    import json
    tmp_manifest = snap_dir / "manifest.json.tmp"
    tmp_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    os.replace(tmp_manifest, snap_dir / "manifest.json")

    logger.info(f"Backup snapshot {snap_id} created ({ok_count} files, {manifest['total_bytes']} bytes)")
    return manifest


def list_backups() -> List[Dict[str, Any]]:
    """Lists all snapshots, newest first."""
    if not BACKUP_ROOT.exists():
        return []
    import json
    out: List[Dict[str, Any]] = []
    for d in sorted(BACKUP_ROOT.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        manifest_path = d / "manifest.json"
        if manifest_path.exists():
            try:
                out.append(json.loads(manifest_path.read_text(encoding="utf-8")))
                continue
            except Exception:
                pass
        out.append({"snapshot_id": d.name, "created_at": None, "file_count": 0,
                    "total_bytes": sum(f.stat().st_size for f in d.iterdir() if f.is_file()),
                    "files": [], "name": "unknown", "note": "manifest missing"})
    return out


def get_backup(snap_id: str) -> Optional[Dict[str, Any]]:
    for b in list_backups():
        if b.get("snapshot_id") == snap_id:
            return b
    return None


def delete_backup(snap_id: str) -> bool:
    snap_dir = BACKUP_ROOT / snap_id
    # Path traversal guard
    if not snap_dir.resolve().is_relative_to(BACKUP_ROOT.resolve()):
        return False
    if snap_dir.exists():
        shutil.rmtree(snap_dir, ignore_errors=True)
        return True
    return False


def restore_backup(snap_id: str) -> Dict[str, Any]:
    """Restores files from a snapshot over the live DBs (integrity-checked).

    Callers should restart the backend afterwards so SQLAlchemy reconnects.
    """
    snap_dir = BACKUP_ROOT / snap_id
    if not snap_dir.exists():
        return {"success": False, "error": f"Snapshot {snap_id} not found"}
    if not snap_dir.resolve().is_relative_to(BACKUP_ROOT.resolve()):
        return {"success": False, "error": "Invalid snapshot path"}

    results: List[Dict[str, Any]] = []
    for f in snap_dir.iterdir():
        if f.name in ("manifest.json", "manifest.json.tmp"):
            continue
        # Verify checksum before touching live data
        expected = None
        manifest = get_backup(snap_id) or {}
        for mf in manifest.get("files", []):
            if mf.get("path") == f.name:
                expected = mf.get("sha256")
        if expected and _sha256(f) != expected:
            results.append({"file": f.name, "status": "skipped_corrupt"})
            continue
        dst = BACKEND_DIR / f.name
        try:
            if f.suffix in (".db", ".sqlite", ".sqlite3"):
                _safe_copy_sqlite(f, dst)
            else:
                shutil.copy2(f, dst)
            results.append({"file": f.name, "status": "restored"})
        except Exception as e:  # noqa: BLE001
            results.append({"file": f.name, "status": "error", "error": str(e)})

    ok = any(r["status"] == "restored" for r in results)
    logger.info(f"Restore from {snap_id}: {results}")
    return {"success": ok, "restored": results, "restart_required": ok}


def rotate_backups(keep: int = MAX_SNAPSHOTS_DEFAULT) -> List[str]:
    """Deletes the oldest snapshots beyond the retention limit."""
    snaps = list_backups()
    removed = []
    for b in snaps[keep:]:
        if delete_backup(b["snapshot_id"]):
            removed.append(b["snapshot_id"])
    if removed:
        logger.info(f"Rotation removed {len(removed)} old snapshots")
    return removed
