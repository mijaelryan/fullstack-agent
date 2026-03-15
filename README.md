# 🤖 Full Stack Code Agent

Agente que recibe instrucciones en lenguaje natural y genera una **app web completa en Next.js** dentro de un sandbox seguro E2B.

## Stack

| Componente | Tecnología |
|---|---|
| LLM | GitHub Models (`gpt-4o`) |
| Sandbox | E2B Code Interpreter |
| Framework generado | Next.js 14 + TypeScript + Tailwind |

## Estructura del repositorio

```
fullstack-agent/
├── run_agent.py       ← punto de entrada (CLI)
├── agent.py           ← loop del agente + llm() + run_agent()
├── lib/
│   ├── sbx_tools.py   ← herramientas de filesystem (Parte 1)
│   ├── context.py     ← compresión de contexto / Runtime Summary (Parte 2)
│   ├── sbx_download.py← descarga del sandbox al sistema local
│   └── prompts.py     ← SYSTEM_PROMPT_WEB_DEV (Parte 3)
├── demo/
│   └── win95-todo-app ← app de ejemplo generada por el agente
├── tests/             ← tests unitarios de cada componente
├── notebook.ipynb     ← test formal de la consigna (Parte 4)
├── workspace/         ← proyectos generados por el agente (gitignored)
├── env.example        ← plantilla de credenciales
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Clonar el repo
git clone https://github.com/mijaelryan/fullstack-agent.git
cd fullstack-agent

# 2. Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
# .venv\Scripts\activate       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar credenciales
cp env.example .env
# Editá .env y completá tus claves:
#   GITHUB_TOKEN → https://github.com/settings/tokens (modelo: gpt-4o)
#   E2B_API_KEY  → https://e2b.dev
```

> **Nota:** Para correr la app generada necesitás [Node.js v18+](https://nodejs.org) instalado localmente.

## Tests

```bash
cd tests/
python test_connection.py    # verifica que LLM y sandbox conectan
python test_tools.py         # prueba las 6 herramientas filesystem
python test_agent_basic.py   # prueba el loop del agente
python test_agent_history.py # prueba el historial entre turnos
python test_download.py      # prueba la descarga del sandbox
python test_tools_fixed.py   # prueba las herramientas después del fix
```

Correr en orden antes de usar el agente por primera vez.

## Uso

```bash
python run_agent.py
```

```
╔══════════════════════════════════════════════════════╗
║          🤖  Full Stack Code Agent                   ║
║  Stack: Next.js 14 · TypeScript · Tailwind CSS       ║
║  Escribí 'exit' o Ctrl+C para salir                  ║
╚══════════════════════════════════════════════════════╝

User > Crea una app de lista de tareas estilo Windows 95
```

El agente escribe los archivos en el sandbox E2B, verifica que compila con `npm run build` y descarga el proyecto a `workspace/`:

```
Agent > El proyecto fue generado. Para ejecutarlo:
  cd workspace/todo-app
  npm install
  npm run dev
```

Sin cerrar el agente, podés continuar con el mismo historial:

```
User > Los botones no se ven. Arreglalo.
```

## Capturas

### Agente en acción

**Inicio y primer prompt:**
![inicio del agente](assets/01_agent_start.jpg)

**Agente escribiendo archivos:**
![agente trabajando](assets/02_agent_working.jpeg)

**App generada — antes del fix (botones con texto invisible):**
![app antes](assets/05_app_before.jpeg)

**Segundo prompt — fix aplicado:**
![segundo prompt](assets/07_agent_task2.jpg)

**App después del fix:**
![app después](assets/09_app_after.jpeg)

**Tercer prompt — compresión de contexto activada (verde):**
![compresión de contexto](assets/12_context_compression.jpeg)

**App final con tachado y contador de tareas:**
![app final](assets/14_app_final.jpeg)

## App de demo

En `demo/win95-todo-app/` hay una app de ejemplo generada por el agente. Para correrla:

```bash
cd demo/win95-todo-app
npm install
npm run dev
```

Abrí `http://localhost:3000`.

## Cómo funciona

```
run_agent(query)
  → maybe_compress()    # comprime si el historial supera 6k tokens estimados
  → llm()               # GitHub Models gpt-4o para generación de código
  → execute_tool()      # herramientas filesystem en E2B
  → _try_download()     # descarga workspace/ al sistema local
  → loop hasta que no haya más tool calls
```

> **Nota técnica:** El agente usa `gpt-4o` para generar código y `gpt-4o-mini` para comprimir el historial — esto es intencional para optimizar el uso de tokens en las sesiones largas.

## Herramientas disponibles

| Función | Qué hace |
|---|---|
| `list_directory(path)` | Lista archivos y carpetas |
| `read_file(path)` | Lee un archivo |
| `write_file(path, content)` | Escribe un archivo (crea dirs intermedios) |
| `search_file_content(pattern)` | Busca regex, devuelve JSON paginado |
| `replace_in_file(path, old, new)` | Reemplaza texto en un archivo |
| `glob(pattern)` | Busca archivos por nombre o extensión |
| `execute_bash(cmd)` | Corre comandos bash (npm install, npm run build, etc.) |

## Notas importantes

- La carpeta `workspace/` es generada automáticamente y está en `.gitignore` — no subirla al repo
- GitHub Models tiene un límite de ~50 requests/día por cuenta y 8k tokens por request
- La compresión de contexto se activa automáticamente a los 6k tokens estimados
- El agente tiene un límite de 40 pasos por sesión como parada de seguridad
- Si el agente falla por límite de tokens, abrí sesión nueva con el prompt completo
