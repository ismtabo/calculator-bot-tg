"""Module of definitions repository through HTTP requests."""
from abc import ABC, abstractmethod
from typing import Dict

from option import Result
from option.result import Err, Ok

from calculator_bot.model import Calculator


class CalculatorRepository(ABC):
    """Repository class for definitions."""

    @abstractmethod
    def create_calculator(self, id_: str) -> Result[Calculator, str]:
        """Create a new calculator."""

    @abstractmethod
    def get_calculator(self, id_: str) -> Result[Calculator, str]:
        """Find calculator by id."""

    @abstractmethod
    def update_calculator(self, id_: str, calc: Calculator) -> Result[Calculator, str]:
        """Update calculator by id."""


class MemoryCalculatorRepository(CalculatorRepository):
    """Repository class for definitions through HTTP requests to RAE's DLE pages."""

    def __init__(self) -> None:
        super().__init__()
        self.__calculators: Dict[str, Calculator] = dict()

    def create_calculator(self, id_: str) -> Result[Calculator, str]:
        """Create a new calculator."""
        if id_ == '':
            return Err('bad_request')
        if id_ in self.__calculators:
            return Err('conflict')
        calc = Calculator(id_, 0, '')
        self.__calculators[id_] = calc
        return Ok(calc)

    def get_calculator(self, id_: str) -> Result[Calculator, str]:
        """Search DLE RAE definitions for a given query."""
        if not id_ in self.__calculators:
            return Err('not_found')
        return Ok(self.__calculators[id_])

    def update_calculator(self, id_: str, calc: Calculator) -> Result[Calculator, str]:
        """Update calculator by id."""
        if not id_ in self.__calculators:
            return Err('not_found')
        self.__calculators[id_] = calc
        return Ok(calc)
