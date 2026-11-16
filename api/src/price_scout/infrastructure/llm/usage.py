from dataclasses import dataclass

from price_scout.domain.shopping_request.models import AgentUsage


@dataclass(frozen=True)
class ModelPricing:
    input_usd_per_mtok: float
    output_usd_per_mtok: float

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens * self.input_usd_per_mtok + output_tokens * self.output_usd_per_mtok
        ) / 1_000_000


class UsageMeter:
    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self._cost_usd: float | None = 0.0

    def add(self, input_tokens: int, output_tokens: int, pricing: ModelPricing | None) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        if pricing is None:
            self._cost_usd = None
        elif self._cost_usd is not None:
            self._cost_usd += pricing.cost_usd(input_tokens, output_tokens)

    def usage(self) -> AgentUsage:
        return AgentUsage(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cost_usd=self._cost_usd,
        )
