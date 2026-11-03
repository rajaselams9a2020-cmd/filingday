# FilingDay — AI-Powered GST Assistant

FilingDay is an AI-powered GST assistant designed to help Chartered Accountant (CA) firms find information from GST-related documents. It uses document retrieval and language models to generate answers based on available source material.

**Project status:** Initial implementation of a GST RAG pipeline with a FastAPI backend, PostgreSQL with pgvector, LLM provider integration, fallback handling, and cost tracking. Additional features are planned.

## Table of Contents

- Problem Statement
- Objectives
- Implemented Features
- Planned Features
- Knowledge Sources
- How It Works
- Technology Stack
- Getting Started
- Run with Docker
- Running Tests
- API Health Checks
- Security and Reliability
- Limitations
- Future Enhancements
- Official Resources

## Problem Statement

CA firms handle GST compliance for multiple clients. Staff frequently need to research GST rates, notifications, input tax credit (ITC), late fees, and return-filing rules.

Manually searching through Acts, Rules, circulars, and notifications can be time-consuming. FilingDay aims to simplify this research by retrieving relevant document passages and generating answers with source references.

## Objectives

- Answer GST-related questions in plain language.
- Retrieve relevant information from GST documents.
- Generate answers grounded in retrieved context.
- Provide source references to support answers.
- Improve reliability through LLM fallback handling.
- Track LLM usage, latency, and estimated cost.
- Support future improvements for deadline-day traffic.

## Implemented Features

### 1. GST Question Answering

Users can submit questions through the API. The application retrieves relevant passages from the available GST document knowledge base and uses them as context for answer generation.

### 2. Document Retrieval

- Extract text from PDF documents.
- Retrieve relevant passages using the implemented retrieval pipeline.
- Include source and page information in retrieved context.

### 3. LLM Integration

- Supports the configured LLM provider.
- Includes a fake provider for local development and testing.
- Supports streaming responses.
- Includes retry and fallback handling for eligible provider failures.

### 4. LLM Cost Tracking

- Records input and output token usage.
- Estimates LLM call cost using configured token prices.
- Records latency and provider information.
- Appends call records to a JSON Lines log file.

### 5. Health and Readiness Checks

- `/health` checks whether the API is running.
- `/ready` checks application readiness, including database connectivity.

### 6. PostgreSQL with pgvector

The Docker setup includes PostgreSQL with the pgvector extension for vector-related database functionality.

## Planned Features

The following features are future enhancements and should not be considered implemented:

- Exact-match and semantic caching using Redis.
- Deadline-day dashboard showing frequently asked questions.
- Human-approved email drafting and sending workflow.
- Automated ingestion of new GST notifications and circulars.
- Large-scale document indexing and version management.
- Load testing and performance monitoring.

## Knowledge Sources

The initial knowledge base uses GST-related PDF documents available to the project.

Official source:

- CBIC GST Portal: https://cbic-gst.gov.in/

Official documents should be treated as the source of truth. Document titles, notification numbers, publication dates, effective dates, and source references should be maintained wherever available.

## How It Works

1. **Question submission:** A user submits a GST-related question.
2. **Document retrieval:** The application searches the available GST documents for relevant passages.
3. **Context construction:** Retrieved passages are assembled with source and page information.
4. **Answer generation:** The configured LLM generates an answer using the retrieved context.
5. **Streaming response:** The API can stream the generated response.
6. **Usage tracking:** LLM usage, latency, and estimated cost are recorded.

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Backend API | Python, FastAPI | Handle API requests |
| Document processing | PDF text extraction | Extract GST document content |
| Database | PostgreSQL | Store application data |
| Vector extension | pgvector | Support vector-related database operations |
| LLM integration | Configured LLM provider | Generate answers |
| Local testing | Fake LLM provider | Test without a hosted LLM |
| Reliability | Retry and fallback handling | Handle eligible provider failures |
| Cost tracking | JSON Lines logs | Record token usage and estimated cost |
| Containerization | Docker, Docker Compose | Run the API and database |

## Getting Started

### Prerequisites

- Python 3.12 or compatible version
- Git
- Docker Desktop with Docker Compose (for Docker setup)
- LLM credentials if using a hosted provider

### 1. Clone the repository

```bash
git clone https://github.com/rajaselams9a2020-cmd/filingday.git
cd filingday
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file using `.env.example` as the reference.

Configure the required values for the selected LLM provider and application environment.

**Important:** Never commit `.env` files, API keys, passwords, or other secrets to Git.

### 5. Run the application locally

Use the application's configured environment and database settings, then start the API:

```powershell
uvicorn app.main:app --reload
```

## Run with Docker

### Prerequisites

- Docker Desktop installed and running.
- Docker Compose enabled.

### 1. Configure environment variables

Create a `.env` file from `.env.example` and configure the required values.

### 2. Build and start the services

```powershell
docker compose up --build
```

This starts:

- FastAPI application
- PostgreSQL with pgvector

The API is available at:

`http://localhost:8001`

PostgreSQL is exposed on port `5432`.

### 3. Check the API

Open a second PowerShell terminal and run:

```powershell
curl.exe http://localhost:8001/health
```

Check application readiness:

```powershell
curl.exe http://localhost:8001/ready
```

### 4. Useful Docker commands

Check running containers:

```powershell
docker compose ps
```

View API logs:

```powershell
docker compose logs -f api
```

Stop the database:

```powershell
docker compose stop db
```

Start the database:

```powershell
docker compose start db
```

Stop and remove containers:

```powershell
docker compose down
```

The named PostgreSQL volume is preserved when using `docker compose down`.

**Warning:** `docker compose down -v` deletes the database volume and its stored data. Use it only when you intentionally want to remove that data.

## Running Tests

Run the test suite:

```powershell
python -m pytest -v
```

The current test suite has **30 passing tests**.

Test coverage includes:

- API health checks
- Chat streaming
- LLM provider behavior
- Retry and fallback handling
- Cost logging
- GST document retrieval
- RAG context construction

Test results may change as the codebase is updated.

## API Health Checks

| Endpoint | Purpose |
|---|---|
| `/health` | Check whether the API is running |
| `/ready` | Check whether the application and database are ready |

## Security and Reliability

- Keep API credentials and passwords in environment variables.
- Do not commit `.env` files.
- Keep `.env` excluded from the Docker build context.
- Use database health checks before starting dependent services.
- Use retry and fallback handling for eligible LLM failures.
- Avoid logging confidential client information.
- Verify generated GST answers against applicable official documents.
- Require professional review before relying on AI-generated tax information.

## Limitations

- AI-generated answers may be incomplete or incorrect.
- Answer quality depends on the available documents and retrieval quality.
- Legal applicability may depend on tax period, taxpayer circumstances, and amendments.
- The current implementation does not include all proposed caching, dashboard, or email-agent features.
- FilingDay does not replace a qualified Chartered Accountant's professional judgment.

## Future Enhancements

- Redis-based exact-match and semantic caching.
- Automated GST document ingestion.
- Document versioning and amendment tracking.
- Deadline-day question dashboard.
- Human-approved email drafting workflow.
- Tamil and multilingual question support.
- Load testing and performance monitoring.
- Improved citation validation.

## Official Resources

- CBIC GST Portal: https://cbic-gst.gov.in/

Always verify GST-related answers against the applicable legislation, notifications, circulars, and effective dates.

## License

Add the license selected for this project before public distribution.