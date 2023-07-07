# -*- coding: utf-8 -*-

import datetime
import logging

import telegram
from django.db.models import Q, Sum
from dtb.settings import MODER_PASSWORD
from tgbot.handlers import keyboard_utils as kb
from tgbot.handlers import manage_data as md
from tgbot.handlers import static_text as st
from tgbot.handlers.utils import handler_logging, send
from tgbot.models import (
    Category,
    Department,
    Expenses,
    Income,
    MoneySource,
    PaymentMethod,
    Project,
    User,
)
from tgbot.utils import extract_user_data_from_update

logger = logging.getLogger("default")


@handler_logging()
def get_moderation(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    if context.chat_data.get("last_message", None) is not None:
        context.bot.delete_message(
            message_id=context.chat_data.get("last_message"),
            chat_id=user_id,
        )
    context.bot.delete_message(
        message_id=update.message.message_id,
        chat_id=user_id,
    )
    if len(context.args) != 1:
        context.chat_data["last_message"] = send(
            text="Неверное кол-во аргументов",
            user_id=user_id,
            reply_markup=kb.back_btm(),
            m_id=True,
        )
        return
    if context.args[0] != MODER_PASSWORD:
        context.chat_data["last_message"] = send(
            text="Неверный пароль.",
            user_id=user_id,
            reply_markup=kb.back_btm(),
            m_id=True,
        )
        return
    User.objects.filter(pk=user_id).update(is_moderator=True)
    context.chat_data["last_message"] = send(
        text="Теперь вы модератор.",
        user_id=user_id,
        reply_markup=kb.back_btm(),
        m_id=True,
    )


@handler_logging()
def start(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    if context.chat_data.get("last_message", None) is not None:
        context.bot.delete_message(
            message_id=update.message.message_id - 1,
            chat_id=user_id,
        )
    context.bot.delete_message(
        message_id=update.message.message_id,
        chat_id=user_id,
    )
    context.chat_data["last_message"] = send(
        text=st.START,
        user_id=user_id,
        reply_markup=kb.fin_btm(),
        # parse_mode=telegram.ParseMode.MARKDOWN,
        m_id=True,
    )


@handler_logging()
def get_special_stat(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    today_8hr = datetime.datetime.combine(
        datetime.date.today(), datetime.datetime.min.time()
    ) + datetime.timedelta(hours=8)
    tommorow_7_59hr = datetime.datetime.combine(
        datetime.date.today(), datetime.datetime.min.time()
    ) + datetime.timedelta(days=1, hours=7, minutes=59)
    query = update.callback_query
    query.answer()
    query_data = query.data.split("#")
    project = query_data[1]
    try:
        sum_of_cash_expenses = Expenses.objects.filter(
            project__name=project,
            payment_method__name="Наличные",
            date__gte=today_8hr,
            date__lte=tommorow_7_59hr,
        ).aggregate(Sum("amount"))["amount__sum"]
    except Exception:
        sum_of_cash_expenses = 0

    try:
        cash_balance_amount_project = (
            Income.objects.filter(
                Q(money_source__name="Наличные", project__name=project)
                | Q(
                    money_source__name="внесение в сейф", project__name=project
                )
            )
        ).aggregate(Sum("amount"))["amount__sum"] - Expenses.objects.filter(
            project__name=project,
            payment_method__name="Наличные",
        ).aggregate(
            Sum("amount")
        )[
            "amount__sum"
        ]
    except Exception:
        cash_balance_amount_project = 0
    context.bot.edit_message_text(
        text=st.STATISTIC.format(
            project, sum_of_cash_expenses, cash_balance_amount_project
        ),
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.make_keyboard_for_start_command(),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


@handler_logging()
def menu(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    last_message_id = context.chat_data.get("last_message", None)
    if last_message_id is not None:
        context.bot.delete_message(
            message_id=last_message_id,
            chat_id=user_id,
        )
    if not update.callback_query:
        context.bot.delete_message(
            message_id=update.message.message_id,
            chat_id=user_id,
        )
    context.user_data.clear()

    context.chat_data["last_message"] = send(
        text="Какую операцию вы хотите провести?",
        user_id=user_id,
        reply_markup=kb.make_keyboard_for_start_command(),
        parse_mode=telegram.ParseMode.MARKDOWN,
        m_id=True,
    )
    return md.FIRST


@handler_logging()
def look_expenses(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    text = ""
    for item in Expenses.objects.all()[:10]:
        text += st.EXPENSES_WITH_ID.format(
            item.id,
            item.project.name,
            item.payment_method.name,
            item.department.name,
            item.category.name,
            item.amount,
            item.date.strftime("%Y-%m-%d %H:%M:%S"),
            item.user.username,
            item.comment,
        )
    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=text,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.back_btm(),
    ).message_id


@handler_logging()
def report_expenses(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    text = ""
    if context.chat_data.get("last_message", None) is not None:
        context.bot.delete_message(
            message_id=update.message.message_id - 1,
            chat_id=user_id,
        )
        context.bot.delete_message(
            message_id=update.message.message_id,
            chat_id=user_id,
        )
    if len(context.args) != 4:
        context.chat_data["last_message"] = send(
            text="Неверное кол-во аргументов",
            user_id=user_id,
            reply_markup=kb.back_btm(),
            m_id=True,
        )
        return

    for i in range(len(context.args)):
        if context.args[i] == "_":
            context.args[i] = ""

    project = context.args[0]
    method = context.args[1]
    department = context.args[2]
    category = context.args[3]

    result = Expenses.objects.filter(
        project__name__istartswith=project,
        payment_method__name__istartswith=method,
        department__name__istartswith=department,
        category__name__istartswith=category,
    )
    if not result.exists():
        text = "Нет объекта по данному запросу"
    else:
        for item in result:
            text += st.EXPENSES_WITH_ID.format(
                item.id,
                item.project.name,
                item.payment_method.name,
                item.department.name,
                item.category.name,
                item.amount,
                item.date.strftime("%Y-%m-%d %H:%M:%S"),
                item.user.username,
                item.comment,
            )
    context.chat_data["last_message"] = send(
        text=text,
        user_id=user_id,
        reply_markup=kb.back_btm(),
        m_id=True,
    )


@handler_logging()
def report_income(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    text = ""
    if context.chat_data.get("last_message", None) is not None:
        context.bot.delete_message(
            message_id=update.message.message_id - 1,
            chat_id=user_id,
        )
        context.bot.delete_message(
            message_id=update.message.message_id,
            chat_id=user_id,
        )
    if len(context.args) != 2:
        context.chat_data["last_message"] = send(
            text="Неверное кол-во аргументов",
            user_id=user_id,
            reply_markup=kb.back_btm(),
            m_id=True,
        )
        return
    for i in range(len(context.args)):
        if context.args[i] == "_":
            context.args[i] = ""
    project = context.args[0]
    source = context.args[1]
    result = Income.objects.filter(
        project__name__istartswith=project,
        money_source__name__istartswith=source,
    )
    if not result.exists():
        text = "Нет объекта по данному запросу"
    else:
        for item in result[:10]:
            text += st.INCOME_WITH_ID.format(
                item.id,
                item.project.name,
                item.money_source.name,
                item.amount,
                item.date.strftime("%Y-%m-%d %H:%M:%S"),
                item.user.username,
            )
    context.chat_data["last_message"] = send(
        text=text,
        user_id=user_id,
        reply_markup=kb.back_btm(),
        m_id=True,
    )


@handler_logging()
def info(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    if context.chat_data.get("last_message", None) is not None:
        context.bot.delete_message(
            message_id=context.chat_data.get("last_message"),
            chat_id=user_id,
        )
    try:
        id = int(context.args[0])
    except Exception:
        context.chat_data["last_message"] = send(
            text=st.ID_PROBLEM,
            user_id=user_id,
            reply_markup=kb.back_btm(),
            m_id=True,
        )
        context.bot.delete_message(
            message_id=update.message.message_id,
            chat_id=user_id,
        )
        return
    context.bot.delete_message(
        message_id=update.message.message_id,
        chat_id=user_id,
    )
    if Expenses.objects.filter(pk=id).exists():
        item = Expenses.objects.get(pk=id)
        text = st.EXPENSES_WITH_ID.format(
            item.id,
            item.project.name,
            item.payment_method.name,
            item.department.name,
            item.category.name,
            item.amount,
            item.date.strftime("%Y-%m-%d %H:%M:%S"),
            item.user.username,
            item.comment,
        )
    elif Income.objects.filter(pk=id).exists():
        item = Income.objects.get(pk=id)
        text = st.INCOME_WITH_ID.format(
            item.id,
            item.project.name,
            item.money_source.name,
            item.amount,
            item.date.strftime("%Y-%m-%d %H:%M:%S"),
            item.user.username,
        )
    else:
        context.chat_data["last_message"] = send(
            text=st.OBJECT_ID_ERROR,
            user_id=user_id,
            reply_markup=kb.back_btm(),
            m_id=True,
        )
    context.chat_data["last_message"] = send(
        text=text, user_id=user_id, reply_markup=kb.back_btm(), m_id=True
    )


@handler_logging()
def look_income(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    text = ""
    for item in Income.objects.all()[:10]:
        text += st.INCOME_WITH_ID.format(
            item.id,
            item.project.name,
            item.money_source.name,
            item.amount,
            item.date.strftime("%Y-%m-%d %H:%M:%S"),
            item.user.username,
        )
    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=text,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.back_btm(),
    ).message_id


@handler_logging()
def update_expenses(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=st.UPDATE_EXPENSES_TEXT,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.back_btm(),
    ).message_id


@handler_logging()
def update_income(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=st.UPDATE_INCOME_TEXT,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.back_btm(),
    ).message_id


@handler_logging()
def upd_ex(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    context.bot.delete_message(
        message_id=update.message.message_id,
        chat_id=user_id,
    )
    try:
        id = int(context.args[0])
    except Exception:
        context.chat_data["last_message"] = context.bot.edit_message_text(
            text=st.ID_PROBLEM,
            chat_id=user_id,
            message_id=context.chat_data.get("last_message"),
            reply_markup=kb.back_btm(),
        ).message_id
        return
    if not Expenses.objects.filter(id=id).exists():
        context.chat_data["last_message"] = context.bot.edit_message_text(
            text=st.OBJECT_ID_ERROR,
            chat_id=user_id,
            message_id=context.chat_data.get("last_message"),
            reply_markup=kb.back_btm(),
        ).message_id
        return
    elif (
        user_id != Expenses.objects.get(pk=id).user.user_id
        or not User.objects.filter(pk=user_id, is_moderator=True).exists()
    ):
        context.chat_data["last_message"] = context.bot.edit_message_text(
            text=st.PERMISSION_UPDATE_ERROR,
            chat_id=user_id,
            message_id=context.chat_data.get("last_message"),
            parse_mode=telegram.ParseMode.MARKDOWN,
            reply_markup=kb.back_btm(),
        ).message_id
        return
    else:
        context.user_data["update"] = True
        context.user_data["pk"] = id
        start_expenses(update, context)


@handler_logging()
def upd_in(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    context.bot.delete_message(
        message_id=update.message.message_id,
        chat_id=user_id,
    )
    try:
        id = int(context.args[0])
    except Exception:
        context.chat_data["last_message"] = context.bot.edit_message_text(
            text=st.ID_PROBLEM,
            chat_id=user_id,
            message_id=context.chat_data.get("last_message"),
            reply_markup=kb.back_btm(),
        ).message_id
        return

    if not Income.objects.filter(id=id).exists():
        context.chat_data["last_message"] = context.bot.edit_message_text(
            text=st.OBJECT_ID_ERROR,
            chat_id=user_id,
            message_id=context.chat_data.get("last_message"),
            reply_markup=kb.back_btm(),
        ).message_id
        return
    elif (
        user_id != Income.objects.get(pk=id).user.user_id
        or not User.objects.filter(pk=user_id, is_moderator=True).exists()
    ):
        text = st.PERMISSION_UPDATE_ERROR
        context.chat_data["last_message"] = context.bot.edit_message_text(
            text=text,
            chat_id=user_id,
            message_id=context.chat_data.get("last_message"),
            parse_mode=telegram.ParseMode.MARKDOWN,
            reply_markup=kb.back_btm(),
        ).message_id
        return
    else:
        context.user_data["update"] = True
        context.user_data["pk"] = id
        start_income(update, context)


@handler_logging()
def statistic(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]

    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=st.CHOOSE_PROJECT,
        chat_id=user_id,
        reply_markup=kb.project_btm(statistic=True),
        message_id=update.callback_query.message.message_id,
        parse_mode=telegram.ParseMode.MARKDOWN,
    ).message_id


@handler_logging()
def start_income(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    try:
        m_id = update.callback_query.message.message_id
    except Exception:
        m_id = context.chat_data.get("last_message")
    context.user_data["operation"] = Income
    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=st.CHOOSE_PROJECT,
        chat_id=user_id,
        reply_markup=kb.project_btm(income=True),
        message_id=m_id,
        parse_mode=telegram.ParseMode.MARKDOWN,
    ).message_id


@handler_logging()
def start_expenses(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    try:
        m_id = update.callback_query.message.message_id
    except Exception:
        m_id = context.chat_data.get("last_message")
    context.user_data["operation"] = Expenses
    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=st.CHOOSE_PROJECT,
        chat_id=user_id,
        reply_markup=kb.project_btm(),
        message_id=m_id,
        parse_mode=telegram.ParseMode.MARKDOWN,
    ).message_id


@handler_logging()
def method(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    query = update.callback_query
    query.answer()
    query_data = query.data.split("#")

    context.user_data["project"] = query_data[1]

    context.bot.edit_message_text(
        text=st.CHOOSE_METHOD,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.method_btm(),
        parse_mode=telegram.ParseMode.MARKDOWN,
    ).message_id


@handler_logging()
def department(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    query = update.callback_query
    query.answer()
    query_data = query.data.split("#")

    context.user_data["method"] = query_data[1]

    context.bot.edit_message_text(
        text=st.CHOOSE_DEPARTMENT,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.department_btm(),
        parse_mode=telegram.ParseMode.MARKDOWN,
    ).message_id


@handler_logging()
def category(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]

    query = update.callback_query
    query.answer()
    query_data = query.data.split("#")

    context.user_data["department"] = query_data[1]

    context.bot.edit_message_text(
        text=st.CHOOSE_CATEGORY,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.category_btm(
            department=query_data[1],
        ),
        parse_mode=telegram.ParseMode.MARKDOWN,
    ).message_id


@handler_logging()
def source(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    query = update.callback_query
    query.answer()
    query_data = query.data.split("#")

    context.user_data["project"] = query_data[1]

    context.bot.edit_message_text(
        text=st.CHOOSE_SOURCE,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.source_btm(),
        parse_mode=telegram.ParseMode.MARKDOWN,
    ).message_id


@handler_logging()
def amount(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]

    query = update.callback_query
    query.answer()
    query_data = query.data.split("#")

    if query_data[2] != md.EXPENSES:
        context.user_data["source"] = query_data[1]
    else:
        context.user_data["category"] = query_data[1]

    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=st.ENTER_AMOUNT,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=telegram.ParseMode.MARKDOWN,
    ).message_id
    return md.SECOND


@handler_logging()
def last_ask(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    context.user_data["amount"] = update.message.text
    context.bot.delete_message(
        message_id=update.message.message_id,
        chat_id=user_id,
    )
    if context.user_data.get("operation") == Income:
        total(update, context)
    else:
        user_id = extract_user_data_from_update(update)["user_id"]

        context.chat_data["last_message"] = context.bot.edit_message_text(
            text=st.COMMENT,
            chat_id=user_id,
            message_id=context.chat_data["last_message"],
            parse_mode=telegram.ParseMode.MARKDOWN,
            reply_markup=kb.com_btm(),
        ).message_id


@handler_logging()
def comment(update, context):
    context.user_data["comment"] = " ".join(context.args)
    total(update, context)


@handler_logging()
def total(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    user = User.get_user(update, context)
    if context.user_data.get("operation") == Income:
        text = st.INCOME_OPERATION.format(
            context.user_data.get("project"),
            context.user_data.get("source"),
            context.user_data.get("amount"),
            user.username,
        )
    else:
        text = st.EXPENSES_OPERATION.format(
            context.user_data.get("project"),
            context.user_data.get("method"),
            context.user_data.get("department"),
            context.user_data.get("category"),
            context.user_data.get("amount"),
            user.username,
            context.user_data.get("comment"),
        )
    if context.user_data.get("comment", None) is not None:
        context.bot.delete_message(
            message_id=update.message.message_id,
            chat_id=user_id,
        )
    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=text,
        chat_id=user_id,
        message_id=context.chat_data.get("last_message"),
        parse_mode=telegram.ParseMode.MARKDOWN,
        reply_markup=kb.total_btm(),
    ).message_id


@handler_logging()
def final(update, context):
    user_id = extract_user_data_from_update(update)["user_id"]
    user = User.get_user(update, context)
    try:
        original_id = int(context.user_data.get("pk"))
    except Exception:
        original_id = 0

    query = update.callback_query
    query.answer()
    query_data = query.data.split("#")

    if query_data[1] == md.REJECT:
        text = st.CANCEL
    else:
        if context.user_data.get("operation") == Income:
            try:
                if context.user_data.get("update") is True:
                    Income.objects.filter(pk=original_id).update(
                        user=user,
                        money_source=MoneySource.objects.filter(
                            name=context.user_data.get("source")
                        ).first(),
                        amount=int(context.user_data.get("amount")),
                        project=Project.objects.filter(
                            name=context.user_data.get("project")
                        ).first(),
                    )
                    text = st.OPERATION_UPD.format(original_id)
                else:
                    id = Income.objects.create(
                        user=user,
                        money_source=MoneySource.objects.filter(
                            name=context.user_data.get("source")
                        ).first(),
                        amount=int(context.user_data.get("amount")),
                        project=Project.objects.filter(
                            name=context.user_data.get("project")
                        ).first(),
                    ).id
                    text = st.OPERATION_UPD.format(id)
            except Exception as err:
                text = err
        else:
            try:
                if context.user_data.get("update") is True:
                    Expenses.objects.filter(pk=original_id).update(
                        user=user,
                        payment_method=PaymentMethod.objects.filter(
                            name=context.user_data.get("method")
                        ).first(),
                        amount=int(context.user_data.get("amount")),
                        project=Project.objects.filter(
                            name=context.user_data.get("project")
                        ).first(),
                        department=Department.objects.filter(
                            name=context.user_data.get("department")
                        ).first(),
                        category=Category.objects.filter(
                            name=context.user_data.get("category")
                        ).first(),
                        comment=context.user_data.get("comment"),
                    )
                    text = st.OPERATION_UPD.format(original_id)
                else:
                    id = Expenses.objects.create(
                        user=user,
                        payment_method=PaymentMethod.objects.filter(
                            name=context.user_data.get("method")
                        ).first(),
                        amount=int(context.user_data.get("amount")),
                        project=Project.objects.filter(
                            name=context.user_data.get("project")
                        ).first(),
                        department=Department.objects.filter(
                            name=context.user_data.get("department")
                        ).first(),
                        category=Category.objects.filter(
                            name=context.user_data.get("category")
                        ).first(),
                        comment=context.user_data.get("comment"),
                    ).id
                    text = st.OPERATION_UPD.format(id)
            except Exception as err:
                text = str(err)

    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=text,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kb.back_btm(),
    ).message_id
    return -1

    context.chat_data["last_message"] = context.bot.edit_message_text(
        text=text,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=telegram.ParseMode.MARKDOWN,
    ).message_id
