from pathlib import Path

from pydantic import Field, ValidationError

from eeva.utils import NetworkModel

PROMPT_ID_PATTERN = r"^[0-9a-zA-Z\-]+$"


class PromptId(NetworkModel):
    id: str = Field(pattern=PROMPT_ID_PATTERN)

    def __str__(self) -> str:
        return self.id


class Prompt(NetworkModel):
    id: PromptId = Field()
    content: str = Field()

    def __str__(self) -> str:
        return self.content


class Prompts:
    dir: Path

    def __init__(self, dir: str | Path):
        if isinstance(dir, str):
            dir = Path(dir)
        self.dir = dir.resolve()
        if not self.dir.exists():
            raise ValueError(f"Prompt directory {self.dir} does not exist.")

    def get(self, prompt_id: PromptId) -> Prompt:
        matching_paths = list(self.dir.rglob(f"{prompt_id.id}.txt"))
        match matching_paths:
            case []:
                raise FileNotFoundError(f"Prompt with ID '{prompt_id.id}' not found in directory '{self.dir}'.")
            case [path]:
                with open(path, "r") as file:
                    return Prompt(id=prompt_id, content=file.read())
            case _:
                raise FileExistsError(
                    f"Multiple prompts found with ID '{prompt_id.id}'. "
                    f"Files: {', '.join(str(p) for p in matching_paths)}"
                )

    def get_all_ids(self) -> list[PromptId]:
        files = [file for file in self.dir.rglob("*.txt") if file.is_file()]
        ids: dict[PromptId, Path] = {}
        for file in files:
            file_name = file.name.removesuffix(".txt")
            try:
                id = PromptId(id=file_name)
            except ValidationError:
                print(f"Invalid prompt ID '{file_name}' found. File path: {file.absolute()}")
                continue
            if id in ids:
                print(f"Duplicate prompt ID '{id}'. Files: {ids[id].absolute()} and {file.absolute()}")
                continue
            ids[id] = file
        return list(ids.keys())
