"""
test_download.py
Prueba la descarga del sandbox al sistema local, incluyendo archivos binarios.

Qué prueba:
  1. Crea archivos de texto en el sandbox (simula lo que haría el agente)
  2. Sube una imagen real desde la PC local al sandbox con upload_file
  3. Descarga todo el proyecto al sistema local con download_workspace
  4. Verifica que todos los archivos existen localmente y que la imagen
     no fue corrompida durante la bajada (tamaño coincide con el original)

Archivos de texto → creados en sandbox E2B
Imagen de prueba  → creada en tu PC local, subida al sandbox, luego descargada

Ejecutar desde la raíz del proyecto:
  PYTHONPATH=. python tests/test_download.py
"""

import os
import struct
import zlib
from dotenv import load_dotenv
load_dotenv()

from e2b_code_interpreter import Sandbox
from lib.sbx_tools import write_file, upload_file
from lib.sbx_download import download_workspace

# ── Crear sandbox ─────────────────────────────────────────────────────────
print("⏳ Creando sandbox E2B...")
sbx = Sandbox.create(timeout=300)
print(f"✅ Sandbox creado (id: {sbx.sandbox_id})")
print()

# ── Paso 1: crear archivos de texto en el sandbox ─────────────────────────
print("── Paso 1: crear archivos de texto en el sandbox ──")
write_file(sbx, "/home/user/workspace/test-app/package.json",      '{"name": "test-app"}')
write_file(sbx, "/home/user/workspace/test-app/app/page.tsx",       'export default function Page() { return <h1>Hola</h1> }')
write_file(sbx, "/home/user/workspace/test-app/components/Button.tsx", 'export default function Button() { return <button>Click</button> }')
print("  [sandbox] 3 archivos de texto creados en /home/user/workspace/test-app/")

# ── Paso 2: subir imagen desde la PC al sandbox ───────────────────────────
print()
print("── Paso 2: subir imagen local al sandbox con upload_file ──")

def _make_minimal_png(path: str) -> int:
    """Genera un PNG 1x1 px válido. Devuelve su tamaño en bytes."""
    def chunk(name, data):
        c = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", c)

    png  = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

local_img  = "tests/test_banner.png"
sbx_img    = "/home/user/workspace/test-app/public/test_banner.png"
local_size = _make_minimal_png(local_img)
print(f"  [local PC] Imagen creada: {local_img} ({local_size} bytes)")

r = upload_file(sbx, local_path=local_img, sbx_path=sbx_img)
print(f"  [sandbox]  {r['message']}")

# ── Paso 3: descargar todo el proyecto ────────────────────────────────────
print()
print("── Paso 3: descargar proyecto del sandbox a workspace/ local ──")
local_path = download_workspace(sbx, "/home/user/workspace/test-app", local_root="workspace")
print(f"  [local PC] Descargado en: {local_path}")

# ── Paso 4: verificar archivos ────────────────────────────────────────────
print()
print("── Paso 4: verificar archivos descargados ──")

text_files = [
    "package.json",
    "app/page.tsx",
    "components/Button.tsx",
]

all_ok = True
for f in text_files:
    full   = os.path.join(local_path, f)
    exists = os.path.exists(full)
    all_ok = all_ok and exists
    print(f"  {'✅' if exists else '❌'} [local PC] {full}")

# Verificar imagen: debe existir y tener el mismo tamaño que el original
img_local = os.path.join(local_path, "public/test_banner.png")
if os.path.exists(img_local):
    downloaded_size = os.path.getsize(img_local)
    match = downloaded_size == local_size
    all_ok = all_ok and match
    print(f"  {'✅' if match else '❌'} [local PC] {img_local}")
    print(f"       tamaño original: {local_size} bytes | descargado: {downloaded_size} bytes"
          + (" → coincide ✅" if match else " → NO coincide ❌ (imagen corrompida)"))
else:
    all_ok = False
    print(f"  ❌ [local PC] {img_local} → no existe")

# ── Limpiar temporal local ────────────────────────────────────────────────
os.remove(local_img)
print()
print("  [local PC] Archivo temporal de prueba eliminado")

# ── Cerrar sandbox ────────────────────────────────────────────────────────
print()
print("⏳ Cerrando sandbox...")
sbx.kill()
print("✅ Sandbox cerrado")
print()
print("✅ Test de descarga OK" if all_ok else "❌ Alguna verificación falló — revisá los detalles arriba")
