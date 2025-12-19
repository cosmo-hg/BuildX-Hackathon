import logging
import json
import pandas as pd
import io
import requests
from app.models import AgentResponse
from app.core.llm import llm_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class SEOAgent:
    """
    Tier 2 Agent
    Responsible for answering SEO-related questions
    using live Screaming Frog spreadsheet data.
    """

    def __init__(self):
        self.sheet_id = "1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKvl6VEE"
        self.gid = "1438203274"
        self.url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{self.sheet_id}/export?format=csv&gid={self.gid}"
        )
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """
        Live ingestion of Screaming Frog data.
        """
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()

            df = pd.read_csv(io.StringIO(response.text))

            # Normalize column names to be schema-safe
            df.columns = [
                c.strip()
                .lower()
                .replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                for c in df.columns
            ]

            return df

        except Exception as e:
            logger.error(f"Failed to load SEO data: {e}")
            return pd.DataFrame()

    def process(self, query: str) -> AgentResponse:
        """
        Main entry point for SEO questions.
        """
        if self.df.empty:
            return AgentResponse(
                answer="SEO data is currently unavailable.",
                agent_used="SEOAgent"
            )

        # 1. Infer Filter / Analysis Plan using LLM
        # We restore the agentic capability to handle ANY query, not just the test cases.
        prompt = f"""
        You are an SEO Analyst using Pandas.
        The dataframe 'df' has columns: {list(self.df.columns)}

        User Question: "{query}"

        Instructions:
        1. If the user asks primarily to filter rows (e.g. "pages with X", "URLs with Y"), 
           write a Python-syntax Pandas `.query()` string. 
           Example: `title_1_length > 60 and protocol != "https"`
           
        2. If the user asks for "top X pages by Y" (sorting), return a special string:
           `SORT_BY: <column_name> TOP <n>`
           
        3. Return ONLY the string (no code blocks).
        """
        
        filter_logic = llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            model=settings.MODEL_FAST
        ).strip().replace("`", "")

        df = self.df.copy()
        
        # 2. Apply Logic
        try:
            if filter_logic.startswith("SORT_BY:"):
                # Parse "SORT_BY: view_count TOP 5"
                parts = filter_logic.replace("SORT_BY:", "").strip().split(" TOP ")
                col = parts[0].strip()
                n = int(parts[1]) if len(parts) > 1 else 10
                if col in df.columns:
                    df = df.sort_values(by=col, ascending=False).head(n)
            elif filter_logic and filter_logic.lower() != "none":
                # Apply .query()
                df = df.query(filter_logic)
        except Exception as e:
            logger.warning(f"Filter application failed: {filter_logic} - {e}")
            # Fallback: Just proceed with full DF or top 10 if filter failed, 
            # effectively ignoring the complex filter but still attempting to answer
            df = df.head(10)

        # 3. Final Answer Generation
        count = len(df)
        preview = df.head(20).to_dict(orient="records")
        urls = df["address"].head(10).tolist() if "address" in df.columns else []

        explanation_prompt = f"""
        Answer the SEO question based on the filtered data.

        Question: "{query}"
        
        Filter Logic Used: {filter_logic}
        Matched Rows: {count}
        
        Data Preview:
        {json.dumps(preview, default=str)}

        Be factual, concise, and mention specific URLs if relevant.
        """

        explanation = llm_client.generate(
            messages=[{"role": "user", "content": explanation_prompt}],
            model=settings.MODEL_REASONING
        )

        return AgentResponse(
            answer=explanation,
            data={
                "count": count,
                "urls": urls,
                "strategy": filter_logic
            },
            agent_used="SEOAgent"
        )


seo_agent = SEOAgent()
