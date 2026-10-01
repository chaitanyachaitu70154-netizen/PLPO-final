"""
Data validation utilities for knowledge states, scores, and dependency graphs.
"""

from typing import Dict, List, Set

def validate_score(score: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamp and validate score within given bounds."""
    if not isinstance(score, (int, float)):
        raise TypeError(f"Score must be numeric, got {type(score)}")
    return max(min_val, min(max_val, float(score)))

def normalize_to_percent(score: float) -> float:
    """Normalize score whether provided as 0-1 ratio or 0-100 percentage."""
    if 0.0 <= score <= 1.0:
        return round(score * 100.0, 1)
    return round(score, 1)

def normalize_to_ratio(score: float) -> float:
    """Normalize score whether provided as 0-1 ratio or 0-100 percentage to 0.0-1.0."""
    if score > 1.0:
        return round(score / 100.0, 4)
    return round(score, 4)

def check_acyclic_graph(adjacency_list: Dict[str, List[str]]) -> bool:
    """
    Verify that a directed graph of prerequisites has no cycles using DFS.
    Returns True if acyclic (valid DAG), False if a cycle is detected.
    """
    visited: Set[str] = set()
    recursion_stack: Set[str] = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        recursion_stack.add(node)
        for neighbor in adjacency_list.get(node, []):
            if neighbor not in visited:
                if not dfs(neighbor):
                    return False
            elif neighbor in recursion_stack:
                return False
        recursion_stack.remove(node)
        return True

    for node in adjacency_list:
        if node not in visited:
            if not dfs(node):
                return False
    return True
