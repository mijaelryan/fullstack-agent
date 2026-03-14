"""
lib/sbx_tools.py
Herramientas de sistema de archivos para el sandbox E2B.
El agente las usa para leer, escribir y navegar el proyecto generado.
"""

import json
import re
from typing import Any, Dict, Optional
from e2b_code_interpreter import Sandbox


# ---------------------------------------------------------------------------
# Excepción base
# ---------------------------------------------------------------------------

class ToolError(Exception):
    """Error controlado dentro de una herramienta del sandbox."""
    pass


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _run(sbx: Sandbox, code: str) -> str:
    """Ejecuta código Python en el sandbox y retorna stdout, o lanza ToolError."""
    execution = sbx.run_code(code)
    if execution.error:
        raise ToolError(f"{execution.error.name}: {execution.error.value}")
    stderr = list(execution.logs.stderr) if execution.logs.stderr else []
    if stderr:
        raise ToolError("\n".join(stderr))
    return "".join(execution.logs.stdout) if execution.logs.stdout else ""


def _run_bash(sbx: Sandbox, cmd: str) -> str:
    """Ejecuta un comando bash en el sandbox y retorna stdout, o lanza ToolError."""
    code = f"""
import subprocess
result = subprocess.run({repr(cmd)}, shell=True, capture_output=True, text=True)
if result.returncode != 0:
    raise RuntimeError(result.stderr.strip() or f"exit code {{result.returncode}}")
print(result.stdout, end="")
"""
    return _run(sbx, code)


# ---------------------------------------------------------------------------
# Parte 1 — Herramientas públicas
# ---------------------------------------------------------------------------

def list_directory(sbx: Sandbox, path: str = ".") -> Dict[str, Any]:
    """
    Lista archivos y carpetas en `path` dentro del sandbox.
    Retorna un dict con 'entries': lista de {name, type, size}.
    """
    try:
        code = f"""
import os, json
entries = []
base = {repr(path)}
for name in sorted(os.listdir(base)):
    full = os.path.join(base, name)
    entries.append({{
        "name": name,
        "type": "dir" if os.path.isdir(full) else "file",
        "size": os.path.getsize(full) if os.path.isfile(full) else None,
    }})
print(json.dumps(entries))
"""
        output = _run(sbx, code)
        return {"path": path, "entries": json.loads(output)}
    except ToolError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def read_file(
    sbx: Sandbox,
    path: str,
    limit: Optional[int] = None,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Lee el contenido de un archivo en el sandbox.
    Soporta `offset` (byte de inicio) y `limit` (máx. caracteres).
    """
    try:
        limit_expr = str(limit) if limit is not None else ""
        code = f"""
with open({repr(path)}, "r", encoding="utf-8") as f:
    f.seek({offset})
    content = f.read({limit_expr})
print(content, end="")
"""
        content = _run(sbx, code)
        return {"path": path, "content": content, "size": len(content)}
    except ToolError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def write_file(sbx: Sandbox, path: str, content: str) -> Dict[str, Any]:
    """
    Escribe `content` en `path` dentro del sandbox.
    Crea los directorios intermedios si no existen.
    """
    try:
        # sbx.files.write es la forma más directa y evita problemas de escaping
        sbx.files.write(path, content)
        return {"message": f"✅ Escrito: {path}", "path": path, "size": len(content)}
    except Exception as e:
        # Fallback: crear dirs y escribir vía Python
        try:
            code = f"""
import os
os.makedirs(os.path.dirname({repr(path)}) or ".", exist_ok=True)
with open({repr(path)}, "w", encoding="utf-8") as f:
    f.write({repr(content)})
print("ok")
"""
            _run(sbx, code)
            return {"message": f"✅ Escrito: {path}", "path": path, "size": len(content)}
        except ToolError as e2:
            return {"error": str(e2)}


def search_file_content(
    sbx: Sandbox,
    pattern: str,
    path: str = ".",
    max_results: int = 20,
    page: int = 0,
) -> Dict[str, Any]:
    """
    Busca `pattern` (regex) en todos los archivos bajo `path`.
    Devuelve JSON paginado: {matches, total, page, has_more}.
    Cada match: {file, line_number, line}.
    """
    try:
        code = f"""
import os, re, json

pattern = re.compile({repr(pattern)})
root    = {repr(path)}
matches = []

for dirpath, _, filenames in os.walk(root):
    for fname in filenames:
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if pattern.search(line):
                        matches.append({{
                            "file":        fpath,
                            "line_number": i,
                            "line":        line.rstrip(),
                        }})
        except Exception:
            continue

page       = {page}
per_page   = {max_results}
start      = page * per_page
end        = start + per_page
page_items = matches[start:end]

print(json.dumps({{
    "matches":  page_items,
    "total":    len(matches),
    "page":     page,
    "has_more": end < len(matches),
}}))
"""
        output = _run(sbx, code)
        return json.loads(output)
    except ToolError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def replace_in_file(sbx: Sandbox, path: str, old: str, new: str) -> Dict[str, Any]:
    """
    (Opcional) Reemplaza la primera ocurrencia de `old` por `new` en `path`.
    Retorna cuántas sustituciones se hicieron.
    """
    try:
        code = f"""
with open({repr(path)}, "r", encoding="utf-8") as f:
    content = f.read()

new_content, count = {repr(old)}, 0
if {repr(old)} in content:
    new_content = content.replace({repr(old)}, {repr(new)}, 1)
    count = 1

with open({repr(path)}, "w", encoding="utf-8") as f:
    f.write(new_content)

print(count)
"""
        count_str = _run(sbx, code).strip()
        count = int(count_str) if count_str.isdigit() else 0
        if count == 0:
            return {"error": f"Texto no encontrado en {path}"}
        return {"message": f"✅ Reemplazado en {path}", "replacements": count}
    except ToolError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def glob(sbx: Sandbox, pattern: str, path: str = ".") -> Dict[str, Any]:
    """
    (Opcional) Busca archivos por nombre/extensión usando glob.
    Ej: pattern='**/*.tsx', path='/app'
    """
    try:
        code = f"""
import glob as _glob, json, os
matches = _glob.glob(os.path.join({repr(path)}, {repr(pattern)}), recursive=True)
print(json.dumps(sorted(matches)))
"""
        output = _run(sbx, code)
        files = json.loads(output)
        return {"pattern": pattern, "path": path, "files": files, "count": len(files)}
    except ToolError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Registry: función → implementación + schema OpenAI
# ---------------------------------------------------------------------------

TOOLS_IMPL = {
    "list_directory":      list_directory,
    "read_file":           read_file,
    "write_file":          write_file,
    "search_file_content": search_file_content,
    "replace_in_file":     replace_in_file,
    "glob":                glob,
}

TOOLS_SCHEMAS = [
    {
        "type": "function",
        "name": "list_directory",
        "description": "Lista archivos y carpetas en un directorio del sandbox.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta del directorio (default '.')"},
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Lee el contenido de un archivo en el sandbox.",
        "parameters": {
            "type": "object",
            "properties": {
                "path":   {"type": "string", "description": "Ruta del archivo"},
                "limit":  {"type": "integer", "description": "Máx. caracteres a leer"},
                "offset": {"type": "integer", "description": "Byte de inicio"},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "write_file",
        "description": "Escribe contenido en un archivo del sandbox (crea dirs intermedios).",
        "parameters": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "Ruta del archivo"},
                "content": {"type": "string", "description": "Contenido a escribir"},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search_file_content",
        "description": "Busca un patrón regex en archivos del sandbox. Devuelve resultados paginados.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern":     {"type": "string",  "description": "Patrón regex a buscar"},
                "path":        {"type": "string",  "description": "Directorio raíz (default '.')"},
                "max_results": {"type": "integer", "description": "Resultados por página (default 20)"},
                "page":        {"type": "integer", "description": "Número de página (default 0)"},
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "replace_in_file",
        "description": "Reemplaza la primera ocurrencia de un texto en un archivo del sandbox.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta del archivo"},
                "old":  {"type": "string", "description": "Texto a reemplazar"},
                "new":  {"type": "string", "description": "Texto nuevo"},
            },
            "required": ["path", "old", "new"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "glob",
        "description": "Busca archivos por nombre o extensión usando glob (ej: '**/*.tsx').",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Patrón glob"},
                "path":    {"type": "string", "description": "Directorio raíz (default '.')"},
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
    },
]
