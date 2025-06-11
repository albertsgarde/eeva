set dotenv-load := true

backend arg="": 
    uv run --directory python/ eeva {{arg}}

b arg="":
    just backend {{arg}}

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