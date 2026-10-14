import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()
reply = client.models.generate_content(
    model=os.environ.get("MODEL", "gemini-flash-lite-latest"),
    contents="Reply with the single word OK.",
)
print(reply.text)
print(
    reply.usage_metadata.prompt_token_count, reply.usage_metadata.candidates_token_count
)
