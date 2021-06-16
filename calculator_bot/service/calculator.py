"""Module for calculator service."""
import re

from option import Result
from option.result import Err
from py_expression_eval import Parser

from calculator_bot.model.calculator import Calculator
from calculator_bot.repository import CalculatorRepository

VALID_EXPRESSION = re.compile('[0-9./=+-c*]')


class CalculatorService:
    """Service class for definitions. Implements calculator operations."""

    def __init__(self, repo: CalculatorRepository) -> None:
        self.repo = repo

    def get_or_create_calculator(self, id_: str) -> Result[Calculator, str]:
        """Creates a new calculator."""
        result = self.repo.get_calculator(id_)
        if result.is_ok:
            return result
        if result.unwrap_err() != 'not_found':
            return result
        return self.repo.create_calculator(id_)

    def evaluate_calculator_expression(self, calc: Calculator, expr: str)\
            -> Result[Calculator, str]:
        """Evaluates expression in calculator identified by id."""
        if calc is None or \
                VALID_EXPRESSION.fullmatch(expr) is None:
            return Err('bad_request')
        if expr == '=':
            calc = self.__calculate_calculator_value(calc)
        elif expr == 'c':
            calc = calc.set_value(0).set_expr('')
        elif not expr.isnumeric() and len(calc.expr) == 0:
            calc = calc.set_expr(str(calc.value)+expr)
        else:
            calc = calc.set_expr(calc.expr + expr)
        return self.repo.update_calculator(calc.id_, calc)

    def __calculate_calculator_value(self, calc: Calculator) -> Calculator:
        parser = Parser()
        try:
            value = parser.parse(calc.expr).evaluate({})
            return calc.set_value(value).set_expr('')
        except Exception:
            return calc
