"""Module of definition controller."""

import logging
from collections import defaultdict
from threading import Lock
from typing import DefaultDict
from uuid import uuid4

from telegram import (InlineKeyboardMarkup, InlineQueryResultArticle,
                      InputTextMessageContent, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, InlineQueryHandler, Updater)
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.message import Message
from telegram.parsemode import ParseMode

from calculator_bot.service.calculator import CalculatorService


class TelegramCalculatorController:
    """Definition Controller for telegram bot inline queries."""

    def __init__(self, token: str, service: CalculatorService) -> None:
        self.token = token
        self.service = service
        self.locks: DefaultDict[str, Lock] = defaultdict(Lock)

    def start(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /start is issued."""
        if update.message is not None:
            update.message.reply_text(
                'Hi! Try to create a new calculator using /new command')

    def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        if update.message is not None:
            update.message.reply_text('Help!')

    def new_command(self, update: Update, context: CallbackContext) -> None:
        """Send a calculator message when the command /new is issued."""
        if update.message is not None:
            update.message.reply_text(
                '__Start typing number to calculate__',
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.create_inline_markup_keyboard()
            )

    def inlinequery(self, update: Update, context: CallbackContext) -> None:
        """Handle the inline query."""
        if update.inline_query is not None:
            results = [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title='Create new calculator',
                    input_message_content=InputTextMessageContent(
                        '__Start typing number to calculate__',
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    reply_markup=self.create_inline_markup_keyboard()
                )
            ]
            update.inline_query.answer(results)

    def callbackquery(self, update: Update, context: CallbackContext) -> None:
        """Handle the callback queries."""
        if update.callback_query:
            message_id: str = str(update.callback_query.message.message_id \
                if update.callback_query.message \
                else update.callback_query.inline_message_id)
            locked = self.locks[message_id].locked()
            expr = update.callback_query.data
            if not expr:
                logging.debug(
                    'failed answering callback query with empty expression')
                return
            result = self.service.get_or_create_calculator(str(message_id))
            if result.is_err:
                logging.error(
                    'failed get or creating calculator for message: %s',
                    result.unwrap_err()
                )
                return
            result = self.service.evaluate_calculator_expression(
                result.unwrap(), expr
            )
            if result.is_err:
                logging.error(
                    'failed evaluating calculator expression: %s', result.unwrap_err())
                return
            calc = result.unwrap()
            text = ('%g' % calc.value).ljust(50)
            text += ('\n> %s' % calc.expr)
            if update.callback_query.message:
                if text != update.callback_query.message.text:
                    message = update.callback_query.message.edit_text(
                        text,
                        reply_markup=self.create_inline_markup_keyboard()
                    )
                    if not isinstance(message, Message):
                        logging.error(
                            'failed editing callback message: %s', message)
            else:
                message = context.bot.edit_message_text(
                    text,
                    inline_message_id=message_id,
                    reply_markup=self.create_inline_markup_keyboard()
                )
                if not isinstance(message, Message):
                    logging.error(
                        'failed editing callback message: %s', message)
            if locked:
                self.locks[message_id].release()

    def create_inline_markup_keyboard(self) -> InlineKeyboardMarkup:
        """Creates inline keyboard markup for calculators."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton('7', callback_data='7'),
                InlineKeyboardButton('8', callback_data='8'),
                InlineKeyboardButton('9', callback_data='9'),
                InlineKeyboardButton('*', callback_data='*'),
                InlineKeyboardButton('/', callback_data='/')
            ],
            [
                InlineKeyboardButton('4', callback_data='4'),
                InlineKeyboardButton('5', callback_data='5'),
                InlineKeyboardButton('6', callback_data='6'),
                InlineKeyboardButton('+', callback_data='+'),
                InlineKeyboardButton('-', callback_data='-')
            ],
            [
                InlineKeyboardButton('1', callback_data='1'),
                InlineKeyboardButton('2', callback_data='2'),
                InlineKeyboardButton('3', callback_data='3'),
                InlineKeyboardButton('=', callback_data='='),
                InlineKeyboardButton('c', callback_data='c'),
            ],
            [
                InlineKeyboardButton('0', callback_data='0'),
                InlineKeyboardButton('.', callback_data='.'),
            ]
        ])

    def run(self) -> None:
        """Run the bot."""
        updater = Updater(self.token)
        me_info = updater.bot.get_me()
        logging.info('Starting updater for bot: %s', me_info)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # on different commands - answer in Telegram
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help_command))
        dispatcher.add_handler(CommandHandler("new", self.new_command))

        # on non command i.e message - echo the message on Telegram
        dispatcher.add_handler(InlineQueryHandler(self.inlinequery))
        dispatcher.add_handler(CallbackQueryHandler(self.callbackquery))

        # Start the Bot
        updater.start_polling()

        # Block until the user presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
