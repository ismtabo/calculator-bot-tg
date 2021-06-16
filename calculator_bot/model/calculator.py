"""Model of definition model."""

from dataclasses import dataclass


@dataclass
class Calculator:
    """Calculator represents a calculator with value and temporal expression."""
    id_: str
    value: float
    expr: str

    def set_value(self, value: float) -> 'Calculator':
        """Creates clone instance with given value"""
        return Calculator(self.id_, value, self.expr)

    def set_expr(self, expr: str) -> 'Calculator':
        """Creates clone instance with given expression"""
        return Calculator(self.id_, self.value, expr)
