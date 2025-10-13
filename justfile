set dotenv-load := true

backend *ARGS: 
    uv run --directory python/ eeva {{ARGS}}

b *ARGS:
    just backend {{ARGS}}

frontend HOSTNAME="localhost" PORT="5173":
    npm run --prefix=interview-frontend dev -- --host={{HOSTNAME}} --port={{PORT}}

f HOSTNAME="localhost" PORT="5173": 
    just frontend {{HOSTNAME}} {{PORT}}

pull:
    jj git fetch
    jj new main

update:
    jj abandon
    just pull
    uv build --project python
    uv sync --project python

u:
    just update

push BRANCH:
    jj bookmark move {{BRANCH}} --to=@-
    jj git push

agent:
    uv run --project python -m eeva.analyzer_agent

hydra *ARGS:
    uv --project python run -m eeva.experiment {{ARGS}}

update-data:
    uv --project python run -m eeva.experiment.fetch_data