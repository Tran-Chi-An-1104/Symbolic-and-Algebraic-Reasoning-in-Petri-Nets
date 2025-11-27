from dd.autoref import BDD


def build_bdd_structures(places, transitions, initial_marking_list):
    """
    Build BDD structures for a 1-safe Petri net.

    Args:
        places: list[str]
        transitions: list[dict] with keys:
             'name', 'inputs', 'outputs'
        initial_marking_list: list[str]  (places with initial token)

    Returns:
        (bdd, var_current, var_next, B_init, T_global)
    """

    bdd = BDD()

    var_current = {}
    var_next = {}
    ordered_vars = []

    for p in places:
        curr = p
        nxt = f"{p}_prime"
        var_current[p] = curr
        var_next[p] = nxt
        ordered_vars.append(curr)
        ordered_vars.append(nxt)

    bdd.declare(*ordered_vars)

    expr_parts = []
    for p in places:
        if p in initial_marking_list:
            expr_parts.append(f"{var_current[p]}")
        else:
            expr_parts.append(f"~{var_current[p]}")
    init_expr = " & ".join(expr_parts)
    B_init = bdd.add_expr(init_expr)

    T_global = bdd.false

    for t in transitions:
        inputs = t["inputs"]
        outputs = t["outputs"]

        pre = [f"{var_current[p]}" for p in inputs]

        post_loss = [f"~{var_next[p]}" for p in inputs]

        post_gain = [f"{var_next[p]}" for p in outputs]

        affected = set(inputs).union(outputs)
        frame = []
        for p in places:
            if p not in affected:
                frame.append(
                    f"(({var_current[p]} & {var_next[p]}) | "
                    f"(~{var_current[p]} & ~{var_next[p]}))"
                )

        parts = pre + post_loss + post_gain + frame
        if not parts:
            continue

        t_expr = " & ".join(parts)
        T_t = bdd.add_expr(t_expr)
        T_global = T_global | T_t

    return bdd, var_current, var_next, B_init, T_global
