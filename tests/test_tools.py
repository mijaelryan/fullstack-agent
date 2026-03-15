from dotenv import load_dotenv
load_dotenv()

import os
from e2b_code_interpreter import Sandbox
from lib.sbx_tools import write_file, read_file, list_directory, search_file_content, replace_in_file, glob

os.environ["E2B_API_KEY"] = os.environ["E2B_API_KEY"]
sbx = Sandbox.create(timeout=300)

# write
r = write_file(sbx, "/home/user/test.txt", "hola mundo\nlínea 2")
print("write:", r)

# read
r = read_file(sbx, "/home/user/test.txt")
print("read:", r)

# list
r = list_directory(sbx, "/home/user")
print("list:", r)

# search
r = search_file_content(sbx, "hola", path="/home/user")
print("search:", r)

# replace
r = replace_in_file(sbx, "/home/user/test.txt", "hola mundo", "hello world")
print("replace:", r)

# glob
r = glob(sbx, "*.txt", path="/home/user")
print("glob:", r)

sbx.kill()
print("\n✅ todas las herramientas OK")