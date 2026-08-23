from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os

load_dotenv()
_client = InferenceClient(api_key=os.getenv("HF_TOKEN"))


def generate_answer(query: str, results: list[dict]) -> str:
    from app.generation.prompts import build_prompt
    prompt = build_prompt(query, results)

    completion = _client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[{"role": "user", "content": prompt}],
)
    return completion.choices[0].message.content