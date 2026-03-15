"""
lib/sbx_download.py
Descarga una carpeta del sandbox E2B al sistema de archivos local (workspace/).
"""

import os
from e2b_code_interpreter import Sandbox


def download_workspace(sbx: Sandbox, sbx_path: str, local_root: str = "workspace") -> str:
    """
    Descarga recursivamente `sbx_path` del sandbox a `local_root/`.

    Ejemplo:
        sbx_path  = "/home/user/workspace/todo-app"
        resultado = "workspace/todo-app"

    Retorna la ruta local donde quedó guardado el proyecto.
    """
    # Nombre de la carpeta destino (último segmento de la ruta)
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
        # Ruta relativa respecto a sbx_path
        relative = os.path.relpath(remote_file, sbx_path)
        local_file = os.path.join(local_path, relative)

        # Crear directorios intermedios
        os.makedirs(os.path.dirname(local_file), exist_ok=True)

        # Descargar contenido
        try:
            content = sbx.files.read(remote_file)
            if isinstance(content, bytes):
                with open(local_file, "wb") as f:
                    f.write(content)
            else:
                with open(local_file, "w", encoding="utf-8") as f:
                    f.write(content)
            downloaded += 1
        except Exception as e:
            print(f"[download] ⚠️  No se pudo descargar {remote_file}: {e}")

    print(f"[download] ✅ {downloaded} archivo(s) descargados → {local_path}")
    return local_path


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
    import json
    try:
        return json.loads(stdout)
    except Exception:
        return []
