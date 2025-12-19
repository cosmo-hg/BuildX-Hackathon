import logging
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.models import QueryRequest
from app.core.orchestrator import orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spike-ai-backend")

app = FastAPI(
    title="Spike AI Backend",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    start = time.time()

    try:
        response = orchestrator.route_request(
            property_id=request.propertyId,
            query=request.query
        )

        return {
            "answer": response.answer,
            "agent_used": response.agent_used,
            "duration": round(time.time() - start, 2)
        }

    except Exception as e:
        logger.error(e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
