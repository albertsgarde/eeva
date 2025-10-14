import asyncio

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field, RootModel

from .types import Profile, Response, User, UserId, UserSet


class AnalysisResult(BaseModel):
    profile: Profile = Field()
    cot: str | None = Field()


class AnalysisResultUser(BaseModel):
    first_name: str = Field()
    last_name: str = Field()
    analysis_results: list[AnalysisResult] = Field()


class AnalysisResultSet(RootModel):
    root: dict[UserId, AnalysisResultUser] = Field()

    def __getitem__(self, item: UserId) -> AnalysisResultUser:
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
) -> tuple[UserId, AnalysisResultUser]:
    tasks = []
    for _ in range(num_profiles):
        tasks.append(asyncio.create_task(analyzer.analyze(user.response)))
    profiles = await asyncio.gather(*tasks)
    result_user = AnalysisResultUser(
        first_name=user.response.first_name,
        last_name=user.response.last_name,
        analysis_results=profiles,
    )
    return (user_id, result_user)


# Create a dict user_id -> Profile for all users in user_data using their responses to run `analyze`
# Use asyncio to run analyze concurrently for all users
async def generate_profiles(
    analyzer: Analyzer, user_data: UserSet, num_profiles: int, user_subset: set[UserId] | None
) -> AnalysisResultSet:
    if user_subset is not None:
        user_data = UserSet({k: v for k, v in user_data.items() if k in user_subset})

    async def analyze_all_users() -> AnalysisResultSet:
        tasks = []
        for user_id, user in user_data.items():
            tasks.append(asyncio.create_task(generate_user_profiles(analyzer, user_id, user, num_profiles)))
        results: list[tuple[UserId, AnalysisResultUser]] = await asyncio.gather(*tasks)
        return AnalysisResultSet({user_id: result for user_id, result in results})

    return await analyze_all_users()
