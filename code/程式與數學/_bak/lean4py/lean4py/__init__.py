from lean4py.logic import (
    Prop,
    Prop_var,
    implies,
    and_,
    or_,
    not_,
    iff,
    Theorem,
    ProofStep,
    assume,
    have,
    exact,
    apply,
    rfl,
    simp,
    prove,
)

from lean4py.sets import (
    Set,
    Set_from,
    in_,
    subset,
    union,
    intersection,
    complement,
    difference,
    cartesian,
    power_set,
    empty_set,
)

from lean4py.algebra import (
    Magma,
    Semigroup,
    Monoid,
    Group,
    AbelianGroup,
    Ring,
    Field,
)

from lean4py.nat import (
    Nat,
    nat,
    zero,
    succ,
    pred,
    is_zero,
    nat_add,
    nat_mul,
    nat_sub,
    nat_le,
    nat_lt,
    nat_eq,
)

from lean4py.tactics import (
    Tactic,
    tactic_rfl,
    tactic_exact,
    tactic_apply,
    tactic_simp,
    tactic_assume,
    tactic_have,
    TacticProof,
)

__version__ = "0.1.0"
__all__ = [
    "Prop", "Prop_var", "implies", "and_", "or_", "not_", "iff",
    "Theorem", "ProofStep", "assume", "have", "exact", "apply", "rfl", "simp", "prove",
    "Set", "Set_from", "in_", "subset", "union", "intersection", "complement",
    "difference", "cartesian", "power_set", "empty_set",
    "Magma", "Semigroup", "Monoid", "Group", "AbelianGroup", "Ring", "Field",
    "Nat", "nat", "zero", "succ", "pred", "is_zero",
    "nat_add", "nat_mul", "nat_sub", "nat_le", "nat_lt", "nat_eq",
    "Tactic", "tactic_rfl", "tactic_exact", "tactic_apply", "tactic_simp",
    "tactic_assume", "tactic_have", "TacticProof",
]