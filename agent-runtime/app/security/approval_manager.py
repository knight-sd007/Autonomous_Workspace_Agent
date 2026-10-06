"""
Human-in-the-Loop (HITL) Approval State Manager.

Enforces cryptographic integrity, session-binding, single-use execution,
and expiration checks on all sensitive/mutating/destructive tool requests.
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import hashlib
import json
import uuid
import threading
import logging

logger = logging.getLogger("p07.security.approvals")


def compute_arguments_hash(tool_kwargs: Dict[str, Any]) -> str:
    """Generates deterministic SHA-256 hash of canonicalized JSON arguments."""
    canonical_json = json.dumps(tool_kwargs, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()


@dataclass
class ApprovalRecord:
    approval_id: str
    session_id: str
    tool_name: str
    resource: str
    tool_kwargs: Dict[str, Any]
    arguments_hash: str
    is_destructive: bool
    reason: str
    created_at_utc: str
    expires_at_utc: str
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, EXPIRED
    user_id: Optional[str] = None


class ApprovalManager:
    """Thread-safe state manager for Human-in-the-Loop approval requests."""

    def __init__(self, default_ttl_seconds: int = 300):
        self._approvals: Dict[str, ApprovalRecord] = {}
        self._lock = threading.Lock()
        self.default_ttl_seconds = default_ttl_seconds

    def create_approval(
        self,
        session_id: str,
        tool_name: str,
        resource: str,
        tool_kwargs: Dict[str, Any],
        reason: str,
        is_destructive: bool = False,
        user_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> ApprovalRecord:
        """Creates a new pending approval record bound to session and arguments."""
        approval_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        ttl = ttl_seconds or self.default_ttl_seconds
        expires = now + timedelta(seconds=ttl)

        args_hash = compute_arguments_hash(tool_kwargs)

        record = ApprovalRecord(
            approval_id=approval_id,
            session_id=session_id,
            tool_name=tool_name,
            resource=resource,
            tool_kwargs=dict(tool_kwargs),
            arguments_hash=args_hash,
            is_destructive=is_destructive,
            reason=reason,
            created_at_utc=now.isoformat(),
            expires_at_utc=expires.isoformat(),
            status="PENDING",
            user_id=user_id
        )

        with self._lock:
            self._approvals[approval_id] = record

        logger.info(f"Created approval [{approval_id}] for tool '{tool_name}' (Session: {session_id}, TTL: {ttl}s)")
        return record

    def get_approval(self, approval_id: str) -> Optional[ApprovalRecord]:
        with self._lock:
            return self._approvals.get(approval_id)

    def evaluate_decision(
        self,
        approval_id: str,
        session_id: str,
        decision: str,
        supplied_kwargs: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[ApprovalRecord]]:
        """
        Validates and updates an approval record.
        Returns (success, message, record).
        """
        decision_norm = decision.strip().lower()
        if decision_norm not in ("approve", "reject"):
            return False, f"Invalid decision '{decision}'. Must be 'approve' or 'reject'.", None

        with self._lock:
            record = self._approvals.get(approval_id)
            if not record:
                return False, f"Approval request '{approval_id}' not found.", None

            # 1. Session Binding Check
            if record.session_id != session_id:
                logger.warning(f"Security Alert: Session mismatch on approval [{approval_id}]. Expected {record.session_id}, received {session_id}")
                return False, "Security Violation: Approval is not bound to the requesting session.", None

            # 2. Status / Replay Check
            if record.status != "PENDING":
                logger.warning(f"Security Alert: Replay attempt on non-pending approval [{approval_id}] (Status: {record.status})")
                return False, f"Approval request has already been processed or is not pending (status: {record.status}).", record

            # 3. Expiry Check
            expires_at = datetime.fromisoformat(record.expires_at_utc)
            now = datetime.now(timezone.utc)
            if now > expires_at:
                record.status = "EXPIRED"
                logger.info(f"Approval [{approval_id}] has expired.")
                return False, "Approval request has expired.", record

            # 4. Arguments Tampering Check (if kwargs supplied with decision)
            if supplied_kwargs is not None:
                supplied_hash = compute_arguments_hash(supplied_kwargs)
                if supplied_hash != record.arguments_hash:
                    logger.warning(f"Security Alert: Tampered arguments detected for approval [{approval_id}]")
                    return False, "Security Violation: Tool arguments have been modified since approval request was issued.", None

            # 5. Apply Decision
            if decision_norm == "approve":
                record.status = "APPROVED"
                logger.info(f"Approval [{approval_id}] APPROVED for tool '{record.tool_name}' on resource '{record.resource}'")
                return True, "Approval granted.", record
            else:
                record.status = "REJECTED"
                logger.info(f"Approval [{approval_id}] REJECTED by user for tool '{record.tool_name}'")
                return True, "Approval rejected.", record
