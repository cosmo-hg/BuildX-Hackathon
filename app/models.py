from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    propertyId: Optional[str] = None

class AgentResponse(BaseModel):
    """
    Standardized response structure from any agent.
    """
    answer: str
    data: Optional[Dict[str, Any]] = None # Raw data if useful for debugging or UI
    agent_used: str

class GA4QuerySchema(BaseModel):
    """
    Schema for the structure we expect the LLM to extract for GA4.
    """
    start_date: str = "30daysAgo"
    end_date: str = "today"
    metrics: List[str]
    dimensions: List[str] = []
    order_by_metric: Optional[str] = None
    limit: int = 10
