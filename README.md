FilingDay — AI-Powered GST Assistant
FilingDay is a proposed AI-powered assistant for Chartered Accountant (CA) firms that helps staff find answers to GST-related questions quickly using official tax documents. It is designed to reduce repetitive research, provide source-cited answers, and support high traffic during GST filing deadlines.
Project status: Project concept / implementation plan. Update the technology stack, setup commands, and performance results to match the actual codebase before publishing.

Table of Contents
- Problem Statement
- Objectives
- Key Features
- Knowledge Sources
- How It Works
- Proposed Architecture
- Technology Stack
- Getting Started
- Example Questions
- Performance Goals
- Security and Reliability
- Limitations
- Future Enhancements
- Official Resources
Problem Statement
CA firms handle GST compliance for multiple clients. During filing deadlines, staff often need to answer repeated questions about tax rates, notifications, input tax credit (ITC), late fees, and return-filing rules.

Manually searching through large collections of Acts, Rules, circulars, and notifications is time-consuming. Traffic can also increase sharply on deadline days, making fast and reliable access to information important.

FilingDay aims to address these challenges through document retrieval, AI-generated answers with citations, caching, and a human-approved email workflow.
Objectives
- Answer common GST questions in plain language.
- Ground answers in official documents and provide citations.
- Reduce repeated processing through exact-match and semantic caching.
- Surface frequently asked questions during filing deadlines.
- Draft client replies and invoice reminders for CA review.
- Test latency and reliability under increased traffic.
Key Features
1. GST Question Answering
Users ask questions in natural language. The system retrieves relevant passages from its indexed GST knowledge base and uses them to draft an answer with source references.
2. Official Document Knowledge Base
The planned knowledge base includes:
- Central GST notifications
- GST rate notifications
- Integrated GST (IGST) notifications
- GST circulars
- Central Goods and Services Tax (CGST) Act
- CGST Rules
The initial scope targets 3,000+ pages of source material. Documents should be parsed, indexed, versioned, and checked for amendments and effective dates.
3. Redis Caching
- Exact-match cache: Reuses an answer for an identical normalized question.
- Semantic cache: Finds questions with sufficiently similar meaning and may reuse a previously generated answer.
- Cache invalidation: Cached legal answers must be refreshed or invalidated when relevant source documents, effective dates, or legal conditions change.
Semantic similarity alone is not enough to guarantee that two tax questions have the same legal answer. The cache should account for important context such as tax period and taxpayer circumstances.
4. Deadline-Day Dashboard
Displays the top 20 questions from the previous hour, along with their validated, cited answers. This helps staff quickly find answers that have already been researched.
5. Human-Approved Email Agent
The planned agent can:
1. Read an authorized client email.
2. Identify the GST question or missing-document issue.
3. Retrieve relevant official sources.
4. Draft a response with citations.
5. Draft an invoice reminder when appropriate.
6. Send nothing until an authorized CA partner approves the draft.
6. Load Testing and Monitoring
Test the system under deadline-day traffic and monitor cache hit rate, p95 latency, error rate, and throughput.
Knowledge Sources
Primary source:
- CBIC GST Portal
Use official documents as the source of truth. Record each document's title, notification or circular number, publication date, effective date where applicable, source URL, and version. Validate extracted text and citations before relying on it for tax-related answers.
How It Works
1. Question submitted: A staff member asks a GST question.
2. Cache lookup: FilingDay checks Redis for a valid exact or semantic cache match.
3. Document retrieval: If no valid cache entry exists, the system searches the indexed official documents using keyword and/or vector search.
4. Answer generation: The language model drafts an answer based on retrieved passages.
5. Citation validation: The system attaches source references and should verify that cited passages support the answer.
6. Response returned: The user receives the answer with citations.
7. Cache update: Eligible answers may be cached with appropriate expiry and invalidation rules.
Proposed Architecture
CA Staff
   |
   v
Web UI / Client
   |
   v
Backend API (e.g., FastAPI)
   |
   +----> Redis Cache
   |         |
   |         +---- Cache hit: return validated answer
   |
   +----> Retrieval Pipeline
   |         |
   |         +----> Document Store / Vector Search
   |         |          |
   |         |          +----> Official GST documents
   |         |
   |         +----> LLM generates grounded answer
   |                    |
   |                    +----> Answer + citations
   |
   +----> Monitoring / Logs

Authorized Email Agent
   |
   v
Draft reply + citations
   |
   v
CA Partner Approval
   |
   v
Send approved email
This is a proposed architecture, not a claim that these components are already implemented.
Technology Stack
The following stack is a suggested starting point; replace it with the tools used in the actual implementation.
Component	Suggested option	Purpose
Backend API	Python + FastAPI	Handle user questions and API requests
Document processing	PDF/text extraction libraries	Extract text and metadata from source documents
Relational storage	PostgreSQL	Store document metadata, users, and audit records
Semantic retrieval	PostgreSQL with vector extension or a vector database	Find relevant passages by meaning
Cache	Redis	Cache repeat answers and support fast lookups
Embeddings	An embedding model	Represent queries and passages for semantic retrieval
Answer generation	An LLM	Generate answers grounded in retrieved passages
Load testing	k6, Locust, or equivalent	Simulate traffic and measure performance


Getting Started
The exact installation steps depend on the implementation. The following is an example for a Python/FastAPI backend.
Prerequisites
- Python 3.11 or a compatible version
- Redis
- PostgreSQL or another configured document/vector store
- API credentials for the selected language model, if using a hosted model
- Git
1. Clone the repository
git clone <YOUR_REPOSITORY_URL>
cd FilingDay
Replace <YOUR_REPOSITORY_URL> with the actual repository URL.
2. Create and activate a virtual environment
python -m venv .venv
macOS/Linux:
source .venv/bin/activate
Windows PowerShell:
.venv\Scripts\Activate.ps1
3. Install dependencies
If the project includes a requirements.txt file:
pip install -r requirements.txt
If it does not, create the dependency file based on the packages actually used by the project.
4. Configure environment variables
Create a local .env file based on the project's .env.example, if available. Typical settings may include:
APP_ENV=development
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/filingday
LLM_API_KEY=replace_with_your_key
These names are illustrative. Match them to the application's actual configuration. Never commit API keys, passwords, client emails, or other secrets to Git.
5. Start dependencies and the backend
Start Redis and PostgreSQL using your local installation or the project's container configuration. Then run the application using its actual entry point. For example, if the FastAPI app is exposed as app.main:app:
uvicorn app.main:app --reload
The example command will work only if that module path matches the repository.
6. Run tests
Use the test command configured by the project. For a Python project using pytest:
pytest
Example Questions
These are example evaluation prompts, not pre-verified tax advice:
1. What late fee applies when GSTR-3B is filed after its due date?
2. Which notification changed the GST rate for a particular restaurant service, and from what date?
3. Can ITC be claimed on a car used by a company director?
Answers may depend on the relevant tax period, taxpayer category, vehicle use, statutory exceptions, and amendments. FilingDay should request additional context when necessary and cite the applicable official provisions.
Performance Goals
Metric	Initial target	Measurement notes
Cache hit rate	60% or higher	Define the eligible request population and measure hits over a representative workload
p95 cache-hit latency	Under 1 second	Measure cache lookup and response latency separately
Deadline-day load	Simulate a 10× traffic spike	Define baseline traffic and target requests per second
Answer quality	Grounded answers with supporting citations	Evaluate citation correctness and legal accuracy using a test set
Reliability	Track error rate and availability	Test under load and during dependency failures


A sub-second p95 target may be realistic for cache hits, but a cache miss requiring retrieval and LLM generation may take longer. Report cache-hit and end-to-end latency separately. Do not report these targets as achieved until they have been measured.
Security and Reliability
- Restrict access to client emails and tax data using role-based permissions.
- Require explicit CA partner approval before sending client-facing messages.
- Keep audit records of generated drafts, approvals, and sent messages.
- Protect API credentials and sensitive configuration using environment variables or a secrets manager.
- Validate source citations and display document dates and effective dates where available.
- Use cache expiry and legal-change invalidation to avoid serving stale answers.
- Log operational metadata carefully; avoid logging unnecessary personal or confidential client data.
- Treat retrieved documents and email content as untrusted input.
- Monitor errors, throughput, cache hit rate, and latency during load tests.
Limitations
- AI-generated answers can be incomplete or incorrect; citations and legal review remain important.
- The accuracy of answers depends on document coverage, extraction quality, retrieval quality, and up-to-date source material.
- Semantic caching can return an unsuitable answer if legally important context differs.
- GST treatment may depend on facts not included in a short question.
- The system supports professional work; it does not replace a qualified CA's judgment.
Future Enhancements
- Automated scheduled ingestion of new CBIC notifications and circulars.
- Version-aware retrieval and amendment comparison.
- Multilingual queries, including Tamil and English.
- User feedback and a reviewed GST question-and-answer library.
- Role-based access and organization-level data isolation.
- Dashboard analytics for popular questions and unresolved queries.
- Automated regression tests for legal updates and citation correctness.
Official Resources
- CBIC GST Portal
Always verify tax positions against the applicable legislation, notifications, circulars, and effective dates.
License
Add the license selected for this project before public distribution.
Add the license selected for this project before public distribution.
