#!/usr/bin/env python3
"""Quick smoke test for the running Flask app's `/ask` endpoint.

Usage:
    python app.py &          # start the server in one terminal (or foreground
                              # in a second terminal)
    python test_client.py    # run this once it's up

Sends each question in SAMPLE_QUESTIONS to POST /ask and prints the answer
and cited pages. Exits non-zero if any request fails outright (connection
error or non-2xx response) — useful as a lightweight post-deploy check. It
does not grade answer quality; that still needs a human (or an eval set).
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:5000"

# A mix of direct lookups and an intentionally out-of-scope question, so you
# can see both the grounded path and the "no relevant context" fallback.
SAMPLE_QUESTIONS = [
    "What causes diabetes?",
    "How much water should I drink each day?",
    "What are the symptoms of the common cold?",
    "What do blood pressure numbers mean?",
    "How should I clean a minor cut?",
    "Why is sleep important for health?",
    "How does vaccination work?",
    "What is the airspeed velocity of an unladen swallow?",  # expect the no-context fallback
]


def ask(question: str) -> dict:
    body = json.dumps({"question": question}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/ask",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    print(f"Smoke-testing {BASE_URL}/ask with {len(SAMPLE_QUESTIONS)} sample question(s)...\n")
    failures = 0

    for question in SAMPLE_QUESTIONS:
        print(f"Q: {question}")
        try:
            result = ask(question)
        except urllib.error.HTTPError as exc:
            print(f"  HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}\n")
            failures += 1
            continue
        except urllib.error.URLError as exc:
            print(f"  Connection failed: {exc.reason}")
            print("  Is the server running? Start it with: python app.py\n")
            failures += 1
            continue

        print(f"A: {result.get('answer')}")
        sources = result.get("sources", [])
        if sources:
            pages = ", ".join(
                f"p.{s['page'] + 1}" for s in sources
                if isinstance(s.get("page"), int) and s["page"] >= 0
            )
            if pages:
                print(f"   sources: {pages}")
        print()

    if failures:
        print(f"{failures}/{len(SAMPLE_QUESTIONS)} question(s) failed at the request level.")
    else:
        print("All questions completed without a request-level failure.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
