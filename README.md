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
│   └── prompts.py     ← SYSTEM_PROMPT_WEB_DEV (Parte 3)
├── notebook.ipynb     ← test formal de la consigna (Parte 4)
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt

export GITHUB_TOKEN=tu_token   # https://github.com/settings/tokens
export E2B_API_KEY=tu_clave    # https://e2b.dev
```

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

El agente escribe los archivos en el sandbox E2B y al terminar indica cómo correr la app:

```
Agent > El proyecto fue generado. Para ejecutarlo:
  cd workspace/todo-app
  npm install
  npm run dev
```

Sin cerrar el agente, podés continuar con el mismo historial:

```
User > Los íconos del nav son blancos y no se ven. Arreglalo.
```

## Cómo funciona

```
run_agent(query)
  → maybe_compress()    # comprime si el historial supera 40k tokens
  → llm()               # GitHub Models gpt-4o
  → execute_tool()      # herramientas filesystem en E2B
  → loop hasta que no haya más tool calls
```

## Herramientas disponibles

| Función | Qué hace |
|---|---|
| `list_directory(path)` | Lista archivos y carpetas |
| `read_file(path)` | Lee un archivo |
| `write_file(path, content)` | Escribe un archivo (crea dirs intermedios) |
| `search_file_content(pattern)` | Busca regex, devuelve JSON paginado |
| `replace_in_file(path, old, new)` | Reemplaza texto en un archivo |
| `glob(pattern)` | Busca archivos por nombre o extensión |
