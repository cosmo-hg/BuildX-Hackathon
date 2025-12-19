# Spike AI Backend Challenge

A production-ready, multi-agent AI backend capable of answering natural language questions about **Google Analytics 4** and **SEO Audits** (Screaming Frog).

## 1. Architecture

The system uses a **Hub-and-Spoke Agentic Architecture** orchestrated by a central reasoning engine.

```mermaid
graph TD
    Client[Client / API Consumer] -->|POST /query| API[FastAPI Entrypoint]
    API --> Orchestrator
    
    subgraph "Core Logic"
        Orchestrator{Orchestrator Agent}
        Orchestrator -->|Intent: Analytics| AnalyticsAgent
        Orchestrator -->|Intent: SEO| SEOAgent
        Orchestrator -->|Intent: Both| FusionEngine[Fusion Logic]
    end
    
    subgraph "Data Sources"
        AnalyticsAgent -->|GA4 Data API| GA4[Google Analytics 4]
        SEOAgent -->|Pandas I/O| GSheets[Google Sheets (Live)]
        FusionEngine --> AnalyticsAgent
        FusionEngine --> SEOAgent
    end
    
    subgraph "Reasoning"
        LLM[LiteLLM / Gemini Models]
        AnalyticsAgent -.->|Schema Inference| LLM
        SEOAgent -.->|Filter Generation| LLM
        Orchestrator -.->|Intent & Synthesis| LLM
    end
```

### 1.1 Components
*   **Orchestrator**: The "Brain". Uses `gemini-2.5-flash` to classify intent (`ANALYTICS`, `SEO`, `BOTH`) and routes requests.
*   **Analytics Agent (Tier 1)**: 
    *   **Logic**: Uses **Schema Inference**. The LLM extracts metrics/dimensions/dates into a strict JSON schema.
    *   **Safety**: Validates against an allowlist (e.g., only `activeUsers`, `pagePath`) before calling the `google-analytics-data` API. No arbitrary code execution.
*   **SEO Agent (Tier 2)**:
    *   **Logic**: **Live Ingestion** of Google Sheet CSVs. Uses LLM to generate Pandas `.query()` strings for flexible natural language filtering.
    *   **Safety**: Operates on a read-only DataFrame copy.
*   **Fusion Engine (Tier 3)**:
    *   **Logic**: Calls both agents, retrieves data, and uses the LLM to synthesize a combined answer (e.g., finding title tags for the most viewed pages).

## 2. Setup Instructions

### Prerequisites
- Python 3.9+
- Valid `credentials.json` for Google Cloud Service Account (placed at root).
- `LITELLM_API_KEY` (MUST be set in `.env` or environment).

### Installation & Run

```bash
# 1. Clone repo and enter directory
cd spike-ai-backend

# 2. Add API Key
echo "LITELLM_API_KEY=sk-..." > .env

# 3. Run the deployment script (Install + Start)
bash deploy.sh
```

The server will start on `http://0.0.0.0:8080`.

## 3. Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LITELLM_API_KEY` | **Required**. Authentication for LLM. | None |
| `GA4_PROPERTY_ID` | Default GA4 Property ID for queries. | None |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key. | `credentials.json` |

## 4. Key Design Decisions & Assumptions

*   **Schema Inference vs Code Gen**: For GA4, we chose **Schema Inference** (structured JSON) over writing SQL/Python code. This eliminates the risk of hallucinated fields or syntax errors and ensures type safety.
*   **Pandas for SEO**: Given the dataset size (Screaming Frog exports), in-memory Pandas processing provides the best balance of performance and flexibility compared to a full database.
*   **Agentic Reasoning**: We restored full agentic reasoning in Tier 2 (SEO) by generating dynamic filters, rather than hardcoding specific logic. This allows the agent to answer *any* filtering question, not just the test cases.
*   **Graceful Degradation**: If specific data is missing (e.g., empty GA4 property), the agents return a descriptive message rather than crashing.

## 5. Evaluation

To run the comprehensive test suite (Tiers 1, 2, and 3):

```bash
python3 scripts/test_runner.py
```

*Note: Ensure `GA4_PROPERTY_ID` is set in `scripts/test_runner.py` or `.env` for Tier 1 tests to pass.*
