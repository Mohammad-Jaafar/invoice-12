import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.schema import Invoice

load_dotenv()

MODEL = os.environ.get("MODEL", "gemini-flash-lite-latest")
MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
PROMPT = (
    "Extract the invoice data from this image. "
    "The invoice may be in Arabic, English or both. "
    "Convert Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩) to Western digits (0123456789). "
    "Copy printed values exactly; do not calculate, fix or guess anything. "
    "Give the currency as an ISO 4217 code. "
    "Give the date as YYYY-MM-DD. "
    "Set supplier_trn to null if no tax registration number is printed."
)


def extract_bytes(
    data: bytes, media_type: str, model: str = MODEL
) -> tuple[Invoice, dict]:
    client = genai.Client()
    response = client.models.generate_content(
        model=model,
        contents=[types.Part.from_bytes(data=data, mime_type=media_type), PROMPT],
        config=types.GenerateContentConfig(
            max_output_tokens=2048,
            response_mime_type="application/json",
            response_json_schema=Invoice.model_json_schema(),
        ),
    )
    usage = response.usage_metadata
    return Invoice.model_validate_json(response.text), {
        "input_tokens": usage.prompt_token_count,
        "output_tokens": usage.candidates_token_count,
    }


def extract_file(path: Path, model: str = MODEL) -> tuple[Invoice, dict]:
    return extract_bytes(path.read_bytes(), MEDIA_TYPES[path.suffix.lower()], model)
