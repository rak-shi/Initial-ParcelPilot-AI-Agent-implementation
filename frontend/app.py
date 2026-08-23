import os
import sys

# ============================================================
# ENVIRONMENT SETTINGS
# ============================================================

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# ============================================================
# PATH SETUP
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORTS
# ============================================================

import streamlit as st

# Suppress unnecessary Transformers logs safely.
try:
    from transformers.utils import logging as transformers_logging
    transformers_logging.set_verbosity_error()
except Exception:
    pass

from backend.services.agent_service import AgentService
from backend.services.auth_service import get_user_context


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ParcelPilot AI Support Agent",
    page_icon="📦",
    layout="wide",
)


# ============================================================
# INITIALIZE AGENT
# ============================================================

@st.cache_resource
def get_agent_service():
    return AgentService()


agent_service = get_agent_service()


# ============================================================
# DEMO USERS
# ============================================================

DEMO_USERS = {
    "Northstar Logistics Customer": "northstar_customer",
    "LumenWorks Customer": "lumen_customer",
    "ParcelPilot Support Agent": "support_agent",
}


# ============================================================
# EXAMPLE QUERIES
# ============================================================

EXAMPLE_QUERIES = [
    "Can Northstar cancel ORD-1001 without a cancellation fee? Explain which policy or agreement applies.",
    "ORD-1001 is delayed. Check its status and tell me whether I should receive a service credit based on the applicable terms.",
    "A pickup was three hours late because of carrier fault. Am I eligible for a service credit? Explain your reasoning.",
    "Check whether there is a known issue related to bulk CSV shipment uploads and whether similar support tickets exist.",
    "Investigate ORD-1001, check the relevant policy and account terms, and prepare an escalation if necessary.",
]


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_user" not in st.session_state:
    st.session_state.selected_user = (
        "Northstar Logistics Customer"
    )


# ============================================================
# PROCESS QUERY
# ============================================================

def process_query(query: str):

    if not query or not query.strip():
        return

    selected_username = DEMO_USERS[
        st.session_state.selected_user
    ]

    user_context = get_user_context(
        selected_username
    )

    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": query,
    })

    # --------------------------------------------------------
    # CALL AGENT DIRECTLY
    #
    # NO FASTAPI
    # NO REQUESTS
    # NO http://127.0.0.1:8000
    # --------------------------------------------------------

    try:

        result = agent_service.handle_query(
            query=query,
            user_context=user_context,
        )

        if isinstance(result, dict):

            answer = (
                result.get("answer")
                or result.get("response")
                or result.get("message")
                or result.get("content")
            )

            if answer is None or not str(answer).strip():
                answer = (
                    "I found relevant information but could not "
                    "generate a response."
                )

            st.session_state.messages.append({
                "role": "assistant",
                "content": str(answer),
                "result": result,
            })

        else:

            answer = (
                str(result)
                if result is not None
                else "I could not generate a response."
            )

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "result": None,
            })

    except Exception as error:

        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "⚠️ An error occurred while processing your request:\n\n"
                f"`{str(error)}`"
            ),
            "result": None,
        })


# ============================================================
# DISPLAY RESPONSE DETAILS
# ============================================================

def display_result_details(result):

    if not isinstance(result, dict):
        return

    # --------------------------------------------------------
    # ORDER DETAILS
    # --------------------------------------------------------

    order = result.get("order")

    if order:
        with st.expander("📦 Order Details"):
            st.json(order)

    # --------------------------------------------------------
    # ACCOUNT DETAILS
    # --------------------------------------------------------

    account = result.get("account")

    if account:
        with st.expander("🏢 Account Details"):
            st.json(account)

    # --------------------------------------------------------
    # TICKET DETAILS
    # --------------------------------------------------------

    ticket = result.get("ticket")

    if ticket:
        with st.expander("🎫 Ticket Details"):
            st.json(ticket)

    # --------------------------------------------------------
    # ACTION DETAILS
    # --------------------------------------------------------

    action = result.get("action")

    if action:
        with st.expander("⚙️ Action Details"):
            st.json(action)

    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    sources = result.get("sources") or []

    if sources:

        if not isinstance(sources, list):
            sources = [sources]

        with st.expander(
            f"📚 Sources Used ({len(sources)})"
        ):

            for index, source in enumerate(sources):

                if not isinstance(source, dict):
                    st.write(str(source))
                    if index < len(sources) - 1:
                        st.divider()
                    continue

                source_name = (
                    source.get("source")
                    or source.get("title")
                    or source.get("name")
                    or source.get("document")
                    or "Unknown document"
                )

                page = source.get("page")
                scope = source.get("scope")
                authority = source.get("authority")
                similarity = source.get("similarity")

                st.markdown(f"**{source_name}**")

                if page is not None:
                    st.markdown(
                        f"- Page: {page}"
                    )

                if scope is not None:
                    st.markdown(
                        f"- Scope: `{scope}`"
                    )

                if authority is not None:
                    st.markdown(
                        f"- Authority: {authority}"
                    )

                if similarity is not None:

                    try:
                        similarity_value = float(similarity)

                        st.markdown(
                            f"- Similarity: {similarity_value:.3f}"
                        )

                    except (TypeError, ValueError):

                        st.markdown(
                            f"- Similarity: {similarity}"
                        )

                if index < len(sources) - 1:
                    st.divider()

    # --------------------------------------------------------
    # CONFIRMATION REQUIRED
    # --------------------------------------------------------

    if result.get("confirmation_required"):

        st.warning(
            "⚠️ This action has NOT been executed yet. "
            "Explicit confirmation is required."
        )

        action = result.get("action") or {}
        action_id = action.get("action_id")

        if action_id:

            st.info(
                f"Pending Action ID: `{action_id}`"
            )

            if st.button(
                "Confirm and Execute Action",
                key=f"confirm_{action_id}",
                type="primary",
            ):

                confirmation_query = (
                    f"Confirm {action_id}"
                )

                process_query(
                    confirmation_query
                )

                st.rerun()

    # --------------------------------------------------------
    # ACTION EXECUTED
    # --------------------------------------------------------

    if result.get("executed"):

        st.success(
            "✅ Action executed successfully."
        )

    # --------------------------------------------------------
    # TOOLS USED
    # --------------------------------------------------------

    tools_used = (
        result.get("tools_used")
        or result.get("tools")
        or []
    )

    if tools_used:

        if isinstance(tools_used, list):
            tools_text = " • ".join(
                str(tool)
                for tool in tools_used
            )
        else:
            tools_text = str(tools_used)

        st.caption(
            f"Tools used: {tools_text}"
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("# 📦 ParcelPilot")

    st.caption(
        "AI-Powered Support Agent"
    )

    st.divider()

    # --------------------------------------------------------
    # USER CONTEXT
    # --------------------------------------------------------

    st.subheader("User Context")

    selected_user = st.selectbox(
        "Select demo user",
        options=list(DEMO_USERS.keys()),
        key="selected_user",
    )

    username = DEMO_USERS[selected_user]

    user_context = get_user_context(
        username
    )

    if user_context:

        display_name = user_context.get(
            "display_name",
            username,
        )

        role = str(
            user_context.get("role", "")
        ).lower()

        account_id = user_context.get(
            "account_id"
        )

        if role == "customer":

            st.success(
                f"Logged in as: {display_name}"
            )

            if account_id:

                st.caption(
                    f"Account: **{account_id}**"
                )

        else:

            st.info(
                f"Logged in as: {display_name}"
            )

            st.caption(
                "Internal ParcelPilot support access"
            )

    st.divider()

    # --------------------------------------------------------
    # CLEAR CONVERSATION
    # --------------------------------------------------------

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # EXAMPLE QUERIES
    # --------------------------------------------------------

    st.subheader("Example Queries")

    for index, example_query in enumerate(
        EXAMPLE_QUERIES
    ):

        if st.button(
            example_query,
            key=f"example_query_{index}",
            use_container_width=True,
        ):

            process_query(example_query)

            st.rerun()


# ============================================================
# MAIN PAGE
# ============================================================

st.title(
    "ParcelPilot AI Support Agent"
)

st.caption(
    "Ask about shipments, cancellations, service credits, "
    "tickets, policies, and product issues."
)

st.divider()


# ============================================================
# DISPLAY CONVERSATION
# ============================================================

for message in st.session_state.messages:

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if message["role"] == "user":

        with st.chat_message(
            "user",
            avatar="👩",
        ):

            st.markdown(
                message["content"]
            )

    # --------------------------------------------------------
    # ASSISTANT
    # --------------------------------------------------------

    else:

        with st.chat_message(
            "assistant",
            avatar="🤖",
        ):

            st.markdown(
                message["content"]
            )

            display_result_details(
                message.get("result")
            )


# ============================================================
# CHAT INPUT
# ============================================================

query = st.chat_input(
    "Ask ParcelPilot about an order, ticket, policy or issue..."
)

if query:

    process_query(query)

    st.rerun()