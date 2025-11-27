import xml.etree.ElementTree as ET
from collections import deque

PNML_NS = "{http://www.pnml.org/version-2009/grammar/pnml}"


def parse_pnml(filename):
    """
    Parse a 1-safe Petri net in PNML format.

    Returns:
        places_dict: dict[place_id] = initial_tokens (int)
        transitions: list[{"name": str, "inputs": [place_id], "outputs": [place_id]}]
        arcs: list[(source_id, target_id)]
        initial_marking_list: list[place_id] with initial token > 0
    """
    tree = ET.parse(filename)
    root = tree.getroot()

    places_dict = {}         # place_id -> initial tokens
    transition_ids = set()   # set of transition ids
    arcs = []                # (source, target)

    for p in root.findall(".//" + PNML_NS + "place"):
        pid = p.attrib["id"]
        marking_node = p.find(
            ".//" + PNML_NS + "initialMarking/" + PNML_NS + "text"
        )
        marking = int(marking_node.text) if marking_node is not None else 0
        places_dict[pid] = marking

    for t in root.findall(".//" + PNML_NS + "transition"):
        tid = t.attrib["id"]
        transition_ids.add(tid)

    for a in root.findall(".//" + PNML_NS + "arc"):
        src = a.attrib["source"]
        tgt = a.attrib["target"]
        arcs.append((src, tgt))

    node_ids = set(places_dict.keys()) | transition_ids
    for src, tgt in arcs:
        if src not in node_ids or tgt not in node_ids:
            raise ValueError(
                f"Inconsistent PNML: arc {src} -> {tgt} references unknown node."
            )

    pre = {tid: [] for tid in transition_ids}
    post = {tid: [] for tid in transition_ids}

    for src, tgt in arcs:
        if src in places_dict and tgt in transition_ids:
            pre[tgt].append(src)
        elif src in transition_ids and tgt in places_dict:
            post[src].append(tgt)

    transitions = []
    for tid in sorted(transition_ids):
        transitions.append(
            {
                "name": tid,
                "inputs": pre[tid],
                "outputs": post[tid],
            }
        )

    initial_marking_list = [p for p, m in places_dict.items() if m > 0]

    return places_dict, transitions, arcs, initial_marking_list


def bfs_reachable_markings(places_dict, transitions):
    """
    Explicit BFS reachability for 1-safe Petri net.

    places_dict: dict[place_id] -> initial_tokens (>=0)
                 (treated as 0/1 in 1-safe assumption)
    transitions: list of dicts with 'inputs', 'outputs'

    Returns:
        reachable: set of tuple marks (ordered by place_order)
        place_order: list of place_ids (sorted)
    """
    place_order = sorted(places_dict.keys())
    place_index = {p: i for i, p in enumerate(place_order)}

    initial_marking = tuple(
        1 if places_dict[p] > 0 else 0 for p in place_order
    )

    def is_enabled(marking, trans):
        for p in trans["inputs"]:
            if marking[place_index[p]] == 0:
                return False
        return True

    def fire(marking, trans):
        m = list(marking)
        for p in trans["inputs"]:
            i = place_index[p]
            m[i] = 0  
        for p in trans["outputs"]:
            i = place_index[p]
            m[i] = 1    
        return tuple(m)

    visited = set([initial_marking])
    reachable = set([initial_marking])
    q = deque([initial_marking])

    while q:
        current = q.popleft()
        for t in transitions:
            if not is_enabled(current, t):
                continue
            new_m = fire(current, t)
            if new_m not in visited:
                visited.add(new_m)
                reachable.add(new_m)
                q.append(new_m)

    return reachable, place_order


if __name__ == "__main__":
    filename = "PetriNetSample.pnml"

    places_dict, transitions, arcs, initial_marking_list = parse_pnml(filename)

    print("Places (initial tokens):")
    for p, m in places_dict.items():
        print(f"  {p}: {m}")

    print("\nTransitions:")
    for t in transitions:
        print(f"  {t['name']}: inputs={t['inputs']}, outputs={t['outputs']}")

    print("\nArcs:")
    for s, t in arcs:
        print(f"  {s} -> {t}")

    reachable, order = bfs_reachable_markings(places_dict, transitions)
    print("\nReachable markings (explicit BFS):")
    for m in sorted(reachable):
        print(dict(zip(order, m)))
