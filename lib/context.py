"""
lib/context.py
Compresión de contexto (Runtime Summary).

Cuando el historial de mensajes supera MAX_TOKENS, tomamos el 70% más
antiguo, lo resumimos con el LLM y lo reemplazamos por dos mensajes
(user + assistant) que contienen el resumen.  Así el agente nunca se
queda sin ventana de contexto en tareas largas.
"""

import json

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

MAX_TOKENS        = 6_000   # tope en tokens estimados antes de comprimir
COMPRESSION_RATIO = 0.70     # fracción de mensajes antiguos a comprimir


# ---------------------------------------------------------------------------
# Conteo de tokens (estimación rápida, ~4 chars/token)
# ---------------------------------------------------------------------------

def count_tokens(messages: list) -> int:
    """
    Estimación de tokens consumidos por una lista de mensajes.
    Usa la heurística ~4 caracteres = 1 token, que es suficientemente
    precisa para decidir cuándo comprimir.
    """
    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    # cubre {"text": "..."}, {"toolResult": {...}}, etc.
                    total_chars += len(json.dumps(part))
        else:
            total_chars += len(str(content))
    return total_chars // 4


# ---------------------------------------------------------------------------
# Núcleo: comprimir el 70% más antiguo
# ---------------------------------------------------------------------------

def compress_context(messages: list, llm_client) -> list:
    """
    Comprime el COMPRESSION_RATIO (70%) de los mensajes más antiguos.

    Proceso:
    1. Divide messages en:  old_msgs (70%) + recent_msgs (30%)
    2. Serializa old_msgs como texto plano
    3. Llama al LLM para que genere un resumen conciso
    4. Retorna:  [resumen_user, resumen_assistant] + recent_msgs

    Parámetros
    ----------
    messages   : historial actual en formato normalizado
    llm_client : cliente OpenAI-compatible (GitHub Models)

    Retorna
    -------
    Lista de mensajes comprimida (más corta que la original).
    """
    if len(messages) < 4:
        # Muy pocos mensajes: no vale la pena comprimir
        return messages

    cut = max(2, int(len(messages) * COMPRESSION_RATIO))

    # Nunca cortar en medio de un par tool_call / tool_result
    # Retroceder hasta encontrar un mensaje "user" limpio (sin toolResult)
    while cut > 0 and cut < len(messages):
        msg = messages[cut]
        content_parts = msg.get("content", [])
        if isinstance(content_parts, list):
            has_tool_result = any(
                isinstance(p, dict) and "toolResult" in p
                for p in content_parts
            )
            if has_tool_result:
                cut += 1
                continue
        break

    old_msgs    = messages[:cut]
    recent_msgs = messages[cut:]

    # Serializar historial antiguo como texto legible
    history_text = _serialize_messages(old_msgs)

    # Pedir al LLM un resumen técnico del historial
    summary_prompt = (
        "Eres un asistente técnico. A continuación tienes el historial de una "
        "conversación entre un usuario y un agente de desarrollo web. "
        "Resume en español, de forma concisa pero completa, qué se pidió, "
        "qué decisiones tomó el agente, qué archivos creó o modificó y "
        "cuál es el estado actual del proyecto. "
        "El resumen será usado como memoria comprimida para continuar el trabajo.\n\n"
        f"HISTORIAL:\n{history_text}"
    )

    try:
        response = llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=1000,
        )
        summary_text = response.choices[0].message.content.strip()
    except Exception as e:
        # Si falla el resumen, devolvemos los mensajes sin comprimir
        print(f"[context] ⚠️  No se pudo comprimir: {e}")
        return messages

    # Construir los dos mensajes de reemplazo
    resumen_user = {
        "role": "user",
        "content": [{
            "text": (
                "[RESUMEN DE CONVERSACIÓN ANTERIOR]\n"
                "El siguiente texto resume el contexto previo para ahorrar tokens:\n\n"
                f"{summary_text}"
            )
        }],
    }
    resumen_assistant = {
        "role": "assistant",
        "content": [{
            "text": (
                "Entendido. Tengo en cuenta el resumen del trabajo anterior "
                "y continúo desde donde quedamos."
            )
        }],
    }

    compressed = [resumen_user, resumen_assistant] + recent_msgs
    tokens_before = count_tokens(messages)
    tokens_after  = count_tokens(compressed)
    print(
        f"[context] 🗜️  Contexto comprimido: "
        f"{tokens_before:,} → {tokens_after:,} tokens estimados "
        f"({len(messages)} → {len(compressed)} mensajes)"
    )
    return compressed


# ---------------------------------------------------------------------------
# Punto de entrada: comprimir solo si supera el límite
# ---------------------------------------------------------------------------

def maybe_compress(messages: list, llm_client) -> list:
    """
    Comprime el contexto solo si count_tokens(messages) >= MAX_TOKENS.
    Llamar esta función al inicio de cada iteración del agente.
    """
    current = count_tokens(messages)
    if current >= MAX_TOKENS:
        print(f"[context] ⚡ Límite alcanzado ({current:,} tokens), comprimiendo…")
        return compress_context(messages, llm_client)
    return messages


# ---------------------------------------------------------------------------
# Helper: serializar mensajes como texto plano para el resumen
# ---------------------------------------------------------------------------

def _serialize_messages(messages: list) -> str:
    """Convierte una lista de mensajes a texto plano legible."""
    lines = []
    for msg in messages:
        role    = msg.get("role", "?").upper()
        content = msg.get("content", "")

        if isinstance(content, str):
            lines.append(f"[{role}]: {content}")
        elif isinstance(content, list):
            parts = []
            for part in content:
                if not isinstance(part, dict):
                    parts.append(str(part))
                    continue
                if "text" in part:
                    parts.append(part["text"])
                elif "toolResult" in part:
                    tr = part["toolResult"]
                    result_data = tr.get("content", [{}])
                    result_str  = json.dumps(result_data[0].get("json", result_data))
                    parts.append(f"[tool_result id={tr.get('toolUseId','')}]: {result_str[:300]}")
                elif "tool_use" in part:
                    tu = part["tool_use"]
                    parts.append(
                        f"[tool_call name={tu.get('name','')} id={tu.get('toolUseId','')}]: "
                        f"{json.dumps(tu.get('input', {}))[:200]}"
                    )
            lines.append(f"[{role}]: " + " | ".join(parts))
        else:
            lines.append(f"[{role}]: {json.dumps(content)[:300]}")

    return "\n".join(lines)
