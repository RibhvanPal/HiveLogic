import networkx as nx
from typing import List, Dict, Optional
from graph.store import save_graph, load_graph, add_relationships
from graph.builder import build_dynamic_graph, KNOWN_SUPPLY_CHAINS

_graph: Optional[nx.DiGraph] = None

def _build_base_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    for source, target, rel_type, weight in KNOWN_SUPPLY_CHAINS:
        G.add_edge(source, target, relation=rel_type, weight=weight)
    return G

def get_graph() -> nx.DiGraph:
    global _graph
    if _graph is not None:
        return _graph
    loaded = load_graph()
    if loaded and loaded.number_of_edges() > 0:
        _graph = loaded
        return _graph
    _graph = _build_base_graph()
    save_graph(_graph)
    return _graph

def enrich_graph_for_ticker(ticker: str, news_text: str = "") -> nx.DiGraph:
    global _graph
    G = get_graph()
    new_relationships = build_dynamic_graph(ticker, news_text)
    if new_relationships:
        G = add_relationships(G, new_relationships)
        _graph = G
        save_graph(G)
    return G

def find_contagion_risks(ticker: str, depth: int = 1) -> List[Dict]:
    G = get_graph()
    ticker_upper = ticker.split(".")[0].upper()
    if ticker_upper not in G:
        return []
    risks = []
    visited = {ticker_upper}
    frontier = [(ticker_upper, [], 0)]
    while frontier:
        node, path, current_depth = frontier.pop(0)
        if current_depth >= depth:
            continue
        for neighbor in G.successors(node):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            edge_data = G.edges[node, neighbor]
            new_path = path + [f"{node} --[{edge_data['relation']}]--> {neighbor}"]
            path_str = " → ".join(
                [ticker_upper] + [p.split("-->")[-1].strip() for p in new_path]
            )
            if edge_data["relation"] not in [
                "commodity_risk",
                "currency_risk",
                "regulatory_risk",
                "supply_chain_risk",
                "geopolitical_risk",
                "revenue_dependency",
                "macro_risk",
                "cost_risk",
            ]:
                continue
            risks.append({
                "entity": neighbor,
                "relation": edge_data["relation"],
                "risk_weight": edge_data["weight"],
                "path": path_str,
                "depth": current_depth + 1,
            })
            frontier.append((neighbor, new_path, current_depth + 1))
    risks.sort(key=lambda x: x["risk_weight"], reverse=True)
    return risks

def summarize_contagion(ticker: str, news_text: str = "") -> List[Dict]:
    enrich_graph_for_ticker(ticker, news_text)
    risks = find_contagion_risks(ticker)
    if not risks:
        return []
    for risk in risks:
        weight = risk["risk_weight"]
        if weight >= 0.75:
            severity = "HIGH"
        elif weight >= 0.40:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        risk["severity"] = severity
        risk["description"] = (
            f"{risk['entity']} affects {ticker.split('.')[0]} "
            f"through {risk['relation'].replace('_', ' ')} exposure "
            f"(confidence: {weight:.0%})"
        )
    return risks[:10]

def get_subgraph(
    ticker: str,
    depth: int = 1,
) -> Dict:

    enrich_graph_for_ticker(ticker)

    G = get_graph()

    ticker_upper = ticker.split(".")[0].upper()

    if ticker_upper not in G:
        return {
            "nodes": [],
            "edges": [],
        }

    nodes = {
        ticker_upper,
    }

    edges = []

    frontier = [
        (ticker_upper, 0),
    ]

    visited = {
        ticker_upper,
    }

    while frontier:

        node, current_depth = frontier.pop(0)

        if current_depth >= depth:
            continue

        for neighbor in G.successors(node):

            edge_data = G.edges[node, neighbor]

            nodes.add(neighbor)

            edges.append(
                {
                    "source": node,
                    "target": neighbor,
                    "relation": edge_data.get(
                        "relation",
                        "",
                    ),
                    "weight": edge_data.get(
                        "weight",
                        0,
                    ),
                }
            )

            if neighbor not in visited:

                visited.add(neighbor)

                frontier.append(
                    (
                        neighbor,
                        current_depth + 1,
                    )
                )

    node_list = []

    for node in nodes:

        node_list.append(
            {
                "id": node,
                "label": node,
                "type":
                    "company"
                    if node == ticker_upper
                    else "related",
            }
        )

    return {
        "nodes": node_list,
        "edges": edges,
    }

def get_graph_stats() -> Dict:
    G = get_graph()
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "companies": [
            n for n in G.nodes()
            if not any(w in n for w in ["_", "Market", "Risk", "Spending", "Prices", "Costs", "Regulations"])
        ],
    }

def invalidate_graph_cache():
    global _graph
    _graph = None