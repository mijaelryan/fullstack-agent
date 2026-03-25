"""
test_agent_history.py
Prueba que el agente mantiene historial entre turnos dentro de la misma sesión.

Qué prueba:
  - Turno 1: el agente crea un archivo en el sandbox E2B
  - Turno 2: el agente recuerda ese archivo y lo modifica sin que se lo
    repitan — demuestra que el historial de conversación funciona

Ambos archivos viven DENTRO del sandbox E2B.
El sandbox se mantiene abierto entre turnos y se cierra al final.

Ejecutar desde la raíz del proyecto:
  PYTHONPATH=. python tests/test_agent_history.py
"""

from dotenv import load_dotenv
load_dotenv()

from agent import build_client, build_sandbox, run_agent

print("⏳ Inicializando cliente y sandbox E2B...")
client = build_client()
sbx    = build_sandbox()
print()

historial = []

# ── Turno 1 ───────────────────────────────────────────────────────────────
print("── Turno 1: crear archivo en el sandbox ──")
historial, _ = run_agent(
    "Crea /home/user/config.txt con el contenido 'color=azul'",
    client=client,
    sbx=sbx,
    messages=historial,
)

# ── Turno 2 ───────────────────────────────────────────────────────────────
print()
print("── Turno 2: el agente debe recordar el archivo del turno anterior ──")
historial, respuesta = run_agent(
    "Cambiá el color en config.txt de azul a rojo",
    client=client,
    sbx=sbx,
    messages=historial,
)

print()
print("── Respuesta del agente (turno 2) ──")
print(respuesta)
print()
print(f"  Mensajes en historial: {len(historial)} (ambos turnos acumulados)")

print()
print("⏳ Cerrando sandbox...")
sbx.kill()
print("✅ Sandbox cerrado")
