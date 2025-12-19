import json
import logging
from typing import Dict, Any
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Metric,
    Dimension
)
from app.core.config import settings
from app.core.llm import llm_client
from app.models import GA4QuerySchema, AgentResponse

logger = logging.getLogger(__name__)

class AnalyticsAgent:
    def __init__(self):
        self.allowed_metrics = {
            "activeUsers",
            "sessions",
            "screenPageViews",
            "eventCount",
            "totalUsers",
            "newUsers"
        }

        self.allowed_dimensions = {
            "date",
            "city",
            "country",
            "deviceCategory",
            "pagePath",
            "source",
            "medium"
        }

        self.client = BetaAnalyticsDataClient()

    def _infer_schema(self, query: str) -> GA4QuerySchema:
        prompt = f"""
        Extract the GA4 reporting parameters from the user query.
        
        Query: "{query}"

        Instructions:
        1. Identify the 'start_date' and 'end_date'. 
           - 'last 7 days' -> start_date='7daysAgo', end_date='today'
           - 'yesterday' -> start_date='yesterday', end_date='yesterday'
           - Default if unspecified: start_date='30daysAgo', end_date='today'
        2. Identify metrics (allowed: activeUsers, sessions, screenPageViews, eventCount, totalUsers, newUsers).
        3. Identify dimensions (allowed: date, city, country, deviceCategory, pagePath, source, medium).
        
        Return JSON:
        {{
          "start_date": "...",
          "end_date": "...",
          "metrics": ["..."],
          "dimensions": ["..."],
          "limit": 10
        }}
        """

        response = llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=settings.MODEL_FAST,
            json_mode=True
        )

        try:
            data = json.loads(response)
            return GA4QuerySchema(**data)
        except Exception:
            logger.error("LLM schema parsing failed")
            raise ValueError("Could not understand analytics request")

    def _validate_schema(self, schema: GA4QuerySchema):
        schema.metrics = [m for m in schema.metrics if m in self.allowed_metrics]
        schema.dimensions = [d for d in schema.dimensions if d in self.allowed_dimensions]

        # Disable ordering entirely for GA4 safety
        schema.order_by_metric = None

        if not schema.metrics:
            raise ValueError("No valid GA4 metrics inferred")

    def _execute_query(self, property_id: str, schema: GA4QuerySchema) -> Dict[str, Any]:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[
                DateRange(
                    start_date=schema.start_date,
                    end_date=schema.end_date
                )
            ],
            metrics=[Metric(name=m) for m in schema.metrics],
            dimensions=[Dimension(name=d) for d in schema.dimensions],
            limit=schema.limit
        )

        response = self.client.run_report(request)

        rows = []
        for row in response.rows:
            item = {}
            for i, d in enumerate(schema.dimensions):
                item[d] = row.dimension_values[i].value
            for i, m in enumerate(schema.metrics):
                item[m] = row.metric_values[i].value
            rows.append(item)

        return {"rows": rows, "schema": schema.model_dump()}

    def _explain(self, query: str, data: Dict[str, Any]) -> str:
        if not data["rows"]:
            return "No data found for this period."

        prompt = f"""
        Explain this GA4 data clearly.

        Question: "{query}"

        Data:
        {json.dumps(data["rows"][:20], indent=2)}

        Be concise and factual.
        """

        return llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=settings.MODEL_REASONING
        )

    def process(self, property_id: str, query: str) -> AgentResponse:
        schema = self._infer_schema(query)
        self._validate_schema(schema)
        data = self._execute_query(property_id, schema)
        answer = self._explain(query, data)

        return AgentResponse(
            answer=answer,
            data=data,
            agent_used="AnalyticsAgent"
        )

analytics_agent = AnalyticsAgent()
