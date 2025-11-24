import pulp
import time
from dd.autoref import BDD

from bdd_reachability import run_bdd_reachability, is_reachable_marking

def detect_deadlock_ilp_bdd(places, transitions, initial_marking_list):
    """
    Detect deadlock using ILP + BDD.

    Args:
        places (list[str])
        transitions (list[dict]): each with 'name', 'inputs', 'outputs'
        initial_marking_list (list[str]): places with initial tokens

    Returns:
        dict: {'deadlock': [0/1 list] or None, 'time': float, 'iterations': int}
    """

    # 1. Compute reachable BDD from Task 3
    bdd_result = run_bdd_reachability(places, transitions, initial_marking_list)
    bdd = bdd_result['bdd']
    R = bdd_result['R']
    var_current = bdd_result['var_current']

    # 2. Prepare pre for transitions (inputs)
    pre = {t['name']: t['inputs'] for t in transitions}

    # 3. Setup ILP for dead markings
    prob = pulp.LpProblem("Deadlock_Detection", pulp.LpMinimize)
    x = {p: pulp.LpVariable(p, cat="Binary") for p in places}

    # Constraints
    for t_name, inputs in pre.items():
        if inputs:  # Skip if no inputs
            prob += pulp.lpSum(x[p] for p in inputs) <= len(inputs) - 1, f"disable_{t_name}"

    prob += 0 # Dummy

    # 4. Iterative solving with cuts
    start_time = time.time()
    iterations = 0
    max_iterations = 1000  # Safety limit

    while iterations < max_iterations:
        iterations += 1
        status = prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=10))

        if status != pulp.LpStatusOptimal:
            # No more solutions -> no deadlock
            end_time = time.time()
            return {'deadlock': None, 'time': end_time - start_time, 'iterations': iterations}

        # Get candidate marking
        marking_dict = {p: int(x[p].value()) for p in places}

        # Check if reachable using BDD
        if is_reachable_marking(bdd, R, var_current, marking_dict):
            end_time = time.time()
            # Convert to list (ordered by places)
            marking_list = [marking_dict[p] for p in places]
            return {'deadlock': marking_list, 'time': end_time - start_time, 'iterations': iterations}

        # Exclude non-reachable marking
        cut_terms = []
        for p in places:
            if marking_dict[p] == 1:
                cut_terms.append(1 - x[p])
            else:
                cut_terms.append(x[p])
        prob += pulp.lpSum(cut_terms) >= 1, f"cut_{iterations}"
        
    end_time = time.time()
    return {'deadlock': None, 'time': end_time - start_time, 'iterations': iterations}

if __name__ == "__main__":
    # Example
    places = ['p1', 'p2', 'p3', 'p4']
    transitions = [
        {'name': 't1', 'inputs': ['p1'], 'outputs': ['p2']},
        {'name': 't2', 'inputs': ['p2'], 'outputs': ['p3']},
        {'name': 't3', 'inputs': ['p3', 'p4'], 'outputs': []} # deadlock if p4 is empty
    ]
    initial_marking_list = ['p1', 'p4']

    result = detect_deadlock_ilp_bdd(places, transitions, initial_marking_list)
    if result['deadlock']:
        print(f"Deadlock found: {result['deadlock']}")
    else:
        print("No deadlock.")
    print(f"Time: {result['time']:.4f}s, Iterations: {result['iterations']}")