"""
test_connection.py
Verifica que las credenciales y conexiones externas funcionan correctamente.

Qué prueba:
  1. Conexión al LLM (GitHub Models / gpt-4o-mini)
  2. Creación y uso de un sandbox E2B

Ejecutar desde la raíz del proyecto:
  PYTHONPATH=. python tests/test_connection.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ── Test 1: cliente GitHub Models ─────────────────────────────────────────
print("=" * 50)
print("Test 1: conexión a GitHub Models (LLM)")
print("=" * 50)

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

print(f"✅ LLM responde: {resp.choices[0].message.content}")

# ── Test 2: sandbox E2B ───────────────────────────────────────────────────
print()
print("=" * 50)
print("Test 2: creación de sandbox E2B")
print("=" * 50)

from e2b_code_interpreter import Sandbox

print("⏳ Creando sandbox E2B...")
sbx = Sandbox.create(timeout=300)
print(f"✅ Sandbox creado (id: {sbx.sandbox_id})")

result = sbx.run_code("print('sandbox ok')")
print(f"✅ Ejecución en sandbox: {result.logs.stdout}")

print("⏳ Cerrando sandbox...")
sbx.kill()
print("✅ Sandbox cerrado")

print()
print("✅ Todas las conexiones OK")
