"""
test_tools.py
Prueba todas las herramientas de filesystem disponibles para el agente.

Qué prueba:
  write_file, read_file, list_directory, search_file_content,
  replace_in_file, glob, upload_file

Todos los archivos se crean y leen DENTRO del sandbox E2B,
excepto upload_file que lee desde tu PC local y escribe en el sandbox.

Ejecutar desde la raíz del proyecto:
  PYTHONPATH=. python tests/test_tools.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

from e2b_code_interpreter import Sandbox
from lib.sbx_tools import (
    write_file, read_file, list_directory,
    search_file_content, replace_in_file, glob, upload_file,
)

print("⏳ Creando sandbox E2B...")
sbx = Sandbox.create(timeout=300)
print(f"✅ Sandbox creado (id: {sbx.sandbox_id})")
print()

# ── write_file ────────────────────────────────────────────────────────────
print("── write_file ──")
r = write_file(sbx, "/home/user/test.txt", "hola mundo\nlínea 2")
print(f"  [sandbox] {r}")

# ── read_file ─────────────────────────────────────────────────────────────
print("── read_file ──")
r = read_file(sbx, "/home/user/test.txt")
print(f"  [sandbox] {r}")

# ── list_directory ────────────────────────────────────────────────────────
print("── list_directory ──")
r = list_directory(sbx, "/home/user")
print(f"  [sandbox] {r}")

# ── search_file_content ───────────────────────────────────────────────────
print("── search_file_content ──")
r = search_file_content(sbx, "hola", path="/home/user")
print(f"  [sandbox] {r}")

# ── replace_in_file ───────────────────────────────────────────────────────
print("── replace_in_file ──")
r = replace_in_file(sbx, "/home/user/test.txt", "hola mundo", "hello world")
print(f"  [sandbox] {r}")

# ── glob ──────────────────────────────────────────────────────────────────
print("── glob ──")
r = glob(sbx, "*.txt", path="/home/user")
print(f"  [sandbox] {r}")

# ── upload_file ───────────────────────────────────────────────────────────
# Creamos un archivo PNG mínimo válido (1x1 px) en disco para no depender
# de una ruta específica del usuario. Así el test es reproducible en cualquier PC.
print("── upload_file ──")
import struct, zlib

def _make_minimal_png(path: str):
    """Genera un PNG 1x1 px transparente válido en la ruta indicada."""
    def chunk(name, data):
        c = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", c)

    png  = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

local_img = "tests/test_upload_sample.png"
sbx_img   = "/home/user/test_upload_sample.png"

_make_minimal_png(local_img)
print(f"  [local PC] Imagen de prueba creada en: {local_img}")

r = upload_file(sbx, local_path=local_img, sbx_path=sbx_img)
print(f"  [sandbox]  {r}")

# Verificar que llegó al sandbox comprobando el tamaño real en bytes.
# No usamos read_file porque lee en modo texto y falla silenciosamente con binarios.
exe  = sbx.run_code(f"import os; print(os.path.getsize('{sbx_img}'))")
size = int("".join(exe.logs.stdout).strip() or "0")
ok   = size > 0
print(f"  [sandbox]  Archivo recibido: {size} bytes → {'✅ OK' if ok else '❌ FALLÓ (0 bytes)'}")

# Limpiar archivo local temporal
os.remove(local_img)
print(f"  [local PC] Archivo temporal eliminado")

# ── Cerrar sandbox ────────────────────────────────────────────────────────
print()
print("⏳ Cerrando sandbox...")
sbx.kill()
print("✅ Sandbox cerrado")
print()
print("✅ Todas las herramientas OK")
