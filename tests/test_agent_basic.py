"""
test_agent_basic.py
Prueba el loop básico del agente: recibe una instrucción, llama al LLM,
ejecuta una tool y responde.

Qué prueba:
  - El agente puede crear un archivo en el sandbox E2B
  - La respuesta final del agente es texto legible

El archivo se crea DENTRO del sandbox E2B, no en tu PC local.

Ejecutar desde la raíz del proyecto:
  PYTHONPATH=. python tests/test_agent_basic.py
"""

from dotenv import load_dotenv
load_dotenv()

from agent import build_client, build_sandbox, run_agent

print("⏳ Inicializando cliente y sandbox E2B...")
client = build_client()
sbx    = build_sandbox()
print()

historial = []

historial, respuesta = run_agent(
    "Crea un archivo /home/user/hola.txt con el texto 'Hola desde el agente'",
    client=client,
    sbx=sbx,
    messages=historial,
)

print()
print("── Respuesta del agente ──")
print(respuesta)

print()
print("⏳ Cerrando sandbox...")
sbx.kill()
print("✅ Sandbox cerrado")
