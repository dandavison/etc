#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Generate a self-contained HTML report for the abstract graph eval."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from graphs import COMPLEXITY_LABELS, GRAPHS, RENDERERS


def esc(s: str) -> str:
    return html.escape(s)


def generate_report(benchmark_path: str, arch_benchmark_path: str, output_path: str) -> None:
    with open(benchmark_path) as f:
        benchmark = json.load(f)
    with open(arch_benchmark_path) as f:
        arch_benchmark = json.load(f)

    formats = benchmark["metadata"]["formats"]
    complexities = benchmark["metadata"]["complexity_levels"]

    renderings: dict[str, dict[str, str]] = {}
    for i, g in enumerate(GRAPHS):
        key = COMPLEXITY_LABELS[i]
        renderings[key] = {}
        for fmt, renderer in RENDERERS.items():
            renderings[key][fmt] = renderer(g)

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

    question_data = benchmark.get("question_breakdown", {})
    parts: list[str] = []
    p = parts.append

    p("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Abstract Graph Eval: Do LLMs Use Semantic Priors?</title>
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

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin: 1rem 0;
}
.comparison-grid > div {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem;
}
.comparison-grid h4 {
  color: var(--accent2);
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}
.delta-positive { color: var(--green); }
.delta-negative { color: var(--red); }
.delta-zero { color: var(--text-muted); }
</style>
</head>
<body>
""")

    p('<h1>Abstract Graph Eval</h1>')
    p('<p class="subtitle">Do LLMs use semantic priors when parsing graph topology? A controlled comparison with meaningless node labels.</p>')

    # --- Motivation ---
    p('<h2>Motivation</h2>')
    p("""<div class="prompt-box">Donald says:

"I'd also be interested in seeing a repeat of this experiment, but instead of system
architecture graphs, arbitrary meaningless graphs (nodes labeled A, B, C, etc.). LLMs
likely are inferring graph facts based on implied semantics of nodes."</div>""")
    p("""<p>This is a follow-up to the <a href="../graph-eval/">system architecture eval</a>.
That experiment found that mermaid, JSON, YAML, and verbal prose all communicated graph topology
well, while ASCII art degraded at higher complexity. But a confound remained: with nodes named
"Load Balancer", "API Gateway", "Database", the LLM may have been <em>inferring</em> edges from
domain knowledge rather than <em>reading</em> them from the representation.</p>
<p>This experiment uses the <strong>identical topologies</strong> but replaces all semantic node names
with abstract letters (A, B, C, &hellip;). Any drop in performance isolates the contribution of
semantic priors.</p>""")

    # --- Design ---
    p('<h2>Experiment Design</h2>')
    p(f"""<ul>
<li><strong>Subject model:</strong> Claude Sonnet 4.6 (temperature=1.0, 3 runs per condition)</li>
<li><strong>Grader model:</strong> Claude Sonnet 4.6 (temperature=0, comparing against algorithmically-computed ground truth)</li>
<li><strong>Formats:</strong> verbal edge list, ASCII art, JSON, YAML, mermaid</li>
<li><strong>Graphs:</strong> 5 directed graphs at increasing complexity (3&rarr;22 nodes, 2&rarr;34 edges)</li>
<li><strong>Key difference from architecture eval:</strong> nodes labeled A, B, C, &hellip; with no edge labels.
Verbal format lists edges as "A &rarr; B" rather than "Client sends HTTP requests to API Server"</li>
<li><strong>Questions per graph:</strong> 6 topology questions &mdash; forward neighbors, backward neighbors, reachability, sources, sinks, total degree</li>
<li><strong>Total eval calls:</strong> 75 subject + 450 grading = 525 API calls</li>
</ul>""")

    # --- Summary Table ---
    p('<h2>Results: Abstract Graphs</h2>')
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
                pct = f'{mean:.0%}\u00b1{std:.0%}'
                cls = "pass-100" if mean >= 1.0 else "pass-90" if mean >= 0.9 else "pass-80" if mean >= 0.8 else "pass-low"
                p(f'<td class="{cls}">{pct}</td>')
            else:
                p('<td>N/A</td>')
        p('</tr>')
    p('</tbody></table>')

    # --- Comparison with architecture eval ---
    p('<h2>Comparison: Architecture vs Abstract Labels</h2>')
    p('<p class="section-note">Same topologies, same questions, same model. Only difference: node naming.</p>')
    p('<table><thead><tr><th>Complexity</th>')
    for fmt in formats:
        p(f'<th colspan="2">{esc(fmt)}</th>')
    p('</tr><tr><th></th>')
    for _ in formats:
        p('<th>Arch</th><th>Abstract</th>')
    p('</tr></thead><tbody>')
    for c in complexities:
        p('<tr>')
        gm = next(m for m in graph_meta if m["complexity"] == c)
        p(f'<td><strong>{esc(c)}</strong></td>')
        for fmt in formats:
            arch_s = arch_benchmark["summary"].get(c, {}).get(fmt, {})
            abs_s = benchmark["summary"].get(c, {}).get(fmt, {})
            arch_mean = arch_s.get("mean_pass_rate", 0) if arch_s else 0
            abs_mean = abs_s.get("mean_pass_rate", 0) if abs_s else 0
            arch_cls = "pass-100" if arch_mean >= 1.0 else "pass-90" if arch_mean >= 0.9 else "pass-80" if arch_mean >= 0.8 else "pass-low"
            abs_cls = "pass-100" if abs_mean >= 1.0 else "pass-90" if abs_mean >= 0.9 else "pass-80" if abs_mean >= 0.8 else "pass-low"
            p(f'<td class="{arch_cls}">{arch_mean:.0%}</td>')
            p(f'<td class="{abs_cls}">{abs_mean:.0%}</td>')
        p('</tr>')
    p('</tbody></table>')

    # Delta table
    p('<h3>Performance Delta (Abstract minus Architecture)</h3>')
    p('<p class="section-note">Negative values (red) show where semantic priors were helping.</p>')
    p('<table><thead><tr><th>Complexity</th>')
    for fmt in formats:
        p(f'<th>{esc(fmt)}</th>')
    p('</tr></thead><tbody>')
    for c in complexities:
        p('<tr>')
        p(f'<td><strong>{esc(c)}</strong></td>')
        for fmt in formats:
            arch_s = arch_benchmark["summary"].get(c, {}).get(fmt, {})
            abs_s = benchmark["summary"].get(c, {}).get(fmt, {})
            arch_mean = arch_s.get("mean_pass_rate", 0) if arch_s else 0
            abs_mean = abs_s.get("mean_pass_rate", 0) if abs_s else 0
            delta = abs_mean - arch_mean
            if abs(delta) < 0.005:
                cls = "delta-zero"
                txt = "0"
            elif delta > 0:
                cls = "delta-positive"
                txt = f"+{delta:.0%}"
            else:
                cls = "delta-negative"
                txt = f"{delta:.0%}"
            p(f'<td class="{cls}">{txt}</td>')
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
        p(f'<h3>{esc(c).upper()} &mdash; {esc(gm["name"])} ({gm["nodes"]}n/{gm["edges"]}e)</h3>')
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

        p(f'<div class="tab-bar">')
        for fi, fmt in enumerate(formats):
            active = "active" if fi == 0 else ""
            p(f'<button class="tab-btn {active}" onclick="switchTab(\'{graph_id}\', \'{fmt}\')">{esc(fmt)}</button>')
        p('</div>')

        for fi, fmt in enumerate(formats):
            active = "active" if fi == 0 else ""
            rendering = renderings[c][fmt]
            p(f'<div class="tab-panel {active}" id="{graph_id}-{fmt}">')
            p(f'<pre class="rendering">{esc(rendering)}</pre>')
            p('</div>')

        p('<h3 style="margin-top:1rem">Questions asked</h3>')
        p('<ol style="padding-left:1.5rem; font-size:0.85rem">')
        for q in gm["questions"]:
            p(f'<li style="margin-bottom:0.3rem">{esc(q["text"])}<br><code>Ground truth: {esc(q["answer"])}</code></li>')
        p('</ol>')

        p('</div></div>')

    # --- Findings ---
    p('<h2>Findings</h2>')
    p("""<ol class="findings">
<li><strong>Donald's hypothesis is strongly confirmed.</strong>
Removing semantic node labels causes significant performance degradation across most formats.
The LLM was relying on domain knowledge ("load balancers connect to gateways") to supplement
its parsing of the graph representation.</li>

<li><strong>Mermaid remains the most robust format.</strong>
100% from small complexity onward, even with abstract labels. Its formal directed-edge syntax
(<code>A --&gt; B</code>) is unambiguous regardless of whether nodes carry meaning.
The only failures are at tiny complexity on Q4 (sources) and Q5 (sinks) &mdash; a reasoning issue
not a parsing issue.</li>

<li><strong>ASCII art collapses completely without semantics.</strong>
From 61% (architecture, medium) to 17% (abstract, medium), reaching 0% at XL. Without semantic
cues about what should connect to what, the model cannot reliably trace arrows through a 2D
character grid.</li>

<li><strong>Verbal and JSON/YAML degrade on negative-universal questions.</strong>
Q4 (sources) and Q5 (sinks) are disproportionately affected. With architecture labels, the model
could reason "Clients and Browsers are obviously entry points." With abstract labels, it must
verify that a node <em>never</em> appears as an edge target &mdash; a harder scan over an unordered list.</li>

<li><strong>The Q4 (sources) failure at tiny is striking.</strong>
A 3-node graph <code>A&rarr;B&rarr;C</code> produces 0/3 on "which nodes have no incoming edges?"
for verbal, ASCII, JSON, and YAML. The model fails to identify A as the sole source of a trivial
graph. Only mermaid is <em>also</em> susceptible at tiny (0/3). This suggests the question framing
itself is hard for the model &mdash; "no incoming edges" requires checking a universal negative.</li>

<li><strong>Surprisingly, some conditions <em>improve</em> without semantics.</strong>
Verbal at XL goes from 89% to 100%. The plain edge list <code>A &rarr; B</code> may actually be
<em>easier</em> to scan than prose like "Auth Service reads user credentials from PostgreSQL" where
the semantic content is distracting from the structural task.</li>

<li><strong>The complexity threshold shifts downward.</strong>
With architecture labels, degradation began at medium (10 nodes). With abstract labels, it begins
at tiny (3 nodes) for some questions. The semantic scaffolding was masking fundamental limitations
in the model's graph reasoning.</li>
</ol>""")

    # --- Practical implications ---
    p('<h2>Practical Implications</h2>')
    p("""<ul>
<li><strong>For LLM consumption of arbitrary graphs:</strong> mermaid is the clear winner. It's the
only format that maintains near-perfect accuracy without semantic assistance.</li>
<li><strong>JSON/YAML edge lists</strong> remain strong for forward/backward neighbor and reachability
queries, but struggle with global properties (sources, sinks) when nodes are abstract.</li>
<li><strong>ASCII art should be avoided</strong> for communicating graph structure to LLMs, especially
when the graph represents something the model cannot semantically reason about.</li>
<li><strong>When using verbal descriptions,</strong> the plain edge-list format (<code>A &rarr; B</code>)
may outperform prose with semantic edge labels at high complexity &mdash; less distraction, more scannable.</li>
<li><strong>Be cautious when an LLM appears to understand your architecture diagram.</strong>
Some of that "understanding" may be pattern-matching on component names rather than genuine
structural comprehension.</li>
</ul>""")

    p("""<footer>
Generated from <a href="https://github.com/dandavison/etc/tree/master/generic-graph-eval">generic-graph-eval</a> experiment.
Follow-up to the <a href="../graph-eval/">architecture graph eval</a>.
Subject model: Claude Sonnet 4.6. March 2026.
</footer>""")

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
    benchmark = sys.argv[1] if len(sys.argv) > 1 else "results/benchmark_20260325_170640.json"
    arch_benchmark = sys.argv[2] if len(sys.argv) > 2 else "/Users/dan/src/todo/graph-eval/results/benchmark_20260325_072205.json"
    output = sys.argv[3] if len(sys.argv) > 3 else "/Users/dan/src/etc/generic-graph-eval/index.html"
    generate_report(benchmark, arch_benchmark, output)
