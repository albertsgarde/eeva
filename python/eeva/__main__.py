import argparse

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Eeva backend")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to",
    )
    parser.add_argument("--reload", action="store_true", default=False)
    args = parser.parse_args()

    uvicorn.run("eeva.app:app", reload=args.reload, host=args.host)


if __name__ == "__main__":
    main()
