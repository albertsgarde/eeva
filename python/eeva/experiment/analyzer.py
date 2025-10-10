from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from .types import Profile, Response


class AnalysisResult(BaseModel):
    profile: Profile = Field()
    cot: str | None = Field()


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
