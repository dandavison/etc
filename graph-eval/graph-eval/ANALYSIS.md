# Graph Representation Eval: How Well Do Different Formats Communicate Topology to LLMs?

## Experiment Design

**Question**: Which textual representation of a box-and-arrow software architecture diagram
most faithfully communicates graph topology to an LLM?

**Formats tested**: verbal prose, ASCII art, JSON, YAML, mermaid

**Subject model**: Claude Sonnet 4.6 (temperature=1.0)

**Grading**: Claude Sonnet 4.6 (temperature=0) comparing against algorithmically-computed
ground truth

**Complexity levels**: 5 graphs ranging from 3 nodes/2 edges to 22 nodes/34 edges

**Questions per graph**: 6 topology questions (forward neighbors, backward neighbors,
reachability, sources, sinks, total degree)

**Runs**: 3 per (graph, format) condition = 75 subject calls total

## Results

### Pass Rates (mean ± stddev)

```
Complexity        verbal       ascii        json        yaml     mermaid
------------------------------------------------------------------------
tiny (3n/2e)     100%±0%     100%±0%     100%±0%     100%±0%     100%±0%
small (6n/7e)    100%±0%     100%±0%     100%±0%     100%±0%     100%±0%
medium (10n/14e)  94%±8%      61%±8%      94%±8%      94%±8%     100%±0%
large (16n/24e)  100%±0%      83%±0%     100%±0%     100%±0%     100%±0%
xl (22n/34e)      89%±8%      94%±8%     100%±0%     100%±0%     100%±0%
```

### Per-Question Breakdown (correct/total, 3 runs each)

The medium graph is where formats begin to differentiate. Results for medium:

```
Question            verbal  ascii  json  yaml  mermaid
Q1:fwd_neighbors      3/3    3/3   3/3   3/3     3/3
Q2:bkwd_neighbors     3/3    0/3   3/3   3/3     3/3
Q3:reachability        3/3    3/3   3/3   3/3     3/3
Q4:sources             3/3    2/3   3/3   3/3     3/3
Q5:sinks               2/3    0/3   2/3   2/3     3/3
Q6:degree              3/3    3/3   3/3   3/3     3/3
```

## Findings

### 1. Mermaid is the only format achieving 100% across all complexities

Zero failures in 90 graded answers across all complexity levels. This makes sense:
mermaid is a formal grammar designed specifically for graph description, with
unambiguous syntax for nodes and directed edges.

### 2. JSON and YAML are excellent and statistically indistinguishable

Both achieve 100% everywhere except for Q5 (sinks) at medium complexity, where
each has a single failure across 3 runs. The failure mode is identical: the model
fails to identify one of the two sink nodes (Postgres or Redis Cache). This is a
*reasoning* issue (requiring negative universal quantification: "this node appears
as `from` in no edge"), not a format comprehension issue.

### 3. Verbal prose is surprisingly robust

Verbal achieves 94-100% at all complexity levels, failing only on the same Q5
(sinks) question at medium and Q4 (sources) at xl. The xl source failure is
notable: the model missed "Task Queue" in 2/3 runs, likely because it appears
only once in a long paragraph and is easy to overlook during a global scan.

### 4. ASCII art degrades from medium complexity onward

ASCII is the clear outlier, with three distinct failure modes:

**Arrow direction confusion (Q2, medium, 0/3)**: The model consistently reads
Redis Cache as connecting to Postgres. In the ASCII art, complex arrow routing
through a vertically-arranged diagram causes the model to misattribute edge
directions. This is a genuine comprehension failure — the arrows are correctly
drawn but the spatial reasoning required to trace them through a dense layout
exceeds the model's reliable capability.

**Global scan failures (Q5 sinks, 0/3 at medium and large)**: The model cannot
reliably determine which nodes have no outgoing connections by scanning a 2D
ASCII layout. It either misses sinks or incorrectly identifies non-sinks.

**Source identification (Q4, medium, 2/3)**: Occasional failure to identify all
root nodes in the diagram.

### 5. The complexity threshold is ~10 nodes / 14 edges

Below this (tiny: 3/2, small: 6/7), all formats achieve perfect scores. At medium
(10/14), ASCII drops to 61% while other formats remain at 94-100%. Above medium,
JSON/YAML/mermaid return to 100% while ASCII stays degraded.

### 6. Q5 (sinks) is the hardest question across all formats

Identifying sink nodes requires universal negative reasoning: verifying that a
node never appears as a source in any edge. This is the only question type where
verbal, JSON, and YAML occasionally fail. Mermaid's formal syntax makes this
enumeration reliable, which is why it achieves 100%.

## Interpretation

The results suggest a clear hierarchy for communicating graph topology to LLMs:

1. **Mermaid** — best choice when available. Formal, unambiguous, designed for purpose.
2. **JSON / YAML** — excellent alternatives. The explicit node/edge structure is
   nearly as parseable as mermaid, with only marginal degradation on global-scan
   questions.
3. **Verbal prose** — surprisingly effective. Natural language descriptions of
   edges are well-understood by LLMs. Slightly weaker on questions requiring
   exhaustive enumeration of all nodes with a given property.
4. **ASCII art** — significantly worse at medium+ complexity. Spatial reasoning
   over 2D text layouts is unreliable for LLMs. Arrow direction confusion and
   global scan failures make this format unsuitable as the primary topology
   description for complex architectures.

### Practical recommendations

- For LLM consumption, prefer mermaid or JSON/YAML edge lists over ASCII diagrams
- ASCII art may still be useful as a *supplement* alongside a structured format
- For simple graphs (≤6 nodes), any format works — don't over-engineer the representation
- If using verbal descriptions for larger graphs, structure them carefully with one edge
  per sentence and explicit directionality

## Methodology Notes

- The ASCII art was hand-crafted to be as readable as possible (not programmatically
  generated). This gives ASCII its best chance; real-world ASCII diagrams would likely
  perform worse.
- Initial run revealed a missing edge in the XL ASCII diagram (Shipping → Event Bus),
  demonstrating that ASCII art has a scalability problem even for the *author*: it's
  hard to verify completeness of hand-drawn diagrams.
- Grading was refined between runs to accept any valid path for reachability questions,
  not just the specific BFS-shortest path.
