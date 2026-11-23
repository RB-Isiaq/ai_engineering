"""Optional image and speech output (OpenAI only; each image costs a few cents)."""

import base64
import tempfile
from io import BytesIO

from PIL import Image

from toolkit import get_client


def destination_art(city: str) -> Image.Image:
    response = get_client("openai").images.generate(
        model="gpt-image-1-mini",
        prompt=(
            f"Travel poster for {city}: its landmarks and street life, "
            "bold flat colours, mid-century illustration style, no text"
        ),
        size="1024x1024",
    )
    return Image.open(BytesIO(base64.b64decode(response.data[0].b64_json)))


def speak(text: str, voice: str = "coral") -> str:
    """Synthesize speech and return the path of an mp3 file (what gr.Audio expects)."""
    audio = get_client("openai").audio.speech.create(
        model="gpt-4o-mini-tts", voice=voice, input=text
    )
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio.content)
        return f.name
