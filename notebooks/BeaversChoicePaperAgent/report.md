# Beaver's Choice Paper Company - agent project report

## What I built

I used pydantic-ai and ended up with four agents. The limit is five, so there is some room left.

The orchestrator is the only one that talks to the customer. It takes the request, asks the inventory agent what we have in stock, asks the quoting agent for a price, and if the customer is actually ordering it hands the quote to the ordering agent. Then it writes the reply.

- Inventory agent: checks stock for the items in the request and compares it with the minimum level.
- Quoting agent: looks up catalog prices, applies a bulk discount based on what past quotes did, and explains the price.
- Ordering agent: sells each item from stock. If there isn't enough, it tries to order the missing amount from the supplier.

The code is split into three files: `schema.py` for the data types, `tools.py` for the tools, and `agent.py` for the agents. The tools are thin wrappers around the starter functions. The request date goes into every agent as a dependency, so the tools always use the real request date and not one the model makes up. The diagram is in `workflow_diagram.mmd`.

## Results

I ran all 20 sample requests (`test_results.csv`).

Cash is at $45,059.70 and inventory at $4,940.30. I checked the database too: the only rows in it are the starting cash and the 18 starting stock orders. The project wants at least 3 fulfilled orders, so this doesn't pass yet.

After reading through the replies, the biggest problem is simply item names. Customers ask for things like "A4 glossy paper" or "heavy cardstock (white)," but our catalog just lists "Glossy paper" and "Cardstock." The tools only accept exact matches, so they come back with "not in catalog" and the agent gives up.

That leads to some odd, self-contradicting replies. Request 10 offers a quote of $130.50 and then says the items aren't in the catalog. Request 1 says glossy paper is in stock, then says we don't sell it.

Restocking never got a chance to run, either. It only triggers after a failed sale, and these sales never made it past the name check. And when just one item in a request was missing, the orchestrator usually turned down the whole order or asked the customer to confirm, rather than selling the parts it could.

So the rejections do come with a reason. It's just usually the wrong one.

## What works

- Each agent has one job and a small set of tools.
- Cash is checked before anything is ordered from the supplier.
- Items must match the catalog name exactly, so bad names don't reach the database (but see below, it's too strict).

## What doesn't work yet

- Name matching is too strict. Real customer wording almost never matches the catalog name, so most items get rejected.
- If one item in an order is missing, the whole order gets declined instead of selling the rest.
- `generate_financial_report` isn't used by any agent. Only the test loop calls it.
- Nothing reorders stock when it drops below the minimum level.
- Quote totals and sale prices come from the model and aren't checked in code. Totally rely on model to do correctly.

## Ideas for improving it

1. Give an agent a reporting tool built on `generate_financial_report`, and let the inventory agent reorder items that fall below their minimum level, so stock is there before the big orders come in.
2. Compare the supplier's delivery date with the date the customer needs the order, and reject or delay it with a clear reason when it can't be met.
3. Make item matching smarter (suggest the closest catalog name and let the agent use it), and let partial orders go through so one missing item doesn't kill the whole request.

