"""Shared types: the dependencies every agent run receives and the structured outputs the agents return."""
from dataclasses import dataclass
from typing import List

from pydantic import BaseModel, Field


@dataclass
class Deps:
    """Shared by every agent run: the request date is fixed by the system, never guessed by the LLM."""
    request_date: str


class StockStatus(BaseModel):
    item_name: str
    in_stock: int
    min_stock_level: int
    needs_restock: bool


class QuoteLine(BaseModel):
    item_name: str
    quantity: int
    unit_price: float
    discount_pct: float
    line_total: float


class Quote(BaseModel):
    lines: List[QuoteLine]
    total: float
    explanation: str = Field(description="Customer-friendly explanation of price and discounts")


class OrderResult(BaseModel):
    fulfilled: List[str] = Field(description="Items sold, with quantity")
    unfulfilled: List[str] = Field(description="Items that could not be sold and why")
    restocked: List[str] = Field(description="Supplier orders placed, with delivery date")
    total_charged: float
    summary: str
