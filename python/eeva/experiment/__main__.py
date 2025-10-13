import os
from dataclasses import dataclass
from pathlib import Path

import hydra
from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig

from . import run
from .run import RunConfig
from .types import QuestionId, UserId


@dataclass
class Config:
    secrets_path: Path
    data_dir: Path

    model: str
    reasoning_effort: str
    identity_prompt_path: str
    identity_extraction_prompt_path: str
    explicit_cot: bool

    num_tests: int

    exclude_questions: list[str]
    include_questions: list[str] | None

    exclude_users: list[str]
    include_users: list[str] | None
    only_couples: bool
    answer_progress_minimum: float
    num_answers_minimum: int


ROOT_PATH = (Path(".")).resolve()
cs = ConfigStore.instance()
cs.store(name="experiment_config", node=Config)


@hydra.main(version_base=None, config_path=str(ROOT_PATH / "config"), config_name="debug")
def main(cfg: Config) -> None:
    os.chdir(ROOT_PATH)
    [model, model_provider] = cfg.model.split(":")
    data_dir = Path(cfg.data_dir).resolve()
    output_dir = Path(HydraConfig.get().runtime.output_dir).resolve()
    run.run(
        RunConfig(
            secrets_path=Path(cfg.secrets_path).resolve(),
            data_dir=data_dir,
            output_dir=output_dir,
            model=model,
            model_provider=model_provider,
            reasoning_effort=cfg.reasoning_effort,
            identity_prompt=(data_dir / cfg.identity_prompt_path)
            .with_suffix(".txt")
            .resolve()
            .read_text(encoding="utf-8"),
            identity_extraction_prompt=(data_dir / cfg.identity_extraction_prompt_path)
            .with_suffix(".txt")
            .resolve()
            .read_text(encoding="utf-8"),
            explicit_cot=cfg.explicit_cot,
            num_tests=cfg.num_tests,
            exclude_questions={QuestionId(qid) for qid in cfg.exclude_questions},
            include_questions={QuestionId(qid) for qid in cfg.include_questions} if cfg.include_questions else None,
            exclude_users={UserId(uid) for uid in cfg.exclude_users},
            include_users={UserId(uid) for uid in cfg.include_users} if cfg.include_users else None,
            only_couples=cfg.only_couples,
            answer_progress_minimum=cfg.answer_progress_minimum,
            num_answers_minimum=cfg.num_answers_minimum,
        )
    )


if __name__ == "__main__":
    main()
