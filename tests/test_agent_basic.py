from dotenv import load_dotenv
load_dotenv()

import os
from agent import build_client, build_sandbox, run_agent

client = build_client()
sbx    = build_sandbox()

historial = []

historial, respuesta = run_agent(
    "Crea un archivo /home/user/hola.txt con el texto 'Hola desde el agente'",
    client=client,
    sbx=sbx,
    messages=historial,
)

print("\n--- RESPUESTA ---")
print(respuesta)

sbx.kill()