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
    args = parser.parse_args()

    uvicorn.run("eeva.app:app", reload=True, host=args.host)


if __name__ == "__main__":
    main()
