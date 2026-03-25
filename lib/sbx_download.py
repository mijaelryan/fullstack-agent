"""
lib/sbx_download.py
Descarga una carpeta del sandbox E2B al sistema de archivos local (workspace/).
"""

import os
import base64
import json
from e2b_code_interpreter import Sandbox

# Extensiones que deben tratarse como binario
BINARY_EXT = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".wav", ".ogg",
    ".pdf", ".zip", ".gz",
}


def download_workspace(sbx: Sandbox, sbx_path: str, local_root: str = "workspace") -> str:
    """
    Descarga recursivamente `sbx_path` del sandbox a `local_root/`.

    Ejemplo:
        sbx_path  = "/home/user/workspace/todo-app"
        resultado = "workspace/todo-app"

    Retorna la ruta local donde quedó guardado el proyecto.
    """
    project_name = sbx_path.rstrip("/").split("/")[-1]
    local_path   = os.path.join(local_root, project_name)

    # Obtener lista de todos los archivos en el sandbox
    files = _list_all_files(sbx, sbx_path)
    # Excluir node_modules y .next — se recrean con npm install
    EXCLUDE = {"/node_modules/", "/.next/"}
    files = [f for f in files if not any(ex in f for ex in EXCLUDE)]

    if not files:
        print(f"[download] ⚠️  No se encontraron archivos en {sbx_path}")
        return local_path

    downloaded = 0
    for remote_file in files:
        relative   = os.path.relpath(remote_file, sbx_path)
        local_file = os.path.join(local_path, relative)
        os.makedirs(os.path.dirname(local_file), exist_ok=True)

        ext       = os.path.splitext(remote_file)[1].lower()
        is_binary = ext in BINARY_EXT

        try:
            if is_binary:
                # Leer como base64 desde el sandbox para que los bytes
                # lleguen intactos sin que E2B los interprete como texto.
                b64 = _read_file_b64(sbx, remote_file)
                with open(local_file, "wb") as f:
                    f.write(base64.b64decode(b64))
            else:
                content = sbx.files.read(remote_file)
                with open(local_file, "w", encoding="utf-8") as f:
                    f.write(content if isinstance(content, str) else content.decode("utf-8"))
            downloaded += 1
        except Exception as e:
            print(f"[download] ⚠️  No se pudo descargar {remote_file}: {e}")

    print(f"[download] ✅ {downloaded} archivo(s) descargados → {local_path}")
    return local_path


def _read_file_b64(sbx: Sandbox, path: str) -> str:
    """Lee un archivo binario del sandbox y lo devuelve como string base64."""
    code = f"""
import base64
with open({repr(path)}, "rb") as f:
    print(base64.b64encode(f.read()).decode("utf-8"), end="")
"""
    execution = sbx.run_code(code)
    return "".join(execution.logs.stdout).strip()


def _list_all_files(sbx: Sandbox, path: str) -> list[str]:
    """Lista recursivamente todos los archivos bajo `path` en el sandbox."""
    code = f"""
import os, json
files = []
for dirpath, _, filenames in os.walk({repr(path)}):
    for fname in filenames:
        files.append(os.path.join(dirpath, fname))
print(json.dumps(files))
"""
    execution = sbx.run_code(code)
    stdout = "".join(execution.logs.stdout).strip()
    if not stdout:
        return []
    try:
        return json.loads(stdout)
    except Exception:
        return []
