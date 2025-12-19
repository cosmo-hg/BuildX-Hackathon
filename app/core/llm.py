import time
import logging
from typing import List, Dict, Any
from openai import OpenAI, APIError
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        json_mode: bool = False,
        max_retries: int = 5
    ) -> str:
        base_delay = 1

        for attempt in range(max_retries):
            try:
                kwargs: Dict[str, Any] = {
                    "model": model,
                    "messages": messages
                }

                # JSON mode is best-effort with Gemini via LiteLLM
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content

                if not content:
                    raise ValueError("Empty response from LLM")

                return content.strip()

            except APIError as e:
                if e.status_code == 429:
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Rate limited. Retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"LLM API error: {e}")
                    raise

            except Exception as e:
                logger.error(f"Unexpected LLM error: {e}")
                raise

        raise RuntimeError("LLM failed after multiple retries")

llm_client = LLMClient()
