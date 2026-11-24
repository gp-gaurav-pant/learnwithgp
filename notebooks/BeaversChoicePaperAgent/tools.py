"""Tools the agents call. They wrap the database helpers in project_starter.py."""
from typing import Dict, List

import pandas as pd
from pydantic_ai import RunContext

from project_starter import (
    create_transaction,
    db_engine,
    generate_financial_report,
    get_all_inventory,
    get_cash_balance,
    get_stock_level,
    get_supplier_delivery_date,
    paper_supplies,
    search_quote_history,
)
from schema import Deps, StockStatus

CATALOG = {item["item_name"]: item for item in paper_supplies}
NAMES_BY_LOWERCASE = {name.lower(): name for name in CATALOG}
FAR_FUTURE = "9999-12-31"


def exact_name(name: str) -> str | None:
    """Return the catalog name for `name`, ignoring case, or None if we don't sell it."""
    return NAMES_BY_LOWERCASE.get(name.strip().lower())


def not_in_catalog(name: str) -> str:
    return f"'{name}' is not in the catalog. Call list_catalog to see the exact names we sell."


def stock_on(item_name: str, date: str) -> int:
    return int(get_stock_level(item_name, date)["current_stock"].iloc[0])


def min_stock_level(item_name: str) -> int:
    row = pd.read_sql(
        "SELECT min_stock_level FROM inventory WHERE item_name = :name",
        db_engine,
        params={"name": item_name},
    )
    return int(row["min_stock_level"].iloc[0]) if not row.empty else 0


def order_from_supplier(item_name: str, quantity: int, request_date: str, needed_by: str | None) -> str:
    """Place a supplier order if it arrives in time and we can pay for it."""
    cost = round(quantity * CATALOG[item_name]["unit_price"], 2)
    delivery_date = get_supplier_delivery_date(request_date, quantity)
    if needed_by and delivery_date > needed_by:
        return f"Not ordered: the supplier would deliver on {delivery_date}, after {needed_by}"
    cash = get_cash_balance(request_date)
    if cost > cash:
        return f"Not ordered: it costs ${cost:.2f} and cash is ${cash:.2f}"
    create_transaction(item_name, "stock_orders", quantity, cost, delivery_date)
    return f"Ordered {quantity} x {item_name} for ${cost:.2f}, arriving {delivery_date}"


# Inventory tools

def list_catalog(ctx: RunContext[Deps]) -> List[str]:
    """Every item we sell, by exact catalog name."""
    return list(CATALOG)


def check_stock(ctx: RunContext[Deps], item_name: str) -> StockStatus:
    """Stock of one item on the request date, with its minimum stock level."""
    found = exact_name(item_name)
    if found is None:
        return StockStatus(item_name=item_name, in_stock=0, min_stock_level=0, needs_restock=False)
    in_stock = stock_on(found, ctx.deps.request_date)
    minimum = min_stock_level(found)
    return StockStatus(
        item_name=found,
        in_stock=in_stock,
        min_stock_level=minimum,
        needs_restock=in_stock < minimum,
    )


def list_inventory(ctx: RunContext[Deps]) -> Dict[str, int]:
    """Every item in stock on the request date, with units."""
    return {name: int(units) for name, units in get_all_inventory(ctx.deps.request_date).items()}


def reorder_if_low(ctx: RunContext[Deps], item_name: str) -> str:
    """If an item (counting stock already on order) is below its minimum level, order enough to get back to it."""
    found = exact_name(item_name)
    if found is None:
        return not_in_catalog(item_name)
    minimum = min_stock_level(found)
    stock_with_orders = stock_on(found, FAR_FUTURE)
    if stock_with_orders >= minimum:
        return f"{found} is fine: {stock_with_orders} (including orders on the way), minimum {minimum}"
    return order_from_supplier(found, minimum - stock_with_orders, ctx.deps.request_date, None)


# Quoting tools

def get_price(ctx: RunContext[Deps], item_name: str) -> str:
    """Catalog name and unit price of an item."""
    found = exact_name(item_name)
    if found is None:
        return not_in_catalog(item_name)
    return f"{found}: ${CATALOG[found]['unit_price']:.2f}"


def past_quotes(ctx: RunContext[Deps], search_terms: List[str]) -> List[Dict]:
    """Past quotes that mention any of the search terms."""
    return search_quote_history(search_terms)


# Ordering tools

def check_finances(ctx: RunContext[Deps]) -> Dict[str, float]:
    """Cash, inventory value and total assets on the request date."""
    report = generate_financial_report(ctx.deps.request_date)
    return {
        "cash_balance": round(report["cash_balance"], 2),
        "inventory_value": round(report["inventory_value"], 2),
        "total_assets": round(report["total_assets"], 2),
    }


def restock_item(ctx: RunContext[Deps], item_name: str, quantity: int, needed_by: str | None = None) -> str:
    """Order more of an item from the supplier. Pass the customer's needed-by date (YYYY-MM-DD) if there is one."""
    found = exact_name(item_name)
    if found is None:
        return not_in_catalog(item_name)
    return order_from_supplier(found, quantity, ctx.deps.request_date, needed_by)


def sell_item(
    ctx: RunContext[Deps],
    item_name: str,
    quantity: int,
    unit_price: float,
    discount: float = 0.0,
    sale_date: str | None = None,
) -> str:
    """Sell an item from stock. `discount` is a fraction, so 0.1 means 10% off.
    `sale_date` (YYYY-MM-DD) is the day the stock is delivered after a supplier order; leave it out otherwise."""
    found = exact_name(item_name)
    if found is None:
        return not_in_catalog(item_name)
    date = sale_date or ctx.deps.request_date
    in_stock = stock_on(found, date)
    if in_stock < quantity:
        return f"Not sold: only {in_stock} of {found} in stock on {date}, {quantity - in_stock} short"
    total = round(quantity * unit_price * (1 - discount), 2)
    create_transaction(found, "sales", quantity, total, date)
    return f"Sold {quantity} x {found} for ${total:.2f} on {date}"
