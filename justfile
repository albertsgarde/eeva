set dotenv-load := true

backend: 
    uv run --directory python/ eeva

b:
    just backend

frontend:
    npm run --prefix=interview-frontend dev

f: 
    just frontend

update:
    git reset --hard
    git pull
    uv build --project python
    uv sync --project python

u:
    just update