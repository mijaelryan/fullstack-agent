import os
from dotenv import load_dotenv

load_dotenv()

# Test 1: cliente GitHub Models
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
)

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Respondé solo: ok"}],
    max_tokens=10,
)

print("LLM:", resp.choices[0].message.content)


# Test 2: sandbox E2B
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create(timeout=300)
result = sbx.run_code("print('sandbox ok')")

print("Sandbox:", result.logs.stdout)

sbx.kill()