# -*- coding: utf-8 -*-

"""Telegram event handlers."""

import telegram
from celery.decorators import task  # event processing in async mode
from dtb.settings import TELEGRAM_TOKEN
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Dispatcher,
    Filters,
    MessageHandler,
    Updater,
)
from tgbot.handlers import admin, files
from tgbot.handlers import handlers as hnd
from tgbot.handlers import location
from tgbot.handlers import manage_data as md

conv_handler = ConversationHandler(  # здесь строится логика разговора
    entry_points=[
        CommandHandler("finance", hnd.menu),
        CallbackQueryHandler(hnd.menu, pattern=f"^{md.BACK}"),
    ],
    states={
        md.FIRST: [
            CommandHandler("update_expenses", hnd.upd_ex),
            CommandHandler("update_income", hnd.upd_in),
            CallbackQueryHandler(
                hnd.update_expenses, pattern=f"^{md.UPDATE_EXPENSES}"
            ),
            CallbackQueryHandler(hnd.menu, pattern=f"^{md.BACK}"),
            CallbackQueryHandler(
                hnd.look_expenses, pattern=f"^{md.LOOK_EXPENSES}"
            ),
            CallbackQueryHandler(
                hnd.look_income, pattern=f"^{md.LOOK_INCOME}"
            ),
            CallbackQueryHandler(hnd.statistic, pattern=f"^{md.STAT}"),
            CallbackQueryHandler(
                hnd.get_special_stat, pattern=f"^{md.GET_STAT}"
            ),
            CallbackQueryHandler(
                hnd.update_income, pattern=f"^{md.UPDATE_INCOME}"
            ),
            CallbackQueryHandler(hnd.start_income, pattern=f"^{md.INCOME}"),
            CallbackQueryHandler(
                hnd.start_expenses, pattern=f"^{md.EXPENSES}"
            ),
            CallbackQueryHandler(
                hnd.start_expenses, pattern=f"^{md.BACK_TO_PROJECT}"
            ),
            CallbackQueryHandler(hnd.source, pattern=f"^{md.SOURCE}"),
            CallbackQueryHandler(hnd.method, pattern=f"^{md.METHOD}"),
            CallbackQueryHandler(hnd.department, pattern=f"^{md.DEPARTMENT}"),
            CallbackQueryHandler(hnd.category, pattern=f"^{md.CATEGORY}"),
            CallbackQueryHandler(hnd.amount, pattern=f"^{md.AMOUNT}"),
            CallbackQueryHandler(
                hnd.start_income, pattern=f"^{md.BACK_TO_IN_PROJECT}"
            ),
        ],
        md.SECOND: [
            CommandHandler("com", hnd.comment),
            MessageHandler(Filters.text, hnd.last_ask),
            CallbackQueryHandler(hnd.total, pattern=f"^{md.TOTAL}"),
        ],
    },
    # точка выхода из разговора
    fallbacks=[
        CommandHandler("finance", hnd.menu),
        CallbackQueryHandler(hnd.final, pattern=f"^{md.FINAL}"),
    ],
)


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
    dp.add_handler(CommandHandler("get_moderation", hnd.get_moderation)),
    dp.add_handler(CommandHandler("start", hnd.start)),
    dp.add_handler(CommandHandler("report_expenses", hnd.report_expenses)),
    dp.add_handler(CommandHandler("report_income", hnd.report_income)),
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("info", hnd.info)),
    dp.add_handler(CommandHandler("get_special_stat", hnd.get_special_stat))
    dp.add_handler(CommandHandler("update_expenses", hnd.upd_ex)),
    dp.add_handler(CommandHandler("update_income", hnd.upd_in)),
    dp.add_handler(CommandHandler("admin", admin.admin))
    dp.add_handler(CommandHandler("stats", admin.stats))
    dp.add_handler(
        MessageHandler(
            Filters.animation,
            files.show_file_id,
        )
    )


def run_pooling():
    """Run bot in pooling mode"""
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp = setup_dispatcher(dp)

    bot_info = telegram.Bot(TELEGRAM_TOKEN).get_me()
    bot_link = "https://t.me/" + bot_info["username"]

    print(f"Pooling of '{bot_link}' started")
    updater.start_polling(timeout=123)
    updater.idle()


@task(ignore_result=True)
def process_telegram_event(update_json):
    update = telegram.Update.de_json(update_json, bot)
    dispatcher.process_update(update)


# Global variable - best way I found to init Telegram bot
bot = telegram.Bot(TELEGRAM_TOKEN)
dispatcher = setup_dispatcher(
    Dispatcher(bot, None, workers=0, use_context=True)
)
TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
