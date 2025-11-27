from collections import deque
import random

OMEGA = float("inf")  


def fire_transition(marking, trans, place_index):
    """
    Firing for general (not necessarily 1-safe) Petri nets.
    marking: tuple of ints or OMEGA
    """
    new_m = list(marking)

    for p in trans["inputs"]:
        i = place_index[p]
        if new_m[i] == OMEGA:
            continue
        if new_m[i] == 0:
            return None  
        new_m[i] -= 1

    for p in trans["outputs"]:
        i = place_index[p]
        if new_m[i] != OMEGA:
            new_m[i] += 1

    return tuple(new_m)


def km_leq(m1, m2):
    """m1 <= m2 componentwise (ω is the largest)."""
    for a, b in zip(m1, m2):
        if a != OMEGA and b != OMEGA and a > b:
            return False
        if a == OMEGA and b != OMEGA:
            return False
    return True


def km_increase_to_omega(marking, ancestor):
    """
    Increase components that strictly grew (w.r.t ancestor) to ω.
    """
    m = list(marking)
    for i in range(len(marking)):
        if ancestor[i] != OMEGA and marking[i] > ancestor[i]:
            m[i] = OMEGA
    return tuple(m)


def karp_miller_tree(places, transitions, initial_marking_list):
    """
    Construct Karp–Miller coverability tree.

    Returns:
        tree: dict[node_marking] = list[child_marking]
        unbounded: bool (True if any ω appears)
    """
    place_index = {p: i for i, p in enumerate(places)}
    n = len(places)

    M0 = tuple(1 if p in initial_marking_list else 0 for p in places)

    root = M0
    tree = {root: []}
    queue = deque([(root, [root])])  

    unbounded = False

    while queue:
        marking, ancestors = queue.popleft()

        for t in transitions:
            child = fire_transition(marking, t, place_index)
            if child is None:
                continue

            accelerated = False
            for anc in ancestors:
                if km_leq(anc, child) and child != anc:
                    child = km_increase_to_omega(child, anc)
                    accelerated = True
                    break

            if any(x == OMEGA for x in child):
                unbounded = True

            if child not in tree:
                tree[child] = []
                tree[marking].append(child)
                queue.append((child, ancestors + [child]))

    return tree, unbounded


def optimize(places, transitions, initial_marking_list, places_weight=None):
    """
    Maximize c^T M over M in (coverability) tree.

    If any place has weight > 0 and some marking has ω there,
    report "Objective unbounded above".

    Returns:
        - "Objective unbounded above" (str), OR
        - (best_marking, best_value)
    """
    tree, unbounded = karp_miller_tree(places, transitions, initial_marking_list)

    if places_weight is None:
        places_weight = {}
        for p in places:
            places_weight[p] = random.randint(1, 10)
            print(f"Place {p} assigned weight {places_weight[p]}")
    else:
        for p in places:
            if p not in places_weight:
                places_weight[p] = 0

    place_index = {p: i for i, p in enumerate(places)}

    for marking in tree.keys():
        for p in places:
            idx = place_index[p]
            if marking[idx] == OMEGA and places_weight[p] > 0:
                return "Objective unbounded above"

    best_value = -float("inf")
    best_marking = None

    for marking in tree.keys():
        value = 0
        for p in places:
            idx = place_index[p]
            if marking[idx] != OMEGA:
                value += marking[idx] * places_weight[p]

        marking_str = ", ".join(
            f"{places[i]}={'ω' if marking[i] == OMEGA else marking[i]}"
            for i in range(len(places))
        )
        print(f"Marking: ({marking_str}) -> Value: {value}")

        if value > best_value:
            best_value = value
            best_marking = marking

    return best_marking, best_value


if __name__ == "__main__":
    places = ["p0", "p1"]
    transitions = [
        {"name": "t0", "inputs": ["p0"], "outputs": ["p0", "p0"]},
    ]
    initial_marking_list = ["p0"]

    result = optimize(places, transitions, initial_marking_list)
    if isinstance(result, str):
        print("Result:", result)
    else:
        best_marking, best_value = result
        print("\nOptimal marking and value:")
        for i, p in enumerate(places):
            val = best_marking[i]
            val_str = "ω" if val == OMEGA else str(val)
            print(f"{p}: {val_str}")
        print("Optimal value:", best_value)
