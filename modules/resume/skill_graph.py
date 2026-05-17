"""Skill adjacency graph using NetworkX."""

import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


def build_skill_graph(skills: List[str], text: str = "") -> Dict[str, Any]:
    """Build a skill adjacency graph from extracted skills.
    
    Skills that appear near each other in the resume text are considered
    related and get an edge between them.
    
    Args:
        skills: List of extracted skill names.
        text: Full resume text for co-occurrence analysis.
        
    Returns:
        Dictionary representation of the skill graph with nodes and edges.
    """
    try:
        import networkx as nx
    except ImportError:
        logger.warning("NetworkX not available, returning simple skill list")
        return {"nodes": [{"id": s, "label": s} for s in skills], "edges": []}

    G = nx.Graph()

    # Add all skills as nodes
    for skill in skills:
        G.add_node(skill)

    if text:
        # Build co-occurrence graph based on proximity in text
        text_lower = text.lower()
        sentences = text_lower.replace("\n", ". ").split(".")

        for sentence in sentences:
            # Find which skills appear in this sentence
            skills_in_sentence = []
            for skill in skills:
                if skill.lower() in sentence:
                    skills_in_sentence.append(skill)

            # Add edges between co-occurring skills
            for i, s1 in enumerate(skills_in_sentence):
                for s2 in skills_in_sentence[i + 1:]:
                    if G.has_edge(s1, s2):
                        G[s1][s2]["weight"] += 1
                    else:
                        G.add_edge(s1, s2, weight=1)

        # Also use category-based edges
        from app.constants import SKILL_TAXONOMY
        for category, category_skills in SKILL_TAXONOMY.items():
            cat_skills_lower = {s.lower() for s in category_skills}
            matching = [s for s in skills if s.lower() in cat_skills_lower]
            for i, s1 in enumerate(matching):
                for s2 in matching[i + 1:]:
                    if G.has_edge(s1, s2):
                        G[s1][s2]["weight"] += 0.5
                    else:
                        G.add_edge(s1, s2, weight=0.5)

    # Convert to dictionary format
    nodes = []
    for node in G.nodes():
        degree = G.degree(node)
        nodes.append({
            "id": node,
            "label": node,
            "degree": degree,
        })

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "weight": data.get("weight", 1),
        })

    # Find skill clusters / communities
    clusters = []
    try:
        if len(G.nodes()) > 2:
            communities = nx.community.greedy_modularity_communities(G)
            for i, community in enumerate(communities):
                clusters.append({
                    "cluster_id": i,
                    "skills": sorted(list(community)),
                })
    except Exception:
        pass

    # Calculate centrality
    centrality = {}
    try:
        if len(G.nodes()) > 1:
            dc = nx.degree_centrality(G)
            centrality = {k: round(v, 3) for k, v in dc.items()}
    except Exception:
        pass

    return {
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "centrality": centrality,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def get_related_skills(skill_graph: Dict[str, Any], skill: str, top_k: int = 5) -> List[str]:
    """Get the most related skills for a given skill from the graph.
    
    Args:
        skill_graph: The skill graph dictionary.
        skill: The skill to find relations for.
        top_k: Maximum number of related skills to return.
        
    Returns:
        List of related skill names sorted by edge weight.
    """
    related = []
    for edge in skill_graph.get("edges", []):
        source = edge.get("source", "")
        target = edge.get("target", "")
        weight = edge.get("weight", 0)
        if source.lower() == skill.lower():
            related.append((target, weight))
        elif target.lower() == skill.lower():
            related.append((source, weight))

    related.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in related[:top_k]]


def get_skill_clusters(skill_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get skill clusters from the graph.
    
    Args:
        skill_graph: The skill graph dictionary.
        
    Returns:
        List of cluster dictionaries.
    """
    return skill_graph.get("clusters", [])
