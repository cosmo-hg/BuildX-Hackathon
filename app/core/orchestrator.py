import logging
from app.models import AgentResponse
from app.agents.analytics import analytics_agent
from app.agents.seo import seo_agent
from app.core.llm import llm_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class Orchestrator:
    def _detect_intent(self, query: str) -> str:
        prompt = f"""
        Classify the intent of this query into one category only:
        ANALYTICS
        SEO
        BOTH

        Query: "{query}"
        """

        response = llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=settings.MODEL_FAST
        ).upper()

        if "BOTH" in response:
            return "BOTH"
        if "SEO" in response:
            return "SEO"
        return "ANALYTICS"

    def route_request(self, property_id: str, query: str) -> AgentResponse:
        intent = self._detect_intent(query)
        logger.info(f"Intent detected: {intent}")

        if intent == "ANALYTICS":
            if not property_id:
                return AgentResponse(
                    answer="A GA4 propertyId is required for analytics queries.",
                    agent_used="System"
                )
            return analytics_agent.process(property_id, query)

        if intent == "SEO":
            return seo_agent.process(query)

        if not property_id:
            return AgentResponse(
                answer="A GA4 propertyId is required for cross analysis.",
                agent_used="System"
            )

        analytics_result = analytics_agent.process(property_id, query)
        seo_result = seo_agent.process(query)

        prompt = f"""
        Combine analytics and SEO insights.

        Analytics:
        {analytics_result.data}

        SEO:
        {seo_result.data}

        User Question:
        "{query}"
        """

        combined_answer = llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=settings.MODEL_REASONING
        )

        return AgentResponse(
            answer=combined_answer,
            data={
                "analytics": analytics_result.data,
                "seo": seo_result.data
            },
            agent_used="Orchestrator"
        )

orchestrator = Orchestrator()
