import json

from price_scout.domain.catalog.models import Offer, SearchIntent
from price_scout.domain.judgment.models import Judgment
from price_scout.infrastructure.llm.prompts import load_prompt
from price_scout.infrastructure.llm.structured import StructuredLlm


class LlmOfferJudge:
    def __init__(
        self,
        llm: StructuredLlm,
        business_context: str | None,
        prompt_version: str = "v1",
        model: str = "unknown",
    ) -> None:
        self._llm = llm
        context = "glossary" if business_context is not None else "no-glossary"
        self._version = f"{model}/{prompt_version}/{context}"
        self._system = load_prompt("judge", prompt_version)
        if business_context is not None:
            self._system += (
                "\n\nUse the business context below to decide. "
                "It outweighs your general knowledge.\n\n"
                f"<business_context>\n{business_context}\n</business_context>"
            )

    @property
    def version(self) -> str:
        return self._version

    def judge(self, intent: SearchIntent, offers: list[Offer]) -> Judgment:
        if not offers:
            return Judgment(products=[], discarded=[])

        request = {
            "query": intent.query,
            "category": intent.category,
            "listings": [
                {"id": o.offer_id, "title": o.title, "store": o.store, "price": o.price}
                for o in offers
            ],
        }
        result = self._llm.parse(
            task="judge",
            system=self._system,
            user=json.dumps(request, ensure_ascii=False),
            output_type=Judgment,
        )
        return result.output
