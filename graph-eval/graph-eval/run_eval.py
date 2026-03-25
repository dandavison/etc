#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["anthropic>=0.40"]
# ///
"""
Graph representation eval runner.

Tests how well different graph representations (verbal, ASCII, JSON, YAML, mermaid)
communicate software architecture topology to an LLM across varying complexity levels.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import anthropic

# Add project root to path so we can import graphs
sys.path.insert(0, str(Path(__file__).parent))

from graphs import COMPLEXITY_LABELS, GRAPHS, RENDERERS, Graph, build_prompt

SUBJECT_MODEL = "claude-sonnet-4-6"
GRADER_MODEL = "claude-sonnet-4-6"
RUNS_PER_CONDITION = 3
MAX_CONCURRENCY = 10


async def run_subject(
    client: anthropic.AsyncAnthropic,
    sem: asyncio.Semaphore,
    graph: Graph,
    fmt: str,
    run_idx: int,
) -> dict:
    """Present a graph representation to the subject model and collect answers."""
    renderer = RENDERERS[fmt]
    representation = renderer(graph)
    questions = graph.questions()
    prompt = build_prompt(representation, questions)

    async with sem:
        t0 = time.monotonic()
        resp = await client.messages.create(
            model=SUBJECT_MODEL,
            max_tokens=2048,
            temperature=1.0,
            messages=[{"role": "user", "content": prompt}],
        )
        elapsed = time.monotonic() - t0

    response_text = resp.content[0].text
    tokens_in = resp.usage.input_tokens
    tokens_out = resp.usage.output_tokens

    return {
        "graph": graph.name,
        "format": fmt,
        "run": run_idx,
        "prompt": prompt,
        "representation": representation,
        "response": response_text,
        "elapsed_s": round(elapsed, 2),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "questions": questions,
    }


GRADER_SYSTEM = """\
You are a precise grader. You will receive a question, the ground-truth answer, and a model's \
response. Determine whether the model's answer to this specific question is correct.

Rules:
- For list questions: the model must name ALL correct items and NO incorrect items. \
  Minor name variations are OK (e.g. "Auth" vs "Auth Service", "Msg Q" vs "Message Queue") \
  if unambiguous in context.
- For reachability/path questions: the model must give the correct yes/no answer. If yes and \
  a path is listed, the path must be valid: every consecutive pair must be a direct edge. \
  The path does NOT need to match the ground-truth path exactly — any valid path is correct. \
  If an edge list is provided, use it to verify the path.
- For count questions: the exact number must match.

Respond with ONLY a JSON object: {"correct": true/false, "explanation": "brief reason"}
"""


async def grade_one(
    client: anthropic.AsyncAnthropic,
    sem: asyncio.Semaphore,
    question: dict[str, str],
    response: str,
) -> dict:
    """Grade a single question answer."""
    edges_info = ""
    if "edges" in question:
        edges_info = f"\nDirect edges in the graph: {question['edges']}\n"
    prompt = (
        f"Question: {question['text']}\n"
        f"Ground-truth answer: {question['answer']}\n"
        f"{edges_info}"
        f"Model's full response (extract the relevant answer):\n{response}"
    )
    async with sem:
        resp = await client.messages.create(
            model=GRADER_MODEL,
            max_tokens=256,
            temperature=0.0,
            system=GRADER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
    text = resp.content[0].text.strip()
    # Extract JSON from response
    try:
        # Handle markdown code blocks
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        result = json.loads(text)
    except (json.JSONDecodeError, IndexError):
        result = {"correct": False, "explanation": f"Grader parse error: {text[:200]}"}

    return {
        "question_id": question["id"],
        "question": question["text"],
        "ground_truth": question["answer"],
        "correct": result.get("correct", False),
        "explanation": result.get("explanation", ""),
    }


async def run_all() -> dict:
    """Run the full eval suite."""
    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    formats = list(RENDERERS.keys())
    print(f"Running eval: {len(GRAPHS)} graphs × {len(formats)} formats × {RUNS_PER_CONDITION} runs")
    print(f"Subject model: {SUBJECT_MODEL}, Grader model: {GRADER_MODEL}")
    print()

    # Phase 1: Run all subject calls
    subject_tasks = []
    for gi, graph in enumerate(GRAPHS):
        for fmt in formats:
            for run_idx in range(RUNS_PER_CONDITION):
                subject_tasks.append(run_subject(client, sem, graph, fmt, run_idx))

    total = len(subject_tasks)
    print(f"Phase 1: Running {total} subject calls...")
    results = await asyncio.gather(*subject_tasks)
    print(f"Phase 1 complete. Collected {len(results)} responses.")
    print()

    # Phase 2: Grade all responses
    grade_tasks = []
    result_question_map: list[tuple[int, int]] = []  # (result_idx, question_idx)
    for ri, r in enumerate(results):
        for qi, q in enumerate(r["questions"]):
            grade_tasks.append(grade_one(client, sem, q, r["response"]))
            result_question_map.append((ri, qi))

    print(f"Phase 2: Grading {len(grade_tasks)} answers...")
    grades = await asyncio.gather(*grade_tasks)
    print(f"Phase 2 complete.")
    print()

    # Attach grades to results
    for grade, (ri, qi) in zip(grades, result_question_map):
        results[ri].setdefault("grades", []).append(grade)

    # Phase 3: Aggregate
    benchmark = aggregate(results, formats)
    return benchmark


def aggregate(results: list[dict], formats: list[str]) -> dict:
    """Aggregate results into a benchmark report."""
    # Structure: complexity -> format -> list of per-run pass rates
    data: dict[str, dict[str, list[dict]]] = {}

    for r in results:
        gi = next(i for i, g in enumerate(GRAPHS) if g.name == r["graph"])  # noqa: B007
        complexity = COMPLEXITY_LABELS[gi]
        fmt = r["format"]
        data.setdefault(complexity, {}).setdefault(fmt, [])

        grades = r.get("grades", [])
        n_correct = sum(1 for g in grades if g["correct"])
        n_total = len(grades)
        pass_rate = n_correct / n_total if n_total > 0 else 0.0

        data[complexity][fmt].append({
            "run": r["run"],
            "pass_rate": pass_rate,
            "n_correct": n_correct,
            "n_total": n_total,
            "elapsed_s": r["elapsed_s"],
            "tokens_in": r["tokens_in"],
            "tokens_out": r["tokens_out"],
            "grades": grades,
            "response": r["response"],
        })

    # Compute summary stats
    summary: dict[str, dict[str, dict]] = {}
    for complexity in COMPLEXITY_LABELS:
        summary[complexity] = {}
        for fmt in formats:
            runs = data.get(complexity, {}).get(fmt, [])
            if not runs:
                continue
            pass_rates = [r["pass_rate"] for r in runs]
            mean_pr = sum(pass_rates) / len(pass_rates)
            variance = sum((p - mean_pr) ** 2 for p in pass_rates) / len(pass_rates)
            stddev = variance ** 0.5
            summary[complexity][fmt] = {
                "mean_pass_rate": round(mean_pr, 3),
                "stddev": round(stddev, 3),
                "min": round(min(pass_rates), 3),
                "max": round(max(pass_rates), 3),
                "runs": len(runs),
            }

    # Per-question breakdown
    question_breakdown: dict[str, dict[str, dict[str, dict]]] = {}
    for complexity in COMPLEXITY_LABELS:
        question_breakdown[complexity] = {}
        for fmt in formats:
            question_breakdown[complexity][fmt] = {}
            runs = data.get(complexity, {}).get(fmt, [])
            for run in runs:
                for g in run["grades"]:
                    qid = g["question_id"]
                    question_breakdown[complexity][fmt].setdefault(qid, {"correct": 0, "total": 0})
                    question_breakdown[complexity][fmt][qid]["total"] += 1
                    if g["correct"]:
                        question_breakdown[complexity][fmt][qid]["correct"] += 1

    return {
        "metadata": {
            "subject_model": SUBJECT_MODEL,
            "grader_model": GRADER_MODEL,
            "runs_per_condition": RUNS_PER_CONDITION,
            "formats": formats,
            "complexity_levels": COMPLEXITY_LABELS,
            "graphs": [g.name for g in GRAPHS],
        },
        "summary": summary,
        "question_breakdown": question_breakdown,
        "raw_data": data,
    }


def print_report(benchmark: dict) -> None:
    """Print a human-readable summary table."""
    formats = benchmark["metadata"]["formats"]
    complexities = benchmark["metadata"]["complexity_levels"]

    # Header
    col_w = 12
    header = f"{'Complexity':<12}" + "".join(f"{fmt:>{col_w}}" for fmt in formats)
    print("=" * len(header))
    print("GRAPH REPRESENTATION EVAL — PASS RATES (mean ± stddev)")
    print(f"Subject: {benchmark['metadata']['subject_model']}")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for complexity in complexities:
        row = f"{complexity:<12}"
        for fmt in formats:
            s = benchmark["summary"].get(complexity, {}).get(fmt)
            if s:
                cell = f"{s['mean_pass_rate']:.0%}±{s['stddev']:.0%}"
                row += f"{cell:>{col_w}}"
            else:
                row += f"{'N/A':>{col_w}}"
        print(row)

    print("-" * len(header))
    print()

    # Per-question breakdown
    print("PER-QUESTION PASS RATES (correct/total across all runs)")
    print("-" * 80)
    qids = ["q1_forward", "q2_backward", "q3_reachable", "q4_sources", "q5_sinks", "q6_degree"]
    q_labels = {
        "q1_forward": "Q1:fwd_neighbors",
        "q2_backward": "Q2:bkwd_neighbors",
        "q3_reachable": "Q3:reachability",
        "q4_sources": "Q4:sources",
        "q5_sinks": "Q5:sinks",
        "q6_degree": "Q6:degree",
    }

    for complexity in complexities:
        print(f"\n  {complexity.upper()}")
        qb = benchmark["question_breakdown"].get(complexity, {})
        header2 = f"    {'Question':<20}" + "".join(f"{fmt:>{col_w}}" for fmt in formats)
        print(header2)
        for qid in qids:
            row = f"    {q_labels[qid]:<20}"
            for fmt in formats:
                info = qb.get(fmt, {}).get(qid)
                if info:
                    cell = f"{info['correct']}/{info['total']}"
                    row += f"{cell:>{col_w}}"
                else:
                    row += f"{'N/A':>{col_w}}"
            print(row)


def main() -> None:
    benchmark = asyncio.run(run_all())

    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = results_dir / f"benchmark_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"Results saved to {out_path}")
    print()

    print_report(benchmark)


if __name__ == "__main__":
    main()
