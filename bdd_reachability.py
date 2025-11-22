from dd.autoref import BDD
import time

try:
    from bdd_encoding import build_bdd_structures
except ImportError:
    def build_bdd_structures(*args, **kwargs):
        raise NotImplementedError("build_bdd_structures not found.")


def compute_reachable_bdd(bdd, var_current, var_next, B_init, T, places):
    """
    Symbolic reachability fixpoint:

        R = B_init
        New = B_init
        while New != False:
            IMG(x') = ∃x (New(x) ∧ T(x,x'))
            IMG_renamed(x) = IMG(x')[x' := x]
            New = IMG_renamed ∧ ¬R
            R = R ∪ New
    """

    # Variable names for existential quantification
    current_vars = [var_current[p] for p in places]

    # Rename mapping: x'_p  ->  x_p
    rename_dict = {
        var_next[p]: bdd.var(var_current[p]) for p in places
    }

    R = B_init
    New = B_init

    print("=== BDD Reachability Fixpoint Running... ===")

    iteration = 0
    while New != bdd.false:
        iteration += 1

        # ∃ current_vars (New ∧ T)
        IMG = bdd.exist(current_vars, New & T)

        # Replace x' with x
        IMG_renamed = bdd.let(rename_dict, IMG)

        # New states
        New = IMG_renamed & ~R

        # Accumulate
        R = R | New

        print(f"Iteration {iteration}: New states added? {New != bdd.false}")

    print("Fixpoint reached.")
    return R


def count_reachable_states(bdd, R, num_places):
    """Return the number of reachable markings (if supported)."""
    try:
        return int(R.count(nvars=num_places))
    except Exception:
        return None


def is_reachable_marking(bdd, R, var_current, marking):
    """Check if a Boolean marking is included in reachable set R."""
    B_M = bdd.true
    for p, val in marking.items():
        var = bdd.var(var_current[p])
        B_M &= var if val == 1 else ~var
    return (B_M & R) != bdd.false


def run_bdd_reachability(places, transitions, initial_marking_list):
    """Build BDD structures, compute reachable set, and count states."""

    bdd, var_current, var_next, B_init, T = build_bdd_structures(
        places, transitions, initial_marking_list
    )

    R = compute_reachable_bdd(bdd, var_current, var_next, B_init, T, places)
    num_states = count_reachable_states(bdd, R, len(places))

    return {
        "bdd": bdd,
        "var_current": var_current,
        "var_next": var_next,
        "B_init": B_init,
        "T": T,
        "R": R,
        "num_reachable": num_states,
    }


def benchmark_reachability(places, transitions, initial_marking_list, explicit_func):
    """Compare explicit BFS vs. symbolic BDD reachability."""

    # Explicit
    print("\nRunning explicit BFS...")
    t0 = time.time()
    explicit_states = explicit_func(places, transitions, initial_marking_list)
    t1 = time.time()

    # BDD
    print("\nRunning BDD reachability...")
    t2 = time.time()
    bdd_result = run_bdd_reachability(places, transitions, initial_marking_list)
    t3 = time.time()

    return {
        "explicit_states": len(explicit_states),
        "explicit_time": t1 - t0,
        "bdd_states": bdd_result["num_reachable"],
        "bdd_time": t3 - t2,
    }


if __name__ == "__main__":
    print("BDD Reachability module loaded.")
