# 📦 ParcelPilot AI Support Agent

An AI-powered support agent designed to help users with shipments, cancellations, service credits, support tickets, policies, customer agreements, and known product issues.

The application combines **AI-based reasoning**, **document retrieval**, **structured data lookup**, and **role-based access control** to provide relevant and transparent support responses.

---

## 🚀 Live Application

Try the deployed application here:

https://rak-shi-initial-parcelpilot-ai-agent-impleme-frontendapp-ozarh9.streamlit.app/

---

## 📌 Project Overview

ParcelPilot AI Support Agent allows different types of users to ask questions about:

- 📦 Shipment and order status
- ❌ Order cancellations
- 💰 Service credit eligibility
- 🎫 Support tickets
- 📚 Support policies and SOPs
- 📄 Customer-specific agreements
- 🛠️ Product issues and known issues

The agent determines the appropriate information sources and tools required to answer each question.

It also applies **access restrictions** and **customer-specific agreement precedence** when generating responses.

---

# 👥 User Access

The application provides three demo users with different access levels.

## 1. 👤 Northstar Logistics Customer

This user represents a customer from **Northstar Logistics**.

### Account

`ACCT-001`

### Access

Account-scoped customer access.

The user can access information related to Northstar Logistics and its authorized orders.

Northstar also has an Enterprise Agreement that can override the standard ParcelPilot policy when applicable.

### Example Questions

- `Can I cancel ORD-1001 without a cancellation fee?`
- `ORD-1001 is delayed. Am I eligible for a service credit?`
- `What is the status of ORD-1001?`
- `Investigate ORD-1001 and check the applicable terms.`

### Example Behavior

For cancellation questions, the AI agent checks:

1. The current order status.
2. The customer's account.
3. The applicable customer agreement.
4. The standard cancellation policy.

If the customer-specific agreement overrides the general policy, the agreement takes precedence.

---

## 2. 👤 LumenWorks Customer

This user represents a customer from **LumenWorks**.

### Account

`ACCT-002`

### Access

Account-scoped customer access.

The user can only access LumenWorks orders and account information.

They should not be able to access Northstar Logistics orders such as `ORD-1001`.

### Example Questions

- `What is the status of order ORD-2001?`
- `Can I cancel ORD-2001?`
- `Am I eligible for a service credit for ORD-2002?`
- `Show me the details of ORD-2001.`

### Example Behavior

The system validates that the requested order belongs to the authorized account before returning information.

For example, a LumenWorks customer should not receive Northstar Logistics order details.

---

## 3. 🧑‍💻 ParcelPilot Support Agent

This represents an internal ParcelPilot support user.

### Access

Internal support access with broader permissions.

The support agent can investigate information across customers, including:

- Orders
- Accounts
- Support tickets
- Policies
- Customer agreements
- Product issues
- Known issues

### Example Questions

- `Investigate ORD-1001 and check the relevant policy and account terms.`
- `Investigate ticket TKT-502 and provide the current details.`
- `Is there a known issue with bulk CSV shipment uploads?`
- `Can Northstar cancel ORD-1001 without a cancellation fee?`
- `Check whether there is a known issue related to bulk CSV shipment uploads and whether similar support tickets exist.`

---

# 🎯 Recommended Demo Questions

| Selected User | Question |
|---|---|
| Northstar Logistics Customer | `Can I cancel ORD-1001 without a cancellation fee?` |
| LumenWorks Customer | `What is the status of order ORD-2001?` |
| ParcelPilot Support Agent | `Investigate ticket TKT-502 and provide the current details.` |
| ParcelPilot Support Agent | `Is there a known issue with bulk CSV shipment uploads?` |

These examples demonstrate the application's different access levels and retrieval capabilities.

---

# 🏗️ Solution Architecture

The application follows the architecture below:

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
---

# 🛠️ Key Features

- 🤖 AI-powered support agent
- 🔐 Role-based and account-scoped access
- 📦 Order and shipment lookup
- 🎫 Support ticket investigation
- 📚 Policy and document retrieval
- 📄 Customer-specific agreement precedence
- 🛠️ Known issue detection
- 🔍 Sources and tools used for transparent responses

---

# 💻 Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| Language | Python |
| AI Model | Gemini |
| API | REST API |
| Document Retrieval | Document Search |
| Data | Structured Order, Account & Ticket Data |

---

# 🔑 Key Product and Technical Decisions

- **Access Control:** Customers can access only their own account data.
- **Agreement Precedence:** Customer-specific agreements can override standard policies.
- **Tool-Based Retrieval:** The agent selects order, account, ticket, or document search based on the query.
- **Transparent Responses:** Sources and tools used are displayed with answers.
- **Known Issue Support:** The agent can retrieve product issues and relevant support information.

---

# 🚀 Live Demo

Try the application here:

https://rak-shi-initial-parcelpilot-ai-agent-impleme-frontendapp-ozarh9.streamlit.app/

---

# 👩‍💻 Author

**Rakshitha Valipireddy**

Built as an AI-powered support agent demonstrating document retrieval, structured data access, access control, and policy-based reasoning.
