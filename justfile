set dotenv-load := true

backend *ARGS: 
    uv run --directory python/ eeva {{ARGS}}

b *ARGS:
    just backend {{ARGS}}

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

push BRANCH:
    jj bookmark move {{BRANCH}} --to=@-
    jj git push