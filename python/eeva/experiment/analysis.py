import asyncio

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field, RootModel

from .types import Profile, Response, User, UserId, UserSet


class AnalysisResult(BaseModel):
    profile: Profile = Field()
    cot: str | None = Field()


class AnalysisResultSet(RootModel):
    root: dict[UserId, list[AnalysisResult]]

    def __getitem__(self, item: UserId) -> list[AnalysisResult]:
        return self.root[item]

    def __iter__(self):
        return iter(self.root.items())

    def __contains__(self, item: UserId) -> bool:
        return item in self.root

    def __len__(self) -> int:
        return len(self.root)

    def items(self):
        return self.root.items()

    def keys(self):
        return self.root.keys()

    def values(self):
        return self.root.values()


class Analyzer(BaseModel):
    identity_prompt: str = Field()
    identity_extraction_prompt: str = Field()
    explicit_cot: bool = Field(default=False)
    llm: BaseChatModel = Field()

    async def analyze(self, response: Response) -> AnalysisResult:
        class CotAnalyzerOutput(BaseModel):
            """ """

            identity_cot: str = Field(description=self.identity_prompt)
            identity: float = Field(ge=0, le=1, description=self.identity_extraction_prompt)

        class AnalyzerOutput(BaseModel):
            """ """

            identity: float = Field(ge=0, le=1, description=self.identity_prompt)

        output_type = CotAnalyzerOutput if self.explicit_cot else AnalyzerOutput

        structured_llm = self.llm.with_structured_output(output_type)

        content = "\n".join(f"{question.question}: {question.response}" for question in response.responses.values())

        raw_output = await structured_llm.ainvoke(
            [
                HumanMessage(content=content),
            ]
        )
        if isinstance(raw_output, dict):
            output = output_type(**raw_output)
        elif isinstance(raw_output, output_type):
            output = raw_output  # type: ignore
        else:
            raise ValueError(f"Unexpected output type: {type(raw_output)}. Expected dict or {output_type.__name__}.")
        avg_identity = output.identity  # type: ignore
        profile = Profile(identity=avg_identity)

        cot = output.identity_cot if self.explicit_cot else None  # type: ignore

        return AnalysisResult(profile=profile, cot=cot)


async def generate_user_profiles(
    analyzer: Analyzer, user_id: UserId, user: User, num_profiles: int
) -> tuple[UserId, list[AnalysisResult]]:
    tasks = []
    for _ in range(num_profiles):
        tasks.append(asyncio.create_task(analyzer.analyze(user.response)))
    profiles = await asyncio.gather(*tasks)
    return (user_id, profiles)


# Create a dict user_id -> Profile for all users in user_data using their responses to run `analyze`
# Use asyncio to run analyze concurrently for all users
async def generate_profiles(
    analyzer: Analyzer, user_data: UserSet, num_profiles: int, user_subset: set[UserId] | None
) -> dict[UserId, list[AnalysisResult]]:
    if user_subset is not None:
        user_data = UserSet({k: v for k, v in user_data.items() if k in user_subset})

    profiles: dict[UserId, list[AnalysisResult]] = {}

    async def analyze_all_users() -> None:
        tasks = []
        for user_id, user in user_data.items():
            tasks.append(asyncio.create_task(generate_user_profiles(analyzer, user_id, user, num_profiles)))
        results: list[tuple[UserId, list[AnalysisResult]]] = await asyncio.gather(*tasks)
        for user_id, user_profiles in results:
            profiles[user_id] = user_profiles

    await analyze_all_users()
    return profiles
