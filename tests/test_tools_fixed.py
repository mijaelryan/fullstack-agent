"""
test_tools_fixed.py
Prueba específica para las herramientas que fallaban en v1.0 cuando se
usaban sobre rutas dentro de workspace/ en lugar de /home/user/.

Qué prueba:
  list_directory, read_file, search_file_content sobre /home/user/workspace/

Ejecutar desde la raíz del proyecto:
  PYTHONPATH=. python tests/test_tools_fixed.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

from e2b_code_interpreter import Sandbox
from lib.sbx_tools import list_directory, read_file, search_file_content, write_file

print("⏳ Creando sandbox E2B...")
sbx = Sandbox.create(timeout=300)
print(f"✅ Sandbox creado (id: {sbx.sandbox_id})")
print()

# Setup — crear archivo de prueba en workspace/
sbx_path = "/home/user/workspace/test/index.tsx"
write_file(sbx, sbx_path, "'use client';\nexport default function Page() { return <h1>hola</h1> }")
print(f"  [sandbox] Archivo creado en: {sbx_path}")
print()

# ── list_directory ────────────────────────────────────────────────────────
print("── list_directory sobre workspace/ ──")
r = list_directory(sbx, "/home/user/workspace/test")
print(f"  [sandbox] {r}")

# ── read_file ─────────────────────────────────────────────────────────────
print("── read_file sobre workspace/ ──")
r = read_file(sbx, sbx_path)
print(f"  [sandbox] {r}")

# ── search_file_content ───────────────────────────────────────────────────
print("── search_file_content sobre workspace/ ──")
r = search_file_content(sbx, "hola", path="/home/user/workspace/test")
print(f"  [sandbox] {r}")

# ── Cerrar sandbox ────────────────────────────────────────────────────────
print()
print("⏳ Cerrando sandbox...")
sbx.kill()
print("✅ Sandbox cerrado")
print()
print("✅ OK")
