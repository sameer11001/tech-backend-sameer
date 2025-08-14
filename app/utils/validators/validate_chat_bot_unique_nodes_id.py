from typing import List


def check_unique_ids(nodes: List) -> List:
    ids = [n.id for n in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate FlowNode.id detected")
    return nodes