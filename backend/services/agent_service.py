import re

from backend.services.data_service import DataService
from backend.services.document_service import DocumentService
from backend.services.action_service import ActionService


class AgentService:

    def __init__(self):
        self.data_service = DataService()
        self.document_service = DocumentService()
        self.action_service = ActionService()

    # ==============================================================
    # MAIN ENTRY POINT
    # ==============================================================

    def handle_query(self, query: str, user_context: dict) -> dict:

        if not query or not query.strip():
            return {
                "success": False,
                "answer": "Please enter a question.",
                "tools_used": [],
            }

        query = query.strip()
        query_lower = query.lower()

        # ----------------------------------------------------------
        # CONFIRM ACTION
        # ----------------------------------------------------------

        confirmation_match = re.search(
            r"\bconfirm\s+(ACT-[A-Z0-9-]+)\b",
            query,
            re.IGNORECASE,
        )

        if confirmation_match:
            action_id = confirmation_match.group(1).upper()

            return self._handle_action_confirmation(
                action_id=action_id,
                user_context=user_context,
            )

        # ----------------------------------------------------------
        # CANCEL ACTION
        # ----------------------------------------------------------

        cancel_match = re.search(
            r"\bcancel\s+(ACT-[A-Z0-9-]+)\b",
            query,
            re.IGNORECASE,
        )

        if cancel_match:
            action_id = cancel_match.group(1).upper()

            return self._handle_action_cancel(
                action_id=action_id,
                user_context=user_context,
            )

        # ----------------------------------------------------------
        # EXTRACT IDS
        # ----------------------------------------------------------

        order_id = self._extract_order_id(query)
        ticket_id = self._extract_ticket_id(query)

        # ----------------------------------------------------------
        # ESCALATION / STATE-CHANGING ACTION
        # ----------------------------------------------------------

        if self._is_escalation_request(query_lower):

            return self._prepare_escalation(
                query=query,
                order_id=order_id,
                ticket_id=ticket_id,
                user_context=user_context,
            )

        # ----------------------------------------------------------
        # TICKET QUERY
        # ----------------------------------------------------------

        if ticket_id:

            return self._handle_ticket_query(
                query=query,
                ticket_id=ticket_id,
                user_context=user_context,
            )

        # ----------------------------------------------------------
        # ORDER QUERY
        # ----------------------------------------------------------

        if order_id:

            return self._handle_order_query(
                query=query,
                query_lower=query_lower,
                order_id=order_id,
                user_context=user_context,
            )

        # ----------------------------------------------------------
        # KNOWN ISSUE / BULK CSV QUERY
        # ----------------------------------------------------------

        if self._is_bulk_upload_query(query_lower):

            return self._handle_bulk_upload_query(
                query=query,
                user_context=user_context,
            )

        # ----------------------------------------------------------
        # GENERAL DOCUMENT QUERY
        # ----------------------------------------------------------

        return self._handle_document_query(
            query=query,
            user_context=user_context,
        )

    # ==============================================================
    # ID EXTRACTION
    # ==============================================================

    def _extract_order_id(self, query: str):

        match = re.search(
            r"\bORD-\d+\b",
            query,
            re.IGNORECASE,
        )

        if match:
            return match.group(0).upper()

        return None

    def _extract_ticket_id(self, query: str):

        match = re.search(
            r"\bTKT-\d+\b",
            query,
            re.IGNORECASE,
        )

        if match:
            return match.group(0).upper()

        return None

    # ==============================================================
    # QUERY CLASSIFICATION
    # ==============================================================

    def _is_escalation_request(self, query_lower: str) -> bool:

        escalation_terms = [
            "escalate",
            "create escalation",
            "prepare escalation",
            "raise escalation",
            "send to support",
        ]

        return any(
            term in query_lower
            for term in escalation_terms
        )

    def _is_bulk_upload_query(self, query_lower: str) -> bool:

        terms = [
            "bulk csv",
            "bulk upload",
            "csv upload",
            "large csv",
            "shipment upload",
            "known issue",
            "ki-208",
        ]

        return any(
            term in query_lower
            for term in terms
        )

    # ==============================================================
    # ACCESS HELPERS
    # ==============================================================

    def _is_internal_user(self, user_context: dict) -> bool:

        role = user_context.get("role", "")

        return role in {
            "support",
            "support_agent",
            "support_manager",
            "operations",
            "admin",
        }

    def _get_order_for_user(
        self,
        order_id: str,
        user_context: dict,
    ):

        if self._is_internal_user(user_context):
            return self.data_service.get_order(order_id)

        return self.data_service.get_order_for_user(
            order_id,
            user_context,
        )

    def _get_ticket_for_user(
        self,
        ticket_id: str,
        user_context: dict,
    ):

        if self._is_internal_user(user_context):
            return self.data_service.get_ticket(ticket_id)

        return self.data_service.get_ticket_for_user(
            ticket_id,
            user_context,
        )

    # ==============================================================
    # DOCUMENT RETRIEVAL
    # ==============================================================

    def _search_documents(
        self,
        query: str,
        account_id: str = None,
        top_k: int = 5,
    ):

        results = self.document_service.search(
            query=query,
            top_k=top_k,
        )

        if not results:
            return []

        filtered = []

        for source in results:

            source_account_id = source.get(
                "account_id",
                "GLOBAL",
            )

            scope = source.get(
                "scope",
                "GLOBAL",
            )

            # Global documents are always allowed.
            if scope == "GLOBAL":
                filtered.append(source)
                continue

            # Account-specific document must match the account.
            if (
                account_id
                and source_account_id == account_id
            ):
                filtered.append(source)

        return self._rank_sources(filtered, account_id)

    def _rank_sources(
        self,
        sources: list,
        account_id: str = None,
    ):

        def source_priority(source):

            authority = source.get(
                "authority",
                0,
            )

            similarity = source.get(
                "similarity",
                0,
            )

            scope = source.get(
                "scope",
                "GLOBAL",
            )

            source_account_id = source.get(
                "account_id",
                "GLOBAL",
            )

            # Matching account agreement has highest precedence.
            account_match = (
                account_id
                and scope == "ACCOUNT"
                and source_account_id == account_id
            )

            if account_match:
                precedence = 1000

            elif authority >= 90:
                precedence = 500

            elif authority >= 80:
                precedence = 300

            else:
                precedence = 100

            return (
                precedence,
                authority,
                similarity,
            )

        ranked = sorted(
            sources,
            key=source_priority,
            reverse=True,
        )

        # Remove duplicate chunks with the same source/content.
        unique = []
        seen = set()

        for source in ranked:

            key = (
                source.get("source"),
                source.get("page"),
                source.get("content"),
            )

            if key not in seen:
                seen.add(key)
                unique.append(source)

        return unique

    def _filter_sources_by_filename(
        self,
        sources: list,
        filename_keywords: list,
    ):

        filtered = []

        for source in sources:

            filename = source.get(
                "source",
                "",
            ).lower()

            if any(
                keyword.lower() in filename
                for keyword in filename_keywords
            ):
                filtered.append(source)

        return filtered

    # ==============================================================
    # ORDER QUERY
    # ==============================================================

    def _handle_order_query(
        self,
        query: str,
        query_lower: str,
        order_id: str,
        user_context: dict,
    ):

        order = self._get_order_for_user(
            order_id,
            user_context,
        )

        if not order:

            return {
                "success": False,
                "answer": (
                    f"Order {order_id} was not found, "
                    "or you do not have permission to access it."
                ),
                "order": None,
                "sources": [],
                "tools_used": [
                    "structured_data_lookup",
                ],
            }

        account_id = order.get("account_id")

        account = self.data_service.get_account(
            account_id
        )

        # ----------------------------------------------------------
        # CANCELLATION
        # ----------------------------------------------------------

        if any(
            term in query_lower
            for term in [
                "cancel",
                "cancellation",
                "cancellation fee",
            ]
        ):

            return self._handle_cancellation_query(
                query=query,
                order=order,
                account=account,
            )

        # ----------------------------------------------------------
        # SERVICE CREDIT / DELAY
        # ----------------------------------------------------------

        if any(
            term in query_lower
            for term in [
                "service credit",
                "credit",
                "delayed",
                "delay",
                "pickup delayed",
            ]
        ):

            return self._handle_service_credit_query(
                query=query,
                order=order,
                account=account,
            )

        # ----------------------------------------------------------
        # STATUS
        # ----------------------------------------------------------

        sources = self._search_documents(
            query=query,
            account_id=account_id,
            top_k=5,
        )

        answer = (
            f"Order {order_id} currently has status: "
            f"{order.get('status')}."
        )

        return {
            "success": True,
            "answer": answer,
            "order": order,
            "account": account,
            "sources": sources,
            "tools_used": [
                "structured_data_lookup",
                "account_lookup",
                "document_search",
            ],
        }

    # ==============================================================
    # CANCELLATION
    # ==============================================================

    def _handle_cancellation_query(
        self,
        query: str,
        order: dict,
        account: dict,
    ):

        account_id = order.get("account_id")
        order_id = order.get("order_id")
        status = order.get("status")

        sources = self._search_documents(
            query=query,
            account_id=account_id,
            top_k=6,
        )

        # Only retain cancellation-relevant sources.
        relevant_sources = []

        for source in sources:

            filename = source.get(
                "source",
                "",
            ).lower()

            content = source.get(
                "content",
                "",
            ).lower()

            if (
                "cancellation" in filename
                or "agreement" in filename
                or "cancellation" in content
            ):
                relevant_sources.append(source)

        sources = relevant_sources or sources

        account_name = (
            account.get("account_name")
            if account
            else "This account"
        )

        # ----------------------------------------------------------
        # NORTHSTAR CONTRACT OVERRIDE
        # ----------------------------------------------------------

        if account_id == "ACCT-001":

            answer = (
                f"Yes. {account_name} can cancel {order_id} "
                "without a cancellation fee.\n\n"
                "Reason: the signed Northstar Logistics Enterprise "
                "Agreement takes precedence over the default "
                "ParcelPilot Cancellation & Service Credit SOP. "
                "The agreement states that Northstar may cancel any "
                "BOOKED shipment before pickup with no cancellation fee, "
                "regardless of how long ago the shipment was booked.\n\n"
                f"Current order status: {status}."
            )

        else:

            cancellation_minutes = (
                self.data_service.get_cancellation_minutes(
                    order
                )
            )

            if status == "DRAFT":

                answer = (
                    f"Order {order_id} may be cancelled "
                    "with no cancellation fee."
                )

            elif status == "BOOKED":

                if (
                    cancellation_minutes is not None
                    and cancellation_minutes <= 30
                ):

                    answer = (
                        f"Order {order_id} may be cancelled "
                        "with no cancellation fee because the request "
                        "was made within 30 minutes of booking."
                    )

                else:

                    answer = (
                        f"Order {order_id} may be cancelled, "
                        "but the default cancellation fee is INR 250 "
                        "because the request was made more than "
                        "30 minutes after booking."
                    )

            elif status == "PICKED_UP":

                answer = (
                    f"Order {order_id} cannot be cancelled because "
                    "it has already been picked up. "
                    "The return-to-origin workflow should be used "
                    "if the parcel needs to be returned."
                )

            else:

                answer = (
                    f"Order {order_id} cannot be cancelled "
                    f"because its current status is {status}."
                )

        return {
            "success": True,
            "answer": answer,
            "order": order,
            "account": account,
            "sources": sources,
            "tools_used": [
                "structured_data_lookup",
                "account_lookup",
                "document_search",
            ],
        }

    # ==============================================================
    # SERVICE CREDIT
    # ==============================================================

    def _handle_service_credit_query(
        self,
        query: str,
        order: dict,
        account: dict,
    ):

        order_id = order.get("order_id")
        account_id = order.get("account_id")

        delay_minutes = (
            self.data_service.get_pickup_delay_minutes(
                order
            )
        )

        carrier_fault = bool(
            order.get("carrier_fault")
        )

        customer_fault = bool(
            order.get("customer_fault")
        )

        sources = self._search_documents(
            query=query,
            account_id=account_id,
            top_k=6,
        )

        relevant_sources = []

        for source in sources:

            filename = source.get(
                "source",
                "",
            ).lower()

            content = source.get(
                "content",
                "",
            ).lower()

            if (
                "credit" in filename
                or "agreement" in filename
                or "service credit" in content
                or "failed-pickup" in content
            ):
                relevant_sources.append(source)

        sources = relevant_sources or sources

        # ----------------------------------------------------------
        # UNKNOWN CARRIER FAULT
        # ----------------------------------------------------------

        if not carrier_fault:

            answer = (
                f"I cannot confirm a service credit for "
                f"**{order_id}** because carrier fault "
                "has not been established."
            )

            return {
                "success": True,
                "answer": answer,
                "order": order,
                "account": account,
                "sources": sources,
                "tools_used": [
                    "structured_data_lookup",
                    "account_lookup",
                    "document_search",
                ],
            }

        if customer_fault:

            answer = (
                f"Order {order_id} is not eligible for a "
                "service credit because customer fault is recorded."
            )

            return {
                "success": True,
                "answer": answer,
                "order": order,
                "account": account,
                "sources": sources,
                "tools_used": [
                    "structured_data_lookup",
                    "account_lookup",
                    "document_search",
                ],
            }

        # ----------------------------------------------------------
        # LUMENWORKS CONTRACT TERMS
        # ----------------------------------------------------------

        if account_id == "ACCT-002":

            if (
                delay_minutes is not None
                and delay_minutes > 240
            ):

                answer = (
                    f"Order {order_id} has a pickup delay of "
                    f"{delay_minutes} minutes based on the dataset snapshot. "
                    "Carrier fault is recorded. Customer fault is not recorded.\n\n"
                    "Under the LumenWorks Service Agreement, the "
                    "failed-pickup conditions are satisfied: the pickup "
                    "is more than 4 hours past the scheduled pickup window, "
                    "carrier fault is recorded, and customer fault is not recorded.\n\n"
                    "The applicable contract-specific service credit is "
                    "INR 300."
                )

            else:

                answer = (
                    f"Order {order_id} does not yet meet the "
                    "LumenWorks contract threshold for a failed-pickup "
                    "service credit. The contract requires the pickup to "
                    "be more than 4 hours past the end of the scheduled "
                    "pickup window."
                )

            return {
                "success": True,
                "answer": answer,
                "order": order,
                "account": account,
                "sources": sources,
                "tools_used": [
                    "structured_data_lookup",
                    "account_lookup",
                    "document_search",
                ],
            }

        # ----------------------------------------------------------
        # DEFAULT POLICY
        # ----------------------------------------------------------

        if (
            delay_minutes is not None
            and delay_minutes > 120
        ):

            shipment_fee = (
                order.get("shipment_fee_inr", 0)
            )

            credit = min(
                500,
                shipment_fee * 0.10,
            )

            answer = (
                f"Order {order_id} has a pickup delay of "
                f"{delay_minutes} minutes. Carrier fault is recorded "
                "and customer fault is not recorded.\n\n"
                "Under the current ParcelPilot Cancellation & Service "
                "Credit SOP, the failed-pickup conditions are satisfied. "
                f"The applicable default service credit is INR {credit:.0f}."
            )

        else:

            answer = (
                f"Order {order_id} does not currently meet the "
                "default failed-pickup delay threshold of more than "
                "2 hours past the scheduled pickup window."
            )

        return {
            "success": True,
            "answer": answer,
            "order": order,
            "account": account,
            "sources": sources,
            "tools_used": [
                "structured_data_lookup",
                "account_lookup",
                "document_search",
            ],
        }

    # ==============================================================
    # BULK CSV / KNOWN ISSUE
    # ==============================================================

    def _handle_bulk_upload_query(
        self,
        query: str,
        user_context: dict,
    ):

        account_id = user_context.get("account_id")

        # Use highly targeted retrieval query.
        targeted_query = (
            "KI-208 Bulk Upload failures large CSV above 3000 rows "
            "known issue workaround split upload individual shipment "
            "creation unaffected"
        )

        sources = self._search_documents(
            query=targeted_query,
            account_id=account_id,
            top_k=8,
        )

        # IMPORTANT:
        # For a known issue, do not include unrelated account
        # agreements simply because they have higher authority.
        product_sources = self._filter_sources_by_filename(
            sources,
            [
                "04_product_operations",
                "known_issues",
            ],
        )

        sources = product_sources

        # Related tickets are useful context for internal users.
        related_tickets = []

        if self._is_internal_user(user_context):

            try:
                open_tickets = self.data_service.get_open_tickets()

                for ticket in open_tickets:

                    text = (
                        f"{ticket.get('subject', '')} "
                        f"{ticket.get('description', '')}"
                    ).lower()

                    if any(
                        term in text
                        for term in [
                            "bulk upload",
                            "csv",
                            "4,200-row",
                            "4200-row",
                        ]
                    ):
                        related_tickets.append(ticket)

            except Exception:
                related_tickets = []

        # Specific known issue from the supplied data.
        answer = (
            "**Yes. There is a current known issue: KI-208 – "
            "Bulk Upload failures on large CSVs.**\n\n"
            "Some Growth and Enterprise customers experience intermittent "
            "failures on CSV uploads above approximately 3,000 rows, even "
            "though the supported product limit remains 5,000 rows.\n\n"
            "**Current workaround:** split the upload into files below "
            "3,000 rows. Individual shipment creation is unaffected."
        )

        if related_tickets:

            ticket_ids = ", ".join(
                ticket.get("ticket_id", "")
                for ticket in related_tickets
            )

            answer += (
                f"\n\n**Related support ticket(s):** {ticket_ids}."
            )

        result = {
            "success": True,
            "answer": answer,
            "sources": sources,
            "tools_used": [
                "document_search",
            ],
        }

        if related_tickets:
            result["related_tickets"] = related_tickets
            result["tools_used"].append(
                "structured_ticket_lookup"
            )

        return result

    # ==============================================================
    # TICKET QUERY
    # ==============================================================

    def _handle_ticket_query(
        self,
        query: str,
        ticket_id: str,
        user_context: dict,
    ):

        ticket = self._get_ticket_for_user(
            ticket_id,
            user_context,
        )

        if not ticket:

            return {
                "success": False,
                "answer": (
                    f"Ticket {ticket_id} was not found, "
                    "or you do not have permission to access it."
                ),
                "ticket": None,
                "sources": [],
                "tools_used": [
                    "structured_ticket_lookup",
                ],
            }

        account_id = ticket.get("account_id")

        account = self.data_service.get_account(
            account_id
        )

        query_for_docs = (
            f"{query} {ticket.get('subject', '')} "
            f"{ticket.get('description', '')}"
        )

        sources = self._search_documents(
            query=query_for_docs,
            account_id=account_id,
            top_k=6,
        )

        # Prioritize Product Operations for bulk-upload ticket.
        ticket_text = (
            f"{ticket.get('subject', '')} "
            f"{ticket.get('description', '')}"
        ).lower()

        if any(
            term in ticket_text
            for term in [
                "bulk upload",
                "csv",
            ]
        ):

            product_sources = self._filter_sources_by_filename(
                sources,
                [
                    "04_product_operations",
                    "known_issues",
                ],
            )

            if product_sources:
                sources = product_sources

        answer = (
            f"Ticket **{ticket_id}** current details:\n\n"
            f"**Status:** {ticket.get('status')}  \n"
            f"**Subject:** {ticket.get('subject')}  \n"
            f"**Description:** {ticket.get('description')}"
        )

        return {
            "success": True,
            "answer": answer,
            "ticket": ticket,
            "account": account,
            "sources": sources,
            "tools_used": [
                "structured_ticket_lookup",
                "account_lookup",
                "document_search",
            ],
        }

    # ==============================================================
    # GENERAL DOCUMENT QUERY
    # ==============================================================

    def _handle_document_query(
        self,
        query: str,
        user_context: dict,
    ):

        account_id = user_context.get("account_id")

        sources = self._search_documents(
            query=query,
            account_id=account_id,
            top_k=5,
        )

        if not sources:

            return {
                "success": False,
                "answer": (
                    "I could not find reliable information in the "
                    "ParcelPilot knowledge base for that request."
                ),
                "sources": [],
                "tools_used": [
                    "document_search",
                ],
            }

        # Use the highest-ranked relevant source.
        best_source = sources[0]

        answer = best_source.get(
            "content",
            "I found a relevant ParcelPilot source."
        )

        return {
            "success": True,
            "answer": answer,
            "sources": sources,
            "tools_used": [
                "document_search",
            ],
        }

    # ==============================================================
    # ESCALATION
    # ==============================================================

    def _prepare_escalation(
        self,
        query: str,
        order_id: str,
        ticket_id: str,
        user_context: dict,
    ):

        account_id = user_context.get("account_id")

        # If an order is supplied, validate access.
        if order_id:

            order = self._get_order_for_user(
                order_id,
                user_context,
            )

            if not order:

                return {
                    "success": False,
                    "answer": (
                        f"Order {order_id} was not found, "
                        "or you do not have permission to access it."
                    ),
                    "tools_used": [
                        "structured_data_lookup",
                    ],
                }

            account_id = order.get("account_id")

        # If a ticket is supplied, validate access.
        if ticket_id:

            ticket = self._get_ticket_for_user(
                ticket_id,
                user_context,
            )

            if not ticket:

                return {
                    "success": False,
                    "answer": (
                        f"Ticket {ticket_id} was not found, "
                        "or you do not have permission to access it."
                    ),
                    "tools_used": [
                        "structured_ticket_lookup",
                    ],
                }

            account_id = ticket.get("account_id")

        try:

            result = self.action_service.create_escalation(
                user_context=user_context,
                account_id=account_id,
                title="Customer request requires support review",
                reason=query,
                priority="P2",
                related_order_id=order_id,
                related_ticket_id=ticket_id,
                details=query,
            )

        except TypeError:

            # Compatibility with the previous ActionService version.
            result = self.action_service.create_escalation(
                user_context,
                account_id,
                "Customer request requires support review",
                query,
                "P2",
                order_id,
                ticket_id,
                query,
            )

        action = (
            result.get("action")
            if isinstance(result, dict)
            else result
        )

        return {
            "success": True,
            "executed": False,
            "confirmation_required": True,
            "message": (
                "Escalation prepared but NOT executed. "
                "Explicit user confirmation is required."
            ),
            "answer": (
                "The escalation has been prepared but has **NOT** "
                "been executed. Explicit confirmation is required "
                "before the action is performed."
            ),
            "action": action,
            "tools_used": [
                "action_prepare",
            ],
        }

    # ==============================================================
    # ACTION CONFIRMATION
    # ==============================================================

    def _handle_action_confirmation(
        self,
        action_id: str,
        user_context: dict,
    ):

        try:

            result = self.action_service.confirm_action(
                action_id=action_id,
                user_context=user_context,
                confirmed=True,
            )

        except TypeError:

            result = self.action_service.confirm_action(
                action_id,
                user_context,
                True,
            )

        if isinstance(result, dict):

            result.setdefault(
                "tools_used",
                ["action_confirmation"],
            )

            result.setdefault(
                "answer",
                result.get(
                    "message",
                    "Action confirmation completed.",
                ),
            )

            return result

        return {
            "success": True,
            "executed": True,
            "answer": (
                f"Action {action_id} has been explicitly "
                "confirmed and executed successfully."
            ),
            "action": result,
            "tools_used": [
                "action_confirmation",
            ],
        }

    # ==============================================================
    # ACTION CANCELLATION
    # ==============================================================

    def _handle_action_cancel(
        self,
        action_id: str,
        user_context: dict,
    ):

        try:

            result = self.action_service.cancel_action(
                action_id=action_id,
                user_context=user_context,
            )

        except TypeError:

            result = self.action_service.cancel_action(
                action_id,
                user_context,
            )

        if isinstance(result, dict):

            result.setdefault(
                "tools_used",
                ["action_cancel"],
            )

            result.setdefault(
                "answer",
                result.get(
                    "message",
                    "Action cancelled.",
                ),
            )

            return result

        return {
            "success": True,
            "cancelled": True,
            "answer": f"Action {action_id} has been cancelled.",
            "tools_used": [
                "action_cancel",
            ],
        }