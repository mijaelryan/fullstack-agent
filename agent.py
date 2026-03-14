"""
agent.py
Agente Full Stack — loop principal con compresión de contexto.

Uso:
    from agent import run_agent, build_client, build_sandbox

    client, sbx = build_client(), build_sandbox()
    historial   = []
    run_agent("Crea una app de lista de tareas estilo Windows 95.", client, sbx, messages=historial)
    run_agent("Los íconos del nav son blancos y no se ven. Arreglalo.", client, sbx, messages=historial)
"""

import json
import os
from typing import Callable

from openai import OpenAI
from e2b_code_interpreter import Sandbox

from lib.sbx_tools import TOOLS_IMPL, TOOLS_SCHEMAS
from lib.context import maybe_compress
from lib.prompts import SYSTEM_PROMPT_WEB_DEV


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

MODEL_ID  = "gpt-4o"          # modelo recomendado para generación de código
MAX_STEPS = 30                 # parada de seguridad


# ---------------------------------------------------------------------------
# Cliente GitHub Models y wrapper LLM
# ---------------------------------------------------------------------------

def build_client(token: str = None) -> OpenAI:
    """
    Crea el cliente OpenAI apuntando a GitHub Models.
    Toma el token de la variable de entorno GITHUB_TOKEN si no se pasa.
    """
    token = token or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("Falta GITHUB_TOKEN en el entorno o como argumento.")
    return OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token,
    )


def build_sandbox(e2b_api_key: str = None, timeout: int = 3600) -> Sandbox:
    """
    Crea y devuelve un sandbox E2B listo para usar.
    Instala Node.js si no está disponible.
    """
    key = e2b_api_key or os.environ.get("E2B_API_KEY")
    if not key:
        raise ValueError("Falta E2B_API_KEY en el entorno o como argumento.")
    os.environ["E2B_API_KEY"] = key

    sbx = Sandbox.create(timeout=timeout)
    print(f"✅ Sandbox creado: {sbx.sandbox_id}")

    # Verificar que Node.js está disponible
    _ensure_node(sbx)
    return sbx


def _ensure_node(sbx: Sandbox):
    """Instala Node.js LTS en el sandbox si no está presente."""
    check = sbx.run_code(
        "import subprocess; r = subprocess.run(['node','--version'], capture_output=True, text=True); print(r.stdout.strip())"
    )
    version = "".join(check.logs.stdout).strip()
    if version.startswith("v"):
        print(f"✅ Node.js disponible: {version}")
        return

    print("⏳ Instalando Node.js LTS…")
    install = sbx.run_code("""
import subprocess
subprocess.run(
    "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs",
    shell=True, capture_output=True
)
r = subprocess.run(['node','--version'], capture_output=True, text=True)
print(r.stdout.strip())
""")
    version = "".join(install.logs.stdout).strip()
    print(f"✅ Node.js instalado: {version}")


# ---------------------------------------------------------------------------
# Función llm() — wrapper normalizado (igual al primer notebook)
# ---------------------------------------------------------------------------

def llm(client: OpenAI, messages: list, system: str, tools: list = None):
    """
    Llama a GitHub Models (OpenAI-compatible) y retorna un _OpenAIResponse
    con .output (lista de partes) y .output_text (texto plano).
    """
    oai_messages = [{"role": "system", "content": system}]

    for m in messages:
        role    = m["role"]
        content = m["content"]

        if isinstance(content, list):
            tool_results = []
            text_parts   = []
            tool_calls   = []

            for part in content:
                if not isinstance(part, dict):
                    continue
                if "text" in part:
                    text_parts.append({"type": "text", "text": part["text"]})
                elif "toolResult" in part:
                    tr          = part["toolResult"]
                    result_text = json.dumps(tr["content"][0].get("json", tr["content"]))
                    tool_results.append({
                        "role":         "tool",
                        "tool_call_id": tr["toolUseId"],
                        "content":      result_text,
                    })
                elif "tool_use" in part:
                    tu = part["tool_use"]
                    tool_calls.append({
                        "id":   tu["toolUseId"],
                        "type": "function",
                        "function": {
                            "name":      tu["name"],
                            "arguments": json.dumps(tu["input"]),
                        },
                    })

            if tool_calls:
                oai_messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
            if tool_results:
                oai_messages.extend(tool_results)
            elif text_parts:
                oai_messages.append({"role": role, "content": text_parts})
        else:
            oai_messages.append({"role": role, "content": content})

    kwargs = dict(model=MODEL_ID, messages=oai_messages)
    if tools:
        kwargs["tools"] = [
            {
                "type": "function",
                "function": {
                    "name":        t["name"],
                    "description": t.get("description", ""),
                    "parameters":  t.get("parameters", {}),
                },
            }
            for t in tools
        ]
        kwargs["tool_choice"] = "auto"

    raw = client.chat.completions.create(**kwargs)
    return _OpenAIResponse(raw)


class _OpenAIResponse:
    def __init__(self, raw):
        self._raw        = raw
        self.output      = []
        self.output_text = ""
        self._msg        = raw.choices[0].message
        self._parse()

    def _parse(self):
        if self._msg.content:
            self.output.append(_TextPart(self._msg.content))
            self.output_text = self._msg.content
        if self._msg.tool_calls:
            for tc in self._msg.tool_calls:
                self.output.append(_ToolUsePart(
                    name=tc.function.name,
                    arguments=tc.function.arguments,
                    call_id=tc.id,
                ))

    def assistant_message(self):
        content = []
        if self._msg.content:
            content.append({"text": self._msg.content})
        if self._msg.tool_calls:
            for tc in self._msg.tool_calls:
                content.append({
                    "tool_use": {
                        "toolUseId": tc.id,
                        "name":      tc.function.name,
                        "input":     json.loads(tc.function.arguments),
                    }
                })
        return {"role": "assistant", "content": content}


class _TextPart:
    type = "message"
    def __init__(self, text):
        self.text    = text
        self.content = text


class _ToolUsePart:
    type = "function_call"
    def __init__(self, name, arguments, call_id):
        self.name      = name
        self.arguments = arguments
        self.call_id   = call_id


# ---------------------------------------------------------------------------
# execute_tool — despacha la herramienta correcta
# ---------------------------------------------------------------------------

def execute_tool(name: str, args: str, tools: dict, **kwargs):
    """
    Ejecuta la herramienta `name` con los argumentos JSON `args`.
    Pasa `sbx` y otros kwargs como argumentos extra a la herramienta.
    """
    try:
        args_dict = json.loads(args)
        if name not in tools:
            return {"error": f"Herramienta '{name}' no encontrada."}
        return tools[name](**args_dict, **kwargs)
    except json.JSONDecodeError as e:
        return {"error": f"No se pudo parsear argumentos de '{name}': {e}"}
    except KeyError as e:
        return {"error": f"Argumento faltante en '{name}': {e}"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# run_agent — Parte 4
# ---------------------------------------------------------------------------

def run_agent(
    query: str,
    client: OpenAI,
    sbx: Sandbox,
    messages: list = None,
    system: str = SYSTEM_PROMPT_WEB_DEV,
    max_steps: int = MAX_STEPS,
) -> tuple[list, str]:
    """
    Ejecuta el agente full stack con compresión de contexto automática.

    Parámetros
    ----------
    query     : instrucción del usuario en lenguaje natural
    client    : cliente OpenAI (GitHub Models)
    sbx       : sandbox E2B activo
    messages  : historial de conversación (se modifica in-place)
    system    : system prompt (por defecto SYSTEM_PROMPT_WEB_DEV)
    max_steps : parada de seguridad

    Retorna
    -------
    (messages, last_text)
    """
    if messages is None:
        messages = []

    # Agregar mensaje del usuario
    messages.append({"role": "user", "content": [{"text": query}]})
    last_text = ""

    print(f"\n{'='*60}")
    print(f"[agente] 🚀 Nueva tarea: {query[:80]}...")
    print(f"{'='*60}")

    for step in range(max_steps):
        # ── Compresión de contexto si hace falta ──────────────────────────
        compressed = maybe_compress(messages, client)
        if compressed is not messages:
            messages.clear()
            messages.extend(compressed)

        # ── Llamada al LLM ────────────────────────────────────────────────
        response = llm(client, messages, system, tools=TOOLS_SCHEMAS)
        messages.append(response.assistant_message())

        print(f"\n[paso #{step + 1}]")

        has_tool_call = False
        tool_results  = []

        for part in response.output:
            if part.type == "message":
                last_text = part.content
                # Mostrar solo los primeros 300 chars para no saturar la consola
                preview = part.content[:300].replace("\n", " ")
                print(f"  💬 {preview}{'…' if len(part.content) > 300 else ''}")

            elif part.type == "function_call":
                has_tool_call = True
                name = part.name

                # Mostrar resumen del tool call
                try:
                    args_preview = json.loads(part.arguments)
                    if "content" in args_preview:
                        # No imprimir archivos completos
                        args_preview["content"] = f"<{len(args_preview['content'])} chars>"
                    print(f"  🔧 {name}({json.dumps(args_preview, ensure_ascii=False)[:120]})")
                except Exception:
                    print(f"  🔧 {name}(...)")

                result = execute_tool(name, part.arguments, TOOLS_IMPL, sbx=sbx)

                # Mostrar resultado resumido
                if "error" in result:
                    print(f"  ❌ Error: {result['error'][:200]}")
                elif "entries" in result:
                    print(f"  ✅ {len(result['entries'])} entradas")
                elif "message" in result:
                    print(f"  ✅ {result['message']}")
                else:
                    preview = str(result)[:120]
                    print(f"  ✅ {preview}")

                tool_results.append({
                    "toolResult": {
                        "toolUseId": part.call_id,
                        "content":   [{"json": result}],
                    }
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        # ── Condición de parada ───────────────────────────────────────────
        if not has_tool_call:
            print(f"\n[agente] ✅ Tarea completada en {step + 1} paso(s).")
            break
    else:
        print(f"\n[agente] ⚠️  Límite de {max_steps} pasos alcanzado.")

    return messages, last_text
