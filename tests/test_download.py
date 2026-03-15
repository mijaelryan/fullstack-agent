from dotenv import load_dotenv
load_dotenv()

import os
from e2b_code_interpreter import Sandbox
from lib.sbx_tools import write_file
from lib.sbx_download import download_workspace

os.environ["E2B_API_KEY"] = os.environ["E2B_API_KEY"]
sbx = Sandbox.create(timeout=300)

# Simular que el agente creó un proyecto
write_file(sbx, "/home/user/workspace/test-app/package.json", '{"name": "test-app"}')
write_file(sbx, "/home/user/workspace/test-app/app/page.tsx", 'export default function Page() { return <h1>Hola</h1> }')
write_file(sbx, "/home/user/workspace/test-app/components/Button.tsx", 'export default function Button() { return <button>Click</button> }')

print("Archivos creados en sandbox ✔")

# Descargar
local_path = download_workspace(sbx, "/home/user/workspace/test-app", local_root="workspace")

# Verificar que existen localmente
for f in ["package.json", "app/page.tsx", "components/Button.tsx"]:
    full = os.path.join(local_path, f)
    exists = os.path.exists(full)
    print(f"  {'✅' if exists else '❌'} {full}")

sbx.kill()