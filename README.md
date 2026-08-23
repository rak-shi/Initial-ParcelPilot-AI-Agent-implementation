# ParcelPilot AI Agent

## AI-powered support and operations assistant for ParcelPilot

ParcelPilot AI Agent is an AI-powered support application designed to help customers and internal support teams answer operational questions using a combination of structured business data and retrieved company documentation.

The system can reason across:

- Shipment and order records
- Customer account information
- Account-specific agreements
- Current support policies
- Cancellation and service-credit SOPs
- Product documentation
- Known issues
- Historical support tickets
- Pending state-changing actions

The project is designed around a key principle:

> **Use structured systems for operational facts, retrieve documents for policy knowledge, apply source precedence when information conflicts, and require explicit confirmation before executing state-changing actions.**

This approach reduces the risk of hallucinated operational information and provides transparency about the sources used to generate an answer.

---

## Repository

**Public GitHub Repository:**

https://github.com/rak-shi/Initial-ParcelPilot-AI-Agent-implementation

---

# Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Key Features](#key-features)
- [Supported User Roles](#supported-user-roles)
- [System Architecture](#system-architecture)
- [Agent Design](#agent-design)
- [Tool Design](#tool-design)
- [Data and Document Handling](#data-and-document-handling)
- [Source Reliability and Conflict Handling](#source-reliability-and-conflict-handling)
- [Security and Access Control](#security-and-access-control)
- [State-Changing Actions and Confirmation](#state-changing-actions-and-confirmation)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Setup Instructions](#setup-instructions)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Streamlit Interface](#streamlit-interface)
- [Example Queries](#example-queries)
- [Testing](#testing)
- [Example Test Scenarios](#example-test-scenarios)
- [Technical Decisions and Trade-offs](#technical-decisions-and-trade-offs)
- [Additional Product Development Ideas](#additional-product-development-ideas)
- [Current Limitations](#current-limitations)
- [Success Metric](#success-metric)
- [AI Tool Usage](#ai-tool-usage)
- [Author](#author)

---

# Project Overview

ParcelPilot is a logistics platform that needs to answer support and operational questions accurately.

A user may ask questions such as:

```text
Can I cancel order ORD-1001 without a cancellation fee?
```

The answer cannot safely be generated from general language-model knowledge alone.

The system may need to determine:

1. Whether the order exists
2. Whether the current user has permission to access it
3. The current shipment status
4. The account associated with the shipment
5. Whether the account has a signed agreement
6. Whether that agreement overrides the default policy
7. What the current policy says
8. Which source has higher authority

Similarly, a user may ask:

```text
Is order ORD-2002 eligible for a service credit because pickup is delayed?
```

The agent must combine structured facts such as:

- Scheduled pickup window
- Actual pickup time
- Carrier fault
- Customer fault
- Shipment fee

with the applicable:

- Service-credit SOP
- Account-specific agreement
- Service-credit caps or exceptions

The goal is therefore not simply to create a chatbot.

The goal is to create an **agent that can select the correct information source, perform controlled data lookup, apply access restrictions, reason across multiple sources, and safely handle actions**.

---

# Problem Statement

Traditional support workflows often require agents to manually search across multiple systems.

For a single customer question, a support employee may need to inspect:

- An order management system
- Account information
- A customer contract
- A support policy
- An operations guide
- Historical support tickets

This creates several problems:

## Fragmented Information

Important information exists across structured databases and unstructured documents.

For example:

- Order status exists in structured operational data.
- Cancellation rules exist in a policy document.
- Customer-specific exceptions exist in an agreement.

A system that searches only documents may miss real-time order facts.

A system that uses only structured data may miss contract exceptions.

---

## Policy Conflicts

A customer-specific agreement may override a general company policy.

For example:

```text
Default cancellation policy:
A cancellation fee may apply after a specified period.

Account-specific agreement:
The customer may cancel any BOOKED shipment before pickup
without a cancellation fee.
```

The agent must recognize that the account-specific agreement has higher relevance for that customer.

---

## Access Control

A customer should not be able to retrieve another customer's operational data.

For example:

```text
Northstar customer -> ORD-1001
```

should be allowed when the order belongs to Northstar.

However:

```text
Northstar customer -> ORD-2001
```

should be denied if that order belongs to LumenWorks.

---

## Unsafe Actions

A request such as:

```text
Please escalate order ORD-1001.
```

should not automatically cause an action to execute without an explicit confirmation step.

The system therefore separates:

```text
Request interpretation
```

from:

```text
Action execution
```

---

# Solution Overview

The solution uses an agent orchestration layer that coordinates multiple specialized services.

```text
                         ┌─────────────────────┐
                         │       User          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Streamlit UI      │
                         │  Chat Interface     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI API      │
                         │    /api/chat        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │        AgentService         │
                    │   Agent Orchestration Layer │
                    └───────┬─────────┬───────────┘
                            │         │
                 ┌──────────┘         └───────────┐
                 ▼                                ▼
      ┌──────────────────┐              ┌──────────────────┐
      │   DataService    │              │ DocumentService  │
      │                  │              │                  │
      │ Orders           │              │ PDF Documents    │
      │ Accounts         │              │ Document Chunks  │
      │ Tickets          │              │ Embeddings       │
      │ Time Calculations│              │ Semantic Search  │
      └────────┬─────────┘              └────────┬─────────┘
               │                                 │
               ▼                                 ▼
      ┌──────────────────┐              ┌──────────────────┐
      │ Structured Data  │              │ Policy Knowledge │
      │ Operational Facts│              │ Contracts        │
      └──────────────────┘              │ Product Guides   │
                                        └──────────────────┘

                            ┌──────────────────┐
                            │  ActionService   │
                            │                  │
                            │ Pending Actions  │
                            │ Confirmation     │
                            │ Execution        │
                            └──────────────────┘
```

---

# Key Features

## 1. Natural-Language Query Handling

Users can ask operational questions in natural language.

Examples:

```text
What is the status of order ORD-2001?
```

```text
Can I cancel order ORD-1001 without a cancellation fee?
```

```text
Is order ORD-2002 eligible for a service credit because pickup is delayed?
```

```text
Investigate ticket TKT-502 and provide the current details.
```

```text
Is there a known issue with bulk CSV upload failing for large shipment files?
```

---

## 2. Structured Order Lookup

The agent can retrieve operational order data.

Examples of structured information include:

- Order ID
- Account ID
- Carrier
- Shipment status
- Booking time
- Pickup window
- Actual pickup time
- Shipment fee
- Carrier fault
- Customer fault
- Cancellation request time
- Operational notes

This information is retrieved from the structured data layer instead of being generated by the language model.

---

## 3. Account Lookup

The agent retrieves account information when required.

Account information may include:

- Account ID
- Account name
- Customer plan
- Account status
- Customer success manager
- Associated contract file
- Premium support status
- Account notes

---

## 4. Ticket Investigation

The agent can retrieve support ticket information.

Example:

```text
Investigate ticket TKT-502 and provide the current details.
```

The response can include relevant information such as:

- Ticket ID
- Current status
- Subject
- Description
- Account association
- Historical context

---

## 5. Document Retrieval

The agent searches relevant documents for policies, agreements, procedures, and product information.

Examples include:

- Current support policy
- Cancellation and service-credit SOP
- Product Operations Guide
- Known issues documentation
- Account-specific agreements

The system retrieves relevant document chunks instead of requiring all document content to be placed directly into the prompt.

---

## 6. Source Transparency

The response includes information about the sources used.

Source metadata may include:

- Document name
- Page number
- Authority
- Similarity score
- Scope

Example:

```text
Source:
05_Northstar_Logistics_Enterprise_Agreement.pdf

Page:
1

Scope:
ACCOUNT

Authority:
100
```

This makes the reasoning process more transparent.

---

## 7. Account-Specific Contract Handling

The agent can retrieve an agreement associated with a customer account.

For example, the Northstar Logistics Enterprise Agreement contains customer-specific cancellation terms.

The agent recognizes that this agreement applies specifically to the Northstar account.

---

## 8. Source Precedence

The system handles conflicts between sources.

A general precedence model is:

```text
Account-specific signed agreement
            ↓
Current company policy / SOP
            ↓
Current product documentation
            ↓
Lower-authority or deprecated documentation
```

A higher-authority, account-specific source should not be ignored simply because another document has a higher semantic similarity score.

---

## 9. Service-Credit Reasoning

The agent combines structured order data with applicable policies.

For example, service-credit eligibility may require evaluation of:

- Pickup delay duration
- Scheduled pickup window
- Actual pickup time
- Carrier responsibility
- Customer-caused issues
- Shipment fee
- Applicable contract terms
- Credit caps

This demonstrates multi-step reasoning across structured and unstructured sources.

---

## 10. Product Known-Issue Lookup

The agent can retrieve information from product documentation.

Example:

```text
Is there a known issue with bulk CSV upload failing for large shipment files?
```

The Product Operations Guide can provide information about:

- Known issue identifiers
- Current issue status
- Affected users
- Product limits
- Workarounds

For example, the application can identify a documented issue involving intermittent bulk-upload failures for larger CSV files while distinguishing that from the officially supported product limit.

---

## 11. Explicit Confirmation for State-Changing Actions

Escalation requests are not executed immediately.

Example:

```text
Please escalate order ORD-1001 to the support team.
```

The agent prepares a pending action.

Example workflow:

```text
User Request
     │
     ▼
Create Pending Action
     │
     ▼
Return Action ID
     │
     ▼
confirmation_required = True
     │
     ▼
User explicitly confirms
     │
     ▼
Execute Action
```

The user must explicitly confirm the action.

Example:

```text
Confirm ACT-XXXX
```

---

## 12. Duplicate Confirmation Prevention

Once an action has been executed, the same action cannot be executed again through repeated confirmation.

This protects against duplicate state-changing operations.

---

## 13. Cross-Account Action Security

A user from one account cannot confirm another account's pending action.

For example:

```text
Northstar user creates pending action
          ↓
Action belongs to Northstar context
          ↓
LumenWorks user tries:
Confirm ACT-XXXX
          ↓
Access denied
```

---

# Supported User Roles

The application currently demonstrates two access patterns.

| User Type | Access |
|---|---|
| Customer | Access restricted to their own account |
| Internal support user | Can access operational data across accounts |

Example users used during testing:

```text
northstar_customer
```

```text
lumen_customer
```

```text
support_agent
```

The authenticated user context contains information such as:

```json
{
  "username": "northstar_customer",
  "display_name": "Northstar Logistics Customer",
  "role": "customer",
  "account_id": "ACCT-001"
}
```

---

# System Architecture

## Frontend Layer

The Streamlit interface provides a chat-based experience.

It supports:

- User selection
- Natural-language questions
- Conversation history
- API communication
- Source display
- Order details
- Account details
- Ticket details
- Action confirmation workflow

---

## API Layer

FastAPI exposes the backend agent through an HTTP API.

The main endpoint is:

```text
POST /api/chat
```

The API receives:

```json
{
  "query": "Can I cancel order ORD-1001 without a cancellation fee?",
  "username": "northstar_customer"
}
```

The API:

1. Validates the request
2. Loads the user context
3. Passes the query to `AgentService`
4. Returns the structured result

---

## Agent Layer

`AgentService` is the central orchestration component.

It coordinates:

- Authentication context
- Intent detection
- Order handling
- Ticket handling
- Document retrieval
- Structured-data lookup
- Policy reasoning
- Contract precedence
- Action confirmation
- Action preparation and execution

---

# Agent Design

The agent follows a controlled routing process.

## Step 1: Validate the Query

The system verifies that a query was provided.

Example error:

```text
Please provide a query.
```

---

## Step 2: Validate User Context

The agent requires authenticated user information.

Without a user context, the system cannot safely perform account-scoped operations.

---

## Step 3: Check Confirmation Requests First

The confirmation check occurs before normal order or ticket routing.

This is important because:

```text
Confirm ACT-123
```

is not an order question.

It is an action confirmation command.

The routing order is conceptually:

```text
Incoming Query
      │
      ▼
Validate Query
      │
      ▼
Validate User Context
      │
      ▼
Is this an Action Confirmation?
      │
      ├── Yes ──► Confirm / Execute Action
      │
      └── No
           │
           ▼
      Is this an Escalation Request?
           │
           ├── Yes ──► Prepare Pending Action
           │
           └── No
                │
                ▼
         Extract Order ID / Ticket ID
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
     Order    Ticket   General
     Query    Query    Query
```

---

## Step 4: Detect Identifiers

The agent detects identifiers such as:

```text
ORD-1001
```

and:

```text
TKT-502
```

These identifiers help route the query to the correct structured-data workflow.

---

## Step 5: Perform Access-Controlled Lookup

Before returning operational information, the agent verifies that the user has permission to access the resource.

For customers:

```text
Order account_id == user account_id
```

must be satisfied.

Internal support users have broader access according to the application's access rules.

---

## Step 6: Retrieve Relevant Documents

The agent searches the document store using the user query and account context.

This allows the system to retrieve:

- Global policies
- Account-specific agreements
- Product documentation

---

## Step 7: Apply Source Precedence

The agent considers:

- Scope
- Authority
- Current/deprecated status
- Account applicability

The highest-similarity result is not automatically treated as the final authority.

---

## Step 8: Generate the Response

The final response can contain:

```text
success
answer
error
order
account
ticket
action
sources
tools_used
confirmation_required
executed
```

---

# Tool Design

## DataService

`DataService` is responsible for structured operational information.

It supports operations such as:

- `get_order`
- `get_order_for_user`
- `get_account`
- `get_account_for_user`
- `get_ticket`
- `get_ticket_for_user`
- `get_account_orders`
- `get_account_tickets`
- `get_pickup_delay_minutes`
- `get_cancellation_minutes`
- `find_account_by_name`
- `is_internal_user`

### Why DataService is Important

Operational facts should come from structured data.

For example:

```text
Current order status
```

should come from the order dataset.

The system should not ask an LLM to guess:

```text
Is the order BOOKED or PICKED_UP?
```

Instead:

```text
AgentService
      ↓
DataService
      ↓
Structured dataset
      ↓
Verified order record
```

---

## SnapshotService

Time-based calculations use the dataset's official snapshot time.

This prevents test results from changing based on the machine's current date and time.

Examples of time-based calculations include:

- Pickup delay duration
- Cancellation timing

The service reads metadata from the dataset README sheet and uses the official snapshot timestamp.

This creates deterministic behavior for the supplied assessment dataset.

---

## DocumentService

`DocumentService` handles document retrieval.

The general process is:

```text
PDF Documents
      │
      ▼
Text Extraction
      │
      ▼
Document Chunking
      │
      ▼
Embedding Generation
      │
      ▼
Vector / Semantic Retrieval
      │
      ▼
Relevant Document Results
```

The project loads document chunks and searches them using semantic similarity.

Returned document metadata includes:

```text
source
page
authority
similarity
scope
```

---

## ActionService

`ActionService` manages state-changing operations.

Actions have a controlled lifecycle.

```text
PREPARED
   │
   ▼
PENDING_CONFIRMATION
   │
   ▼
User confirms
   │
   ▼
EXECUTED
```

The system verifies:

- Action existence
- Action ownership or authorization
- Action status
- Whether the action has already been executed

This prevents accidental or duplicate execution.

---

## AuthService

`AuthService` provides the authenticated user context.

The context is passed into the agent rather than allowing the model to determine user permissions from natural-language text.

This is important because authorization should be enforced by application logic.

Example:

```text
"Please show me another customer's order"
```

does not bypass access control simply because the user asks.

---

# Data and Document Handling

The system intentionally separates two categories of information.

## Structured Data

Structured data is used for operational facts.

Examples:

- Orders
- Accounts
- Tickets
- Pickup timestamps
- Fees
- Statuses
- Fault indicators

### Benefits

- More deterministic
- Easier to validate
- Less hallucination risk
- Supports access control
- Supports exact calculations

---

## Documents

Documents are used for knowledge that is naturally maintained as policies or agreements.

Examples:

- Cancellation policies
- Service-credit rules
- Support policies
- Product guides
- Known issues
- Enterprise agreements

### Benefits

- Policies can change without changing all application code
- Account-specific exceptions can be represented separately
- Retrieved sources can be displayed to users

---

# Source Reliability and Conflict Handling

Retrieval alone is not enough.

A document may be highly semantically relevant but still not be the correct authority.

For example:

```text
Document A:
Highly similar to the query
but deprecated
```

and:

```text
Document B:
Slightly less similar
but current
```

The current document should have greater authority.

Similarly:

```text
Global policy
```

may be overridden by:

```text
Account-specific signed agreement
```

The system therefore considers metadata beyond similarity.

## Source Attributes

### Authority

Represents the source's relative reliability.

Example:

```text
Account agreement -> 100
Current policy -> 90
Current product guide -> 80
Deprecated document -> 0
```

### Scope

Represents where the document applies.

Examples:

```text
ACCOUNT
```

and:

```text
GLOBAL
```

An account-specific source is particularly important when the query concerns that account.

---

## Example Conflict

Default SOP:

```text
A BOOKED shipment may incur a cancellation fee after a specified period.
```

Northstar Agreement:

```text
Northstar may cancel any BOOKED shipment before pickup
with no cancellation fee.
```

For a Northstar order, the agreement takes precedence.

The agent should therefore explain both:

1. The default policy
2. The account-specific exception

and return the appropriate result.

---

# Security and Access Control

Security is enforced in the service layer.

The user context contains:

```text
username
display_name
role
account_id
```

For a customer:

```text
Requested resource account_id
must match
Authenticated user account_id
```

If the accounts do not match, access is denied.

Example:

```text
Northstar Customer
Account: ACCT-001

Attempts to access:
ORD-2001

Order belongs to:
ACCT-002
```

Result:

```text
Access denied.
```

---

## Internal Support Access

An internal support user can access records across accounts according to the application's internal-user rules.

Example:

```text
support_agent
```

can investigate orders or tickets belonging to different accounts.

---

# State-Changing Actions and Confirmation

State-changing actions are treated differently from information requests.

A request such as:

```text
What is the status of ORD-1001?
```

only retrieves information.

However:

```text
Please escalate ORD-1001.
```

can create an operational action.

Therefore the application uses confirmation.

## Phase 1: Prepare

The user requests:

```text
Please escalate order ORD-1001.
```

The system:

- Validates access
- Validates the order
- Creates a pending action
- Generates an action ID
- Returns `confirmation_required = true`

Example:

```json
{
  "success": true,
  "confirmation_required": true,
  "executed": false,
  "action": {
    "action_id": "ACT-XXXX",
    "status": "PENDING_CONFIRMATION"
  }
}
```

---

## Phase 2: Confirm

The user explicitly submits:

```text
Confirm ACT-XXXX
```

The system verifies:

- The action exists
- The user is authorized
- The action is pending
- The action has not already been executed

Only then is it executed.

---

## Phase 3: Prevent Duplicate Confirmation

If the user repeats:

```text
Confirm ACT-XXXX
```

after execution, the action should not execute again.

---

# Project Structure

The project follows a service-oriented structure.

```text
Initial-ParcelPilot-AI-Agent-implementation/
│
├── backend/
│   │
│   ├── services/
│   │   ├── agent_service.py
│   │   ├── data_service.py
│   │   ├── document_service.py
│   │   ├── action_service.py
│   │   ├── auth_service.py
│   │   └── snapshot_service.py
│   │
│   ├── main.py
│   └── config.py
│
├── frontend/
│   └── app.py
│
├── scripts/
│   └── test_agent_service.py
│
├── data/
│   └── assessment datasets and application data
│
├── documents/
│   └── policy and agreement documents
│
├── requirements.txt
├── README.md
└── .gitignore
```

The exact data/document subfolder names may depend on the local project configuration.

---

# Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend and agent implementation |
| FastAPI | REST API |
| Uvicorn | ASGI server |
| Streamlit | Chat-based frontend |
| Pandas | Dataset and Excel handling |
| Sentence Transformers | Text embeddings |
| Hugging Face | Embedding model loading |
| PDF processing libraries | Document text extraction |
| Git | Version control |
| GitHub | Public repository hosting |

---

# Setup Instructions

## Prerequisites

Install:

- Python
- Git
- pip

Verify Python:

```bash
python --version
```

Verify Git:

```bash
git --version
```

---

## 1. Clone the Repository

Clone the project:

```bash
git clone https://github.com/rak-shi/Initial-ParcelPilot-AI-Agent-implementation.git
```

Move into the repository:

```bash
cd Initial-ParcelPilot-AI-Agent-implementation
```

---

## 2. Create a Virtual Environment

Create:

```bash
python -m venv venv
```

---

## 3. Activate the Virtual Environment

### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

The terminal should show:

```text
(venv)
```

before the command prompt.

---

## 4. Install Dependencies

Run:

```bash
pip install -r requirements.txt
```

If required, verify installation:

```bash
pip list
```

---

# Running the Application

The application uses two processes:

1. FastAPI backend
2. Streamlit frontend

The backend must remain running while the Streamlit application sends requests to it.

---

## Run the FastAPI Backend

From the project root:

```bash
uvicorn backend.main:app --reload
```

Expected output will include a local server address similar to:

```text
http://127.0.0.1:8000
```

The API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The root endpoint returns:

```json
{
  "message": "ParcelPilot AI Agent API is running."
}
```

---

## Run the Streamlit Frontend

Open a second terminal.

Move to the project folder:

```powershell
cd D:\projects_vs\ParcelPilot-AI-Agent
```

Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Run Streamlit:

```bash
streamlit run frontend/app.py
```

Streamlit normally provides:

```text
http://localhost:8501
```

Open that address in the browser.

---

# API Documentation

## Root Endpoint

```text
GET /
```

Example response:

```json
{
  "message": "ParcelPilot AI Agent API is running."
}
```

---

## Chat Endpoint

```text
POST /api/chat
```

Example request:

```json
{
  "query": "Can I cancel order ORD-1001 without a cancellation fee?",
  "username": "northstar_customer"
}
```

Example response structure:

```json
{
  "success": true,
  "answer": "Yes. Northstar Logistics can cancel ORD-1001 without a cancellation fee.",
  "error": null,
  "data": null,
  "order": {},
  "account": {},
  "ticket": null,
  "action": null,
  "sources": [],
  "tools_used": [
    "structured_data_lookup",
    "account_lookup",
    "document_search"
  ],
  "confirmation_required": false,
  "executed": false
}
```

---

# Streamlit Interface

The frontend provides a simple chat interface for interacting with the backend agent.

The interface is intended to display:

- User query
- Agent answer
- Conversation history
- Order information
- Account information
- Ticket information
- Retrieved document sources
- Tools used
- Pending actions
- Confirmation requirements

For example, an order answer can display:

```text
Answer

📦 Order Details

🏢 Account Details

📚 Sources Used

Tools used
```

The expandable sections allow the user to inspect supporting operational information without placing all raw data directly into the main answer.

---

# Example Queries

## Northstar Cancellation

Login or select:

```text
northstar_customer
```

Ask:

```text
Can I cancel order ORD-1001 without a cancellation fee?
```

The agent should evaluate:

1. Order status
2. Account identity
3. Northstar agreement
4. Current cancellation SOP
5. Source precedence

The account-specific agreement can override the default cancellation policy.

---

## LumenWorks Service Credit

Login or select:

```text
lumen_customer
```

Ask:

```text
Is order ORD-2002 eligible for a service credit because pickup is delayed?
```

The agent should evaluate:

- Order data
- Pickup delay
- Carrier fault
- Customer fault
- Applicable service-credit policy
- Account-specific terms

---

## Product Known Issue

Ask:

```text
Is there a known issue with bulk CSV upload failing for large shipment files?
```

The agent searches the Product Operations Guide and known-issue information.

The response should identify the relevant documented issue rather than incorrectly returning a cancellation policy as the answer.

---

## Ticket Investigation

Ask:

```text
Investigate ticket TKT-502 and provide the current details.
```

The system retrieves the ticket through structured access and can provide relevant account context.

---

## Cross-Account Access Test

As:

```text
northstar_customer
```

ask:

```text
What is the status of order ORD-2001?
```

Because the order belongs to another account, the request should be denied.

---

## Internal Support Access

As:

```text
support_agent
```

ask:

```text
Can order ORD-2001 be cancelled?
```

The internal support context has broader access than an account-scoped customer context.

---

## Prepare Escalation

Ask:

```text
Please escalate order ORD-1001 to the support team.
```

The agent should prepare an action rather than immediately executing it.

---

## Confirm Escalation

Use the returned action ID:

```text
Confirm ACT-XXXX
```

The action should execute only after explicit confirmation.

---

# Testing

The project includes an agent service test script.

Run:

```bash
python -m scripts.test_agent_service
```

The test suite verifies multiple important behaviors.

---

# Example Test Scenarios

## Test 1: Northstar Cancellation Query

Query:

```text
Can I cancel order ORD-1001 without a cancellation fee?
```

Validates:

- Structured order lookup
- Account lookup
- Document search
- Contract precedence
- Multi-step reasoning

---

## Test 2: LumenWorks Service Credit Query

Query:

```text
Is order ORD-2002 eligible for a service credit because pickup is delayed?
```

Validates:

- Structured data lookup
- Pickup delay calculation
- Snapshot-time handling
- Service-credit reasoning
- Policy and agreement handling

---

## Test 3: Cross-Account Order Access

A Northstar user attempts to access a LumenWorks order.

Expected behavior:

```text
Access denied.
```

Validates account isolation.

---

## Test 4: Internal Support Access

An internal support user accesses another account's order.

Expected behavior:

```text
Access permitted according to internal support rules.
```

---

## Test 5: Product Documentation / Known Issue

Query:

```text
Is there a known issue with bulk CSV upload failing for large shipment files?
```

Validates:

- Document retrieval
- Product documentation lookup
- Known-issue retrieval
- Current source selection

---

## Test 6: Ticket Investigation

Query:

```text
Investigate ticket TKT-502 and provide the current details.
```

Validates:

- Ticket lookup
- Account access
- Ticket context
- Supporting document retrieval

---

## Test 7: Escalation Preparation

Query:

```text
Please escalate order ORD-1001 to the support team.
```

Expected:

```text
confirmation_required = true
executed = false
```

---

## Test 8: Action Confirmation

Query:

```text
Confirm ACT-XXXX
```

Expected:

```text
success = true
executed = true
```

---

## Test 9: Duplicate Confirmation Prevention

The same action is confirmed again.

Expected:

```text
success = false
```

The action must not execute twice.

---

## Test 10: Cross-Account Action Security

A user from another account attempts:

```text
Confirm ACT-XXXX
```

Expected:

```text
Access denied.
```

---

# Technical Decisions and Trade-offs

## Decision 1: Structured Data for Operational Facts

### Choice

Use `DataService` for orders, accounts, and tickets.

### Reason

Operational facts must be reliable.

The system should not rely on a generative model to determine:

```text
Current order status
```

or:

```text
Shipment fee
```

### Trade-off

This requires explicit schemas and service methods.

However, the improved reliability is appropriate for operational workflows.

---

## Decision 2: Retrieval for Policies and Agreements

### Choice

Use document retrieval for unstructured knowledge.

### Reason

Policies and contracts can change independently from application code.

### Trade-off

Retrieval introduces risks such as:

- Irrelevant document results
- Similar but incorrect sources
- Chunking limitations

This is mitigated through source metadata and authority handling.

---

## Decision 3: Source Metadata Beyond Similarity

### Choice

Do not rely only on semantic similarity.

### Reason

A deprecated document may have high similarity.

An account agreement may have lower similarity but greater authority.

### Trade-off

The ranking logic becomes more complex.

However, policy correctness is more important than simply returning the highest embedding score.

---

## Decision 4: Explicit Confirmation

### Choice

Separate action preparation from execution.

### Reason

State-changing actions should have a safety boundary.

### Trade-off

The workflow requires an additional user interaction.

This trade-off is justified because it prevents accidental execution.

---

## Decision 5: Deterministic Snapshot Time

### Choice

Use the dataset's official snapshot timestamp.

### Reason

The supplied dataset represents a specific point in time.

Using the machine clock could make test results change.

### Trade-off

The system is designed for the assessment dataset rather than real-time operational time.

A production version would combine current system time with event timestamps and data freshness controls.

---

# Additional Product Development Ideas

If development continued, I would prioritize the following features.

## Priority 1: Real Carrier Integrations

Integrate carrier APIs and event streams.

The system could retrieve:

- Real-time tracking
- Actual pickup events
- Delivery events
- Carrier delay information
- Exception events

### Why this matters

Some operational status information may lag behind physical carrier events.

Direct integration would improve answer accuracy.

---

## Priority 2: Human Approval Workflow

Introduce approval workflows for sensitive actions.

Examples:

- High-value service credits
- Contract exceptions
- Large customer-impacting actions
- Manual overrides

### Why this matters

Not every operational action should be fully automated.

A human-in-the-loop workflow provides a controlled path for higher-risk decisions.

---

## Priority 3: Persistent Conversation Memory

Add secure conversation memory.

Example:

```text
User:
Can I cancel ORD-1001?

Agent:
...

User:
What about the cancellation fee?
```

The system could understand that the follow-up refers to the previously discussed order.

### Why this matters

It creates a more natural support experience.

Memory must remain:

- Account-scoped
- Session-aware
- Secure
- Expirable

---

## Priority 4: Agent Analytics Dashboard

Create a dashboard for:

- Query volume
- Most common issues
- Escalation rate
- Resolution rate
- Response latency
- Retrieval quality
- Source usage
- User feedback

### Why this matters

The product should be measurable.

Analytics would identify:

- Documentation gaps
- Common product problems
- Agent failure patterns

---

## Priority 5: User Feedback

Add:

```text
👍 Helpful
```

and:

```text
👎 Not Helpful
```

feedback.

Negative feedback could be associated with:

- Query type
- Retrieved sources
- Account type
- Agent route

### Why this matters

This creates a feedback loop for improving the system.

---

## Priority 6: Automated Document Ingestion

Build an ingestion pipeline for new documents.

Workflow:

```text
New Document
      ↓
Validation
      ↓
Metadata Assignment
      ↓
Text Extraction
      ↓
Chunking
      ↓
Embedding
      ↓
Index Update
      ↓
Available to Agent
```

### Why this matters

Policies and product documentation change over time.

Manual ingestion does not scale.

---

## Priority 7: Production Authentication

Replace demonstration username selection with production authentication.

Possible improvements:

- OAuth
- SSO
- JWT-based authentication
- Role-based access control
- Account claims

### Why this matters

Authorization should be based on verified identity.

---

# Current Limitations

This submission focuses on the core requirements and intentionally does not implement a complete production platform.

Current limitations include:

- No production authentication provider
- No real carrier API integration
- No production-grade persistent database architecture
- No persistent multi-session conversation memory
- No advanced human approval dashboard
- No comprehensive monitoring platform
- No automated document ingestion workflow
- No full user-management interface
- Limited deployment and scaling configuration

These were intentionally deprioritized to focus on:

1. Correct agent orchestration
2. Access control
3. Structured-data handling
4. Document retrieval
5. Source reliability
6. Conflict handling
7. Safe action execution

---

# Success Metric

The primary metric I would use is:

> **Percentage of support queries resolved without requiring human escalation while maintaining acceptable answer accuracy.**

This measures whether the product is genuinely useful rather than simply measuring how many responses the model generates.

Additional metrics could include:

| Metric | Purpose |
|---|---|
| Answer accuracy | Measures correctness |
| Self-service resolution rate | Measures support workload reduction |
| Escalation rate | Identifies unresolved issues |
| Incorrect escalation rate | Measures action quality |
| Retrieval relevance | Measures document search quality |
| Source coverage | Measures whether answers are supported |
| User satisfaction | Measures perceived usefulness |
| Response latency | Measures user experience |
| Unauthorized access attempts blocked | Measures security effectiveness |

---

# AI Tool Usage

AI coding assistance was used during development for:

- Understanding implementation approaches
- Python debugging
- Reviewing service integration
- Identifying issues in function parameters
- Debugging structured-data errors
- Improving agent routing
- Designing confirmation handling
- Developing FastAPI integration
- Developing the Streamlit interface
- Creating and reviewing tests
- Drafting project documentation

The generated suggestions were reviewed and adapted to the project implementation.

The final application behavior was tested using the project test scenarios and API responses.

AI assistance was used as a development aid rather than as a replacement for testing or implementation verification.

---

# Major Learning Points

This project demonstrates that an operational AI agent should not be designed as a single prompt that attempts to answer every question.

Different types of information require different handling.

```text
Operational Facts
      ↓
Structured Data Tools
```

```text
Policies and Agreements
      ↓
Document Retrieval
```

```text
Conflicting Sources
      ↓
Authority and Scope Rules
```

```text
State-Changing Requests
      ↓
Confirmation and Authorization
```

The agent orchestration layer connects these capabilities into a controlled workflow.

---

# Future Architecture Direction

A production architecture could evolve toward:

```text
Users
  │
  ▼
Web / Mobile Application
  │
  ▼
API Gateway
  │
  ▼
Authentication / Authorization
  │
  ▼
Agent Orchestrator
  │
  ├──────────────┬──────────────┬───────────────┐
  ▼              ▼              ▼               ▼
Order Tool   Ticket Tool   Document Tool   Action Tool
  │              │              │               │
  ▼              ▼              ▼               ▼
Operational    Support      Vector DB      Workflow /
Database       Database     + Documents    Approval System
                                     
                       │
                       ▼
                  Observability
                       │
                       ▼
              Logs / Metrics / Traces
```

Additional production capabilities would include:

- Rate limiting
- Audit logs
- Role-based permissions
- Tool-level authorization
- Request tracing
- Monitoring
- Retrieval evaluation
- Prompt and response evaluation
- Data retention policies
- Automated testing pipelines

---

# Conclusion

ParcelPilot AI Agent demonstrates a practical approach to building a support agent for an operational environment.

The project combines:

- Natural-language interaction
- Structured-data retrieval
- Account-scoped access control
- Document retrieval
- Contract-aware reasoning
- Source authority handling
- Conflict resolution
- Ticket investigation
- Product known-issue lookup
- Safe state-changing actions
- Explicit confirmation
- Duplicate action prevention
- Cross-account security

The central design decision is to avoid treating the AI model as the source of truth.

Instead, the system retrieves operational facts from structured tools and policy knowledge from relevant documents.

The agent then coordinates these sources and applies application-level rules for authorization, source precedence, and action safety.

This architecture provides a foundation that can be extended with real-time integrations, production authentication, analytics, approval workflows, persistent memory, and automated document ingestion.

---

# Author

**Rakshitha Valipireddy**

GitHub:

https://github.com/rak-shi

Project Repository:

https://github.com/rak-shi/Initial-ParcelPilot-AI-Agent-implementation
