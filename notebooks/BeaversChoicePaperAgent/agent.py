import os
from typing import List

import dotenv
from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from schema import Deps, OrderResult, Quote, StockStatus
from tools import (
    check_finances, check_stock, get_price, list_catalog, list_inventory,
    past_quotes, reorder_if_low, restock_item, sell_item,
)

dotenv.load_dotenv()

# pydantic-ai stops a run after 50 model calls by default, and the agents share one count per request,
# so every run needs the higher limit, not just the orchestrator
LIMITS = UsageLimits(request_limit=200)


def build_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        os.getenv("MODEL_NAME", "gpt-4o-mini"),
        provider=OpenAIProvider(
            base_url=os.getenv("OPENAI_BASE_URL", "https://openai.vocareum.com/v1"),
            api_key=os.getenv("UDACITY_OPENAI_API_KEY"),
        ),
    )


class InventoryAgent:
    """InventoryAgent reports stock levels of the items inquired about."""

    INSTRUCTIONS = (
        "You are the inventory agent for Beaver's Choice Paper Company. "
        "Use the tools to report stock for the items asked about, using exact catalog names. "
        "Customers don't use our exact catalog names, so look up the right name with list_catalog; "
        "if we don't sell the item, report it with in_stock 0. "
        "If an item is below its minimum stock level, reorder it. Never invent numbers."
    )

    def __init__(self, model: Model):
        self.agent = Agent(
            model,
            deps_type=Deps,
            output_type=List[StockStatus],
            tools=[list_catalog, check_stock, list_inventory, reorder_if_low],
            instructions=self.INSTRUCTIONS,
        )

    async def run(self, prompt: str, deps: Deps, usage=None) -> List[StockStatus]:
        print("[Agent] InventoryAgent called")
        return (await self.agent.run(prompt, deps=deps, usage=usage, usage_limits=LIMITS)).output


class QuotingAgent:
    """Prices a request with catalog prices, bulk discounts etc."""

    INSTRUCTIONS = (
        "You write price quotes for Beaver's Choice Paper Company. "
        "Price each requested item from our catalog, apply a bulk discount the way past quotes did, "
        "and explain the price briefly. "
        "Customers don't use our exact catalog names, so look up the right name with list_catalog. "
        "Look up each item's price once, then write the quote. "
        "If past quotes don't show a discount for a similar order, don't give one. "
        "If we don't sell an item, leave it out and say so."
    )

    def __init__(self, model: Model):
        self.agent = Agent(
            model,
            deps_type=Deps,
            output_type=Quote,
            tools=[list_catalog, get_price, past_quotes],
            instructions=self.INSTRUCTIONS,
        )

    async def run(self, prompt: str, deps: Deps, usage=None) -> Quote:
        print("[Agent] QuotingAgent called")
        return (await self.agent.run(prompt, deps=deps, usage=usage, usage_limits=LIMITS)).output


class OrderingAgent:
    """Fulfils an approved quote: sells from stock and restocks from the supplier when short."""

    INSTRUCTIONS = (
        "You handle orders for Beaver's Choice Paper Company once a quote has been approved. "
        "You get the quote and the date the customer needs the order by. "
        "Go through the quote item by item and sell each one at the unit price and discount "
        "shown in the quote. If we don't have enough in stock, order the missing amount from the "
        "supplier and sell it on the date the supplier delivers. "
        "Check the company finances before ordering from the supplier. "
        "If an item can't be done, for example the delivery would be too late or we can't pay for it, "
        "leave it out, explain why, and carry on with the other items."
    )

    def __init__(self, model: Model):
        self.agent = Agent(
            model,
            deps_type=Deps,
            output_type=OrderResult,
            tools=[list_catalog, check_finances, restock_item, sell_item],
            instructions=self.INSTRUCTIONS,
        )

    async def run(self, prompt: str, deps: Deps, usage=None) -> OrderResult:
        print("[Agent] OrderingAgent called")
        return (await self.agent.run(prompt, deps=deps, usage=usage, usage_limits=LIMITS)).output


class OrchestratorAgent:
    """Customer-facing agent. Delegates to the three specialist agents through tools."""

    INSTRUCTIONS = """You handle customer requests for Beaver's Choice Paper Company. Follow these steps:

        #1. Work out which items and quantities the customer wants.
        #2. Check what we have in stock.
        #3. Get a quote.
        #4. If the customer is placing an order, have it processed with the date they need it by. Items we can't supply are left out, the rest still go through.
        #5. Reply to the customer with the quote and the outcome of the order, 
    
    and say clearly if anything is unavailable or delayed."""

    def __init__(
        self,
        model: Model,
        inventory: InventoryAgent,
        quoting: QuotingAgent,
        ordering: OrderingAgent,
    ):
        self.inventory = inventory
        self.quoting = quoting
        self.ordering = ordering
        self.agent = Agent(model, deps_type=Deps, instructions=self.INSTRUCTIONS)
        self.agent.tool(self.check_inventory)
        self.agent.tool(self.make_quote)
        self.agent.tool(self.place_order)

    async def check_inventory(self, ctx: RunContext[Deps], items_needed: str) -> str:
        """Ask the inventory agent about stock for the listed items and quantities."""
        stock = await self.inventory.run(items_needed, ctx.deps, ctx.usage)
        return "\n".join(s.model_dump_json() for s in stock)

    async def make_quote(self, ctx: RunContext[Deps], request: str) -> str:
        """Ask the quoting agent to price the request."""
        return (await self.quoting.run(request, ctx.deps, ctx.usage)).model_dump_json()

    async def place_order(self, ctx: RunContext[Deps], quote_json: str, needed_by: str) -> str:
        """Ask the ordering agent to fulfil an approved quote (JSON from make_quote).
        needed_by is the date the customer needs the order by, as YYYY-MM-DD."""
        prompt = f"Needed by: {needed_by}\nQuote: {quote_json}"
        return (await self.ordering.run(prompt, ctx.deps, ctx.usage)).model_dump_json()

    def handle(self, request_with_date: str, request_date: str) -> str:
        print("[Agent] OrchestratorAgent called")
        return self.agent.run_sync(
            request_with_date, deps=Deps(request_date=request_date), usage_limits=LIMITS
        ).output


class MultiAgentSystem:
    """Builds the four agents on one model and exposes a single entry point."""

    def __init__(self, model: Model | None = None):
        model = model or build_model()
        self.inventory = InventoryAgent(model)
        self.quoting = QuotingAgent(model)
        self.ordering = OrderingAgent(model)
        self.orchestrator = OrchestratorAgent(model, self.inventory, self.quoting, self.ordering)

    def handle(self, request_with_date: str, request_date: str) -> str:
        return self.orchestrator.handle(request_with_date, request_date)
