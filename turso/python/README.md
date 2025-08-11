# Agente A2A Turso - Python/FastAPI

Agente A2A para gerenciamento de persistência de dados com Turso Database, implementado em Python com FastAPI e uv.

## Instalação

```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

uv pip install -e .
```

## Execução

```bash
python main.py
```

Ou com uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 4243
```