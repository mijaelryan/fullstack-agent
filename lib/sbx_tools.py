"""
lib/sbx_tools.py
Herramientas de sistema de archivos para el sandbox E2B.
"""

import json
from typing import Any, Dict, Optional
from e2b_code_interpreter import Sandbox


class ToolError(Exception):
    pass


def _run(sbx: Sandbox, code: str) -> str:
    execution = sbx.run_code(code)
    if execution.error:
        raise ToolError(f"{execution.error.name}: {execution.error.value}")
    stderr = [str(s) for s in execution.logs.stderr] if execution.logs.stderr else []
    if stderr:
        raise ToolError("\n".join(stderr))
    return "".join(str(s) for s in execution.logs.stdout) if execution.logs.stdout else ""


def list_directory(sbx: Sandbox, path: str = ".") -> Dict[str, Any]:
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
    except Exception as e:
        return {"error": str(e)}


def read_file(sbx: Sandbox, path: str, limit: Optional[int] = None, offset: int = 0) -> Dict[str, Any]:
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
    except Exception as e:
        return {"error": str(e)}


def write_file(sbx: Sandbox, path: str, content: str) -> Dict[str, Any]:
    try:
        sbx.files.write(path, content)
        return {"message": f"✅ Escrito: {path}", "path": path, "size": len(content)}
    except Exception:
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
        except ToolError as e:
            return {"error": str(e)}


def search_file_content(sbx: Sandbox, pattern: str, path: str = ".", max_results: int = 20, page: int = 0) -> Dict[str, Any]:
    try:
        code = f"""
import os, re, json
pattern = re.compile({repr(pattern)})
root    = {repr(path)}
matches = []
EXCLUDE = {"node_modules", ".next", ".git", "dist", "build"}
for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d not in EXCLUDE]
    for fname in filenames:
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if pattern.search(line):
                        matches.append({{"file": fpath, "line_number": i, "line": line.rstrip()}})
        except Exception:
            continue
page       = {page}
per_page   = {max_results}
start      = page * per_page
end        = start + per_page
print(json.dumps({{"matches": matches[start:end], "total": len(matches), "page": page, "has_more": end < len(matches)}}))
"""
        output = _run(sbx, code)
        return json.loads(output)
    except Exception as e:
        return {"error": str(e)}


def replace_in_file(sbx: Sandbox, path: str, old: str, new: str) -> Dict[str, Any]:
    try:
        code = f"""
with open({repr(path)}, "r", encoding="utf-8") as f:
    content = f.read()
count = 0
if {repr(old)} in content:
    content = content.replace({repr(old)}, {repr(new)}, 1)
    count = 1
with open({repr(path)}, "w", encoding="utf-8") as f:
    f.write(content)
print(count)
"""
        count_str = _run(sbx, code).strip()
        count = int(count_str) if count_str.isdigit() else 0
        if count == 0:
            return {"error": f"Texto no encontrado en {path}"}
        return {"message": f"✅ Reemplazado en {path}", "replacements": count}
    except Exception as e:
        return {"error": str(e)}


def glob(sbx: Sandbox, pattern: str, path: str = ".") -> Dict[str, Any]:
    try:
        code = f"""
import glob as _glob, json, os
matches = _glob.glob(os.path.join({repr(path)}, {repr(pattern)}), recursive=True)
print(json.dumps(sorted(matches)))
"""
        output = _run(sbx, code)
        files = json.loads(output)
        return {"pattern": pattern, "path": path, "files": files, "count": len(files)}
    except Exception as e:
        return {"error": str(e)}


def execute_bash(sbx: Sandbox, cmd: str, workdir: str = "/home/user/workspace") -> Dict[str, Any]:
    try:
        code = f"""
import subprocess, os
result = subprocess.run({repr(cmd)}, shell=True, capture_output=True, text=True, cwd={repr(workdir)})
import json
print(json.dumps({{"stdout": result.stdout[:4000], "stderr": result.stderr[:4000], "exit_code": result.returncode}}))
"""
        # Usar run_code directamente para capturar stdout sin que stderr aborte
        execution = sbx.run_code(code)
        output = "".join(str(s) for s in execution.logs.stdout) if execution.logs.stdout else ""
        if not output:
            return {"error": "Sin output del sandbox", "success": False}
        data = json.loads(output.strip())
        success = data["exit_code"] == 0
        data["success"] = success
        data["message"] = "✅ Comando exitoso" if success else f"❌ Error (exit {data['exit_code']}): {data['stderr'][:300]}"
        return data
    except Exception as e:
        return {"error": str(e), "success": False}


TOOLS_IMPL = {
    "list_directory":      list_directory,
    "read_file":           read_file,
    "write_file":          write_file,
    "search_file_content": search_file_content,
    "replace_in_file":     replace_in_file,
    "glob":                glob,
    "execute_bash":        execute_bash,
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
                "path":   {"type": "string",  "description": "Ruta del archivo"},
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
    {
        "type": "function",
        "name": "execute_bash",
        "description": "Ejecuta un comando bash en el sandbox. Usalo para npm install, npm run build, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "cmd":     {"type": "string", "description": "Comando bash a ejecutar"},
                "workdir": {"type": "string", "description": "Directorio de trabajo (default /home/user/workspace)"},
            },
            "required": ["cmd"],
            "additionalProperties": False,
        },
    },
]
