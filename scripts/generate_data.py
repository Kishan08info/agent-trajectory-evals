"""Generate the demo data for agent-trajectory-evals.

Everything is synthetic and seeded (seed 42), so a from-scratch re-run
produces byte-identical data files. The corpus docs are hand-written
(fictional "Northwind Analytics"); the orders table is generated from a
fixed seed; the task set's expected answers are COMPUTED from the generated
orders, never hand-typed, so the goldens always agree with the data.

Run:  python scripts/generate_data.py
Writes: data/corpus.jsonl, data/orders.json, data/tasks.json
"""

import json
import random
from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# ---------------------------------------------------------------- corpus
# Each doc: id, title, date (ISO), text. d02 is deliberately STALE: a 2024
# pricing archive whose prices were superseded in Jan 2025. The freshness
# cutoff (2025-01-01) is what keeps it out of the baseline agent's retrieval.
DOCS = [
    {
        "id": "d01",
        "title": "Pricing (current, January 2025)",
        "date": "2025-01-15",
        "text": (
            "Northwind Analytics pricing, effective January 2025. "
            "Starter plan: $49 per month. Growth plan: $99 per month. "
            "Pro plan: $199 per month. Enterprise plan: custom pricing. "
            "All plans are billed monthly. Prices are in USD."
        ),
    },
    {
        "id": "d02",
        "title": "Pricing archive (June 2024)",
        "date": "2024-06-01",
        "text": (
            "Northwind Analytics pricing archive, June 2024. Monthly price list. "
            "Starter plan monthly price: $29 per month. "
            "Growth plan monthly price: $49 per month. "
            "Pro plan monthly price: $99 per month. "
            "These monthly prices were replaced by the January 2025 price list."
        ),
    },
    {
        "id": "d03",
        "title": "Refund policy",
        "date": "2025-01-15",
        "text": (
            "Refunds: customers may request a full refund within 30 days of "
            "purchase. Refunds are issued to the original payment method within "
            "5 business days. No partial-month refunds are given."
        ),
    },
    {
        "id": "d04",
        "title": "Enterprise plan features",
        "date": "2025-02-01",
        "text": (
            "Enterprise plan features: single sign-on (SSO), a dedicated support "
            "manager, custom data retention, and a 99.9% uptime SLA. Enterprise "
            "customers also get priority onboarding."
        ),
    },
    {
        "id": "d05",
        "title": "Onboarding guide",
        "date": "2025-01-15",
        "text": (
            "Onboarding: new workspaces activate in three steps. Invite your team, "
            "connect a data source, and run your first report. Activation usually "
            "takes less than one business day."
        ),
    },
    {
        "id": "d06",
        "title": "API rate limits",
        "date": "2025-03-01",
        "text": (
            "API rate limits per day: Starter 1,000 requests per day, Growth "
            "5,000 requests per day, Pro 10,000 requests per day, Enterprise "
            "unlimited requests per day."
        ),
    },
    {
        "id": "d07",
        "title": "Cancellation and churn",
        "date": "2025-01-15",
        "text": (
            "Churn: subscriptions cancelled before the renewal date stop at the end "
            "of the current billing period. Cancelled workspaces keep read access "
            "for 30 days."
        ),
    },
    {
        "id": "d08",
        "title": "Data retention",
        "date": "2025-01-15",
        "text": (
            "Data retention: Starter 90 days, Growth 1 year, Pro 3 years, "
            "Enterprise custom retention. Deleted data cannot be recovered."
        ),
    },
    {
        "id": "d09",
        "title": "Support SLAs",
        "date": "2025-02-10",
        "text": (
            "Support SLAs: Starter email support within 2 business days, Growth "
            "within 1 business day, Pro within 4 hours, Enterprise within 1 hour "
            "with a dedicated manager."
        ),
    },
    {
        "id": "d10",
        "title": "Security and compliance",
        "date": "2025-01-15",
        "text": (
            "Security: Northwind Analytics is SOC 2 Type II certified. Data is "
            "encrypted in transit and at rest. SSO is available on the Enterprise "
            "plan only."
        ),
    },
]

# ---------------------------------------------------------------- orders
PLAN_PRICE = {"starter": 49, "growth": 99, "pro": 199, "enterprise": 499}
CUSTOMERS = [
    {"id": "C0101", "name": "Acme Corp", "plan": "starter"},
    {"id": "C0102", "name": "Beta Ltd", "plan": "growth"},
    {"id": "C0103", "name": "Gamma Inc", "plan": "pro"},
    {"id": "C0104", "name": "Delta LLC", "plan": "enterprise"},
    {"id": "C0105", "name": "Epsilon Co", "plan": "pro"},
    {"id": "C0106", "name": "Zeta Group", "plan": "growth"},
    {"id": "C0107", "name": "Eta Systems", "plan": "starter"},
    {"id": "C0108", "name": "Theta Labs", "plan": "enterprise"},
]
MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]


def generate_orders():
    rng = random.Random(SEED)
    orders = []
    n = 0
    for cust in CUSTOMERS:
        for month in MONTHS:
            n += 1
            r = rng.random()
            status = "paid" if r < 0.85 else ("refunded" if r < 0.93 else "failed")
            orders.append(
                {
                    "order_id": f"O{n:04d}",
                    "customer_id": cust["id"],
                    "plan": cust["plan"],
                    "month": month,
                    "amount": PLAN_PRICE[cust["plan"]],
                    "status": status,
                }
            )
    return orders


# ---------------------------------------------------------------- tasks
# Golden tool sequences are written as (tool, {key args}) pairs. Expected
# answers are computed from the generated orders below, so goldens can never
# drift from the data.
TASK_DEFS = [
    {
        "id": "t01",
        "question": "What is the monthly price of the Growth plan?",
        "answerable": True,
        "golden": [("search_docs", {"query": "Growth plan price"})],
        "answer_keywords": ["$99", "Growth"],
    },
    {
        "id": "t02",
        "question": "Within how many days can a customer request a full refund?",
        "answerable": True,
        "golden": [("search_docs", {"query": "refund policy"})],
        "answer_keywords": ["30 days"],
    },
    {
        "id": "t03",
        "question": "What is the API daily request limit on the Pro plan?",
        "answerable": True,
        "golden": [("search_docs", {"query": "API rate limit Pro"})],
        "answer_keywords": ["10,000"],
    },
    {
        "id": "t04",
        "question": "How much did customer C0105 pay in total across paid orders?",
        "answerable": True,
        "golden": [
            ("get_customer", {"customer_id": "C0105"}),
            ("list_orders", {"customer_id": "C0105", "status": "paid"}),
        ],
        "answer_keywords": None,  # computed: "$<total>"
    },
    {
        "id": "t05",
        "question": "Which plan is customer C0102 on, and what does it cost per month?",
        "answerable": True,
        "golden": [
            ("get_customer", {"customer_id": "C0102"}),
            ("search_docs", {"query": "Growth plan price"}),
        ],
        "answer_keywords": ["growth", "$99"],
    },
    {
        "id": "t06",
        "question": "What was the total paid revenue in March 2026?",
        "answerable": True,
        "golden": [("revenue_by_month", {"month": "2026-03"})],
        "answer_keywords": None,  # computed: "$<total>"
    },
    {
        "id": "t07",
        "question": "How many paid orders did enterprise customers place in February 2026?",
        "answerable": True,
        "golden": [
            ("orders_by_plan", {"plan": "enterprise", "month": "2026-02", "status": "paid"})
        ],
        "answer_keywords": None,  # computed: "<count>"
    },
    {
        "id": "t08",
        "question": "What is the monthly price of the Starter plan?",
        "answerable": True,
        "golden": [("search_docs", {"query": "Starter plan price"})],
        "answer_keywords": ["$49", "Starter"],
    },
    {
        "id": "t09",
        "question": "Does the Enterprise plan include single sign-on (SSO)?",
        "answerable": True,
        "golden": [("search_docs", {"query": "Enterprise SSO"})],
        "answer_keywords": ["SSO"],
    },
    {
        "id": "t10",
        "question": "What is the support response time for Pro customers?",
        "answerable": True,
        "golden": [("search_docs", {"query": "support SLA Pro"})],
        "answer_keywords": ["4 hours"],
    },
    {
        "id": "t11",
        "question": "What is the name of the company's CEO?",
        "answerable": False,
        "golden": [],
        "answer_keywords": [],
    },
    {
        "id": "t12",
        "question": "What was the total paid revenue in 2025?",
        "answerable": False,
        "golden": [],
        "answer_keywords": [],
    },
]


def build_tasks(orders):
    def paid_total(customer_id=None, month=None):
        return sum(
            o["amount"]
            for o in orders
            if o["status"] == "paid"
            and (customer_id is None or o["customer_id"] == customer_id)
            and (month is None or o["month"] == month)
        )

    tasks = []
    for td in TASK_DEFS:
        t = dict(td)
        t["golden"] = [{"tool": tool, "args": args} for tool, args in td["golden"]]
        if td["id"] == "t04":
            total = paid_total(customer_id="C0105")
            t["answer_keywords"] = [f"${total}"]
            t["expected_answer"] = (
                f"Customer C0105 paid ${total} in total across paid orders."
            )
        elif td["id"] == "t06":
            total = paid_total(month="2026-03")
            t["answer_keywords"] = [f"${total}"]
            t["expected_answer"] = f"Total paid revenue in March 2026 was ${total}."
        elif td["id"] == "t07":
            count = sum(
                1
                for o in orders
                if o["plan"] == "enterprise"
                and o["month"] == "2026-02"
                and o["status"] == "paid"
            )
            # Full phrase, not the bare number: "2" alone would also match
            # the "2" inside the month string "2026-02".
            t["answer_keywords"] = [f"{count} paid orders"]
            t["expected_answer"] = (
                f"Enterprise customers placed {count} paid orders in February 2026."
            )
        elif td["answerable"]:
            t["expected_answer"] = " ".join(td["answer_keywords"])
        else:
            t["expected_answer"] = None
        tasks.append(t)
    return tasks


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / "corpus.jsonl", "w") as f:
        for doc in DOCS:
            f.write(json.dumps(doc, sort_keys=True) + "\n")
    orders = generate_orders()
    with open(DATA / "orders.json", "w") as f:
        json.dump(
            {"customers": CUSTOMERS, "orders": orders}, f, indent=2, sort_keys=True
        )
        f.write("\n")
    tasks = build_tasks(orders)
    with open(DATA / "tasks.json", "w") as f:
        json.dump(tasks, f, indent=2, sort_keys=True)
        f.write("\n")
    print(
        f"wrote {len(DOCS)} docs, {len(CUSTOMERS)} customers, "
        f"{len(orders)} orders, {len(tasks)} tasks"
    )


if __name__ == "__main__":
    main()
