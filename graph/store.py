import os
import json
from pathlib import Path
from typing import Optional
import networkx as nx
from networkx.readwrite import json_graph

GRAPH_STORE_PATH = os.getenv("GRAPH_STORE_PATH", "data/graph_store.json")

def save_graph(G: nx.DiGraph) -> bool:
    #Persist graph to JSON file
    try:
        Path(GRAPH_STORE_PATH).parent.mkdir(parents=True, exist_ok=True)
        data = json_graph.node_link_data(G)
        with open(GRAPH_STORE_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Graph Store] Saved {G.number_of_nodes()} nodes, {G.number_of_edges()} edges → {GRAPH_STORE_PATH}")
        return True
    except Exception as e:
        print(f"[Graph Store] Save failed: {e}")
        return False

def load_graph() -> Optional[nx.DiGraph]:
    # Load graph from JSON file
    try:
        if not Path(GRAPH_STORE_PATH).exists():
            return None
        with open(GRAPH_STORE_PATH) as f:
            data = json.load(f)
        G = json_graph.node_link_graph(data, directed=True)
        print(f"[Graph Store] Loaded {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    except Exception as e:
        print(f"[Graph Store] Load failed: {e}")
        return None

def add_relationships(G: nx.DiGraph, relationships: list) -> nx.DiGraph:
    #Add new relationships to graph without duplicating. relationships: list of (source, target, relation_type, weight)
    added = 0
    for source, target, rel_type, weight in relationships:
        if not G.has_edge(source, target):
            G.add_edge(source, target, relation=rel_type, weight=weight)
            added += 1
        else:
            # Update weight if new one is higher confidence
            existing = G.edges[source, target]["weight"]
            if weight > existing:
                G.edges[source, target]["weight"] = weight
    if added:
        print(f"[Graph Store] Added {added} new relationships")
    return G