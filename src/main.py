from PNML_Read import parse_pnml, bfs_reachable_markings
from bdd_encoding import build_bdd_structures
from bdd_reachability import compute_reachable_bdd, count_reachable_states
from ilp_bdd_deadlock import detect_deadlock_ilp_bdd
from optimization import optimize


def run_all(filename):
    places_dict, transitions, arcs, initial_marking_list = parse_pnml(filename)
    places = sorted(places_dict.keys())

    print("=== Explicit reachability (BFS) ===")
    reachable, place_order = bfs_reachable_markings(places_dict, transitions)
    print("Number of reachable markings (explicit):", len(reachable))

    print("\n=== BDD reachability ===")
    bdd, var_current, var_next, B_init, T = build_bdd_structures(
        places, transitions, initial_marking_list
    )
    R = compute_reachable_bdd(bdd, var_current, var_next, B_init, T, places)
    num_bdd = count_reachable_states(bdd, R, len(places))
    print("Number of reachable markings (BDD):", num_bdd)

    print("\n=== Deadlock detection (ILP + BDD) ===")
    dl_result = detect_deadlock_ilp_bdd(places, transitions, initial_marking_list)
    print("Deadlock marking (if any):", dl_result["deadlock"])
    print("Deadlock search time:", dl_result["time"], "s")
    print("ILP iterations:", dl_result["iterations"])

    print("\n=== Optimization over reachable markings (Karp–Miller) ===")
    opt_result = optimize(places, transitions, initial_marking_list)
    if isinstance(opt_result, str):
        print(opt_result)
    else:
        best_marking, best_value = opt_result
        print("Best value:", best_value)
        print("Best marking:")
        for i, p in enumerate(places):
            val = best_marking[i]
            val_str = "ω" if val == float("inf") else str(val)
            print(f"  {p}: {val_str}")


if __name__ == "__main__":
    filenames = [
        "PetriNetSample.pnml",
        "PetriNetSample_Deadlock.pnml",
        "PetriNetSample_Deadlock2.pnml",
    ]

    for fn in filenames:
        run_all(fn)
