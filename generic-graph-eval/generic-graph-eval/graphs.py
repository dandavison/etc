"""Abstract graph definitions and representation renderers.

Same topologies as the system-architecture eval, but with meaningless
node labels (A, B, C, …) to test pure topological comprehension
without semantic priors.
"""

from __future__ import annotations

import json
import textwrap
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Edge:
    src: str
    dst: str
    label: str


@dataclass
class Graph:
    name: str
    description: str
    nodes: list[str]
    edges: list[Edge]
    q_forward_node: str
    q_backward_node: str
    q_reach_src: str
    q_reach_dst: str
    q_degree_node: str

    _fwd: dict[str, set[str]] = field(default_factory=dict, repr=False)
    _bwd: dict[str, set[str]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._fwd = {n: set() for n in self.nodes}
        self._bwd = {n: set() for n in self.nodes}
        for e in self.edges:
            self._fwd[e.src].add(e.dst)
            self._bwd[e.dst].add(e.src)

    def forward_neighbors(self, node: str) -> set[str]:
        return self._fwd[node]

    def backward_neighbors(self, node: str) -> set[str]:
        return self._bwd[node]

    def is_reachable(self, src: str, dst: str) -> bool:
        visited: set[str] = set()
        q: deque[str] = deque([src])
        while q:
            cur = q.popleft()
            if cur == dst:
                return True
            if cur in visited:
                continue
            visited.add(cur)
            q.extend(self._fwd[cur])
        return False

    def find_path(self, src: str, dst: str) -> list[str] | None:
        visited: set[str] = set()
        q: deque[list[str]] = deque([[src]])
        while q:
            path = q.popleft()
            cur = path[-1]
            if cur == dst:
                return path
            if cur in visited:
                continue
            visited.add(cur)
            for nxt in sorted(self._fwd[cur]):
                q.append(path + [nxt])
        return None

    def sources(self) -> set[str]:
        return {n for n in self.nodes if not self._bwd[n]}

    def sinks(self) -> set[str]:
        return {n for n in self.nodes if not self._fwd[n]}

    def total_degree(self, node: str) -> int:
        return len(self._fwd[node]) + len(self._bwd[node])

    def ground_truth(self) -> dict[str, object]:
        path = self.find_path(self.q_reach_src, self.q_reach_dst)
        return {
            "q1_forward": sorted(self.forward_neighbors(self.q_forward_node)),
            "q2_backward": sorted(self.backward_neighbors(self.q_backward_node)),
            "q3_reachable": self.is_reachable(self.q_reach_src, self.q_reach_dst),
            "q3_path": path,
            "q4_sources": sorted(self.sources()),
            "q5_sinks": sorted(self.sinks()),
            "q6_degree": self.total_degree(self.q_degree_node),
        }

    def edge_list_str(self) -> str:
        return "; ".join(f"{e.src} -> {e.dst}" for e in self.edges)

    def questions(self) -> list[dict[str, str]]:
        gt = self.ground_truth()
        edges_str = self.edge_list_str()
        return [
            {
                "id": "q1_forward",
                "text": f"What nodes does {self.q_forward_node} have directed edges to? List all of them.",
                "answer": ", ".join(gt["q1_forward"]),  # type: ignore[arg-type]
            },
            {
                "id": "q2_backward",
                "text": f"What nodes have directed edges to {self.q_backward_node}? List all of them.",
                "answer": ", ".join(gt["q2_backward"]),  # type: ignore[arg-type]
            },
            {
                "id": "q3_reachable",
                "text": f"Is there a directed path from {self.q_reach_src} to {self.q_reach_dst}? Answer yes or no, and if yes, list the nodes on the path in order.",
                "answer": "yes, path: " + " -> ".join(gt["q3_path"]) if gt["q3_reachable"] else "no",  # type: ignore[union-attr]
                "edges": edges_str,
            },
            {
                "id": "q4_sources",
                "text": "Which nodes have no incoming edges (nothing points to them)? List all.",
                "answer": ", ".join(gt["q4_sources"]),  # type: ignore[arg-type]
            },
            {
                "id": "q5_sinks",
                "text": "Which nodes have no outgoing edges (they don't point to anything)? List all.",
                "answer": ", ".join(gt["q5_sinks"]),  # type: ignore[arg-type]
            },
            {
                "id": "q6_degree",
                "text": f"How many total direct connections does {self.q_degree_node} have, counting both incoming and outgoing edges?",
                "answer": str(gt["q6_degree"]),
            },
        ]


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def render_verbal(g: Graph) -> str:
    lines = [f"This is a directed graph with {len(g.nodes)} nodes: {', '.join(g.nodes)}."]
    lines.append("")
    lines.append("The directed edges are:")
    for e in g.edges:
        lines.append(f"  {e.src} -> {e.dst}")
    return "\n".join(lines)


def render_json(g: Graph) -> str:
    obj = {
        "nodes": g.nodes,
        "edges": [{"from": e.src, "to": e.dst} for e in g.edges],
    }
    return json.dumps(obj, indent=2)


def render_yaml(g: Graph) -> str:
    lines = ["nodes:"]
    for n in g.nodes:
        lines.append(f"  - {n}")
    lines.append("edges:")
    for e in g.edges:
        lines.append(f"  - from: {e.src}")
        lines.append(f"    to: {e.dst}")
    return "\n".join(lines)


def render_mermaid(g: Graph) -> str:
    lines = ["graph LR"]
    for e in g.edges:
        lines.append(f"    {e.src} --> {e.dst}")
    return "\n".join(lines)


_ASCII_ART: dict[str, str] = {
    "G1": """\
+---+     +---+     +---+
| A |---->| B |---->| C |
+---+     +---+     +---+""",

    "G2": """\
                    +---+     +---+
               +--->| C |---->| E |
               |    +---+     +---+
+---+    +---+ |      ^
| A |--->| B |-+      | F->C
+---+    +---+ |      |
               |    +---+     +---+
               +--->| D |---->| F |
                    +---+     +---+""",

    "G3": """\
+---+     +---+     +---+
| A |---->| B |---->| C |
+---+     +---+     +---+
  |         |         |
  v         v         v
+---+     +---+     +---+
| D |     | E |     | F |
+---+     +---+     +---+
  |         |  \\      |
  v         v   \\     v
+---+     +---+  \\  +---+     +---+
| G |     | H |   +>| I |---->| J |
+---+     +---+     +---+     +---+""",

    "G4": """\
+---+   +---+
| A |   | B |
+-+-+   +-+-+
  |       |
  v       v
  +---+---+
  |   C   |
  +---+---+
      |
      v
  +---+---+
  |   D   |
  +-+--+-++
    |  | |
    v  v  +------+------+------+
  +--+ |         |      |      |
  | E| v     +---+  +---+  +---+
  +--++---+  | H |  | I |  | J |
   |  | F |  +-+-+  +-+-+  +-+-+
   |  +---+    |      |      |
   |    |      |      |      |
   v    v      v      v      |
 +---+ +---+ +---+          |
 | K | | L | | M |          |
 +---+ +---+ +---+          |
                |            |
                v            v
              +---+       +---+
              | N |       | O |
              +---+       +---+
                |
                v
              +---+
              | P |
              +---+""",

    "G5": """\
+---+       +---+
| A |       | B |
+-+-+       +-+-+
  |   +---+   |
  +-->| C |<--+
  |   +-+-+   |
  |     |     |
  |     v     |
  |   +---+   |
  +-->| D |<--+
      +-+-+
        |
        v
      +---+
      | E |
      +-+-+-+-+--+-+
        |   | |  | |
        v   | v  | v
      +---+ | +--++ +---+
      | F | | | H | | K |
      +---+ | +---+ +---+
        |   v   |
        v +---+ v
      +---+| I |+---+
      | G |+---+| L |
      +---+  |  +---+
             v
+---+      +---+       +---+
| Q |----->| J |       | M |
+---+      +---+       +---+
                          |
           +---+          v
           | R |        +---+       +---+
           +---+        | N |       | P |
             |          +---+       +---+
             v            |
           +---+          v
           | S |        +---+
           +---+        | O |
             |          +---+
             v
           +---+
           | T |
           +---+
             |
             v
           +---+        +---+
           | U |        | V |
           +---+        +---+

E -> K, E -> H, E -> F
H -> I, H -> L
I -> J
R -> S -> T -> U
M -> N -> O
Q -> J
V has no connections (isolated sink)
""",
}


def render_ascii(g: Graph) -> str:
    return _ASCII_ART[g.name]


RENDERERS: dict[str, callable] = {  # type: ignore[type-arg]
    "verbal": render_verbal,
    "ascii": render_ascii,
    "json": render_json,
    "yaml": render_yaml,
    "mermaid": render_mermaid,
}


# ---------------------------------------------------------------------------
# Graph definitions — same topologies as architecture eval, abstract labels
# ---------------------------------------------------------------------------

# Mapping: original architecture experiment node -> letter
# G1 (tiny): Client->A, API Server->B, Database->C
# G2 (small): Client->A, Gateway->B, Auth Service->C, Order Service->D,
#              User DB->E, Order DB->F
# G3 (medium): Browser->A, CDN->B, API Gateway->C, Auth Service->D,
#              Product Service->E, Order Service->F, Message Queue->G,
#              Notification Service->H, Redis Cache->I, Postgres->J
# G4 (large): Mobile App->A, Web App->B, Load Balancer->C, API Gateway->D,
#             Auth Service->E, User Service->F, Order Service->G,
#             Payment Service->H, Search Service->I, Analytics Service->J,
#             Event Bus->K, Notification Service->L, Stripe API->M,
#             Elasticsearch->N, PostgreSQL->O, Redis->P
# G5 (xl): Mobile App->A, Web App->B, CDN->C, Load Balancer->D,
#          API Gateway->E, Auth Service->F, User Service->G,
#          Order Service->H, Inventory Service->I, Payment Service->J,
#          Shipping Service->K, Notification Service->L,
#          Search Service->M, Analytics Service->N,
#          Recommendation Service->O, Event Bus->P,
#          Task Queue->Q, PostgreSQL->R, MongoDB->S, Redis->T,
#          Elasticsearch->U, Stripe API->V

GRAPHS: list[Graph] = [
    # --- Tiny: 3 nodes, 2 edges (same as Simple Pipeline) ---
    Graph(
        name="G1",
        description="A directed graph with 3 nodes and 2 edges.",
        nodes=["A", "B", "C"],
        edges=[
            Edge("A", "B", ""),
            Edge("B", "C", ""),
        ],
        q_forward_node="A",
        q_backward_node="C",
        q_reach_src="A",
        q_reach_dst="C",
        q_degree_node="B",
    ),
    # --- Small: 6 nodes, 7 edges (same as Basic Microservices) ---
    Graph(
        name="G2",
        description="A directed graph with 6 nodes and 7 edges.",
        nodes=["A", "B", "C", "D", "E", "F"],
        edges=[
            Edge("A", "B", ""),
            Edge("B", "C", ""),
            Edge("B", "D", ""),
            Edge("C", "E", ""),
            Edge("D", "F", ""),
            Edge("D", "C", ""),
            Edge("D", "B", ""),
        ],
        q_forward_node="B",
        q_backward_node="C",
        q_reach_src="A",
        q_reach_dst="F",
        q_degree_node="D",
    ),
    # --- Medium: 10 nodes, 14 edges (same as E-commerce Backend) ---
    Graph(
        name="G3",
        description="A directed graph with 10 nodes and 14 edges.",
        nodes=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
        edges=[
            Edge("A", "B", ""),
            Edge("A", "C", ""),
            Edge("C", "D", ""),
            Edge("C", "E", ""),
            Edge("C", "F", ""),
            Edge("D", "J", ""),
            Edge("E", "J", ""),
            Edge("E", "I", ""),
            Edge("F", "J", ""),
            Edge("F", "G", ""),
            Edge("F", "I", ""),
            Edge("G", "H", ""),
            Edge("H", "J", ""),
            Edge("B", "C", ""),
        ],
        q_forward_node="F",
        q_backward_node="J",
        q_reach_src="A",
        q_reach_dst="H",
        q_degree_node="C",
    ),
    # --- Large: 16 nodes, 24 edges (same as Platform Architecture) ---
    Graph(
        name="G4",
        description="A directed graph with 16 nodes and 24 edges.",
        nodes=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
               "K", "L", "M", "N", "O", "P"],
        edges=[
            Edge("A", "C", ""),
            Edge("B", "C", ""),
            Edge("C", "D", ""),
            Edge("D", "E", ""),
            Edge("D", "F", ""),
            Edge("D", "G", ""),
            Edge("D", "I", ""),
            Edge("E", "P", ""),
            Edge("E", "O", ""),
            Edge("F", "O", ""),
            Edge("G", "O", ""),
            Edge("G", "H", ""),
            Edge("G", "K", ""),
            Edge("H", "M", ""),
            Edge("H", "K", ""),
            Edge("K", "L", ""),
            Edge("K", "J", ""),
            Edge("L", "O", ""),
            Edge("J", "O", ""),
            Edge("I", "N", ""),
            Edge("I", "P", ""),
            Edge("F", "K", ""),
            Edge("F", "P", ""),
            Edge("G", "P", ""),
        ],
        q_forward_node="G",
        q_backward_node="K",
        q_reach_src="A",
        q_reach_dst="M",
        q_degree_node="D",
    ),
    # --- XL: 22 nodes, 34 edges (same as Distributed Platform) ---
    Graph(
        name="G5",
        description="A directed graph with 22 nodes and 34 edges.",
        nodes=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
               "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V"],
        edges=[
            Edge("A", "C", ""),
            Edge("B", "C", ""),
            Edge("A", "D", ""),
            Edge("B", "D", ""),
            Edge("C", "D", ""),
            Edge("D", "E", ""),
            Edge("E", "F", ""),
            Edge("E", "G", ""),
            Edge("E", "H", ""),
            Edge("E", "M", ""),
            Edge("E", "O", ""),
            Edge("F", "T", ""),
            Edge("F", "R", ""),
            Edge("G", "R", ""),
            Edge("G", "T", ""),
            Edge("G", "P", ""),
            Edge("H", "R", ""),
            Edge("H", "I", ""),
            Edge("H", "J", ""),
            Edge("H", "P", ""),
            Edge("I", "S", ""),
            Edge("I", "T", ""),
            Edge("J", "V", ""),
            Edge("J", "P", ""),
            Edge("K", "S", ""),
            Edge("K", "P", ""),
            Edge("P", "L", ""),
            Edge("P", "N", ""),
            Edge("P", "K", ""),
            Edge("Q", "O", ""),
            Edge("L", "R", ""),
            Edge("N", "R", ""),
            Edge("M", "U", ""),
            Edge("O", "S", ""),
        ],
        q_forward_node="E",
        q_backward_node="R",
        q_reach_src="B",
        q_reach_dst="V",
        q_degree_node="P",
    ),
]


COMPLEXITY_LABELS = ["tiny", "small", "medium", "large", "xl"]


def build_prompt(representation: str, questions: list[dict[str, str]]) -> str:
    q_text = "\n".join(f"Q{i+1}: {q['text']}" for i, q in enumerate(questions))
    return textwrap.dedent(f"""\
        You are examining a directed graph. The graph is described below.

        {representation}

        Based solely on the graph description above, answer each of the following questions.
        Be precise and concise. For list questions, list every matching node and no others.

        {q_text}
    """)
