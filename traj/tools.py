"""Deterministic tools for the demo agent.

Two tool families, both backed by the generated data files:

* ``search_docs`` — TF-IDF retrieval over the fictional Northwind Analytics
  corpus (stdlib only). An optional freshness cutoff drops documents dated
  before it; disabling the cutoff is how the ``stale`` agent variant ends up
  answering from the superseded 2024 pricing archive.
* Warehouse tools (``get_customer``, ``list_orders``, ``revenue_by_month``,
  ``orders_by_plan``) — plain lookups over ``orders.json``.

Every tool returns a small dict with a human-readable ``observation`` string
(the agent answers from observations) plus structured fields the judge and
the tests can check. No network, no randomness.
"""

import json
import math
import re
from pathlib import Path

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "what", "which", "who",
    "whom", "how", "many", "much", "does", "do", "did", "in", "on", "of",
    "for", "to", "and", "or", "per", "by", "with", "within", "across",
    "did", "it", "its", "that", "this", "from", "at", "as", "be", "can",
    "i", "you", "he", "she", "we", "they", "my", "your", "his", "her",
    "their", "our", "me", "him", "us", "them", "there", "here", "when",
    "where", "why", "not", "no", "yes", "if", "then", "than", "so", "but",
    "all", "any", "each", "few", "more", "most", "other", "some", "such",
    "only", "own", "same", "too", "very", "just", "also", "into", "over",
    "under", "again", "further", "once", "name", "total", "across",
}

TOKEN_RE = re.compile(r"[a-z0-9$]+")


def tokenize(text):
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


class ToolRegistry:
    """All tools the demo agent may call, plus the retrieval index."""

    def __init__(self, data_dir, freshness_cutoff="2025-01-01"):
        data_dir = Path(data_dir)
        self.freshness_cutoff = freshness_cutoff
        with open(data_dir / "corpus.jsonl") as f:
            self.docs = [json.loads(line) for line in f if line.strip()]
        with open(data_dir / "orders.json") as f:
            store = json.load(f)
        self.customers = {c["id"]: c for c in store["customers"]}
        self.orders = store["orders"]
        self._build_index()

    # ---------------------------------------------------------- retrieval
    def _build_index(self):
        self._df = {}
        self._doc_tf = []
        for doc in self.docs:
            toks = tokenize(doc["title"] + " " + doc["text"])
            tf = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            self._doc_tf.append(tf)
            for t in set(toks):
                self._df[t] = self._df.get(t, 0) + 1
        n = len(self.docs)
        self._idf = {t: math.log((n + 1) / (df + 1)) + 1.0 for t, df in self._df.items()}

    def _score(self, query, doc_idx):
        qtoks = tokenize(query)
        if not qtoks:
            return 0.0
        tf = self._doc_tf[doc_idx]
        score = 0.0
        for t in set(qtoks):
            if t in tf:
                score += tf[t] * self._idf.get(t, 0.0)
        # Small bonus for the query's distinctive tokens appearing in the title.
        title_toks = set(tokenize(self.docs[doc_idx]["title"]))
        score += 0.5 * len(set(qtoks) & title_toks)
        return score

    def search_docs(self, query, k=3):
        """Return the top-k docs by TF-IDF score, honouring the cutoff."""
        scored = []
        for i, doc in enumerate(self.docs):
            if self.freshness_cutoff and doc["date"] < self.freshness_cutoff:
                continue
            s = self._score(query, i)
            if s > 0:
                scored.append((s, doc["id"], doc))
        # Highest score first; ties break by doc id so runs are deterministic.
        scored.sort(key=lambda x: (-x[0], x[1]))
        top = [d for _, _, d in scored[:k]]
        obs = "\n".join(
            f"[{d['id']}] {d['title']} ({d['date']}): {d['text']}" for d in top
        ) or "No matching documents found."
        return {
            "tool": "search_docs",
            "args": {"query": query},
            "doc_ids": [d["id"] for d in top],
            "observation": obs,
        }

    # ---------------------------------------------------------- warehouse
    def get_customer(self, customer_id):
        cust = self.customers.get(customer_id)
        if cust is None:
            return {
                "tool": "get_customer",
                "args": {"customer_id": customer_id},
                "observation": f"No customer with id {customer_id}.",
                "found": False,
            }
        return {
            "tool": "get_customer",
            "args": {"customer_id": customer_id},
            "observation": (
                f"Customer {cust['id']} ({cust['name']}) is on the "
                f"{cust['plan']} plan."
            ),
            "found": True,
            "plan": cust["plan"],
        }

    def list_orders(self, customer_id, status):
        rows = [
            o for o in self.orders
            if o["customer_id"] == customer_id and o["status"] == status
        ]
        total = sum(o["amount"] for o in rows)
        lines = ", ".join(f"{o['order_id']} ${o['amount']} ({o['month']})" for o in rows)
        return {
            "tool": "list_orders",
            "args": {"customer_id": customer_id, "status": status},
            "observation": (
                f"Customer {customer_id} has {len(rows)} {status} orders "
                f"totalling ${total}: {lines or 'none'}."
            ),
            "count": len(rows),
            "total": total,
        }

    def revenue_by_month(self, month):
        rows = [o for o in self.orders if o["month"] == month and o["status"] == "paid"]
        total = sum(o["amount"] for o in rows)
        return {
            "tool": "revenue_by_month",
            "args": {"month": month},
            "observation": (
                f"Total paid revenue in {month} was ${total} "
                f"across {len(rows)} paid orders."
            ),
            "count": len(rows),
            "total": total,
        }

    def orders_by_plan(self, plan, month, status):
        rows = [
            o for o in self.orders
            if o["plan"] == plan and o["month"] == month and o["status"] == status
        ]
        return {
            "tool": "orders_by_plan",
            "args": {"plan": plan, "month": month, "status": status},
            "observation": (
                f"{plan} customers placed {len(rows)} {status} orders "
                f"in {month}."
            ),
            "count": len(rows),
        }

    # ---------------------------------------------------------- dispatch
    def call(self, tool, args):
        fn = {
            "search_docs": lambda: self.search_docs(args["query"]),
            "get_customer": lambda: self.get_customer(args["customer_id"]),
            "list_orders": lambda: self.list_orders(args["customer_id"], args["status"]),
            "revenue_by_month": lambda: self.revenue_by_month(args["month"]),
            "orders_by_plan": lambda: self.orders_by_plan(
                args["plan"], args["month"], args["status"]
            ),
        }[tool]
        return fn()
