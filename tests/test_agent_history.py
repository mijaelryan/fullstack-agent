from dotenv import load_dotenv
load_dotenv()

from agent import build_client, build_sandbox, run_agent

client = build_client()
sbx    = build_sandbox()

historial = []

# Turno 1
run_agent(
    "Crea /home/user/config.txt con el contenido 'color=azul'",
    client=client, sbx=sbx, messages=historial,
)

# Turno 2 — el agente debe recordar el archivo del turno anterior
historial, respuesta = run_agent(
    "Cambiá el color en config.txt de azul a rojo",
    client=client, sbx=sbx, messages=historial,
)

print("\n--- RESPUESTA ---")
print(respuesta)

sbx.kill()