"""lean - Formal mathematics and theorem proving inspired by Lean for math4py."""

from .logic import (
    Prop, Prop_var, implies, and_, or_, not_, iff,
    Theorem, ProofStep, assume, have, exact, apply, rfl, simp, prove,
)

from .sets import (
    Set, Set_from, in_, subset,
    union, intersection, complement, difference,
    cartesian, power_set, empty_set,
)

from .algebra import (
    Magma, Semigroup, Monoid, Group, AbelianGroup, Ring, Field,
)

from .nat import (
    Nat, nat, zero, succ, pred, is_zero,
    nat_add, nat_mul, nat_sub, nat_le, nat_lt, nat_eq,
)

from .tactics import (
    Tactic, tactic_rfl, tactic_exact, tactic_apply, tactic_simp,
    tactic_assume, tactic_have, TacticProof,
)

__all__ = [
    # logic
    "Prop", "Prop_var", "implies", "and_", "or_", "not_", "iff",
    "Theorem", "ProofStep", "assume", "have", "exact", "apply", "rfl", "simp", "prove",
    # sets
    "Set", "Set_from", "in_", "subset",
    "union", "intersection", "complement", "difference",
    "cartesian", "power_set", "empty_set",
    # algebra
    "Magma", "Semigroup", "Monoid", "Group", "AbelianGroup", "Ring", "Field",
    # nat
    "Nat", "nat", "zero", "succ", "pred", "is_zero",
    "nat_add", "nat_mul", "nat_sub", "nat_le", "nat_lt", "nat_eq",
    # tactics
    "Tactic", "tactic_rfl", "tactic_exact", "tactic_apply", "tactic_simp",
    "tactic_assume", "tactic_have", "TacticProof",
]