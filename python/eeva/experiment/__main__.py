import os
from dataclasses import dataclass
from pathlib import Path

import hydra
from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig

from . import run
from .run import RunConfig


@dataclass
class Config:
    secrets_path: Path
    data_dir: Path
    prompts_dir: Path

    model: str
    reasoning_effort: str
    identity_prompt_path: str
    identity_extraction_prompt_path: str
    explicit_cot: bool
    two_step_analysis: bool
    system_prompt_path: str | None
    user_prompt_path: str

    num_tests: int

    question_exclusion_sets: list[str]
    question_inclusion_sets: list[str] | None

    user_exclusion_sets: list[str]
    user_inclusion_sets: list[str] | None
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
    prompts_dir = (data_dir / cfg.prompts_dir).resolve()
    output_dir = Path(HydraConfig.get().runtime.output_dir).resolve()
    run.run(
        RunConfig(
            secrets_path=Path(cfg.secrets_path).resolve(),
            data_dir=data_dir,
            output_dir=output_dir,
            model=model,
            model_provider=model_provider,
            reasoning_effort=cfg.reasoning_effort,
            identity_prompt=(prompts_dir / cfg.identity_prompt_path)
            .with_suffix(".txt")
            .resolve()
            .read_text(encoding="utf-8"),
            identity_extraction_prompt=(prompts_dir / cfg.identity_extraction_prompt_path)
            .with_suffix(".txt")
            .resolve()
            .read_text(encoding="utf-8"),
            explicit_cot=cfg.explicit_cot,
            two_step_analysis=cfg.two_step_analysis,
            system_prompt=(prompts_dir / cfg.system_prompt_path)
            .with_suffix(".txt")
            .resolve()
            .read_text(encoding="utf-8")
            if cfg.system_prompt_path
            else None,
            user_prompt=(prompts_dir / cfg.user_prompt_path).with_suffix(".txt").resolve().read_text(encoding="utf-8"),
            num_tests=cfg.num_tests,
            question_exclusion_sets={set_name for set_name in cfg.question_exclusion_sets},
            question_inclusion_sets={set_name for set_name in cfg.question_inclusion_sets}
            if cfg.question_inclusion_sets
            else None,
            user_exclusion_sets={set_name for set_name in cfg.user_exclusion_sets},
            user_inclusion_sets={set_name for set_name in cfg.user_inclusion_sets} if cfg.user_inclusion_sets else None,
            only_couples=cfg.only_couples,
            answer_progress_minimum=cfg.answer_progress_minimum,
            num_answers_minimum=cfg.num_answers_minimum,
        )
    )


if __name__ == "__main__":
    main()
