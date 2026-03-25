"""Graph definitions and representation renderers for the eval."""

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
    # Per-graph question parameters (node names chosen for interesting topology)
    q_forward_node: str  # Q1: list forward neighbors
    q_backward_node: str  # Q2: list backward neighbors
    q_reach_src: str  # Q3: reachability from
    q_reach_dst: str  # Q3: reachability to
    q_degree_node: str  # Q6: total degree

    # Precomputed adjacency
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
        """Compute ground truth answers for all 6 question types."""
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
                "text": f"What components does {self.q_forward_node} directly send data or requests to? List all of them.",
                "answer": ", ".join(gt["q1_forward"]),  # type: ignore[arg-type]
            },
            {
                "id": "q2_backward",
                "text": f"What components directly send data or requests to {self.q_backward_node}? List all of them.",
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
                "text": "Which components have no incoming connections (nothing sends data to them)? List all.",
                "answer": ", ".join(gt["q4_sources"]),  # type: ignore[arg-type]
            },
            {
                "id": "q5_sinks",
                "text": "Which components have no outgoing connections (they don't send data to anything)? List all.",
                "answer": ", ".join(gt["q5_sinks"]),  # type: ignore[arg-type]
            },
            {
                "id": "q6_degree",
                "text": f"How many total direct connections does {self.q_degree_node} have, counting both incoming and outgoing?",
                "answer": str(gt["q6_degree"]),
            },
        ]


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def render_verbal(g: Graph) -> str:
    lines = [f"This system is called {g.name}. {g.description}"]
    lines.append("")
    lines.append(f"The system consists of the following components: {', '.join(g.nodes)}.")
    lines.append("")
    # Group edges by source for readable prose
    by_src: dict[str, list[Edge]] = {}
    for e in g.edges:
        by_src.setdefault(e.src, []).append(e)
    for src in g.nodes:
        if src not in by_src:
            continue
        targets = by_src[src]
        if len(targets) == 1:
            e = targets[0]
            lines.append(f"{src} {e.label} to {e.dst}.")
        else:
            parts = [f"{e.dst} ({e.label})" for e in targets]
            lines.append(f"{src} connects to: {', '.join(parts)}.")
    return "\n".join(lines)


def render_json(g: Graph) -> str:
    obj = {
        "nodes": g.nodes,
        "edges": [{"from": e.src, "to": e.dst, "label": e.label} for e in g.edges],
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
        lines.append(f"    label: {e.label}")
    return "\n".join(lines)


def render_mermaid(g: Graph) -> str:
    def _id(name: str) -> str:
        return name.replace(" ", "_")

    lines = ["graph LR"]
    for e in g.edges:
        sid, did = _id(e.src), _id(e.dst)
        src_label = f'{sid}["{e.src}"]' if " " in e.src else sid
        dst_label = f'{did}["{e.dst}"]' if " " in e.dst else did
        lines.append(f"    {src_label} -->|{e.label}| {dst_label}")
    return "\n".join(lines)


_ASCII_ART: dict[str, str] = {
    "Simple Pipeline": """\
+--------+   HTTP    +------------+  queries  +----------+
| Client |---------->| API Server |---------->| Database |
+--------+           +------------+           +----------+""",

    "Basic Microservices": """\
                          authenticates   +--------------+  reads/writes  +----------+
                      +------------------>| Auth Service |--------------->| User DB  |
                      |                   +--------------+               +----------+
+--------+  requests  +---------+              ^
| Client |----------->| Gateway |              | validates tokens
+--------+            +---------+              |
                      |   ^         routes     |
                      |   | callbacks  +---------------+  reads/writes  +----------+
                      +---|----------->| Order Service |--------------->| Order DB |
                          +------------+---------------+               +----------+""",

    "E-commerce Backend": """\
               fetches assets    +-----+  cache miss  +-------------+
           +------------------->| CDN |-------------->| API Gateway |
           |                    +-----+               +------+------+
+---------+                                 |         |      |
| Browser |          API requests           |         |      |
+---------+------------------------------->-+         |      |
                                                      |      |
                          authenticates               |      |
                     +--------------------------------+      |
                     |          routes products               |
                     |     +----------------------------------+-------+
                     |     |          routes orders                    |
                     |     |     +------------------------------------+
                     v     v     v
              +---------+ +---------+ +---------+
              |  Auth   | | Product | |  Order  |
              | Service | | Service | | Service |
              +---------+ +---------+ +---------+
                  |         |    |      |  |   |
                  |  reads  |    |      |  |   | publishes
    reads creds   | catalog |   |caches|  |   | events
                  |         |   |      |  |   |
                  v         v   |      |  |   v
              +----------+  |   |      |  | +-------+  delivers  +--------+
              | Postgres |<-+   |      +--+>| Msg Q |----------->| Notify |
              +----------+<-----+------+    +-------+            | Service|
                  ^         |          |                         +--------+
                  |         v          v                            |
                  |    +-----------+                                |
                  +----|Redis Cache|           logs notification    |
                       +-----------+           status              |
                                      +----------------------------+""",

    "Platform Architecture": """\
+------------+     +----------+
| Mobile App |--+  |  Web App |--+
+------------+  |  +----------+  |
                |                |
                v                v
             +---------------+
             | Load Balancer |
             +-------+-------+
                     |
                     v
             +-------+-------+
             |  API Gateway  |
             +--+--+--+--+--+
                |  |  |  |
    +-----------+  |  |  +-------------+
    |              |  |                |
    v              v  v                v
+------+  +------+ +-------+  +--------+
| Auth |  | User | | Order |  | Search |
| Svc  |  | Svc  | |  Svc  |  |  Svc   |
+--+---+  +--+---+ +--+----+  +---+----+
   |  |      |  |     |  |  |      |  |
   |  |      |  |     |  |  |      |  |
   |  v      |  v     |  |  v      |  v
   | +-----+ | +----+ |  | +-----+ | +-----+
   | |Redis| | |Evnt| |  | |Paymt| | |Elstc|
   | |     | | |Bus | |  | | Svc | | |Srch |
   | +--+--+ | +-+--+ |  | +--+--+ | +-----+
   |    |    |   |     |  |    |    |
   v    |    v   |     v  |    v    |
+----------+ |  +------+  | +------+
| Postgres | |  | Redis |  | |Stripe|
+----------+ |  +------+  | | API  |
             |             | +------+
             v             v
      +---------+   +-----------+
      |Analytics|   |Notify Svc |
      |  Svc    |   +-----------+
      +---------+         |
             |            |
             v            v
          +----------+
          | Postgres |
          +----------+

Event Bus receives from: Order Svc, Payment Svc, User Svc
Event Bus delivers to: Notification Svc, Analytics Svc
All services writing to Postgres: Auth, User, Order, Notification, Analytics
Redis used by: Auth (sessions), Search (cache), User (profiles), Order (status)""",

    "Distributed Platform": """\
+------------+    +----------+
| Mobile App |    |  Web App |
+-----+------+    +----+-----+
      |   |             |   |
      |   | fetches     |   | fetches
      |   | assets      |   | assets
      |   v             |   v
      |  +-----+        |
      |  | CDN |<-------+
      |  +--+--+        |
      |     | forwards   |
      |     | dynamic    |
      v     v            v
   +--------------------+
   |   Load Balancer    |
   +---------+----------+
             |
             v
   +---------+----------+
   |    API Gateway      |
   +--+--+--+--+--+----+
      |  |  |  |  |
      |  |  |  |  +---> Recommendation Svc ---> MongoDB
      |  |  |  |
      |  |  |  +------> Search Svc -----------> Elasticsearch
      |  |  |
      |  |  +----------> Order Svc --+---> PostgreSQL
      |  |                 |  |      |
      |  |                 |  |      +--> Event Bus --+--> Notification Svc --> PostgreSQL
      |  |                 |  |      |     ^          +--> Analytics Svc -----> PostgreSQL
      |  |                 |  |      |     |          +--> Shipping Svc ------> MongoDB
      |  |                 |  |      |     |                  |
      |  |                 |  |      |     +------------------+ (publishes shipping events)
      |  |                 |  +----> Inventory Svc -----> MongoDB
      |  |                 |            |
      |  |                 |            +--> Redis (stock cache)
      |  |                 |
      |  |                 +--> Payment Svc ---> Stripe API
      |  |                        |
      |  |                        +--> Event Bus
      |  |
      |  +---> User Svc --+--> PostgreSQL
      |                    +--> Redis (profiles)
      |                    +--> Event Bus
      |
      +------> Auth Svc --+--> Redis (sessions)
                           +--> PostgreSQL

Task Queue ---> Recommendation Svc""",
}


def render_ascii(g: Graph) -> str:
    """Return hand-crafted ASCII art for known graphs."""
    return _ASCII_ART[g.name]


RENDERERS: dict[str, callable] = {  # type: ignore[type-arg]
    "verbal": render_verbal,
    "ascii": render_ascii,
    "json": render_json,
    "yaml": render_yaml,
    "mermaid": render_mermaid,
}


# ---------------------------------------------------------------------------
# Graph definitions — increasing complexity
# ---------------------------------------------------------------------------


GRAPHS: list[Graph] = [
    # --- Tiny: 3 nodes, 2 edges ---
    Graph(
        name="Simple Pipeline",
        description="A minimal request pipeline.",
        nodes=["Client", "API Server", "Database"],
        edges=[
            Edge("Client", "API Server", "sends HTTP requests"),
            Edge("API Server", "Database", "queries"),
        ],
        q_forward_node="Client",
        q_backward_node="Database",
        q_reach_src="Client",
        q_reach_dst="Database",
        q_degree_node="API Server",
    ),
    # --- Small: 6 nodes, 7 edges ---
    Graph(
        name="Basic Microservices",
        description="A small microservices backend with authentication.",
        nodes=["Client", "Gateway", "Auth Service", "Order Service", "User DB", "Order DB"],
        edges=[
            Edge("Client", "Gateway", "sends requests"),
            Edge("Gateway", "Auth Service", "authenticates"),
            Edge("Gateway", "Order Service", "routes orders"),
            Edge("Auth Service", "User DB", "reads/writes users"),
            Edge("Order Service", "Order DB", "reads/writes orders"),
            Edge("Order Service", "Auth Service", "validates tokens"),
            Edge("Order Service", "Gateway", "sends callbacks"),
        ],
        q_forward_node="Gateway",
        q_backward_node="Auth Service",
        q_reach_src="Client",
        q_reach_dst="Order DB",
        q_degree_node="Order Service",
    ),
    # --- Medium: 10 nodes, 14 edges ---
    Graph(
        name="E-commerce Backend",
        description="An e-commerce platform with caching, async processing, and a CDN.",
        nodes=[
            "Browser", "CDN", "API Gateway", "Auth Service", "Product Service",
            "Order Service", "Message Queue", "Notification Service", "Redis Cache", "Postgres",
        ],
        edges=[
            Edge("Browser", "CDN", "fetches static assets"),
            Edge("Browser", "API Gateway", "sends API requests"),
            Edge("API Gateway", "Auth Service", "authenticates requests"),
            Edge("API Gateway", "Product Service", "routes product queries"),
            Edge("API Gateway", "Order Service", "routes order mutations"),
            Edge("Auth Service", "Postgres", "reads user credentials"),
            Edge("Product Service", "Postgres", "reads product catalog"),
            Edge("Product Service", "Redis Cache", "caches product data"),
            Edge("Order Service", "Postgres", "writes order records"),
            Edge("Order Service", "Message Queue", "publishes order events"),
            Edge("Order Service", "Redis Cache", "checks inventory cache"),
            Edge("Message Queue", "Notification Service", "delivers order events"),
            Edge("Notification Service", "Postgres", "logs notification status"),
            Edge("CDN", "API Gateway", "forwards cache misses"),
        ],
        q_forward_node="Order Service",
        q_backward_node="Postgres",
        q_reach_src="Browser",
        q_reach_dst="Notification Service",
        q_degree_node="API Gateway",
    ),
    # --- Large: 16 nodes, 24 edges ---
    Graph(
        name="Platform Architecture",
        description="A full platform with event-driven processing, search, analytics, and external integrations.",
        nodes=[
            "Mobile App", "Web App", "Load Balancer", "API Gateway", "Auth Service",
            "User Service", "Order Service", "Payment Service", "Search Service",
            "Analytics Service", "Event Bus", "Notification Service",
            "Stripe API", "Elasticsearch", "PostgreSQL", "Redis",
        ],
        edges=[
            Edge("Mobile App", "Load Balancer", "sends requests"),
            Edge("Web App", "Load Balancer", "sends requests"),
            Edge("Load Balancer", "API Gateway", "distributes traffic"),
            Edge("API Gateway", "Auth Service", "authenticates"),
            Edge("API Gateway", "User Service", "routes user ops"),
            Edge("API Gateway", "Order Service", "routes order ops"),
            Edge("API Gateway", "Search Service", "routes search queries"),
            Edge("Auth Service", "Redis", "checks session cache"),
            Edge("Auth Service", "PostgreSQL", "reads credentials"),
            Edge("User Service", "PostgreSQL", "reads/writes user profiles"),
            Edge("Order Service", "PostgreSQL", "reads/writes orders"),
            Edge("Order Service", "Payment Service", "initiates payments"),
            Edge("Order Service", "Event Bus", "publishes order events"),
            Edge("Payment Service", "Stripe API", "processes charges"),
            Edge("Payment Service", "Event Bus", "publishes payment events"),
            Edge("Event Bus", "Notification Service", "delivers events"),
            Edge("Event Bus", "Analytics Service", "delivers events"),
            Edge("Notification Service", "PostgreSQL", "logs notifications"),
            Edge("Analytics Service", "PostgreSQL", "writes analytics data"),
            Edge("Search Service", "Elasticsearch", "queries index"),
            Edge("Search Service", "Redis", "caches results"),
            Edge("User Service", "Event Bus", "publishes user events"),
            Edge("User Service", "Redis", "caches profiles"),
            Edge("Order Service", "Redis", "caches order status"),
        ],
        q_forward_node="Order Service",
        q_backward_node="Event Bus",
        q_reach_src="Mobile App",
        q_reach_dst="Stripe API",
        q_degree_node="API Gateway",
    ),
    # --- XL: 22 nodes, 34 edges ---
    Graph(
        name="Distributed Platform",
        description="A large distributed system with service mesh, observability, multiple data stores, and external integrations.",
        nodes=[
            "Mobile App", "Web App", "CDN", "Load Balancer", "API Gateway",
            "Auth Service", "User Service", "Order Service", "Inventory Service",
            "Payment Service", "Shipping Service", "Notification Service",
            "Search Service", "Analytics Service", "Recommendation Service",
            "Event Bus", "Task Queue",
            "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Stripe API",
        ],
        edges=[
            Edge("Mobile App", "CDN", "fetches assets"),
            Edge("Web App", "CDN", "fetches assets"),
            Edge("Mobile App", "Load Balancer", "sends API requests"),
            Edge("Web App", "Load Balancer", "sends API requests"),
            Edge("CDN", "Load Balancer", "forwards dynamic requests"),
            Edge("Load Balancer", "API Gateway", "distributes traffic"),
            Edge("API Gateway", "Auth Service", "authenticates"),
            Edge("API Gateway", "User Service", "routes user ops"),
            Edge("API Gateway", "Order Service", "routes order ops"),
            Edge("API Gateway", "Search Service", "routes search queries"),
            Edge("API Gateway", "Recommendation Service", "routes recommendations"),
            Edge("Auth Service", "Redis", "checks sessions"),
            Edge("Auth Service", "PostgreSQL", "reads credentials"),
            Edge("User Service", "PostgreSQL", "reads/writes profiles"),
            Edge("User Service", "Redis", "caches profiles"),
            Edge("User Service", "Event Bus", "publishes user events"),
            Edge("Order Service", "PostgreSQL", "reads/writes orders"),
            Edge("Order Service", "Inventory Service", "checks stock"),
            Edge("Order Service", "Payment Service", "initiates payment"),
            Edge("Order Service", "Event Bus", "publishes order events"),
            Edge("Inventory Service", "MongoDB", "reads/writes inventory"),
            Edge("Inventory Service", "Redis", "caches stock levels"),
            Edge("Payment Service", "Stripe API", "processes charges"),
            Edge("Payment Service", "Event Bus", "publishes payment events"),
            Edge("Shipping Service", "MongoDB", "reads/writes shipments"),
            Edge("Shipping Service", "Event Bus", "publishes shipping events"),
            Edge("Event Bus", "Notification Service", "delivers events"),
            Edge("Event Bus", "Analytics Service", "delivers events"),
            Edge("Event Bus", "Shipping Service", "delivers order events"),
            Edge("Task Queue", "Recommendation Service", "triggers recomputation"),
            Edge("Notification Service", "PostgreSQL", "logs notifications"),
            Edge("Analytics Service", "PostgreSQL", "writes analytics"),
            Edge("Search Service", "Elasticsearch", "queries index"),
            Edge("Recommendation Service", "MongoDB", "reads user behavior"),
        ],
        q_forward_node="API Gateway",
        q_backward_node="PostgreSQL",
        q_reach_src="Web App",
        q_reach_dst="Stripe API",
        q_degree_node="Event Bus",
    ),
]


COMPLEXITY_LABELS = ["tiny", "small", "medium", "large", "xl"]


def build_prompt(representation: str, questions: list[dict[str, str]]) -> str:
    """Build the full prompt for a single eval call."""
    q_text = "\n".join(f"Q{i+1}: {q['text']}" for i, q in enumerate(questions))
    return textwrap.dedent(f"""\
        You are examining a software system architecture. The architecture is described below.

        {representation}

        Based solely on the architecture description above, answer each of the following questions.
        Be precise and concise. For list questions, list every matching component and no others.

        {q_text}
    """)
