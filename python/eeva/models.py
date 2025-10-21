import typing
from typing import Any, Type, TypeVar

from langchain import chat_models
from langchain.chat_models.base import BaseChatModel
from langchain_core.language_models import LanguageModelInput
from pydantic import BaseModel, Field


class ModelPricingInfo(BaseModel):
    input: float = Field(ge=0, description="Cost per 1 non-cached input token in USD")
    cached_input: float = Field(ge=0, description="Cost per 1 cached input token in USD")
    output: float = Field(ge=0, description="Cost per 1 output token in USD")

    @staticmethod
    def from_per_mil(input: float, cached_input: float, output: float) -> "ModelPricingInfo":
        return ModelPricingInfo(
            input=input / 1_000_000,
            cached_input=cached_input / 1_000_000,
            output=output / 1_000_000,
        )

    def calculate(self, input: int, cached_input: int, output: int) -> float:
        return self.input * input + self.cached_input * cached_input + self.output * output


class ModelSpecifier(BaseModel):
    class Config:
        frozen = True

    name: str = Field()
    provider: str = Field()

    def init_chat_model(self, **kwargs) -> BaseChatModel:
        if self.provider == "anthropic":
            if "reasoning_effort" in kwargs:
                del kwargs["reasoning_effort"]
        return chat_models.init_chat_model(self.name, model_provider=self.provider, **kwargs)


model_pricing: dict[ModelSpecifier, ModelPricingInfo] = {
    ModelSpecifier(name="gpt-5-nano", provider="openai"): ModelPricingInfo.from_per_mil(
        input=0.05, cached_input=0.005, output=0.4
    ),
    ModelSpecifier(name="gpt-5-mini", provider="openai"): ModelPricingInfo.from_per_mil(
        input=0.25, cached_input=0.025, output=2.0
    ),
    ModelSpecifier(name="gpt-5", provider="openai"): ModelPricingInfo.from_per_mil(
        input=1.25, cached_input=0.125, output=10.0
    ),
    ModelSpecifier(name="claude-3-5-haiku-20241022", provider="anthropic"): ModelPricingInfo.from_per_mil(
        input=0.8, cached_input=0.08, output=4.0
    ),
    ModelSpecifier(name="claude-sonnet-4-5-20250929", provider="anthropic"): ModelPricingInfo.from_per_mil(
        input=3.0, cached_input=0.32, output=15.0
    ),
}


class UsageData(BaseModel):
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0, description="Number of input tokens served from cache")
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)

    @staticmethod
    def from_raw(raw: dict[str, Any], model_specifier: ModelSpecifier) -> "UsageData":
        if model_specifier.provider == "openai":
            input_tokens = raw["token_usage"]["prompt_tokens"]
            cached_input_tokens = raw["token_usage"]["prompt_tokens_details"]["cached_tokens"]
            output_tokens = raw["token_usage"]["completion_tokens"]
            reasoning_tokens = raw["token_usage"]["completion_tokens_details"]["reasoning_tokens"]
        elif model_specifier.provider == "anthropic":
            input_tokens = raw["usage"]["input_tokens"]
            cached_input_tokens = raw["usage"]["cache_read_input_tokens"]
            output_tokens = raw["usage"]["output_tokens"]
            reasoning_tokens = 0
        else:
            raise ValueError(f"Unknown model provider: {model_specifier.provider}")
        return UsageData(
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
        )

    def calculate_cost(self, pricing_info: ModelPricingInfo) -> float:
        return pricing_info.calculate(self.input_tokens, self.cached_input_tokens, self.output_tokens)

    def combine(self, other: "UsageData") -> "UsageData":
        return UsageData(
            input_tokens=self.input_tokens + other.input_tokens,
            cached_input_tokens=self.cached_input_tokens + other.cached_input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
        )


R = TypeVar("R", bound=BaseModel)


class Model(BaseModel):
    specifier: ModelSpecifier = Field()
    llm: BaseChatModel = Field()

    @staticmethod
    def from_specifier(specifier: ModelSpecifier, **kwargs) -> "Model":
        llm = specifier.init_chat_model(**kwargs)
        return Model(specifier=specifier, llm=llm)

    def pricing_info(self) -> ModelPricingInfo:
        if self.specifier in model_pricing:
            return model_pricing[self.specifier]
        else:
            raise ValueError(f"No pricing info for model specifier: {self.specifier}")

    async def get_structured_output(self, input: LanguageModelInput, output_type: Type[R]) -> tuple[R, UsageData]:
        str_llm = self.llm.with_structured_output(output_type, include_raw=True)
        message = typing.cast(dict[str, Any], await str_llm.ainvoke(input))
        parsed: R = message["parsed"]
        raw_metadata = message["raw"].response_metadata
        metadata = UsageData.from_raw(raw_metadata, self.specifier)
        return parsed, metadata

    async def get_unstructured_output(self, input: LanguageModelInput) -> tuple[str, UsageData]:
        response = await self.llm.ainvoke(input)
        if isinstance(response.content, str):
            content = response.content
        else:
            raise ValueError(f"Unexpected response content type: {type(response.content)}. Expected str.")
        raw_metadata = response.response_metadata
        metadata = UsageData.from_raw(raw_metadata, self.specifier)
        return content, metadata
