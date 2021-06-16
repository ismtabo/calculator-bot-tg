import unittest

from .test_calculator_bot import TestCalculatorRepository, TestCalculatorService


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestCalculatorRepository)
    suite.addTest(TestCalculatorService)
