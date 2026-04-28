from lean4py.logic import Prop, ProofStep


class Tactic:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"tactic.{self.name}"


def tactic_rfl() -> Tactic:
    return Tactic("rfl")


def tactic_exact(p: Prop) -> Tactic:
    return Tactic(f"exact {p.name}")


def tactic_apply(h: str) -> Tactic:
    return Tactic(f"apply {h}")


def tactic_simp() -> Tactic:
    return Tactic("simp")


def tactic_assume(name: str) -> Tactic:
    return Tactic(f"assume {name}")


def tactic_have(name: str) -> Tactic:
    return Tactic(f"have {name}")


class TacticProof:
    def __init__(self, steps: list = None):
        self.steps = steps or []

    def add(self, step: Tactic):
        self.steps.append(step)

    def __repr__(self):
        return "\n".join(f"  {s}" for s in self.steps)