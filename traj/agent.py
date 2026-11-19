"""A small rule-based tool-using agent (a stand-in for an LLM agent).

The agent is deliberately NOT an LLM: it plans with keyword rules, retrieves
with TF-IDF, and composes answers from tool observations with templates.
That is the point of the harness — it measures *trajectories* (which tools
were called, in what order, with which arguments, and whether the final
answer follows from the observations), and the same CLI scores traces
recorded from any real agent via ``traj score``.

Variants (selected by config) degrade the trajectory in a specific,
measurable way, so the harness can prove it catches each failure mode:

* ``baseline``  — the reference policy; should pass every gate.
* ``chatty``    — repeats every tool call once to "double-check": right
  answers, wasteful trajectory (extra calls, low efficiency).
* ``sloppy``    — wrong first tool on multi-step tasks, drops the price
  lookup on t05, and queries refunded instead of paid orders on t07.
* ``stale``     — retrieval without the freshness cutoff: the superseded
  2024 pricing archive outranks the current price list, so pricing answers
  go wrong while the tool sequence stays perfect.
* ``no_abstain``— answers unanswerable tasks from whatever the search
  returns instead of abstaining.
"""

import re
import time

from .tools import ToolRegistry, tokenize

PLANS = ("starter", "growth", "pro", "enterprise")
MONTH_RE = re.compile(r"20\d\d-(?:0[1-9]|1[0-2])")
MONTH_NAME_RE = re.compile(
    r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(20\d\d)",
    re.IGNORECASE,
)
MONTH_NUM = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}
CUSTOMER_RE = re.compile(r"C\d{4}")


def parse_month(question):
    """'2026-03' or 'March 2026' -> '2026-03'."""
    m = MONTH_RE.search(question)
    if m:
        return m.group(0)
    m = MONTH_NAME_RE.search(question)
    if m:
        return f"{m.group(2)}-{MONTH_NUM[m.group(1).lower()]}"
    return None
MONEY_RE = re.compile(r"\$(\d[\d,]*)")
COUNT_RE = re.compile(r"placed (\d+) .* orders|has (\d+) .* orders")


def _best_sentence(question, text):
    """Sentence in ``text`` sharing the most content tokens with the question."""
    qtoks = set(tokenize(question))
    best, best_score = None, -1
    for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
        if not sent:
            continue
        score = len(qtoks & set(tokenize(sent)))
        if score > best_score:
            best, best_score = sent, score
    return best or text


class Agent:
    def __init__(self, data_dir, variant="baseline"):
        self.variant = variant
        cutoff = None if variant == "stale" else "2025-01-01"
        self.tools = ToolRegistry(data_dir, freshness_cutoff=cutoff)

    # ------------------------------------------------------------ planning
    def _classify(self, question):
        q = question.lower()
        if "ceo" in q or "2025" in q and "revenue" in q and "total paid" in q:
            return "unanswerable"
        if "price" in q and any(p in q for p in PLANS):
            return "pricing"
        if "refund" in q:
            return "refund"
        if "api" in q and "limit" in q:
            return "api_limit"
        if "sso" in q:
            return "sso"
        if "support" in q:
            return "support_sla"
        if "customer" in q and "total" in q:
            return "customer_total"
        if "customer" in q and "plan" in q:
            return "customer_plan"
        if "total paid revenue" in q:
            return "monthly_revenue"
        if "how many" in q and "orders" in q:
            return "plan_orders"
        return "unanswerable"

    def _plan(self, task):
        """First planned step(s) for a task; later steps depend on observations."""
        kind = self._classify(task["question"])
        q = task["question"]
        if kind == "pricing":
            plan = next(p for p in PLANS if p in q.lower())
            return kind, [("search_docs", {"query": f"{plan.capitalize()} plan price"})]
        if kind == "refund":
            return kind, [("search_docs", {"query": "refund policy"})]
        if kind == "api_limit":
            return kind, [("search_docs", {"query": "API rate limit Pro"})]
        if kind == "sso":
            return kind, [("search_docs", {"query": "Enterprise SSO"})]
        if kind == "support_sla":
            return kind, [("search_docs", {"query": "support SLA Pro"})]
        if kind == "customer_total":
            cid = CUSTOMER_RE.search(q).group(0)
            return kind, [
                ("get_customer", {"customer_id": cid}),
                ("list_orders", {"customer_id": cid, "status": "paid"}),
            ]
        if kind == "customer_plan":
            cid = CUSTOMER_RE.search(q).group(0)
            return kind, [("get_customer", {"customer_id": cid})]
        if kind == "monthly_revenue":
            month = parse_month(q)
            return kind, [("revenue_by_month", {"month": month})]
        if kind == "plan_orders":
            plan = next(p for p in PLANS if p in q.lower())
            month = parse_month(q)
            return kind, [
                ("orders_by_plan", {"plan": plan, "month": month, "status": "paid"})
            ]
        return kind, []

    # ------------------------------------------------------------ running
    def run(self, task):
        started = time.monotonic()
        kind, planned = self._plan(task)
        steps = []
        observations = []

        def execute(tool, args):
            result = self.tools.call(tool, args)
            steps.append(
                {"tool": tool, "args": dict(args), "observation": result["observation"]}
            )
            observations.append(result["observation"])
            return result

        # --- variant distortions to the plan ---------------------------
        if self.variant == "sloppy" and kind in ("customer_total", "customer_plan"):
            execute("search_docs", {"query": "customer help"})
        if self.variant == "sloppy" and kind == "plan_orders":
            planned = [
                ("orders_by_plan", {
                    "plan": planned[0][1]["plan"],
                    "month": planned[0][1]["month"],
                    "status": "refunded",  # wrong argument: golden says "paid"
                })
            ]
        if self.variant == "sloppy" and kind == "customer_plan":
            planned = planned[:1]  # drops the price lookup entirely

        # --- execute ----------------------------------------------------
        results = {}
        for tool, args in planned:
            results[tool] = execute(tool, args)
            if self.variant == "chatty":
                execute(tool, args)  # "let me double-check that"

        # Staged second step: customer_plan needs the plan from get_customer.
        if kind == "customer_plan" and self.variant != "sloppy":
            plan = results["get_customer"].get("plan")
            if plan:
                step = ("search_docs", {"query": f"{plan.capitalize()} plan price"})
                results["search_docs"] = execute(*step)
                if self.variant == "chatty":
                    execute(*step)

        answer, abstained = self._answer(task, kind, steps, observations)
        return {
            "task_id": task["id"],
            "agent": self.variant,
            "kind": kind,
            "steps": steps,
            "answer": answer,
            "abstained": abstained,
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
        }

    # ------------------------------------------------------------ answering
    def _answer(self, task, kind, steps, observations):
        q = task["question"]
        if kind == "unanswerable":
            if self.variant == "no_abstain":
                # Answers anyway, from whatever the search returns.
                result = self.tools.search_docs(q)
                steps.append(
                    {"tool": "search_docs", "args": {"query": q},
                     "observation": result["observation"]}
                )
                top = result["doc_ids"][:1]
                if top:
                    doc = next(d for d in self.tools.docs if d["id"] == top[0])
                    return _best_sentence(q, doc["text"]), False
                return "No clear answer found in the documents.", False
            return "I don't know — the available documents and data do not cover this.", True

        if kind in ("pricing", "refund", "api_limit", "sso", "support_sla"):
            top = steps[-1]["observation"]
            if ": " not in top:
                return "I don't know — no matching documents found.", False
            # Observation format: "[d01] Title (date): text"
            text = top.split(": ", 1)[1] if ": " in top else top
            return _best_sentence(q, text), False

        if kind == "customer_total":
            obs = steps[-1]["observation"]
            m = MONEY_RE.search(obs)
            cid = CUSTOMER_RE.search(q).group(0)
            total = m.group(1) if m else "?"
            return f"Customer {cid} paid ${total} in total across paid orders.", False

        if kind == "customer_plan":
            cust_step = next(s for s in steps if s["tool"] == "get_customer")
            cust_obs = cust_step["observation"]
            plan = next((p for p in PLANS if p in cust_obs.lower()), "unknown")
            search_steps = [s for s in steps if s["tool"] == "search_docs"]
            doc_steps = [s for s in search_steps if ": " in s["observation"]]
            if not doc_steps:
                return f"Customer is on the {plan} plan.", False
            price_text = doc_steps[-1]["observation"].split(": ", 1)[1]
            # Prefer the sentence naming this customer's plan (breaks the
            # Starter/Growth tie: both match "plan" + "per month" equally).
            plan_sentence = next(
                (s for s in re.split(r"(?<=[.!?])\s+", price_text)
                 if plan in s.lower() and "$" in s),
                None,
            )
            sentence = plan_sentence or _best_sentence(q, price_text)
            price = MONEY_RE.search(sentence)
            price = f"${price.group(1)}" if price else "unknown price"
            return (
                f"Customer is on the {plan} plan, which costs {price} per month."
            ), False

        if kind == "monthly_revenue":
            obs = steps[-1]["observation"]
            m = MONEY_RE.search(obs)
            month = parse_month(q)
            return f"Total paid revenue in {month} was ${m.group(1)}.", False

        if kind == "plan_orders":
            obs = steps[-1]["observation"]
            m = COUNT_RE.search(obs)
            count = m.group(1) or m.group(2) if m else "?"
            plan = next(p for p in PLANS if p in q.lower())
            month = parse_month(q)
            return (
                f"{plan.capitalize()} customers placed {count} paid orders "
                f"in {month}."
            ), False

        return "I don't know.", True
