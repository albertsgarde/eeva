import asyncio
import json
import os
import typing
from pathlib import Path
from random import Random
from typing import Annotated, Awaitable, Callable

import aiofiles
import anyio
import numpy as np
import regex as re
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel, Field, RootModel

from eeva import utils
from eeva.analyzer import Response
from eeva.utils import Model


class Profile(BaseModel):
    identity: float = Field(ge=0, le=1)


class User(BaseModel):
    response: Response = Field()
    prod_profile: Profile | None = Field()


Couple = Annotated[tuple[str, str], Field()]
CouplePairs = Annotated[dict[str, Couple], Field()]


Analyzer = Callable[[Response], Awaitable[Profile]]


_NUMBER_RE = re.compile(r"^(\d+)\.log$")


def _taken_numbers(log_dir: Path) -> set[int]:
    try:
        names = os.listdir(log_dir)
    except FileNotFoundError:
        return set()
    taken = set()
    for name in names:
        m = _NUMBER_RE.match(name)
        if m:
            taken.add(int(m.group(1)))
    return taken


def next_log_path(log_dir: Path) -> Path:
    """
    Return LOG_DIR/{number}.log where number is the smallest positive integer
    not already present. Does NOT create the file.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    taken = _taken_numbers(log_dir)
    n = 0
    while n in taken:
        n += 1
    return log_dir / f"{n}.log"


class Config(BaseModel):
    num_test_samples: int = Field(gt=0, description="Number of samples to generate per user")
    max_iters: int = Field(gt=0, description="Maximum number of agent iterations")
    timeout: float = Field(ge=0, description="Timeout for each test in seconds")
    analyzer_model: Model = Field(description="LLM to use for the analyzer")
    agent_model: Model = Field(description="LLM to use for the agent")


CONFIG = Config(
    num_test_samples=5,
    max_iters=5,
    timeout=120,
    analyzer_model=Model(model_name="gpt-5-nano", model_provider="openai"),
    agent_model=Model(model_name="gpt-5-nano", model_provider="openai"),
)

WORKSPACE_DIR = Path(".").resolve()
DATA_DIR = WORKSPACE_DIR / "data"
BASE_DIR = DATA_DIR / "agent_workspace"
LOG_DIR = WORKSPACE_DIR / "output" / "logs"
PROMPT_DIR = DATA_DIR / "prompts"
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = next_log_path(LOG_DIR)

utils.load_secrets(WORKSPACE_DIR / "secrets.json")


def _safe_path(path: Path) -> Path:
    """
    Resolve path inside BASE_DIR to avoid escaping the workspace.
    """
    full = (BASE_DIR / path).resolve()
    if not full.is_relative_to(BASE_DIR):
        raise ValueError("Path escapes workspace")
    return full


async def generate_user_profiles(
    user_id: str, user: User, num_profiles: int, analyzer: Analyzer
) -> tuple[str, list[Profile]]:
    tasks = []
    for _ in range(num_profiles):
        tasks.append(asyncio.ensure_future(analyzer(user.response)))
    return user_id, await asyncio.gather(*tasks)


async def generate_profiles(
    user_data: dict[str, User], num_profiles: int, user_subset: set[str] | None, analyzer: Analyzer
) -> dict[str, list[Profile]]:
    if user_subset is not None:
        user_data = {k: v for k, v in user_data.items() if k in user_subset}

    profiles: dict[str, list[Profile]] = {}

    async def analyze_all_users():
        tasks = []
        for user_id, user in user_data.items():
            tasks.append(asyncio.create_task(generate_user_profiles(user_id, user, num_profiles, analyzer)))
        results = await asyncio.gather(*tasks)
        for user_id, user_profiles in results:
            profiles[user_id] = user_profiles

    await analyze_all_users()
    return profiles


class TestResult(BaseModel):
    absolute_diff_delta: float = Field()
    relative_diff_delta: float = Field()
    absolute_steps_to_partner_delta: float = Field()
    relative_steps_to_partner_delta: float = Field()


class LogEntry(BaseModel):
    analyzer_model: Model = Field()
    agent_model: Model = Field()
    result: TestResult = Field()
    identity_prompt: str = Field()


async def log(identity_prompt: str, result: TestResult) -> None:
    entry = LogEntry(
        analyzer_model=CONFIG.analyzer_model,
        agent_model=CONFIG.agent_model,
        result=result,
        identity_prompt=identity_prompt,
    )
    async with aiofiles.open(LOG_FILE, "a", encoding="utf-8") as f:
        await f.write(f"{entry.model_dump_json()}\n")


async def log_err(identity_prompt: str, error: str) -> None:
    entry = {
        "analyzer_model": CONFIG.analyzer_model.model_name,
        "agent_model": CONFIG.agent_model.model_name,
        "error": error,
        "identity_prompt": identity_prompt,
    }
    async with aiofiles.open(LOG_FILE, "a", encoding="utf-8") as f:
        await f.write(f"{json.dumps(entry)}\n")


@tool()
async def test_prompt(identity_prompt: str) -> TestResult:
    """
    Analyze (generate a identity score for) each user response individually with the specified prompt and
    check how well the identity scores of couples align.
    Returns a TestResult with various statistics about how well the prompt performed:
        `absolute_diff_delta`: The mean difference between the average couple difference and the average
        difference of randomly generated couples. A positive value means the prompt is better than random,
        and the higher the value, the better.
        `relative_diff_delta`: The mean ratio between the average couple difference and the average
        difference of randomly generated couples. A value greater than 1 means the prompt is better than random,
        and the higher the value, the better.
    """

    try:
        with anyio.fail_after(CONFIG.timeout) as cancel_scope:
            llm = CONFIG.analyzer_model.init_chat_model()
            with open(DATA_DIR / "user_data.json", "r", encoding="utf-8") as f:

                class UserSetDeserializer(RootModel[dict[str, User]]):
                    pass

                user_data = UserSetDeserializer.model_validate_json(f.read()).root

            with open(DATA_DIR / "couples.json", "r", encoding="utf-8") as f:
                couple_pairs_raw: dict[str, list[str]] = json.load(f)
                couple_pairs: dict[str, Couple] = {k: (v[0], v[1]) for k, v in couple_pairs_raw.items()}

            async def analyze(response: Response) -> Profile:
                class AnalyzerOutput(BaseModel):
                    """ """

                    identity: float = Field(ge=0, le=1, description=identity_prompt)

                structured_llm = llm.with_structured_output(AnalyzerOutput)

                content = "\n".join(
                    f"{question.question}: {question.response}" for question in response.responses.values()
                )

                raw_output = await structured_llm.ainvoke(
                    [
                        SystemMessage(content="Please analyze the identity of this set of answers."),
                        HumanMessage(content=content),
                    ]
                )
                if isinstance(raw_output, dict):
                    output = AnalyzerOutput(**raw_output)
                elif isinstance(raw_output, AnalyzerOutput):
                    output = typing.cast(AnalyzerOutput, raw_output)
                else:
                    raise ValueError(f"Unexpected output type: {type(raw_output)}. Expected dict or AnalyzerOutput.")
                avg_identity = output.identity
                profile = Profile(identity=avg_identity)

                return profile

            profiles = await generate_profiles(user_data, CONFIG.num_test_samples, None, analyze)
            profile_list = [(id, profile) for id, profile in profiles.items()]

            values = np.array(
                [[profile.identity for profile in user_profiles] for _id, user_profiles in profile_list]
            ).T  # shape (num_samples, num_users)
            assert values.shape[0] == CONFIG.num_test_samples
            couple_indices_list = []
            for id1, id2 in couple_pairs.values():
                idx1 = None
                idx2 = None
                for idx, (id, _profile) in enumerate(profile_list):
                    if id == id1:
                        idx1 = idx
                    if id == id2:
                        idx2 = idx
                if idx1 is not None and idx2 is not None:
                    couple_indices_list.append([idx1, idx2])

            couple_indices = np.array(couple_indices_list)  # shape (num_couples, 2)

            couple_values = values[:, couple_indices]  # shape (num_samples, num_couples, 2)
            couple_diffs = np.abs(couple_values[:, :, 0] - couple_values[:, :, 1])  # shape (num_samples, num_couples)
            avg_couple_diff = np.mean(couple_diffs, axis=1)  # shape (num_samples,)

            def gen_random_couples(num_users: int, num_random_couples: int, rng):
                return rng.sample(range(num_users), 2 * num_random_couples)

            def gen_random_couple_sets(num_users: int, num_random_couples: int, num_sets: int, rng):
                return np.array(
                    [gen_random_couples(num_users, num_random_couples, rng) for _ in range(num_sets)]
                ).reshape(num_sets, num_random_couples, 2)

            rng = Random(45)
            random_couple_sets = gen_random_couple_sets(
                values.shape[1], len(couple_pairs), 100_000, rng
            )  # shape (num_random_sets, num_couples, 2)

            random_couple_diffs = np.abs(
                values[:, random_couple_sets[:, :, 0]] - values[:, random_couple_sets[:, :, 1]]
            )  # shape (num_samples, num_random_sets, num_couples)
            random_avgs = random_couple_diffs.mean(axis=(1, 2))  # shape (num_samples,)

            diffs_square = np.abs(values[:, :, None] - values[:, None, :])  # shape (num_samples, num_users, num_users)

            steps_to_partner = (
                np.sum(diffs_square[:, couple_indices] <= couple_diffs[:, :, None, None], axis=3) - 2
            )  # shape (num_samples, num_couples)

            avg_steps_to_partner = np.mean(steps_to_partner, axis=(1, 2))  # shape (num_samples,)

            random_steps_to_partner = (
                np.sum(
                    diffs_square[:, random_couple_sets] <= random_couple_diffs[:, :, :, None, None],
                    axis=4,
                )
                - 2
            )
            random_avg_steps_to_partner = np.mean(random_steps_to_partner, axis=(1, 2, 3))

            test_result = TestResult(
                absolute_diff_delta=np.mean(random_avgs - avg_couple_diff),
                relative_diff_delta=np.mean(random_avgs / (avg_couple_diff + 1e-8)),
                absolute_steps_to_partner_delta=np.mean(random_avg_steps_to_partner - avg_steps_to_partner),
                relative_steps_to_partner_delta=np.mean(random_avg_steps_to_partner / (avg_steps_to_partner + 1e-8)),
            )
        if cancel_scope.cancelled_caught:
            raise TimeoutError(f"Test timed out after {CONFIG.timeout} seconds")

    except Exception as e:
        await log_err(identity_prompt, str(e))
        raise

    await log(identity_prompt, test_result)

    return test_result


TOOLS = [test_prompt]

# --- Agent construction -----------------------------------------------


def build_agent(model: Model):
    llm = model.init_chat_model()

    with open(PROMPT_DIR / "agent_system_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read().format(**CONFIG.model_dump())
    with open(PROMPT_DIR / "agent_human_prompt.txt", "r", encoding="utf-8") as f:
        human_prompt = f.read().format(**CONFIG.model_dump())
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt),
            ("ai", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(llm, TOOLS, prompt=prompt)
    executor = AgentExecutor(agent=agent, tools=TOOLS, verbose=True)
    return executor


# --- A tiny supervisor loop (optional) --------------------------------
# LangChain's AgentExecutor will handle calling tools based on the model’s decisions.
# We just call it with the composed instruction. We also track iterations with a
# simple token in memory the agent can update by writing a status file, but we’ll
# keep it simple: we’ll give the agent a max-iteration budget in the prompt.


async def main():
    executor = build_agent(CONFIG.agent_model)
    result = await executor.ainvoke(
        {
            "root": BASE_DIR,
        },
    )
    print("\n=== FINAL AGENT OUTPUT ===\n")
    print(result["output"])


if __name__ == "__main__":
    print(f"Workspace: {BASE_DIR}")
    asyncio.run(main())
