#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Generate a self-contained HTML report for the graph representation eval."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from graphs import COMPLEXITY_LABELS, GRAPHS, RENDERERS


def esc(s: str) -> str:
    return html.escape(s)


def generate_report(benchmark_path: str, output_path: str) -> None:
    with open(benchmark_path) as f:
        benchmark = json.load(f)

    formats = benchmark["metadata"]["formats"]
    complexities = benchmark["metadata"]["complexity_levels"]

    # Collect renderings
    renderings: dict[str, dict[str, str]] = {}
    for i, g in enumerate(GRAPHS):
        key = COMPLEXITY_LABELS[i]
        renderings[key] = {}
        for fmt, renderer in RENDERERS.items():
            renderings[key][fmt] = renderer(g)

    # Graph metadata
    graph_meta = []
    for i, g in enumerate(GRAPHS):
        graph_meta.append({
            "complexity": COMPLEXITY_LABELS[i],
            "name": g.name,
            "nodes": len(g.nodes),
            "edges": len(g.edges),
            "node_list": g.nodes,
            "questions": g.questions(),
        })

    # Build per-question data for the detailed view
    question_data = benchmark.get("question_breakdown", {})

    # Build the HTML
    parts: list[str] = []
    p = parts.append

    p("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Graph Representation Eval</title>
<style>
:root {
  --bg: #1a1a2e;
  --surface: #16213e;
  --surface2: #0f3460;
  --text: #e0e0e0;
  --text-muted: #8892b0;
  --accent: #64ffda;
  --accent2: #bd93f9;
  --red: #ff5555;
  --orange: #ffb86c;
  --green: #50fa7b;
  --yellow: #f1fa8c;
  --border: #233554;
  --mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  --sans: 'Inter', -apple-system, system-ui, sans-serif;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: var(--sans);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}
h1 { color: var(--accent); font-size: 1.8rem; margin-bottom: 0.5rem; }
h2 { color: var(--accent2); font-size: 1.4rem; margin: 2rem 0 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }
h3 { color: var(--text); font-size: 1.1rem; margin: 1.5rem 0 0.5rem; }
p, li { color: var(--text-muted); margin-bottom: 0.5rem; }
strong { color: var(--text); }
a { color: var(--accent); }
code { font-family: var(--mono); font-size: 0.85em; background: var(--surface); padding: 0.15em 0.4em; border-radius: 3px; }

.prompt-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent2);
  padding: 1.2rem;
  margin: 1rem 0;
  border-radius: 4px;
  font-size: 0.9rem;
  white-space: pre-wrap;
  color: var(--text-muted);
  line-height: 1.5;
}

table {
  border-collapse: collapse;
  width: 100%;
  margin: 1rem 0;
  font-size: 0.9rem;
}
th, td {
  padding: 0.6rem 0.8rem;
  text-align: center;
  border: 1px solid var(--border);
}
th {
  background: var(--surface2);
  color: var(--accent);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}
td { background: var(--surface); }
td:first-child, th:first-child { text-align: left; }

.pass-100 { color: var(--green); font-weight: 700; }
.pass-90 { color: var(--yellow); font-weight: 600; }
.pass-80 { color: var(--orange); font-weight: 600; }
.pass-low { color: var(--red); font-weight: 700; }

.graph-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  margin: 1.5rem 0;
  overflow: hidden;
}
.graph-header {
  background: var(--surface2);
  padding: 0.8rem 1.2rem;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.graph-header:hover { background: #1a4a7a; }
.graph-header h3 { margin: 0; }
.graph-header .meta { color: var(--text-muted); font-size: 0.85rem; }
.graph-body { padding: 1.2rem; display: none; }
.graph-body.open { display: block; }

.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--border);
  margin-bottom: 1rem;
}
.tab-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.85rem;
  font-family: var(--sans);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.15s;
}
.tab-btn:hover { color: var(--text); }
.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}
.tab-panel { display: none; }
.tab-panel.active { display: block; }

pre.rendering {
  background: #0d1117;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1rem;
  overflow-x: auto;
  font-family: var(--mono);
  font-size: 0.78rem;
  line-height: 1.4;
  color: #c9d1d9;
  white-space: pre;
  max-height: 600px;
}

.findings { margin: 1rem 0; }
.findings li { margin-bottom: 0.8rem; padding-left: 0.5rem; }
.findings li strong { color: var(--accent); }

.q-table td.pass { color: var(--green); }
.q-table td.fail { color: var(--red); font-weight: 700; }

.subtitle { color: var(--text-muted); font-size: 0.95rem; margin-bottom: 2rem; }
.section-note { color: var(--text-muted); font-size: 0.85rem; font-style: italic; margin: 0.5rem 0 1rem; }

footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--text-muted); font-size: 0.8rem; }
</style>
</head>
<body>
""")

    p('<h1>Graph Representation Eval</h1>')
    p('<p class="subtitle">How well do different textual formats communicate software architecture topology to an LLM?</p>')

    # --- Prompt ---
    p('<h2>The Prompt</h2>')
    p('<div class="prompt-box">')
    prompt_text = """I'd like you to investigate the question of how the following methods of communicating graph structures to an LLM compare. I'd like you to do this via formal evals, using the techniques described in the /skill-creator skill. Note however that here you're not actually creating a skill; you're performing a set of eval experiments.

The methods of communicating graph structure are
1. verbally
2. via ASCII art
3. via JSON
4. via YAML
5. via mermaid

I'd like you to investigate which of these result in faithfully communicating a graph to an LLM. The "graphs" will be "box-and-arrow" system architecture diagrams as commonly used in software engineering. You must investigate a range of complexities of these diagrams; we want to know where -- if anywhere -- along this complexity spectrum the ability of a particular method of representation breaks down in its ability to communicate the topology faithfully to the LLM. For ASCII art, JSON, and YAML you can invent the exact way in which the graph is represented; this choice should be something that a human author might realistically use while also aiming to be very effective at communicating the topology to the LLM. In other words, the choice should be aimed at giving those methods a good chance of showing that they can match or outperform purely verbal transmission, or transmission via a formal grammar intended for the purpose (mermaid)."""
    p(esc(prompt_text))
    p('</div>')

    # --- Design ---
    p('<h2>Experiment Design</h2>')
    p("""<ul>
<li><strong>Subject model:</strong> Claude Sonnet 4.6 (temperature=1.0, 3 runs per condition)</li>
<li><strong>Grader model:</strong> Claude Sonnet 4.6 (temperature=0, comparing against algorithmically-computed ground truth)</li>
<li><strong>Formats:</strong> verbal prose, ASCII art, JSON, YAML, mermaid</li>
<li><strong>Graphs:</strong> 5 software architecture diagrams at increasing complexity (3→22 nodes, 2→34 edges)</li>
<li><strong>Questions per graph:</strong> 6 topology questions &mdash; forward neighbors, backward neighbors, reachability, sources, sinks, total degree</li>
<li><strong>Total eval calls:</strong> 75 subject + 450 grading = 525 API calls</li>
</ul>""")

    # --- Summary Table ---
    p('<h2>Results: Pass Rates</h2>')
    p('<table><thead><tr><th>Complexity</th>')
    for fmt in formats:
        p(f'<th>{esc(fmt)}</th>')
    p('</tr></thead><tbody>')
    for c in complexities:
        p('<tr>')
        gm = next(m for m in graph_meta if m["complexity"] == c)
        p(f'<td><strong>{esc(c)}</strong> ({gm["nodes"]}n/{gm["edges"]}e)</td>')
        for fmt in formats:
            s = benchmark["summary"].get(c, {}).get(fmt, {})
            if s:
                mean = s["mean_pass_rate"]
                std = s["stddev"]
                pct = f'{mean:.0%}±{std:.0%}'
                if mean >= 1.0:
                    cls = "pass-100"
                elif mean >= 0.9:
                    cls = "pass-90"
                elif mean >= 0.8:
                    cls = "pass-80"
                else:
                    cls = "pass-low"
                p(f'<td class="{cls}">{pct}</td>')
            else:
                p('<td>N/A</td>')
        p('</tr>')
    p('</tbody></table>')

    # --- Per-question breakdown ---
    p('<h2>Per-Question Breakdown</h2>')
    p('<p class="section-note">Correct / total across 3 runs per condition</p>')

    qids = ["q1_forward", "q2_backward", "q3_reachable", "q4_sources", "q5_sinks", "q6_degree"]
    q_labels = {
        "q1_forward": "Q1: Forward neighbors",
        "q2_backward": "Q2: Backward neighbors",
        "q3_reachable": "Q3: Reachability",
        "q4_sources": "Q4: Sources (no incoming)",
        "q5_sinks": "Q5: Sinks (no outgoing)",
        "q6_degree": "Q6: Total degree",
    }

    for c in complexities:
        gm = next(m for m in graph_meta if m["complexity"] == c)
        p(f'<h3>{esc(c).upper()} &mdash; {esc(gm["name"])}</h3>')
        p('<table class="q-table"><thead><tr><th>Question</th>')
        for fmt in formats:
            p(f'<th>{esc(fmt)}</th>')
        p('</tr></thead><tbody>')
        qb = question_data.get(c, {})
        for qid in qids:
            p(f'<tr><td>{esc(q_labels[qid])}</td>')
            for fmt in formats:
                info = qb.get(fmt, {}).get(qid)
                if info:
                    correct = info["correct"]
                    total = info["total"]
                    cls = "pass" if correct == total else "fail"
                    p(f'<td class="{cls}">{correct}/{total}</td>')
                else:
                    p('<td>N/A</td>')
            p('</tr>')
        p('</tbody></table>')

    # --- Graphs and Renderings ---
    p('<h2>Graphs &amp; Renderings</h2>')
    p('<p class="section-note">Click each graph to expand and view all 5 representations</p>')

    for i, c in enumerate(complexities):
        gm = graph_meta[i]
        graph_id = f'graph-{c}'
        p(f'<div class="graph-section">')
        p(f'<div class="graph-header" onclick="toggleGraph(\'{graph_id}\')">')
        p(f'<h3>{esc(c).upper()}: {esc(gm["name"])}</h3>')
        p(f'<span class="meta">{gm["nodes"]} nodes, {gm["edges"]} edges &mdash; [{", ".join(esc(n) for n in gm["node_list"])}]</span>')
        p('</div>')
        p(f'<div class="graph-body" id="{graph_id}">')

        # Tab bar
        p(f'<div class="tab-bar">')
        for fi, fmt in enumerate(formats):
            active = "active" if fi == 0 else ""
            p(f'<button class="tab-btn {active}" onclick="switchTab(\'{graph_id}\', \'{fmt}\')">{esc(fmt)}</button>')
        p('</div>')

        # Tab panels
        for fi, fmt in enumerate(formats):
            active = "active" if fi == 0 else ""
            rendering = renderings[c][fmt]
            p(f'<div class="tab-panel {active}" id="{graph_id}-{fmt}">')
            p(f'<pre class="rendering">{esc(rendering)}</pre>')
            p('</div>')

        # Questions
        p('<h3 style="margin-top:1rem">Questions asked</h3>')
        p('<ol style="padding-left:1.5rem; font-size:0.85rem">')
        for q in gm["questions"]:
            p(f'<li style="margin-bottom:0.3rem">{esc(q["text"])}<br><code>Ground truth: {esc(q["answer"])}</code></li>')
        p('</ol>')

        p('</div></div>')

    # --- Findings ---
    p('<h2>Findings</h2>')
    p("""<ol class="findings">
<li><strong>Mermaid is the only format achieving 100% across all complexities.</strong>
Zero failures in 90 graded answers. A formal grammar designed for graph description produces
unambiguous syntax that LLMs parse reliably.</li>

<li><strong>JSON and YAML are excellent and statistically indistinguishable.</strong>
100% everywhere except Q5 (sinks) at medium complexity, where each has a single failure in 3 runs.
The failure is a <em>reasoning</em> issue (negative universal quantification), not a format comprehension issue.</li>

<li><strong>Verbal prose is surprisingly robust.</strong>
Competitive with structured formats, failing only on exhaustive enumeration questions (sinks, sources)
at higher complexity. Natural language edge descriptions are well-understood by LLMs.</li>

<li><strong>ASCII art degrades significantly from ~10 nodes onward.</strong> Three failure modes:
<ul>
<li><strong>Arrow direction confusion</strong> &mdash; the model misreads which way arrows point in dense layouts
(Q2 backward neighbors: 0/3 at medium)</li>
<li><strong>Global scan failures</strong> &mdash; cannot reliably identify sinks by scanning a 2D layout
(Q5: 0/3 at medium and large)</li>
<li><strong>Author-side scalability</strong> &mdash; the hand-crafted XL ASCII art had a missing edge in the first run,
showing the format has a completeness problem for authors too</li>
</ul></li>

<li><strong>The complexity threshold is ~10 nodes / 14 edges.</strong>
Below this, all formats are perfect. At medium (10/14), ASCII drops to 61% while others remain at 94&ndash;100%.</li>

<li><strong>Q5 (sinks) is universally the hardest question.</strong>
Requires verifying that a node <em>never</em> appears as a source in any edge &mdash; negative universal quantification.
Only mermaid achieves 100% on this question across all complexities.</li>
</ol>""")

    # --- Recommendations ---
    p('<h2>Practical Recommendations</h2>')
    p("""<ul>
<li>For LLM consumption, prefer <strong>mermaid</strong> or <strong>JSON/YAML edge lists</strong> over ASCII diagrams</li>
<li>ASCII art may still be useful as a <em>supplement</em> alongside a structured format</li>
<li>For simple graphs (&le;6 nodes), any format works &mdash; don&rsquo;t over-engineer the representation</li>
<li>If using verbal descriptions for larger graphs, structure them carefully: one edge per sentence, explicit directionality</li>
</ul>""")

    # --- Methodology ---
    p('<h2>Methodology Notes</h2>')
    p("""<ul>
<li>ASCII art was hand-crafted (not programmatically generated) to give the format its best chance.
Real-world ASCII diagrams would likely perform worse.</li>
<li>Initial run revealed a missing edge in the XL ASCII diagram, requiring a second run with fixes.
Both benchmark files are preserved in the results.</li>
<li>Grading was refined between runs to accept any valid path for reachability questions,
not just the specific BFS-shortest path.</li>
<li>Temperature=1.0 for the subject model ensures variance between runs;
temperature=0 for the grader ensures deterministic grading.</li>
</ul>""")

    p("""<footer>
Generated from <a href="https://github.com/dandavison/etc/tree/master/graph-eval">graph-eval</a> experiment.
Subject model: Claude Sonnet 4.6. March 2026.
</footer>""")

    # --- JS ---
    p("""
<script>
function toggleGraph(id) {
  const el = document.getElementById(id);
  el.classList.toggle('open');
}
function switchTab(graphId, fmt) {
  const section = document.getElementById(graphId);
  section.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  section.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  section.querySelector(`.tab-btn[onclick*="'${fmt}'"]`).classList.add('active');
  document.getElementById(`${graphId}-${fmt}`).classList.add('active');
}
</script>
</body>
</html>""")

    html_content = "\n".join(parts)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html_content)
    print(f"Report written to {output_path} ({len(html_content)} bytes)")


if __name__ == "__main__":
    benchmark = sys.argv[1] if len(sys.argv) > 1 else "results/benchmark_20260325_072205.json"
    output = sys.argv[2] if len(sys.argv) > 2 else "/Users/dan/src/etc/graph-eval/index.html"
    generate_report(benchmark, output)
