import os

class Config:
    # LiteLLM (required)
    LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
    LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://3.110.18.218")

    if not LITELLM_API_KEY:
        raise RuntimeError(
            "LITELLM_API_KEY is not set. Please export your LiteLLM API key."
        )

    # GA4
    GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")

    MODEL_FAST = "gemini-2.5-flash"
    MODEL_REASONING = "gemini-2.5-pro"

settings = Config()
