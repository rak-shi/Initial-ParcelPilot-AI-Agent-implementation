# ParcelPilot AI Support Agent

An AI-powered support agent designed to help users with shipments, cancellations, service credits, support tickets, policies, customer agreements, and known product issues.

The application combines **AI-based reasoning**, **document retrieval**, **structured data lookup**, and **role-based access control** to provide relevant and transparent support responses.

---

## 🚀 Live Application

Try the deployed application here:

**[ParcelPilot AI Support Agent – Live Demo](https://rak-shi-initial-parcelpilot-ai-agent-impleme-frontendapp-ozarh9.streamlit.app/)**

---

##  Project Overview

ParcelPilot AI Support Agent allows different types of users to ask questions about:

- 📦 Shipment and order status
- ❌ Order cancellations
- 💰 Service credit eligibility
- 🎫 Support tickets
- 📚 Support policies and SOPs
- 📄 Customer-specific agreements
- 🛠️ Product issues and known issues

The agent determines which information sources and tools are required to answer each question, and applies **access restrictions** and **customer-specific agreement precedence** when generating responses.

---

## 🛠️ Key Features

- 🤖 AI-powered support agent
- 👥 Multiple user access levels
- 🔐 Role-based and account-scoped access
- 📦 Order and shipment status lookup
- ❌ Cancellation policy handling
- 💰 Service credit eligibility checks
- 🎫 Support ticket investigation
- 📚 Policy and SOP document retrieval
- 📄 Customer-specific agreement precedence
- 🛠️ Known product issue detection
- 🔍 Source-based, transparent responses (tools + sources shown)
- 🚨 Escalation workflow with explicit confirmation
- 🔁 Duplicate action prevention

---

## 👥 User Access

The application provides three demo users with different access levels, to demonstrate role-based and account-scoped authorization.

### 1. 👤 Northstar Logistics Customer

**Account:** `ACCT-001`
**Access:** Account-scoped customer access.

Can access information related to Northstar Logistics and its authorized orders. Northstar also has an Enterprise Agreement that can override the standard ParcelPilot policy when applicable.

**Example Questions**
- `Can I cancel ORD-1001 without a cancellation fee?`
- `ORD-1001 is delayed. Am I eligible for a service credit?`
- `What is the status of ORD-1001?`
- `Investigate ORD-1001 and check the applicable terms.`

**Example Behavior:** For cancellation questions, the agent checks the order status, the customer's account, the applicable customer agreement, and the standard cancellation policy — applying the agreement's terms if it overrides the general policy.

### 2. 👤 LumenWorks Customer

**Account:** `ACCT-002`
**Access:** Account-scoped customer access.

Can only access LumenWorks orders and account information, and should not be able to access Northstar Logistics orders such as `ORD-1001`.

**Example Questions**
- `What is the status of order ORD-2001?`
- `Can I cancel ORD-2001?`
- `Am I eligible for a service credit for ORD-2002?`
- `Show me the details of ORD-2001.`

**Example Behavior:** The system validates that a requested order belongs to the authorized account before returning any information.

### 3. 🧑‍💻 ParcelPilot Support Agent

**Access:** Internal support access with broader permissions.

Can investigate information across customers, including orders, accounts, support tickets, policies, customer agreements, and known product issues.

**Example Questions**
- `Investigate ORD-1001 and check the relevant policy and account terms.`
- `Investigate ticket TKT-502 and provide the current details.`
- `Is there a known issue with bulk CSV shipment uploads?`
- `Can Northstar cancel ORD-1001 without a cancellation fee?`
- `Check whether there is a known issue related to bulk CSV shipment uploads and whether similar support tickets exist.`

---

## 🎯 Recommended Demo Questions

| Selected User | Question |
|---|---|
| Northstar Logistics Customer | `Can I cancel ORD-1001 without a cancellation fee?` |
| LumenWorks Customer | `What is the status of order ORD-2001?` |
| ParcelPilot Support Agent | `Investigate ticket TKT-502 and provide the current details.` |
| ParcelPilot Support Agent | `Is there a known issue with bulk CSV shipment uploads?` |

These examples demonstrate role-based access control, account-scoped data access, document retrieval, and structured order/ticket lookup.

---

## 🏗️ Solution Architecture

```text
                    ┌───────────────────────┐
                    │      User / Demo      │
                    │ Northstar / Lumen /   │
                    │ ParcelPilot Support   │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Streamlit Frontend  │
                    │                       │
                    │ • User Selection      │
                    │ • Example Queries     │
                    │ • Chat Interface      │
                    │ • Results & Sources   │
                    └───────────┬───────────┘
                                │ API Request
                                ▼
                    ┌───────────────────────┐
                    │    FastAPI Backend    │
                    │                       │
                    │ • Request Handling    │
                    │ • Access Context      │
                    │ • Chat API            │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   ParcelPilot Agent   │
                    │                       │
                    │ • Query Analysis      │
                    │ • Tool Selection      │
                    │ • Policy Reasoning    │
                    │ • Response Generation │
                    └───────────┬───────────┘
                                │
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
    ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
    │ Structured Data│ │ Document Search│ │ Account / Ticket│
    │                │ │                │ │ Lookup         │
    │ • Orders       │ │ • Policies     │ │ • Accounts     │
    │ • Shipments    │ │ • SOPs         │ │ • Tickets      │
    │                │ │ • Agreements   │ │                │
    │                │ │ • Known Issues │ │                │
    └────────────────┘ └────────────────┘ └────────────────┘
```

The agent separates information retrieval from state-changing actions. Actions such as escalation require explicit confirmation before execution:

```text
Request Action
     ↓
Create Pending Action
     ↓
PENDING_CONFIRMATION
     ↓
Confirm ACT-XXXX
     ↓
Validate User and Ownership
     ↓
Execute Action
```

---

## 💻 Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| Language | Python |
| AI Model | Google Gemini |
| Orchestration | LangGraph |
| Vector Store | ChromaDB |
| Embeddings | Sentence Transformers |
| Data Handling | Pandas |
| Document Parsing | PDFPlumber / PyPDF |
| API | REST API |
| Deployment | Streamlit Community Cloud + backend hosting |

---

## 🔑 Key Product and Technical Decisions

- **Access Control:** Customers can access only their own account data; the internal support agent has broader access.
- **Agreement Precedence:** Customer-specific agreements can override standard policies (e.g. Northstar's Enterprise Agreement).
- **Tool-Based Retrieval:** The agent selects order lookup, account lookup, ticket lookup, or document search based on the question.
- **Transparent Responses:** Sources and tools used are displayed alongside answers for explainability.
- **Known Issue Support:** The agent can retrieve product known issues and investigate related support tickets.
- **Safe State Changes:** Escalations and other state-changing actions require explicit user confirmation before execution.

---

## 🚀 Setup and Run Locally

**1. Clone the repository**

```bash
git clone https://github.com/rak-shi/Initial-ParcelPilot-AI-Agent-implementation.git
cd Initial-ParcelPilot-AI-Agent-implementation
```

**2. Create a virtual environment**

```bash
python -m venv venv
```

Activate it — Windows: `venv\Scripts\activate` · Mac/Linux: `source venv/bin/activate`

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure your Gemini API key**

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

> Do not upload the `.env` file or API key to GitHub.

**5. Run the FastAPI backend**

```bash
cd backend
uvicorn main:app --reload
```

The backend runs locally at `http://127.0.0.1:8000`.

**6. Run the Streamlit frontend**

In a new terminal, with the virtual environment active:

```bash
streamlit run frontend/app.py
```

The application opens at `http://localhost:8501`.

---

## 📚 Source Reliability

When multiple documents contain conflicting information, the agent uses the following precedence:

```
Account-Specific Signed Agreement
            ↓
Current Global Policy / SOP
            ↓
Current Product Documentation
            ↓
Deprecated Documentation
```

Customer-specific agreements can override default policies, while deprecated documents never override current sources.

---

## 🔐 Security and Access Control

The application uses user context to prevent cross-account data access. Example contexts:

- `northstar_customer`
- `lumen_customer`
- `support_agent`

Users can only access data and confirm actions associated with their authorized account.

---

## 4. Architecture Note

### ParcelPilot AI Agent – Architecture

ParcelPilot is a tool-oriented support agent that resolves customer and internal support requests by combining structured business data with policy documentation, rather than relying solely on document retrieval or a raw LLM response.

#### 4.1 Agent Design

The main entry point is:

`AgentService.handle_query(query, user_context)`

The agent handles several categories of requests, including order status and cancellation queries, service credit eligibility, ticket investigation, product known issues, account-specific policy questions, escalation requests, and explicit confirmation of pending actions.

The agent follows a controlled workflow:

```
User Query → Authentication / User Context → Intent Detection →
Select Required Tools → Structured Data + Document Retrieval →
Access Control Validation → Source Ranking / Conflict Resolution →
Reasoning and Response Generation → Optional Pending Action →
Explicit User Confirmation → Action Execution
```

A key design decision was to separate reading information from performing state-changing actions. For example, when a user asks *"Please escalate order ORD-1001 to the support team,"* the system does not immediately execute the escalation. Instead, it creates a pending action and returns an action ID:

```
ACT-XXXX
Status: PENDING_CONFIRMATION
```

The user must explicitly confirm it with `Confirm ACT-XXXX` before the escalation executes — preventing accidental state-changing operations.

#### 4.2 Tool Design

- **AgentService** — the orchestration layer. Processes natural-language queries, detects intent, calls structured-data and document retrieval services, applies account access rules, resolves policy conflicts, and prepares state-changing actions requiring explicit confirmation.
- **DataService** — handles structured business data: accounts, orders, tickets, pickup timing, cancellation timing. Supports `get_order()`, `get_order_for_user()`, `get_account()`, `get_account_for_user()`, `get_ticket()`, `get_ticket_for_user()`, `get_pickup_delay_minutes()`, `get_cancellation_minutes()`. This lets the agent calculate from real data (e.g. service credit eligibility from pickup window, actual pickup time, fault attribution, shipment fee, and contract terms) rather than inferring values from documents.
- **DocumentService** — retrieves from ParcelPilot documentation: support policies, cancellation/service credit SOPs, product operations docs, known issues, customer agreements, deprecated policies. For example, a query about bulk CSV upload failures retrieves **KI-208**, explaining intermittent failures above ~3,000 rows (despite a supported limit of 5,000) and the documented workaround of splitting uploads below ~3,000 rows.
- **ActionService** — handles state-changing operations via `Create Action → PENDING_CONFIRMATION → Return Action ID → User Explicitly Confirms → Validate User Ownership → Execute Action → Mark as Executed`. Prevents execution without confirmation, duplicate confirmation, cross-account confirmation, and unauthorized action access.
- **AuthService** — provides user context (`northstar_customer`, `lumen_customer`, `support_agent`) used to determine account membership, internal-user status, and which orders/tickets a user can access.

#### 4.3 Document and Structured-Data Handling

**Structured data** is used for facts requiring precise values — order ID, order status, account ID, ticket status, pickup timestamps, shipment fee, carrier/customer fault. A query like *"What is the status of ORD-1001?"* is answered directly from the structured dataset.

**Documents** are used for policies, contracts, procedures, and product knowledge — cancellation eligibility, service credit eligibility, fees, known issues, SLAs.

The agent combines both when necessary. For *"Can I cancel ORD-1001 without a cancellation fee?"*, it retrieves the order, checks its status, identifies the account, retrieves the account-specific agreement and the default cancellation policy, applies source precedence, and generates the answer.

#### 4.4 Source Reliability and Conflict Handling

```
Account-Specific Signed Agreement → Current Global Policy / SOP →
Current Product Documentation → Deprecated Documentation
```

For example, the Northstar Logistics Enterprise Agreement allows Northstar to cancel any BOOKED shipment before pickup without a fee, while the default SOP normally applies a fee after 30 minutes. Since the Northstar agreement is account-specific and higher authority (`Northstar Agreement > Default Cancellation SOP`), the agent correctly answers: *"Yes. Northstar Logistics can cancel ORD-1001 without a cancellation fee."* Deprecated sources never override current policies.

#### 4.5 Major Technical Trade-Offs

- **Rule-based intent detection** instead of a fully autonomous agent — the dataset supports a limited, known set of workflows, so keyword-based routing gives more predictable behavior, easier debugging, clearer access control, and reduced risk of unsafe actions. A more autonomous LLM-based planner could be added later.
- **In-memory pending actions** — sufficient to demonstrate confirmation, ownership, and duplicate prevention. In production, actions would be persisted in a database with ID, user, account, type, payload, status, timestamps, and audit history.
- **Local document retrieval** — suitable for the assessment dataset. A production version would add better embeddings, metadata filtering, hybrid keyword + vector search, reranking, chunk-level citations, and document version management.

---

## 5. Product Note

### Additional Client Problem I Chose

Along with answering support questions, I addressed the problem of handling actions safely — answering a question and performing an action are different things, and an action like escalation could be triggered accidentally or without full intent.

I implemented a confirmation flow: an escalation request creates a pending action marked `PENDING_CONFIRMATION` rather than executing immediately. The user must explicitly confirm with `Confirm ACT-XXXX`. Before executing, the system checks that the action exists, is still pending, and belongs to the requesting user/account — and once executed, it cannot be confirmed again.

I chose this problem because it adds an important safety layer and shows the agent handling workflows, not just retrieving information.

### What I Would Build Next

1. **Persistent actions and audit history** — store actions in a database (ID, user, account, type, status, timestamps, confirmation history) so they remain traceable across restarts.
2. **Better document retrieval and citations** — semantic search, metadata filtering, hybrid keyword + vector search, reranking, and precise UI citations linking answers to the exact policy/agreement section.
3. **Real authentication and access control** — replace predefined user contexts with proper authentication and role-based permissions.
4. **Human approval for sensitive actions** — extend the workflow so high-value credits, refunds, or contract exceptions require manager review before execution.
5. **Conversation context** — session memory so follow-ups (e.g. *"What workaround should we recommend?"* after investigating a ticket) resolve correctly.
6. **Monitoring and evaluation** — track tool usage, failed queries, retrieval quality, incorrect answers, blocked unauthorized attempts, and user feedback.

### What I Intentionally Left Out

Full production authentication, database-backed persistent action storage, external carrier API integration, real-time shipment tracking, advanced conversation memory, manager approval workflows and UI, large-scale document ingestion, background processing, and production monitoring infrastructure.

These would matter in a real product, but I focused my time on making the core agent workflow correct — structured data access, document retrieval, source precedence, account-level security, and safe action confirmation.

### Metric I Would Use

The main metric is **Support Resolution Rate** — how many support requests are successfully handled by the agent without unnecessary escalation to a human.

I would also track: accuracy of responses, whether the correct sources were used, time taken to resolve a request, unauthorized access attempts correctly blocked, successful completion of actions after confirmation, and user feedback.

The most important measure is whether ParcelPilot helps users resolve issues faster while staying accurate and safe.

---

## 🔗 Links

- **Live Application:** https://rak-shi-initial-parcelpilot-ai-agent-impleme-frontendapp-ozarh9.streamlit.app/
- **GitHub Repository:** https://github.com/rak-shi/Initial-ParcelPilot-AI-Agent-implementation

##  Author

**Rakshitha Valipireddy**
AI/ML-focused developer with experience in Python, FastAPI, Streamlit, machine learning, LLM applications, document retrieval, and AI-powered applications.

##  Conclusion

ParcelPilot AI Support Agent demonstrates how AI can be combined with structured data, document retrieval, customer-specific policies, and access control to build a reliable support system — one that considers who is asking, what they're authorized to access, which tools are needed, which policy or agreement applies, and which sources support the final answer.
