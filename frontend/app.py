import streamlit as st
import requests


# ==============================================================
# CONFIGURATION
# ==============================================================

API_URL = "http://127.0.0.1:8000/api/chat"

st.set_page_config(
    page_title="ParcelPilot AI Agent",
    page_icon="📦",
    layout="wide",
)


# ==============================================================
# SESSION STATE
# ==============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "username" not in st.session_state:
    st.session_state.username = "northstar_customer"


# ==============================================================
# SIDEBAR
# ==============================================================

with st.sidebar:

    st.title("📦 ParcelPilot")

    st.caption("AI-Powered Support Agent")

    st.divider()

    st.subheader("User Access")

    username = st.selectbox(
        "Select user",
        options=[
            "northstar_customer",
            "lumen_customer",
            "support_agent",
        ],
        index=[
            "northstar_customer",
            "lumen_customer",
            "support_agent",
        ].index(st.session_state.username),
    )

    st.session_state.username = username

    user_labels = {
        "northstar_customer": "Northstar Logistics Customer",
        "lumen_customer": "LumenWorks Customer",
        "support_agent": "ParcelPilot Support Agent",
    }

    st.success(f"Logged in as: {user_labels[username]}")

    st.divider()

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.subheader("Try asking")

    example_questions = [
        "Can I cancel order ORD-1001 without a cancellation fee?",
        "Is order ORD-2002 eligible for a service credit because pickup is delayed?",
        "What is the status of order ORD-2001?",
        "Is there a known issue with bulk CSV upload failing for large shipment files?",
        "Investigate ticket TKT-502 and provide the current details.",
    ]

    for question in example_questions:

        if st.button(
            question,
            key=f"example_{question}",
            use_container_width=True,
        ):
            st.session_state.pending_question = question
            st.rerun()


# ==============================================================
# MAIN HEADER
# ==============================================================

st.title("ParcelPilot AI Support Agent")

st.caption(
    "Ask about shipments, cancellations, service credits, "
    "tickets, policies, and product issues."
)

st.divider()


# ==============================================================
# API FUNCTION
# ==============================================================

def call_agent(query, username):

    payload = {
        "query": query,
        "username": username,
    }

    try:

        response = requests.post(
            API_URL,
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "error": (
                "Cannot connect to the ParcelPilot API. "
                "Make sure FastAPI is running at "
                "http://127.0.0.1:8000"
            ),
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "The AI Agent request timed out.",
        }

    except requests.exceptions.RequestException as error:

        return {
            "success": False,
            "error": f"API error: {str(error)}",
        }


# ==============================================================
# RESPONSE DISPLAY
# ==============================================================

def display_response(result):

    if not result.get("success"):

        st.error(
            result.get(
                "error",
                result.get(
                    "answer",
                    "The request could not be completed."
                ),
            )
        )

        return

    # ----------------------------------------------------------
    # MAIN ANSWER
    # ----------------------------------------------------------

    answer = result.get("answer")

    if answer:
        st.markdown(answer)

    # ----------------------------------------------------------
    # CONFIRMATION REQUIRED
    # ----------------------------------------------------------

    if result.get("confirmation_required"):

        action = result.get("action") or {}

        action_id = action.get("action_id")

        st.warning(
            "⚠️ This action has NOT been executed yet. "
            "Explicit confirmation is required."
        )

        if action_id:

            st.info(
                f"Pending Action ID: `{action_id}`"
            )

            if st.button(
                "Confirm and Execute Action",
                key=f"confirm_{action_id}",
                type="primary",
            ):

                confirm_query = f"Confirm {action_id}"

                with st.spinner(
                    "Confirming action..."
                ):

                    confirmation_result = call_agent(
                        query=confirm_query,
                        username=st.session_state.username,
                    )

                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": confirm_query,
                    }
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": confirmation_result,
                    }
                )

                st.rerun()

    # ----------------------------------------------------------
    # ACTION EXECUTED
    # ----------------------------------------------------------

    if result.get("executed"):

        st.success(
            "✅ Action executed successfully."
        )

    # ----------------------------------------------------------
    # ORDER DETAILS
    # ----------------------------------------------------------

    order = result.get("order")

    if order:

        with st.expander("📦 Order Details"):

            st.json(order)

    # ----------------------------------------------------------
    # ACCOUNT DETAILS
    # ----------------------------------------------------------

    account = result.get("account")

    if account:

        with st.expander("🏢 Account Details"):

            st.json(account)

    # ----------------------------------------------------------
    # TICKET DETAILS
    # ----------------------------------------------------------

    ticket = result.get("ticket")

    if ticket:

        with st.expander("🎫 Ticket Details"):

            st.json(ticket)

    # ----------------------------------------------------------
    # ACTION DETAILS
    # ----------------------------------------------------------

    action = result.get("action")

    if action:

        with st.expander("⚙️ Action Details"):

            st.json(action)

    # ----------------------------------------------------------
    # SOURCES
    # ----------------------------------------------------------

    sources = result.get("sources", [])

    if sources:

        with st.expander(
            f"📚 Sources Used ({len(sources)})"
        ):

            for source in sources:

                source_name = source.get(
                    "source",
                    "Unknown document",
                )

                page = source.get(
                    "page",
                    "N/A",
                )

                scope = source.get(
                    "scope",
                    "GLOBAL",
                )

                authority = source.get(
                    "authority",
                    "N/A",
                )

                similarity = source.get(
                    "similarity",
                    0,
                )

                st.markdown(
                    f"""
**{source_name}**

- Page: {page}
- Scope: `{scope}`
- Authority: {authority}
- Similarity: {similarity:.3f}

---
"""
                )

    # ----------------------------------------------------------
    # TOOLS USED
    # ----------------------------------------------------------

    tools_used = result.get("tools_used", [])

    if tools_used:

        st.caption(
            "Tools used: "
            + " • ".join(tools_used)
        )


# ==============================================================
# DISPLAY CHAT HISTORY
# ==============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "user":

            st.markdown(message["content"])

        else:

            display_response(message["content"])


# ==============================================================
# GET USER INPUT
# ==============================================================

user_query = None


# Example question clicked from sidebar
if "pending_question" in st.session_state:

    user_query = st.session_state.pending_question

    del st.session_state.pending_question


# Normal chat input
chat_input = st.chat_input(
    "Ask ParcelPilot about an order, ticket, policy or issue..."
)

if chat_input:

    user_query = chat_input


# ==============================================================
# PROCESS QUERY
# ==============================================================

if user_query:

    # ----------------------------------------------------------
    # SHOW USER MESSAGE
    # ----------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )

    with st.chat_message("user"):

        st.markdown(user_query)

    # ----------------------------------------------------------
    # CALL API
    # ----------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "ParcelPilot AI Agent is thinking..."
        ):

            result = call_agent(
                query=user_query,
                username=st.session_state.username,
            )

        display_response(result)

    # ----------------------------------------------------------
    # SAVE RESPONSE
    # ----------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result,
        }
    )