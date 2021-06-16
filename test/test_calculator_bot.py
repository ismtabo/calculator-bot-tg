from typing import Union
from calculator_bot.repository.calculator import CalculatorRepository
from math import exp
import unittest
from unittest.mock import Mock, MagicMock

from option import Err, Ok
from option.result import Result

from calculator_bot.model import Calculator
from calculator_bot.repository import MemoryCalculatorRepository
from calculator_bot.service import CalculatorService


class TestCalculatorRepository(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.repository = MemoryCalculatorRepository()

    def test_create_calculator(self):
        expected = Calculator('id', 0, '')
        result = self.repository.create_calculator('id')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected, result.unwrap())

    def test_create_calculator_empty_id(self):
        result = self.repository.create_calculator('')
        self.assertFalse(result.is_ok)
        result.expect_err('bad_request')

    def test_create_calculator_conflict(self):
        self.repository.create_calculator('id')
        result = self.repository.create_calculator('id')
        self.assertFalse(result.is_ok)
        result.expect_err('conflict')

    def test_error_get_calculator_when_not_found(self):
        result = self.repository.get_calculator('unknown')
        self.assertFalse(result.is_ok)
        result.expect_err('not_found')

    def test_get_calculator(self):
        expected = self.repository.create_calculator('id').unwrap()
        result = self.repository.get_calculator(expected.id_)
        self.assertTrue(result.is_ok)
        self.assertEqual(expected, result.unwrap())

    def test_error_update_calculator_when_calculator_not_found(self):
        result = self.repository.update_calculator(
            'unknown', Calculator('', 0, '')
        )
        self.assertFalse(result.is_ok)
        result.expect_err('not_found')

    def test_update_calculator(self):
        expected = self.repository.create_calculator('id').unwrap()
        expected.value = float('inf')
        result = self.repository.update_calculator(expected.id_, expected)
        self.assertTrue(result.is_ok)
        self.assertEqual(expected, result.unwrap())


class TestCalculatorService(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.mockedRepo = MagicMock(spec=CalculatorRepository)
        self.service = CalculatorService(self.mockedRepo)

    def test_get_or_create_calculator_when_get_existent(self):
        expected = Calculator('id_', 0, '')
        self.mockedRepo.get_calculator.return_value = Ok(expected)
        result = self.service.get_or_create_calculator('id_')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected, result.unwrap())

    def test_get_or_create_calculator_when_get_unknown_error(self):
        self.mockedRepo.get_calculator.return_value = Err('unknown')
        result = self.service.get_or_create_calculator('id_')
        self.assertFalse(result.is_ok)
        result.expect_err('unknown')

    def test_get_or_create_calculator_when_get_not_found_then_create(self):
        expected = Calculator('id_', 0, '')
        self.mockedRepo.get_calculator.return_value = Err('not_found')
        self.mockedRepo.create_calculator.return_value = Ok(expected)
        result = self.service.get_or_create_calculator('id_')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected, result.unwrap())

    def test_get_or_create_calculator_when_create_error(self):
        expected = Calculator('id_', 0, '')
        self.mockedRepo.get_calculator.return_value = Err('not_found')
        self.mockedRepo.create_calculator.return_value = Err('unknown')
        result = self.service.get_or_create_calculator('id_')
        self.assertFalse(result.is_ok)
        result.expect_err('unknown')

    def test_error_evaluate_calculator_expression_when_bad_expression(self):
        calc = Calculator('', 0, '')
        result = self.service.evaluate_calculator_expression(calc, '')
        self.assertFalse(result.is_ok)
        result.expect_err('bad_request')

    def test_error_evaluate_calculator_expression_when_none_calculator(self):
        result = self.service.evaluate_calculator_expression(None, '')
        self.assertFalse(result.is_ok)
        result.expect_err('bad_request')

    def test_error_evaluate_calculator_expression_when_update_fails(self):
        calc = Calculator('', 0, '')
        self.mockedRepo.update_calculator.return_value = Err('not_found')
        result = self.service.evaluate_calculator_expression(calc, '0')
        self.assertFalse(result.is_ok)
        result.expect_err('not_found')

    def test_evaluate_calculator_expression_when_set_numeric_on_empty_expression(self):
        expected = Calculator('', 0, '')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '1')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('1'), result.unwrap())

    def test_evaluate_calculator_expression_when_set_operator_on_empty_expression(self):
        expected = Calculator('', 0, '')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '+')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('0+'), result.unwrap())

    def test_evaluate_calculator_expression_when_set_operator_after_number(self):
        expected = Calculator('', 0, '1')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '+')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('1+'), result.unwrap())

    def test_evaluate_calculator_expression_when_set_number_after_operator(self):
        expected = Calculator('', 0, '0+')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '1')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('0+1'), result.unwrap())

    def test_evaluate_calculator_expression_when_set_operator_on_empty_expression_and_existent_value(self):
        expected = Calculator('', 10, '')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '1')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('1'), result.unwrap())

    def test_evaluate_calculator_expression_when_equals_expression(self):
        expected = Calculator('', 0, '10*10')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '=')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_value(100).set_expr(''), result.unwrap())

    def test_evaluate_calculator_expression_when_equals_only_number(self):
        expected = Calculator('', 0, '10')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '=')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_value(10).set_expr(''), result.unwrap())

    def test_evaluate_calculator_expression_when_equals_and_incomplete_expression(self):
        expected = Calculator('', 0, '10-')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '=')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected, result.unwrap())

    def test_evaluate_calculator_expression_when_reset_calculator(self):
        expected = Calculator('', 20, '10')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, 'c')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_value(0).set_expr(''), result.unwrap())

    def test_evaluate_calculator_expression_when_comma_on_empty(self):
        expected = Calculator('', 0, '')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '.')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('0.'), result.unwrap())

    def test_evaluate_calculator_expression_when_number_on_coma(self):
        expected = Calculator('', 0, '0.')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '1')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('0.1'), result.unwrap())

    def test_evaluate_calculator_expression_when_comma_on_number(self):
        expected = Calculator('', 20, '10')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '.')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('10.'), result.unwrap())

    def test_evaluate_calculator_expression_when_operator_on_incomplete_decimal(self):
        expected = Calculator('', 20, '10.')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '+')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('10.+'), result.unwrap())

    def test_evaluate_calculator_expression_when_comma_on_incomplete_operator(self):
        expected = Calculator('', 20, '10+')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '.')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_expr('10+.'), result.unwrap())

    def test_evaluate_calculator_expression_when_equals_and_decimal_stared_with_point(self):
        expected = Calculator('', 20, '0.1')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '=')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_value(.1).set_expr(''), result.unwrap())

    def test_evaluate_calculator_expression_when_equals_and_incomplete_decimal(self):
        expected = Calculator('', 20, '10.')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '=')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_value(
            10.0).set_expr(''), result.unwrap())

    def test_evaluate_calculator_expression_when_equals_on_operation_and_incomplete_decimal(self):
        expected = Calculator('', 20, '20+10.')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '=')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_value(
            30.0).set_expr(''), result.unwrap())

    def test_evaluate_calculator_expression_when_equals_on_operation_and_empty_decimal(self):
        expected = Calculator('', 20, '20+.')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '=')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_value(
            20.0).set_expr(''), result.unwrap())

    def test_evaluate_calculator_expression_when_equals_on_operation_and_decimal(self):
        expected = Calculator('', 20, '20+.1')
        self.mockedRepo.update_calculator.side_effect = lambda _, c: Ok(c)
        result = self.service.evaluate_calculator_expression(expected, '=')
        self.assertTrue(result.is_ok)
        self.assertEqual(expected.set_value(
            20.1).set_expr(''), result.unwrap())


if __name__ == '__main__':
    unittest.main()
