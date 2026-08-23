from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.config import BASE_DIR


class ActionService:
    """
    Handles mocked state-changing actions.

    IMPORTANT:
    - Actions are first prepared as PENDING_CONFIRMATION.
    - Nothing is written as an executed escalation until confirm_action()
      is explicitly called.
    """

    def __init__(self):
        self.storage_dir = BASE_DIR / "data" / "processed" / "actions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.pending_file = self.storage_dir / "pending_actions.json"
        self.executed_file = self.storage_dir / "executed_actions.json"

        self._ensure_file(self.pending_file)
        self._ensure_file(self.executed_file)

    # ============================================================
    # FILE HELPERS
    # ============================================================

    def _ensure_file(self, file_path: Path) -> None:
        """Create an empty JSON list if the file does not exist."""
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump([], file, indent=2)

    def _load_actions(self, file_path: Path) -> list[dict]:
        """Load actions from a JSON file."""
        self._ensure_file(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                return data

            return []

        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_actions(
        self,
        file_path: Path,
        actions: list[dict],
    ) -> None:
        """Save actions to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(
                actions,
                file,
                indent=2,
                ensure_ascii=False,
            )

    # ============================================================
    # ACCESS CONTROL
    # ============================================================

    def _can_access_account(
        self,
        user_context: dict,
        account_id: str,
    ) -> bool:
        """
        Enforce account-level access.

        Customers:
            Can only create actions for their own account.

        Internal users:
            Can create actions for any account.
        """

        role = user_context.get("role")
        user_account_id = user_context.get("account_id")

        internal_roles = {
            "support",
            "admin",
            "operations",
            "manager",
        }

        if role in internal_roles:
            return True

        if role == "customer":
            return user_account_id == account_id

        return False

    # ============================================================
    # PREPARE ESCALATION
    # ============================================================

    def prepare_escalation(
        self,
        user_context: dict,
        account_id: str,
        reason: str,
        title: Optional[str] = None,
        priority: str = "P2",
        related_order_id: Optional[str] = None,
        related_ticket_id: Optional[str] = None,
        details: Optional[str] = None,
    ) -> dict:
        """
        PREPARE an escalation.

        This does NOT execute the action.

        The returned action must be explicitly confirmed using
        confirm_action() before it becomes an executed escalation.
        """

        if not account_id:
            return {
                "success": False,
                "error": "account_id is required.",
            }

        if not reason or not reason.strip():
            return {
                "success": False,
                "error": "A reason is required to prepare an escalation.",
            }

        if not self._can_access_account(
            user_context=user_context,
            account_id=account_id,
        ):
            return {
                "success": False,
                "error": (
                    "Access denied. You are not authorised to "
                    "create an action for this account."
                ),
            }

        allowed_priorities = {"P1", "P2", "P3"}

        priority = priority.upper().strip()

        if priority not in allowed_priorities:
            return {
                "success": False,
                "error": (
                    f"Invalid priority '{priority}'. "
                    "Allowed values are P1, P2, or P3."
                ),
            }

        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"

        if not title:
            title = f"Support escalation for {account_id}"

        now = datetime.now(timezone.utc).isoformat()

        action = {
            "action_id": action_id,
            "action_type": "CREATE_ESCALATION",
            "status": "PENDING_CONFIRMATION",
            "confirmation_required": True,

            "created_at": now,
            "confirmed_at": None,
            "executed_at": None,

            "requested_by": {
                "username": user_context.get("username"),
                "display_name": user_context.get("display_name"),
                "role": user_context.get("role"),
                "account_id": user_context.get("account_id"),
            },

            "account_id": account_id,

            "title": title,
            "reason": reason,
            "priority": priority,

            "related_order_id": related_order_id,
            "related_ticket_id": related_ticket_id,
            "details": details,
        }

        pending_actions = self._load_actions(
            self.pending_file
        )

        pending_actions.append(action)

        self._save_actions(
            self.pending_file,
            pending_actions,
        )

        return {
            "success": True,
            "executed": False,
            "confirmation_required": True,
            "message": (
                "Escalation prepared but NOT executed. "
                "Explicit user confirmation is required."
            ),
            "action": action,
        }

    # ============================================================
    # GET PENDING ACTION
    # ============================================================

    def get_pending_action(
        self,
        action_id: str,
        user_context: dict,
    ) -> Optional[dict]:
        """
        Retrieve a pending action if the user is authorised
        to access it.
        """

        pending_actions = self._load_actions(
            self.pending_file
        )

        for action in pending_actions:
            if action.get("action_id") == action_id:

                account_id = action.get("account_id")

                if not self._can_access_account(
                    user_context=user_context,
                    account_id=account_id,
                ):
                    return None

                return action

        return None

    # ============================================================
    # CONFIRM ACTION
    # ============================================================

    def confirm_action(
        self,
        action_id: str,
        user_context: dict,
        confirmed: bool,
    ) -> dict:
        """
        Execute an action ONLY after explicit confirmation.

        confirmed=True:
            Moves action from pending to executed.

        confirmed=False:
            Cancels the pending action.
        """

        pending_actions = self._load_actions(
            self.pending_file
        )

        action_to_process = None
        remaining_actions = []

        for action in pending_actions:

            if action.get("action_id") == action_id:
                action_to_process = action
            else:
                remaining_actions.append(action)

        if action_to_process is None:
            return {
                "success": False,
                "error": (
                    "Pending action not found. It may already "
                    "have been confirmed or cancelled."
                ),
            }

        account_id = action_to_process.get("account_id")

        if not self._can_access_account(
            user_context=user_context,
            account_id=account_id,
        ):
            return {
                "success": False,
                "error": (
                    "Access denied. You are not authorised "
                    "to confirm this action."
                ),
            }

        # --------------------------------------------------------
        # USER REJECTED ACTION
        # --------------------------------------------------------

        if not confirmed:

            action_to_process[
                "status"
            ] = "CANCELLED"

            action_to_process[
                "confirmation_required"
            ] = False

            action_to_process[
                "confirmed_at"
            ] = datetime.now(timezone.utc).isoformat()

            self._save_actions(
                self.pending_file,
                remaining_actions,
            )

            return {
                "success": True,
                "executed": False,
                "cancelled": True,
                "message": "Action cancelled. No escalation was created.",
                "action": action_to_process,
            }

        # --------------------------------------------------------
        # EXPLICIT USER CONFIRMATION RECEIVED
        # --------------------------------------------------------

        now = datetime.now(timezone.utc).isoformat()

        action_to_process[
            "status"
        ] = "EXECUTED"

        action_to_process[
            "confirmation_required"
        ] = False

        action_to_process[
            "confirmed_at"
        ] = now

        action_to_process[
            "executed_at"
        ] = now

        action_to_process[
            "confirmed_by"
        ] = {
            "username": user_context.get("username"),
            "display_name": user_context.get("display_name"),
            "role": user_context.get("role"),
        }

        # Remove from pending actions.
        self._save_actions(
            self.pending_file,
            remaining_actions,
        )

        # Add to executed actions.
        executed_actions = self._load_actions(
            self.executed_file
        )

        executed_actions.append(
            action_to_process
        )

        self._save_actions(
            self.executed_file,
            executed_actions,
        )

        return {
            "success": True,
            "executed": True,
            "cancelled": False,
            "message": (
                "Escalation confirmed and successfully created."
            ),
            "action": action_to_process,
        }

    # ============================================================
    # LIST EXECUTED ACTIONS
    # ============================================================

    def get_executed_actions(
        self,
        user_context: dict,
    ) -> list[dict]:
        """
        Customers can only see actions belonging to their account.

        Internal users can see all executed actions.
        """

        actions = self._load_actions(
            self.executed_file
        )

        role = user_context.get("role")

        internal_roles = {
            "support",
            "admin",
            "operations",
            "manager",
        }

        if role in internal_roles:
            return actions

        account_id = user_context.get("account_id")

        return [
            action
            for action in actions
            if action.get("account_id") == account_id
        ]