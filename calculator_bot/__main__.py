"""
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic inline bot example. Applies different text transformations.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import logging
import os
import sys

from calculator_bot.controller import TelegramCalculatorController
from calculator_bot.repository import (CalculatorRepository,
                                       MemoryCalculatorRepository)
from calculator_bot.service.calculator import CalculatorService

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

if __name__ == '__main__':
    token = os.getenv("TG_TOKEN")
    log_level = os.getenv("LOG_LEVEL") or logging.ERROR

    if not token:
        logging.error("Missing telegram token. May forgive to set TG_TOKEN?")
        sys.exit(1)

    # Enable logger
    logging.basicConfig(level=log_level)

    repo: CalculatorRepository = MemoryCalculatorRepository()
    svc: CalculatorService = CalculatorService(repo)
    ctrl = TelegramCalculatorController(token, svc)
    ctrl.run()
