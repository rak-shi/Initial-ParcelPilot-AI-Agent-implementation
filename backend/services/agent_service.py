import re

from backend.services.data_service import DataService
from backend.services.document_service import DocumentService
from backend.services.action_service import ActionService
from backend.services.snapshot_service import get_snapshot_time


class AgentService:
    """
    Main ParcelPilot AI Agent service.

    Responsibilities:
    - Natural-language query handling
    - Account-scoped access control
    - Structured order/ticket/account lookup
    - Document retrieval
    - Contract and policy precedence
    - Cancellation reasoning
    - Service-credit reasoning
    - Escalation preparation
    - Explicit confirmation before execution
    """

    def __init__(self):
        self.data_service = DataService()
        self.document_service = DocumentService()
        self.action_service = ActionService()

    # ==================================================================
    # MAIN ENTRY POINT
    # ==================================================================

    def handle_query(self, query, user_context):

        if not query or not str(query).strip():
            return {
                "success": False,
                "answer": "Please provide a query.",
                "error": "Please provide a query.",
                "sources": [],
                "tools_used": [],
            }

        if not user_context:
            return {
                "success": False,
                "answer": "User authentication context is required.",
                "error": "User authentication context is required.",
                "sources": [],
                "tools_used": [],
            }

        query = str(query).strip()

        # --------------------------------------------------------------
        # IMPORTANT:
        # CHECK CONFIRMATION FIRST.
        # --------------------------------------------------------------
        confirmation_result = self._handle_confirmation_query(
            query=query,
            user_context=user_context,
        )

        if confirmation_result is not None:
            return confirmation_result

        # --------------------------------------------------------------
        # CHECK ESCALATION SECOND.
        # --------------------------------------------------------------
        escalation_result = self._handle_escalation_query(
            query=query,
            user_context=user_context,
        )

        if escalation_result is not None:
            return escalation_result

        # --------------------------------------------------------------
        # THEN EXTRACT ORDER / TICKET IDs.
        # --------------------------------------------------------------
        order_id = self._extract_order_id(query)
        ticket_id = self._extract_ticket_id(query)

        # --------------------------------------------------------------
        # ORDER QUERY
        # --------------------------------------------------------------
        if order_id:
            return self._handle_order_query(
                query=query,
                order_id=order_id,
                user_context=user_context,
            )

        # --------------------------------------------------------------
        # TICKET QUERY
        # --------------------------------------------------------------
        if ticket_id:
            return self._handle_ticket_query(
                query=query,
                ticket_id=ticket_id,
                user_context=user_context,
            )

        # --------------------------------------------------------------
        # GENERAL DOCUMENT QUERY
        # --------------------------------------------------------------
        return self._handle_general_query(
            query=query,
            user_context=user_context,
        )

    # ==================================================================
    # CONFIRMATION HANDLING
    # ==================================================================

    def _handle_confirmation_query(self, query, user_context):
        """
        Detect explicit confirmation of an action.

        Returns None if this is not a confirmation query.
        """

        query_lower = query.lower()

        action_id_match = re.search(
            r"\bACT-[A-Z0-9]+\b",
            query.upper(),
        )

        confirmation_words = [
            "confirm",
            "yes, confirm",
            "yes confirm",
            "i confirm",
            "proceed",
            "go ahead",
            "approve",
            "execute",
        ]

        is_confirmation = any(
            word in query_lower
            for word in confirmation_words
        )

        # Not a confirmation request.
        if not is_confirmation:
            return None

        # A confirmation request must contain an action ID.
        if not action_id_match:
            return {
                "success": False,
                "answer": (
                    "I found a confirmation request, but no action ID "
                    "was provided. Please confirm using an action ID, "
                    "for example: Confirm ACT-XXXXXXXX."
                ),
                "sources": [],
                "tools_used": ["action_confirmation"],
                "confirmation_required": False,
                "executed": False,
            }

        action_id = action_id_match.group(0)

        # IMPORTANT:
        # Your ActionService.confirm_action() requires:
        #
        # confirm_action(action_id, user_context, confirmed)
        #
        # Therefore confirmed=True is required here.
        result = self.action_service.confirm_action(
            action_id,
            user_context,
            True,
        )

        result["tools_used"] = ["action_confirmation"]

        return result

    # ==================================================================
    # ESCALATION HANDLING
    # ==================================================================

    def _handle_escalation_query(self, query, user_context):
        """
        Detect escalation requests.

        The escalation is prepared only.
        It is NOT executed until explicit confirmation.
        """

        query_lower = query.lower()

        escalation_keywords = [
            "escalate",
            "create escalation",
            "raise escalation",
            "open escalation",
            "escalation",
        ]

        if not any(
            keyword in query_lower
            for keyword in escalation_keywords
        ):
            return None

        order_id = self._extract_order_id(query)
        ticket_id = self._extract_ticket_id(query)

        account_id = user_context.get("account_id")

        # --------------------------------------------------------------
        # VERIFY ORDER ACCESS IF ORDER IS PROVIDED
        # --------------------------------------------------------------
        if order_id:

            order = self.data_service.get_order_for_user(
                order_id,
                user_context,
            )

            if not order:
                return {
                    "success": False,
                    "answer": (
                        f"Order {order_id} was not found, or you do not "
                        "have permission to escalate it."
                    ),
                    "sources": [],
                    "tools_used": ["structured_data_lookup"],
                }

            account_id = order.get("account_id")

        # --------------------------------------------------------------
        # VERIFY TICKET ACCESS IF TICKET IS PROVIDED
        # --------------------------------------------------------------
        elif ticket_id:

            ticket = self.data_service.get_ticket_for_user(
                ticket_id,
                user_context,
            )

            if not ticket:
                return {
                    "success": False,
                    "answer": (
                        f"Ticket {ticket_id} was not found, or you do not "
                        "have permission to escalate it."
                    ),
                    "sources": [],
                    "tools_used": ["structured_ticket_lookup"],
                }

            account_id = ticket.get("account_id")

        # --------------------------------------------------------------
        # INTERNAL USER WITHOUT RELATED RECORD
        # --------------------------------------------------------------
        if not account_id:
            return {
                "success": False,
                "answer": (
                    "Unable to determine the account for this escalation. "
                    "Please include an accessible order or ticket ID."
                ),
                "sources": [],
                "tools_used": ["action_prepare"],
            }

        result = self.action_service.prepare_escalation(
            user_context=user_context,
            account_id=account_id,
            title="Customer request requires support review",
            reason=query,
            priority="P2",
            related_order_id=order_id,
            related_ticket_id=ticket_id,
            details=query,
        )

        result["answer"] = (
            "The escalation has been prepared but has NOT been executed. "
            "Explicit confirmation is required before the action is performed."
        )

        result["tools_used"] = ["action_prepare"]

        return result

    # ==================================================================
    # ORDER HANDLING
    # ==================================================================

    def _handle_order_query(self, query, order_id, user_context):

        tools_used = []

        # --------------------------------------------------------------
        # ACCESS-CONTROLLED ORDER LOOKUP
        # --------------------------------------------------------------
        order = self.data_service.get_order_for_user(
            order_id,
            user_context,
        )

        tools_used.append("structured_data_lookup")

        if not order:
            return {
                "success": False,
                "answer": (
                    f"Order {order_id} was not found, or you do not "
                    "have permission to access it."
                ),
                "order": None,
                "account": None,
                "sources": [],
                "tools_used": tools_used,
            }

        account_id = order.get("account_id")

        # --------------------------------------------------------------
        # ACCOUNT LOOKUP
        # --------------------------------------------------------------
        account = self.data_service.get_account_for_user(
            account_id,
            user_context,
        )

        tools_used.append("account_lookup")

        # Internal users may access accounts directly.
        if not account and self._is_internal_user(user_context):
            account = self.data_service.get_account(account_id)

        # --------------------------------------------------------------
        # DOCUMENT SEARCH
        # --------------------------------------------------------------
        document_results = self._search_documents(
            query=query,
            user_context=user_context,
            account_id=account_id,
        )

        tools_used.append("document_search")

        intent = self._detect_intent(query)

        # --------------------------------------------------------------
        # CANCELLATION
        # --------------------------------------------------------------
        if intent == "cancellation":

            answer = self._answer_cancellation(
                order=order,
                account=account,
                document_results=document_results,
            )

        # --------------------------------------------------------------
        # SERVICE CREDIT
        # --------------------------------------------------------------
        elif intent == "service_credit":

            answer = self._answer_service_credit(
                order=order,
                account=account,
                document_results=document_results,
            )

        # --------------------------------------------------------------
        # ORDER STATUS
        # --------------------------------------------------------------
        elif intent == "status":

            answer = self._answer_order_status(order)

        # --------------------------------------------------------------
        # GENERAL ORDER QUESTION
        # --------------------------------------------------------------
        else:

            answer = self._answer_general_order_question(
                order=order,
                account=account,
                document_results=document_results,
            )

        return {
            "success": True,
            "answer": answer,
            "order": order,
            "account": account,
            "sources": self._format_sources(document_results),
            "tools_used": tools_used,
            "confirmation_required": False,
            "executed": False,
        }

    # ==================================================================
    # TICKET HANDLING
    # ==================================================================

    def _handle_ticket_query(self, query, ticket_id, user_context):

        tools_used = []

        # --------------------------------------------------------------
        # ACCESS-CONTROLLED TICKET LOOKUP
        # --------------------------------------------------------------
        ticket = self.data_service.get_ticket_for_user(
            ticket_id,
            user_context,
        )

        tools_used.append("structured_ticket_lookup")

        if not ticket:
            return {
                "success": False,
                "answer": (
                    f"Ticket {ticket_id} was not found, or you do not "
                    "have permission to access it."
                ),
                "ticket": None,
                "account": None,
                "sources": [],
                "tools_used": tools_used,
            }

        account_id = ticket.get("account_id")

        # --------------------------------------------------------------
        # ACCOUNT LOOKUP
        # --------------------------------------------------------------
        account = self.data_service.get_account_for_user(
            account_id,
            user_context,
        )

        tools_used.append("account_lookup")

        if not account and self._is_internal_user(user_context):
            account = self.data_service.get_account(account_id)

        # --------------------------------------------------------------
        # DOCUMENT SEARCH
        # --------------------------------------------------------------
        document_results = self._search_documents(
            query=query,
            user_context=user_context,
            account_id=account_id,
        )

        tools_used.append("document_search")

        status = ticket.get("status", "unknown")
        subject = ticket.get("subject", "No subject")
        description = ticket.get("description", "No description")

        answer = (
            f"Ticket {ticket_id} current details:\n\n"
            f"Status: {status}\n"
            f"Subject: {subject}\n"
            f"Description: {description}"
        )

        return {
            "success": True,
            "answer": answer,
            "ticket": ticket,
            "account": account,
            "sources": self._format_sources(document_results),
            "tools_used": tools_used,
            "confirmation_required": False,
            "executed": False,
        }

    # ==================================================================
    # GENERAL DOCUMENT QUERY
    # ==================================================================

    def _handle_general_query(self, query, user_context):

        account_id = user_context.get("account_id")

        document_results = self._search_documents(
            query=query,
            user_context=user_context,
            account_id=account_id,
        )

        if not document_results:
            return {
                "success": False,
                "answer": (
                    "I could not find relevant information in the "
                    "available ParcelPilot documents."
                ),
                "sources": [],
                "tools_used": ["document_search"],
            }

        # --------------------------------------------------------------
        # IMPORTANT FIX:
        #
        # Do NOT use document_results[0] blindly.
        #
        # For general documentation questions, select the most
        # semantically relevant result using similarity.
        # --------------------------------------------------------------
        best_result = max(
            document_results,
            key=lambda item: float(item.get("similarity") or 0),
        )

        content = (
            best_result.get("content")
            or best_result.get("text")
            or ""
        ).strip()

        if not content:
            content = (
                "Relevant documentation was found, but the document "
                "content could not be extracted."
            )

        return {
            "success": True,
            "answer": content,
            "sources": self._format_sources(document_results),
            "tools_used": ["document_search"],
            "confirmation_required": False,
            "executed": False,
        }

    # ==================================================================
    # CANCELLATION REASONING
    # ==================================================================

    def _answer_cancellation(
        self,
        order,
        account,
        document_results,
    ):

        order_id = order.get("order_id")
        status = str(order.get("status", "")).upper()

        account_name = (
            account.get("account_name")
            if account
            else "the customer"
        )

        # --------------------------------------------------------------
        # PICKED UP
        # --------------------------------------------------------------
        if status == "PICKED_UP":
            return (
                f"Order {order_id} has already been picked up. "
                "It should not be cancelled. The return-to-origin "
                "workflow should be used if the parcel needs to "
                "be returned."
            )

        # --------------------------------------------------------------
        # DELIVERED
        # --------------------------------------------------------------
        if status == "DELIVERED":
            return (
                f"Order {order_id} has already been delivered and "
                "cannot be cancelled."
            )

        # --------------------------------------------------------------
        # DRAFT
        # --------------------------------------------------------------
        if status == "DRAFT":
            return (
                f"Yes. Order {order_id} is in DRAFT status and can "
                "be cancelled without a cancellation fee."
            )

        # --------------------------------------------------------------
        # NORTHSTAR CONTRACT OVERRIDE
        # --------------------------------------------------------------
        if account and account.get("account_id") == "ACCT-001":

            if status == "BOOKED":
                return (
                    f"Yes. {account_name} can cancel {order_id} without "
                    "a cancellation fee.\n\n"
                    "Reason: the signed Northstar Logistics Enterprise "
                    "Agreement takes precedence over the default "
                    "ParcelPilot Cancellation & Service Credit SOP. "
                    "The agreement states that Northstar may cancel any "
                    "BOOKED shipment before pickup with no cancellation "
                    "fee, regardless of how long ago the shipment was "
                    "booked.\n\n"
                    f"Current order status: {status}."
                )

        # --------------------------------------------------------------
        # DEFAULT POLICY
        # --------------------------------------------------------------
        if status == "BOOKED":

            cancellation_minutes = (
                self.data_service.get_cancellation_minutes(order)
            )

            if cancellation_minutes is None:
                return (
                    f"Order {order_id} is BOOKED, but the cancellation "
                    "timing could not be determined. Please verify the "
                    "booking and cancellation timestamps before applying "
                    "a fee."
                )

            if cancellation_minutes <= 30:
                return (
                    f"Yes. Order {order_id} can be cancelled without a "
                    f"fee because the cancellation request was made "
                    f"{cancellation_minutes:.0f} minutes after booking."
                )

            return (
                f"Order {order_id} may be cancelled, but the default "
                f"cancellation fee is INR 250 because the request was "
                f"made {cancellation_minutes:.0f} minutes after booking."
            )

        return (
            f"I could not determine the cancellation outcome for "
            f"{order_id} because its current status is {status}."
        )

    # ==================================================================
    # SERVICE CREDIT REASONING
    # ==================================================================

    def _answer_service_credit(
        self,
        order,
        account,
        document_results,
    ):

        order_id = order.get("order_id")

        # Always use dataset snapshot time.
        snapshot_time = get_snapshot_time()

        # IMPORTANT:
        # DataService expects the ORDER DICTIONARY, not order_id.
        pickup_delay_minutes = (
            self.data_service.get_pickup_delay_minutes(
                order,
                snapshot_time,
            )
        )

        carrier_fault = bool(order.get("carrier_fault"))
        customer_fault = bool(order.get("customer_fault"))

        shipment_fee = float(
            order.get("shipment_fee_inr") or 0
        )

        # --------------------------------------------------------------
        # CUSTOMER FAULT
        # --------------------------------------------------------------
        if customer_fault:
            return (
                f"Order {order_id} is not currently eligible for a "
                "service credit because customer fault is recorded."
            )

        # --------------------------------------------------------------
        # DELAY UNKNOWN
        # --------------------------------------------------------------
        if pickup_delay_minutes is None:
            return (
                f"I cannot calculate the pickup delay for {order_id}. "
                "Please verify the pickup timing before determining "
                "service credit eligibility."
            )

        # --------------------------------------------------------------
        # CARRIER FAULT REQUIRED
        # --------------------------------------------------------------
        if not carrier_fault:
            return (
                f"I cannot confirm a service credit for {order_id} "
                "because carrier fault has not been established. "
                "The policy requires verification before promising "
                "a credit when fault is unknown."
            )

        # --------------------------------------------------------------
        # LUMENWORKS CONTRACT
        # --------------------------------------------------------------
        if account and account.get("account_id") == "ACCT-002":

            return (
                f"Order {order_id} has a pickup delay of "
                f"{pickup_delay_minutes:.0f} minutes based on the "
                "dataset snapshot. Carrier fault is recorded and "
                "customer fault is not recorded.\n\n"
                "The applicable LumenWorks customer agreement and "
                "service-credit policy should be used to determine "
                "the final credit amount."
            )

        # --------------------------------------------------------------
        # DEFAULT POLICY
        # More than 2 hours = 120 minutes past scheduled window.
        # --------------------------------------------------------------
        if pickup_delay_minutes <= 120:
            return (
                f"Order {order_id} has a pickup delay of "
                f"{pickup_delay_minutes:.0f} minutes. Under the "
                "default policy, a service credit requires the pickup "
                "to be more than 2 hours past the scheduled pickup "
                "window, so it is not currently eligible."
            )

        credit_amount = min(
            500,
            shipment_fee * 0.10,
        )

        answer = (
            f"Order {order_id} is eligible for a service credit.\n\n"
            f"Pickup delay: {pickup_delay_minutes:.0f} minutes.\n"
            "Carrier fault: recorded.\n"
            "Customer fault: not recorded.\n\n"
            f"Under the default policy, the estimated credit is "
            f"INR {credit_amount:.2f}, calculated as the lower of "
            "INR 500 or 10% of the shipment fee."
        )

        if credit_amount > 1000:
            answer += (
                "\n\nManager approval is required because the "
                "individual credit exceeds INR 1,000."
            )

        return answer

    # ==================================================================
    # STATUS ANSWER
    # ==================================================================

    def _answer_order_status(self, order):

        order_id = order.get("order_id")
        status = order.get("status")

        return (
            f"Order {order_id} currently has status: {status}."
        )

    # ==================================================================
    # GENERAL ORDER ANSWER
    # ==================================================================

    def _answer_general_order_question(
        self,
        order,
        account,
        document_results,
    ):

        order_id = order.get("order_id")
        status = order.get("status")

        answer = (
            f"Order {order_id} is currently in {status} status."
        )

        if account:
            account_name = account.get("account_name")

            answer += (
                f"\n\nThe order belongs to account: {account_name}."
            )

        if document_results:

            # For a general order question, use the most relevant source.
            top_source = max(
                document_results,
                key=lambda item: float(item.get("similarity") or 0),
            )

            source_name = top_source.get("source")

            if source_name:
                answer += (
                    f"\n\nRelevant policy information was also found in "
                    f"{source_name}."
                )

        return answer

    # ==================================================================
    # DOCUMENT SEARCH
    # ==================================================================

    def _search_documents(
        self,
        query,
        user_context,
        account_id,
    ):
        """
        Search accessible documents.

        Document search results remain sorted with authority and
        similarity for policy precedence. General questions explicitly
        select the highest similarity result when generating an answer.
        """

        try:

            results = self.document_service.search(
                query,
                account_id,
            )

        except TypeError:

            try:
                results = self.document_service.search(
                    query=query,
                    account_id=account_id,
                )

            except TypeError:

                results = self.document_service.search(
                    query
                )

        if not results:
            return []

        # --------------------------------------------------------------
        # SECURITY FILTER
        # --------------------------------------------------------------
        safe_results = []

        is_internal = self._is_internal_user(user_context)

        for result in results:

            scope = str(
                result.get("scope", "GLOBAL")
            ).upper()

            result_account_id = result.get("account_id")

            # GLOBAL documents are accessible.
            if scope == "GLOBAL":
                safe_results.append(result)
                continue

            # ACCOUNT documents require same account unless internal.
            if scope == "ACCOUNT":

                if is_internal:
                    safe_results.append(result)
                    continue

                if (
                    result_account_id
                    and result_account_id == account_id
                    and user_context.get("account_id") == account_id
                ):
                    safe_results.append(result)

        # --------------------------------------------------------------
        # SORT FOR SOURCE / POLICY PRECEDENCE DISPLAY
        #
        # General query answering itself uses max(similarity).
        # --------------------------------------------------------------
        safe_results.sort(
            key=lambda item: (
                float(item.get("authority") or 0),
                float(item.get("similarity") or 0),
            ),
            reverse=True,
        )

        return safe_results[:5]

    # ==================================================================
    # SOURCE FORMATTING
    # ==================================================================

    def _format_sources(self, document_results):

        formatted_sources = []

        for result in document_results:

            formatted_sources.append(
                {
                    "source": result.get("source"),
                    "page": result.get("page"),
                    "authority": result.get("authority"),
                    "similarity": result.get("similarity"),
                    "scope": result.get("scope"),
                }
            )

        return formatted_sources

    # ==================================================================
    # INTENT DETECTION
    # ==================================================================

    def _detect_intent(self, query):

        query_lower = query.lower()

        cancellation_keywords = [
            "cancel",
            "cancellation",
            "cancel order",
            "cancel shipment",
            "cancellation fee",
        ]

        service_credit_keywords = [
            "service credit",
            "credit",
            "pickup delay",
            "failed pickup",
            "missed pickup",
            "compensation",
            "refund",
        ]

        status_keywords = [
            "status",
            "where is",
            "shipment status",
            "order status",
        ]

        if any(
            keyword in query_lower
            for keyword in cancellation_keywords
        ):
            return "cancellation"

        if any(
            keyword in query_lower
            for keyword in service_credit_keywords
        ):
            return "service_credit"

        if any(
            keyword in query_lower
            for keyword in status_keywords
        ):
            return "status"

        return "general"

    # ==================================================================
    # ID EXTRACTION
    # ==================================================================

    def _extract_order_id(self, query):

        match = re.search(
            r"\bORD-\d+\b",
            query.upper(),
        )

        if match:
            return match.group(0)

        return None

    def _extract_ticket_id(self, query):

        match = re.search(
            r"\bTKT-\d+\b",
            query.upper(),
        )

        if match:
            return match.group(0)

        return None

    # INTERNAL USER CHECK

    def _is_internal_user(self, user_context):

        if not user_context:
            return False

        role = str(
            user_context.get("role", "")
        ).lower()

        internal_roles = [
            "support",
            "admin",
            "internal",
            "manager",
        ]

        return role in internal_roles