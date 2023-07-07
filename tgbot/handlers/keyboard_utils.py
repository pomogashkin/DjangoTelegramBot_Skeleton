# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.handlers import manage_data as md
from tgbot.handlers import static_text as st
from tgbot.models import (
    Category,
    Department,
    MoneySource,
    PaymentMethod,
    Project,
)


def make_btn_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                st.go_back, callback_data=f"{md.BUTTON_BACK_IN_PLACE}"
            ),
        ]
    ]

    return InlineKeyboardMarkup(buttons)


def make_keyboard_for_start_command(n_cols=2):
    buttons = [
        InlineKeyboardButton(
            st.INCOME,
            callback_data=f"{md.INCOME}",
        ),
        InlineKeyboardButton(
            st.EXPENSES,
            callback_data=f"{md.EXPENSES}",
        ),
        InlineKeyboardButton(
            st.UPDATE_INCOME,
            callback_data=f"{md.UPDATE_INCOME}",
        ),
        InlineKeyboardButton(
            st.UPDATE_EXPENSES,
            callback_data=f"{md.UPDATE_EXPENSES}",
        ),
        InlineKeyboardButton(
            st.LOOK_INCOME,
            callback_data=f"{md.LOOK_INCOME}",
        ),
        InlineKeyboardButton(
            st.LOOK_EXPENSES,
            callback_data=f"{md.LOOK_EXPENSES}",
        ),
        InlineKeyboardButton(
            st.STAT,
            callback_data=f"{md.STAT}",
        ),
    ]
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    return InlineKeyboardMarkup(menu)


def project_btm(
    n_cols=2,
    statistic=False,
    header_buttons=None,
    footer_buttons=None,
    income=False,
):
    if income:
        firts_arg = md.SOURCE
    elif statistic:
        firts_arg = md.GET_STAT
    else:
        firts_arg = md.METHOD
    buttons = [
        InlineKeyboardButton(
            f"{item.name}",
            callback_data=(f"{firts_arg}#{item.name}"),
        )
        for item in Project.objects.all()
    ]
    buttons.append(
        InlineKeyboardButton(
            "Назад",
            callback_data=(f"{md.BACK}"),
        )
    )
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]

    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return InlineKeyboardMarkup(menu)


def method_btm(n_cols=2):
    buttons = [
        InlineKeyboardButton(
            f"{item.name}",
            callback_data=(f"{md.DEPARTMENT}#{item.name}"),
        )
        for item in PaymentMethod.objects.all()
    ]
    buttons.append(
        InlineKeyboardButton(
            "Назад",
            callback_data=(f"{md.BACK_TO_PROJECT}"),
        )
    )
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    return InlineKeyboardMarkup(menu)


def category_btm(department, n_cols=2):
    buttons = [
        InlineKeyboardButton(
            f"{item.name}",
            callback_data=(f"{md.AMOUNT}#{item.name}#{md.EXPENSES}"),
        )
        for item in Category.objects.filter(departments__name=department)
    ]
    buttons.append(
        InlineKeyboardButton(
            "Назад",
            callback_data=(f"{md.BACK}"),
        )
    )
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    return InlineKeyboardMarkup(menu)


def source_btm(n_cols=2):
    buttons = [
        InlineKeyboardButton(
            f"{item.name}",
            callback_data=(f"{md.AMOUNT}#{item.name}#None"),
        )
        for item in MoneySource.objects.all()
    ]
    buttons.append(
        InlineKeyboardButton(
            "Назад",
            callback_data=(f"{md.BACK}"),
        )
    )
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    return InlineKeyboardMarkup(menu)


def department_btm(n_cols=2):
    buttons = [
        InlineKeyboardButton(
            f"{item.name}",
            callback_data=(f"{md.CATEGORY}#{item.name}"),
        )
        for item in Department.objects.all()
    ]
    buttons.append(
        InlineKeyboardButton(
            "Назад",
            callback_data=(f"{md.BACK}"),
        )
    )
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    return InlineKeyboardMarkup(menu)


def total_btm(n_cols=2):
    buttons = [
        InlineKeyboardButton(
            f"{st.CONFIRM}",
            callback_data=(f"{md.FINAL}#{md.CONFIRM}"),
        ),
        InlineKeyboardButton(
            f"{st.REJECT}",
            callback_data=(f"{md.FINAL}#{md.REJECT}"),
        ),
    ]
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    return InlineKeyboardMarkup(menu)


def com_btm(n_cols=2):
    buttons = [
        InlineKeyboardButton(
            "Далее",
            callback_data=(f"{md.TOTAL}"),
        )
    ]
    buttons.append(
        InlineKeyboardButton(
            "Назад",
            callback_data=(f"{md.BACK}"),
        )
    )
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    return InlineKeyboardMarkup(menu)


def back_btm(n_cols=2):
    buttons = [
        InlineKeyboardButton(
            "Назад",
            callback_data=(f"{md.BACK}"),
        )
    ]
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    return InlineKeyboardMarkup(menu)


def fin_btm(n_cols=2):
    buttons = [
        InlineKeyboardButton(
            "К финансам",
            callback_data=(f"{md.BACK}"),
        )
    ]
    menu = [buttons[i : i + n_cols] for i in range(0, len(buttons), n_cols)]
    return InlineKeyboardMarkup(menu)
