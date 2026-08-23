# ParcelPilot AI Support Agent

An AI-powered support agent built for the ParcelPilot assessment. The application handles customer support queries using structured shipment data, policy documents, account-specific agreements, and controlled state-changing workflows.

## Features

- Order and shipment status lookup
- Cancellation policy handling
- Service credit eligibility checks
- Ticket investigation
- Product known issues lookup
- Account-specific policy and agreement handling
- Source reliability and conflict resolution
- Customer access control
- Escalation workflow
- Explicit confirmation for state-changing actions
- Duplicate action prevention
- Document-based retrieval using AI

## Architecture

```
User
  ↓
Streamlit Frontend
  ↓
FastAPI Backend
  ↓
AgentService
  ├── DataService
  ├── DocumentService
  ├── ActionService
  └── AuthService
       ↓
Structured Data + Policy Documents
       ↓
AI Response / Pending Action
```

The agent separates information retrieval from state-changing actions. Actions such as escalation require explicit confirmation before execution.

```
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

## Tech Stack

- Python
- FastAPI
- Streamlit
- Google Gemini
- LangGraph
- ChromaDB
- Sentence Transformers
- Pandas
- PDFPlumber / PyPDF

## Project Structure

```
Initial-ParcelPilot-AI-Agent-implementation/
│
├── backend/
│   ├── main.py
│   ├── services/
│   ├── data/
│   └── documents/
│
├── frontend/
│   └── app.py
│
├── requirements.txt
├── README.md
└── .env
```

## Setup and Run

**1. Clone the repository**

```bash
git clone https://github.com/rak-shi/Initial-ParcelPilot-AI-Agent-implementation.git
cd Initial-ParcelPilot-AI-Agent-implementation
```

**2. Create a virtual environment**

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure your Gemini API key**

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

> Do not upload the `.env` file or API key to GitHub.

**5. Run the FastAPI backend**

```bash
cd backend
uvicorn main:app --reload
```

The backend will run locally on `http://127.0.0.1:8000`.

**6. Run the Streamlit frontend**

Open another terminal, activate the virtual environment, and run:

```bash
streamlit run frontend/app.py
```

The application will open in your browser.

## Example Queries

Try queries such as:

- `What is the status of order ORD-1001?`
- `Can I cancel order ORD-1001?`
- `Is there a known issue with bulk CSV upload failing for large shipment files?`
- `Am I eligible for a service credit?`
- `Please escalate order ORD-1001.`

After an action is created, explicitly confirm it using:

```
Confirm ACT-XXXX
```

## Source Reliability

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

This ensures that customer-specific agreements can override default policies, while deprecated documents never override current sources.

## Security and Access Control

The application uses user context to prevent cross-account data access. Example contexts include:

- `northstar_customer`
- `lumen_customer`
- `support_agent`

Users can only access data and confirm actions associated with their authorized account.

## Repository

GitHub Repository: [Initial-ParcelPilot-AI-Agent-implementation](https://github.com/rak-shi/Initial-ParcelPilot-AI-Agent-implementation)

## Future Improvements

Possible production improvements include:

- Database-backed action and audit history
- Real authentication and role-based access control
- Hybrid document retrieval and reranking
- Chunk-level source citations
- External carrier API integration
- Conversation memory
- Manager approval workflows
- Monitoring and evaluation

## Assessment Scope

This implementation focuses on demonstrating the core ParcelPilot agent requirements, including document retrieval, structured data handling, access control, source conflict handling, and safe confirmation of state-changing actions.

---

# 4. Architecture Note

## ParcelPilot AI Agent – Architecture

ParcelPilot is a tool-oriented support agent that resolves customer and internal support requests by combining structured business data with policy documentation, rather than relying solely on document retrieval or a raw LLM response.

### 1. Agent Design

The main entry point is:

`AgentService.handle_query(query, user_context)`

The agent handles several categories of requests, including:

- Order status and cancellation queries
- Service credit eligibility
- Ticket investigation
- Product known issues
- Account-specific policy questions
- Escalation requests
- Explicit confirmation of pending actions

The agent follows a controlled workflow:

```
User Query
↓
Authentication / User Context
↓
Intent Detection
↓
Select Required Tools
↓
Structured Data + Document Retrieval
↓
Access Control Validation
↓
Source Ranking / Conflict Resolution
↓
Reasoning and Response Generation
↓
Optional Pending Action
↓
Explicit User Confirmation
↓
Action Execution
```

A key design decision was to separate reading information from performing state-changing actions. For example, when a user asks:

*"Please escalate order ORD-1001 to the support team."*

the system does not immediately execute the escalation. Instead, it creates a pending action and returns an action ID:

```
ACT-XXXX
Status: PENDING_CONFIRMATION
```

The user must explicitly confirm the action:

```
Confirm ACT-XXXX
```

Only then is the escalation executed. This prevents accidental state-changing operations and provides a safer workflow.

### 2. Tool Design

The system is divided into separate services, each responsible for a specific capability.

**AgentService** is the orchestration layer. Its responsibilities include processing natural-language queries, detecting the relevant intent, calling structured-data and document retrieval services, applying account access rules, resolving policy conflicts, and preparing state-changing actions that require explicit confirmation before execution. The agent coordinates the other services rather than putting all logic into a single component.

**DataService** handles structured business data — accounts, orders, tickets, pickup timing, cancellation timing, and account-specific orders and tickets. Supported operations include `get_order()`, `get_order_for_user()`, `get_account()`, `get_account_for_user()`, `get_ticket()`, `get_ticket_for_user()`, `get_pickup_delay_minutes()`, and `get_cancellation_minutes()`. This lets the agent calculate from actual structured data rather than inferring values from documents — for example, the service credit workflow uses scheduled pickup window, actual pickup time, carrier fault, customer fault, shipment fee, and account-specific contract terms.

**DocumentService** retrieves information from ParcelPilot documentation — current support policies, cancellation and service credit SOPs, product operations documentation, known issues, customer-specific agreements, and deprecated policies. For a query like *"Is there a known issue with bulk CSV upload failing for large shipment files?"*, the agent searches the knowledge base and retrieves the relevant documentation — in this dataset, **KI-208 (Bulk Upload failures on large CSVs)**, which explains that some Growth and Enterprise customers see intermittent failures above ~3,000 rows despite a supported limit of 5,000, with a documented workaround of splitting uploads below ~3,000 rows.

**ActionService** handles state-changing operations around a confirmation workflow:

```
Create Action → PENDING_CONFIRMATION → Return Action ID →
User Explicitly Confirms → Validate User Ownership →
Execute Action → Mark as Executed
```

It prevents execution without confirmation, duplicate confirmation, cross-account confirmation, and unauthorized action access — for example, if a Northstar user creates an escalation action, a LumenWorks user cannot confirm it.

**AuthService** provides the user context used for authorization (e.g. `northstar_customer`, `lumen_customer`, `support_agent`), determining which account a user belongs to, whether they're an internal support user, and which orders and tickets they can access. This matters because the agent should never expose one customer's information to another.

### 3. Document and Structured-Data Handling

ParcelPilot uses two types of information. **Structured data** is used for facts requiring precise values — order ID, order status, account ID, ticket status, pickup timestamps, shipment fee, carrier fault, customer fault. For *"What is the status of order ORD-1001?"*, the system retrieves the order directly from the structured dataset rather than searching documents.

**Documents** are used for policies, contracts, procedures, and product knowledge — whether an order can be cancelled, service credit eligibility, cancellation fees, known product issues, applicable support SLAs. This separation avoids using document retrieval for information that should come directly from the database.

The agent combines both sources when necessary. For *"Can I cancel order ORD-1001 without a cancellation fee?"*, it: retrieves ORD-1001, checks its current status, identifies the customer's account, retrieves the account-specific agreement, retrieves the default cancellation policy, applies source precedence, and generates the answer — an example of multi-step reasoning across both structured data and document retrieval.

### 4. Source Reliability and Conflict Handling

Not all documents carry equal authority. The system uses a source reliability model based on scope, authority, current/deprecated status, and account relevance, with a simplified precedence order:

```
Account-Specific Signed Agreement
↓
Current Global Policy / SOP
↓
Current Product Documentation
↓
Deprecated Documentation
```

For example, the Northstar Logistics Enterprise Agreement states Northstar may cancel any BOOKED shipment before pickup without a cancellation fee, while the default ParcelPilot Cancellation & Service Credit SOP normally applies a fee after 30 minutes. Because the Northstar agreement is account-specific and higher authority, the agent uses the contract-specific rule for Northstar:

```
Northstar Agreement > Default Cancellation SOP
```

This lets the agent correctly answer: *"Yes. Northstar Logistics can cancel ORD-1001 without a cancellation fee."* Deprecated sources are given the lowest reliability and never override current policies.

### 5. Major Technical Trade-Offs

**Rule-based intent detection.** I used controlled, keyword-based routing instead of a fully autonomous agent, since the dataset supports a limited, known set of workflows (cancellation, service credits, order lookup, ticket lookup, known issues, escalation, confirmation). This gives more predictable behavior, easier debugging, clearer access control, lower implementation complexity, and reduced risk of unsafe actions. A more autonomous LLM-based planner could be added in a future version.

**In-memory pending actions.** Pending actions are currently managed within the application workflow — sufficient to demonstrate confirmation requirements, action ownership, and duplicate prevention. In production, I would persist pending actions in a database with action ID, user ID, account ID, action type, action payload, status, creation time, expiration time, and audit history.

**Local document retrieval.** The current retrieval approach is suitable for the assessment dataset. A production version would add better semantic embeddings, metadata filtering before retrieval, hybrid keyword + vector search, reranking, chunk-level citations, and document version management.

---

# 5. Product Note

### Additional Client Problem I Chose

Along with answering support questions, I wanted to address the problem of handling actions safely. In a support system, answering a question and performing an action are different things.

For example, if a user asks:

*"Please escalate order ORD-1001 to the support team."*

I did not want the agent to immediately perform the escalation — an action like this could be triggered accidentally or without the user fully intending to proceed.

To handle this, I implemented a simple confirmation flow. When the user requests an escalation, the system creates a pending action with an action ID and marks it as `PENDING_CONFIRMATION`. The action is not executed at this stage. The user must explicitly confirm it using a command such as:

```
Confirm ACT-XXXX
```

Before executing the action, the system checks that the action exists, is still pending, and belongs to the user or account trying to confirm it. Once an action has been executed, it cannot be confirmed again.

I chose this problem because it adds an important safety layer to the agent, and it demonstrates that the agent can handle workflows — not just retrieve information and generate answers.

### What I Would Build Next

If I continued developing ParcelPilot, my first priority would be making the action workflow more production-ready:

1. **Persistent actions and audit history** — store actions in a database (action ID, user, account, action type, status, timestamps, confirmation history) so they remain traceable even if the application restarts.
2. **Better document retrieval and citations** — semantic search, metadata filtering, hybrid keyword + vector search, and reranking, plus precise UI citations linking an answer to the exact section of a policy or agreement, so support users can verify why the agent gave a particular answer.
3. **Real authentication and access control** — replace the predefined user contexts with proper authentication and role-based permissions, since customers should only access their own orders, tickets, and actions while internal support users may need broader role-based access.
4. **Human approval for sensitive actions** — extend the pending-action workflow so high-value service credits, refunds, or contract exceptions require manager review and approval before execution, not just user confirmation.
5. **Conversation context** — session memory so a follow-up like *"What workaround should we recommend?"* after *"Investigate ticket TKT-502"* is understood as referring to that ticket.
6. **Monitoring and evaluation** — track tool usage, failed queries, retrieval quality, incorrect answers, blocked unauthorized access attempts, and user feedback to see where the system needs improvement as usage grows.

### What I Intentionally Left Out

I focused this submission on building and demonstrating the core requirements rather than a complete production system. I intentionally left out:

- Full production authentication
- Database-backed persistent action storage
- External carrier API integration
- Real-time shipment tracking
- Advanced conversation memory
- Manager approval workflows and UI
- Large-scale document ingestion
- Background processing
- Production monitoring infrastructure

These would be useful in a real product, but I chose to focus my time on making the core agent workflow correct — structured data access, document retrieval, source precedence, account-level security, and safe action confirmation.

### Metric I Would Use

The main metric I would use to measure whether ParcelPilot is useful is **Support Resolution Rate** — how many support requests are successfully handled by the agent without requiring unnecessary escalation to a human support representative.

I would also track:

- Accuracy of responses
- Whether the correct sources were used
- Time taken to resolve a request
- Number of unauthorized access attempts correctly blocked
- Successful completion of actions after confirmation
- User feedback

The most important measure, though, is whether ParcelPilot helps users resolve support issues faster while still providing accurate and safe responses.
