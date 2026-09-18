import os
import asyncio
import logging
from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.warning("GOOGLE_API_KEY is not set. Translation will be disabled.")

client = genai.Client(api_key=api_key) if api_key else None


class Translator:
    def __init__(self, first_language="English", language_to="Persian"):
        self.first_language = first_language
        self.language_to = language_to

    def translate(self, text):
        if not text:
            return ""

        if client is None:
            logger.warning("Gemini client is not configured")
            return text

        prompt = f"""You are a translator.
Translate the following text to {self.language_to}.
Do not explain anything. Only return the translation.

Text:
{text}
"""

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )
            result = (response.text or "").strip()
            if not result:
                logger.warning("Empty translation response")
                return text
            return result
        except Exception as e:
            logger.error("Translation failed: %s", e)
            return text

    async def translate_async(self, text):
        if not text:
            return ""
        return await asyncio.to_thread(self.translate, text)