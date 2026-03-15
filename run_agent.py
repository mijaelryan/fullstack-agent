"""
run_agent.py
Interfaz CLI del agente Full Stack.

Uso:
    python run_agent.py
"""

import os
import sys

# Cargar .env ANTES de verificar credenciales
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Verificar credenciales antes de importar nada pesado
# ---------------------------------------------------------------------------

def _check_env():
    missing = [v for v in ("GITHUB_TOKEN", "E2B_API_KEY") if not os.environ.get(v)]
    if missing:
        print(f"\n❌  Faltan variables de entorno: {', '.join(missing)}")
        print("    Exportálas antes de ejecutar:")
        for v in missing:
            print(f"      export {v}=tu_clave")
        sys.exit(1)

_check_env()

from agent import build_client, build_sandbox, run_agent  # noqa: E402

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

BANNER = """
╔══════════════════════════════════════════════════════╗
║          🤖  Full Stack Code Agent                   ║
║  Stack: Next.js 14 · TypeScript · Tailwind CSS       ║
║  Escribí 'exit' o Ctrl+C para salir                  ║
╚══════════════════════════════════════════════════════╝
"""

def main():
    print(BANNER)

    print("⏳ Inicializando cliente y sandbox E2B…")
    try:
        client = build_client()
        sbx    = build_sandbox()
    except Exception as e:
        print(f"❌  Error al inicializar: {e}")
        sys.exit(1)

    historial = []

    print("\n✅ Listo. Podés empezar a escribir.\n")

    while True:
        try:
            query = input("User > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Sesión terminada.")
            break

        if not query:
            continue

        if query.lower() in ("exit", "salir", "quit"):
            print("👋 Sesión terminada.")
            break

        historial, respuesta = run_agent(
            query,
            client=client,
            sbx=sbx,
            messages=historial,
        )

        print(f"\nAgent > {respuesta}\n")

    # Cerrar sandbox al salir
    try:
        sbx.kill()
        print("🧹 Sandbox cerrado.")
    except Exception:
        pass


if __name__ == "__main__":
    main()
