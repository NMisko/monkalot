"""Module for parsing and doing math."""

from __future__ import division
import pyparsing as pyp
import math
import operator


class NumericStringParser(object):
    """
    Most of this code comes from the fourFn.py pyparsing example.

    http://pyparsing.wikispaces.com/file/view/fourFn.py
    http://pyparsing.wikispaces.com/message/view/home/15549426
    __author__='Paul McGuire'

    All I've done is rewrap Paul McGuire's fourFn.py as a class, so I can use it
    more easily in other places.
    """

    def __init__(self):
        """
        Initialize parser.

        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        point = pyp.Literal(".")
        e = pyp.CaselessLiteral("E")
        fnumber = pyp.Combine(
            pyp.Word("+-" + pyp.nums, pyp.nums)
            + pyp.Optional(point + pyp.Optional(pyp.Word(pyp.nums)))
            + pyp.Optional(e + pyp.Word("+-" + pyp.nums, pyp.nums))
        )
        ident = pyp.Word(pyp.alphas, pyp.alphas + pyp.nums + "_$")
        plus = pyp.Literal("+")
        minus = pyp.Literal("-")
        mult = pyp.Literal("*")
        div = pyp.Literal("/")
        lpar = pyp.Literal("(").suppress()
        rpar = pyp.Literal(")").suppress()
        addop = plus | minus
        multop = mult | div
        expop = pyp.Literal("^")
        pi = pyp.CaselessLiteral("PI")
        expr = pyp.Forward()
        atom = (
            (
                pyp.Optional(pyp.oneOf("- +"))
                + (pi | e | fnumber | ident + lpar + expr + rpar).setParseAction(
                    self.push_first
                )
            )
            | pyp.Optional(pyp.oneOf("- +")) + pyp.Group(lpar + expr + rpar)
        ).setParseAction(self.push_u_minus)
        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = pyp.Forward()
        factor << atom + pyp.ZeroOrMore((expop + factor).setParseAction(self.push_first))
        term = factor + pyp.ZeroOrMore((multop + factor).setParseAction(self.push_first))
        expr << term + pyp.ZeroOrMore((addop + term).setParseAction(self.push_first))
        self.bnf = expr
        # map operator symbols to corresponding arithmetic operations
        epsilon = 1e-12
        self.opn = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "^": operator.pow,
        }
        self.fn = {
            "abs": abs,
            "trunc": lambda a: int(a),
            "round": round,
            "sgn": lambda a: abs(a) > epsilon and a > 0 or 0,
        }

        for n in dir(math):
            f = getattr(math, n)
            if callable(f):
                self.fn[n] = f

        self.exprStack = []

    def push_first(self, strg, loc, toks):
        """Push first token."""
        self.exprStack.append(toks[0])

    def push_u_minus(self, strg, loc, toks):
        """Push a unary minus."""
        if toks and toks[0] == "-":
            self.exprStack.append("unary -")

    def evaluate_stack(self, s):
        """Evaluate content of stack."""
        op = s.pop()
        if op == "unary -":
            return -self.evaluate_stack(s)
        if op in "+-*/^":
            op2 = self.evaluate_stack(s)
            op1 = self.evaluate_stack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            return self.fn[op](self.evaluate_stack(s))
        elif op[0].isalpha():
            return 0
        else:
            return float(op)

    def eval(self, num_string, parseAll=True):
        """Evaluate value of string."""
        self.exprStack = []
        self.bnf.parseString(num_string, parseAll)
        val = self.evaluate_stack(self.exprStack[:])
        return val
