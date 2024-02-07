# mypy: disable-error-code="empty-body"
from __future__ import annotations

import inspect

from egglog import *
from egglog.exp.program_gen import *


class Math(Expr):
    def __init__(self, value: i64Like) -> None:
        ...

    @classmethod
    def var(cls, v: StringLike) -> Math:
        ...

    def __add__(self, other: Math) -> Math:
        ...

    def __mul__(self, other: Math) -> Math:
        ...

    def __neg__(self) -> Math:
        ...

    @method(cost=1000)  # type: ignore[misc]
    @property
    def program(self) -> Program:
        ...


@function
def assume_pos(x: Math) -> Math:
    ...


@ruleset
def to_program_ruleset(
    s: String,
    y_expr: String,
    z_expr: String,
    old_statements: String,
    x: Math,
    i: i64,
    y: Math,
    z: Math,
    old_gensym: i64,
):
    yield rewrite(Math.var(s).program).to(Program(s))
    yield rewrite(Math(i).program).to(Program(i.to_string()))
    yield rewrite((y + z).program).to((y.program + " + " + z.program).assign())
    yield rewrite((y * z).program).to((y.program + " * " + z.program).assign())
    yield rewrite((-y).program).to(Program("-") + y.program)
    assigned_x = x.program.assign()
    yield rewrite(assume_pos(x).program).to(assigned_x.statement(Program("assert ") + assigned_x + " > 0"))


def test_to_string(snapshot_py) -> None:
    first = assume_pos(-Math.var("x")) + Math.var("y")
    fn = (first + Math(2) + first).program.function_two(Math.var("x").program, Math.var("y").program, "my_fn")
    egraph = EGraph()
    egraph.register(fn)
    egraph.register(fn.compile())
    egraph.run(to_program_ruleset * 100 + program_gen_ruleset * 200)
    # egraph.display(n_inline_leaves=1)
    assert egraph.eval(fn.expr) == "my_fn"
    assert egraph.eval(fn.statements) == snapshot_py


def test_py_object():
    x = Math.var("x")
    y = Math.var("y")
    z = Math.var("z")
    fn = (x + y + z).program.function_two(x.program, y.program)
    egraph = EGraph()
    egraph.register(fn.eval_py_object({"z": 10}))
    egraph.run(to_program_ruleset * 100 + program_gen_ruleset * 100)
    res = egraph.eval(fn.py_object)
    assert res(1, 2) == 13  # type: ignore[operator]
    assert inspect.getsource(res)  # type: ignore[arg-type]
