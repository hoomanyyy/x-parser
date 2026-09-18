import os
import asyncio
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

class Translator:
    def __init__(self, first_language="English", language_to="Persian"):
        self.first_language = first_language
        self.language_to = language_to

    def translate(self, text):
        if not text:
            return ""

        prompt = f"""
            1_you are an translator ai that translate languages
            2_and dont do any extra thing
            3_just translate languages

            first_language: {self.first_language}
            language_to: {self.language_to}
            text: {text}

            and remember if one text first_language was not first_language you should automatic detect language
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip() if response.text else text
        except Exception:
            return text

    async def translate_async(self, text):
        if not text:
            return ""
        return await asyncio.to_thread(self.translate, text)