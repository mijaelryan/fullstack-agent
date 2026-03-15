from dotenv import load_dotenv
load_dotenv()

import os
from e2b_code_interpreter import Sandbox
from lib.sbx_tools import list_directory, read_file, search_file_content, write_file

os.environ["E2B_API_KEY"] = os.environ["E2B_API_KEY"]
sbx = Sandbox.create(timeout=300)

# Setup
write_file(sbx, "/home/user/workspace/test/index.tsx", "'use client';\nexport default function Page() { return <h1>hola</h1> }")

# Las tres que fallaban
r = list_directory(sbx, "/home/user/workspace/test")
print("list_directory:", r)

r = read_file(sbx, "/home/user/workspace/test/index.tsx")
print("read_file:", r)

r = search_file_content(sbx, "hola", path="/home/user/workspace/test")
print("search_file_content:", r)

sbx.kill()
print("\n✅ OK")