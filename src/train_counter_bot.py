"""Main module of TrainCounterBot, a Telegram bot."""

from datetime import date
from datetime import datetime
import os
from sys import argv
from sys import platform

import telebot
from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton
from telebot.types import Message

from counter import Counter


DATA_DIR_PATH = os.getenv("DATA_DIR_PATH")
if DATA_DIR_PATH is None:
    error_txt = (
        "ERROR: No data dir provided. Please, set the DATA_DIR_PATH "
        "environment variable."
    )
    print(error_txt)
    exit(1)

LOG_PATH = f"{DATA_DIR_PATH}/counter.log"

TOKEN = os.getenv("BOT_TOKEN")
if TOKEN is None:
    error_txt = (
        "ERROR: No token provided. Please, set the BOT_TOKEN "
        "environment variable."
    )
    print(error_txt)
    exit(1)

bot = telebot.TeleBot(TOKEN)


def log_write(text: str):
    """Write text to log file."""

    log_text = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}: {text}\n"
    with open(LOG_PATH, "a+") as file:
        file.write(log_text)


def get_counters(cid):
    """Returns a list with the counters of the specified chat."""

    file_path = f"{DATA_DIR_PATH}/counters_{cid}.csv"
    if not os.path.exists(file_path):
        return []

    ls = []
    try:
        with open(file_path, "r") as file:
            for line in file:
                props = line.split(";")
                ls.append(
                    Counter(
                        cid,
                        *props[:-1],
                        date(*list(map(int, props[-1].split("-"))))
                    )
                )
    except Exception as e:
        error_txt = f"ERROR: Problem detected while reading counters ({e})."
        print(error_txt)
        log_write(error_txt)

    return ls


def get_counter_by_name(cid, name):
    for c in get_counters(cid):
        if c.name == name:
            return c
    return None


def add_counter(cid, type, name, increase):
    try:
        if any([c.name == name for c in get_counters(cid)]):
            bot.send_message(
                chat_id=cid,
                text=(
                    f"🛑 There is already another counter named {name}\n"
                    "Check out your counters list with /counters."
                ),
            )
        else:
            with open(f"{DATA_DIR_PATH}/counters_{cid}.csv", "a+") as f:
                f.write(
                    f"{type};{name};{increase};{increase};{date.today()}\n"
                )
    except Exception as e:
        txt_error = f"ERROR: Problem detected while adding counter. {e}"
        print(txt_error)
        log_write(txt_error)
        bot.send_message(
            chat_id=cid,
            text="🛑 There was a server error while adding your counter.",
        )


def update_counter(cid, counter):
    counters = get_counters(cid)
    with open(f"{DATA_DIR_PATH}/counters_{cid}.csv", "w") as f:
        for c in counters:
            if c.name == counter.name:
                f.write(repr(counter)+"\n")
            else:
                f.write(repr(c)+"\n")


def get_callback_arguments(data):
    return data.split(":")[-1].split(";")


def get_simple_keyboard():
    """Returns the keyboard used in simple counters."""

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("+1",  callback_data=f"simple+"),
        InlineKeyboardButton("-1", callback_data=f"simple-"),
    )

    return keyboard


def get_counter_keyboard(name):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="-1",
            callback_data=f"decrease_counter:{name};-1",
        ),
        InlineKeyboardButton(
            text="-5",
            callback_data=f"decrease_counter:{name};-5",
        ),
    )
    keyboard.add(
        InlineKeyboardButton(
            text="-20",
            callback_data=f"decrease_counter:{name};-20",
        ),
        InlineKeyboardButton(
            text="-30",
            callback_data=f"decrease_counter:{name};-30",
        ),
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Set manually",
            callback_data=f"set_counter:{name}",
        ),
    )
    return keyboard


def reprint_counter(cid, mid, counter):
    text = (
        f"*{counter.name}: {counter.value}*\n"
        f"Type: {counter.type}\n"
        f"Increase step: +{counter.increase}"
    )
    bot.edit_message_text(
        text=text,
        chat_id=cid,
        message_id=mid,
        parse_mode="markdown",
        reply_markup=get_counter_keyboard(counter.name),
    )


def reprint_list(cid, mid):
    text = "*Your counters*\n"
    keyboard = InlineKeyboardMarkup()
    for counter in get_counters(cid):
        keyboard.add(
            InlineKeyboardButton(
                text=str(counter),
                callback_data=f"display_counter:{counter.name}",
            ),
        )
    keyboard.add(
        InlineKeyboardButton(
            text="♻️ Remove a counter",
            callback_data="remove_a_counter",
        )
    )

    bot.edit_message_text(
        text=text,
        chat_id=cid,
        message_id=mid,
        parse_mode="markdown",
        reply_markup=keyboard,
    )


def send_chained_questions(
    cid,
    callback,
    *questions,
    delete_all=False,
    last_message=None,
):
    """Send multiple questions and collect user"s anwsers."""

    def lastStep(answ, old_answs=[], old_qts=[]):
        answers = list(old_answs)
        answers.append(answ)
        if delete_all:
            for msg in old_qts+answers:
                bot.delete_message(cid, msg.message_id)
        if last_message is not None:
            bot.send_message(cid, last_message)
        callback([a.text for a in answers])

    steps = []
    steps.append(lastStep)
    for i, qt in enumerate(questions[:0:-1]):
        def newStep(answ, old_answs=[], old_qts=[]):
            newQt = bot.send_message(cid, qt)
            bot.register_next_step_handler(
                newQt, steps[i], old_answs+[answ], old_qts+[newQt])

        steps.append(newStep)

    first_qt = bot.send_message(cid, questions[0])
    bot.register_next_step_handler(first_qt, steps[-1], old_qts=[first_qt])


@bot.message_handler(commands=["menu"])
def send_menu(message):
    """Displays the bot"s menu to the user."""

    cid = message.chat.id

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="New simple counter",
            callback_data="counter_simple",
        ),
    )
    keyboard.add(
        InlineKeyboardButton(
            text="New daily counter",
            callback_data="new_counter_daily",
        ),
        InlineKeyboardButton(
            text="New Weekly counter",
            callback_data="new_counter_weekly",
        ),
    )
    keyboard.add(
        InlineKeyboardButton(
            text="🗒 Counters list",
            callback_data="counters",
        )
    )
    bot.send_message(
        chat_id=cid,
        text=(
            "*MENU*\n"
            " - Simple counters can be increased/decreased by 1.\n"
            " - Daily and weekly counters increase over time."
        ),
        parse_mode="markdown",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: call.data == "counter_simple")
def send_simple_counter(call):
    cid = call.message.chat.id

    bot.send_message(
        chat_id=cid,
        text="Simple counter: 0",
        reply_markup=get_simple_keyboard(),
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("simple"))
def simple_counter_change(call):
    mid = call.message.message_id
    cid = call.message.chat.id

    count = int(call.message.text.split(" ")[-1])
    count = count+1 if call.data == "simple+" else count-1

    bot.edit_message_text(
        text=f"Simple counter: {count}",
        chat_id=cid,
        message_id=mid,
        reply_markup=get_simple_keyboard(),
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("new_counter")
)
def create_frec_counter(call):
    cid = call.message.chat.id

    day = call.data == "new_counter_daily"
    type = "daily" if day else "weekly"

    def callback(answers):
        assert len(answers) == 2
        name, increase = answers

        try:
            assert not ";" in name
            increase = int(increase)
        except AssertionError:
            bot.send_message(
                chat_id=cid,
                text=(
                    "Counter names should not include weird characters... "
                    "Please, try again."
                )
            )
        except ValueError:
            bot.send_message(
                chat_id=cid,
                text=(
                    "That doesn't look like a natural number... "
                    "Please, try again."
                ),
            )

        add_counter(cid, type, name, increase)

    send_chained_questions(
        cid,
        callback,
        "How do you want to name the counter?",
        f"Next! What is the {type} increase value?",
        delete_all=True,
        last_message=(
            "Great! You may use /counters to check your current "
            "list of counters."
        ),
    )


@bot.message_handler(commands=["counters"])
@bot.callback_query_handler(lambda call: call.data == "counters")
def display_counters(msg_or_call):
    cid = msg_or_call.chat.id if type(
        msg_or_call) == Message else msg_or_call.message.chat.id

    ls = get_counters(cid)
    text = "*LIST*\nSelect a counter."
    keyboard = InlineKeyboardMarkup()
    for counter in ls:
        keyboard.add(
            InlineKeyboardButton(
                text=str(counter),
                callback_data=f"display_counter:{counter.name}",
            ),
        )
    keyboard.add(
        InlineKeyboardButton(
            text="♻️ Remove a counter",
            callback_data="remove_a_counter",
        )
    )

    bot.send_message(
        chat_id=cid,
        text=text,
        parse_mode="markdown",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(
    lambda call: call.data.startswith("display_counter")
)
def display_counter(call):
    cid = call.message.chat.id
    name = call.data.split(":")[-1]

    counter = get_counter_by_name(cid, name)

    text = (
        f"*{counter.name}: {counter.value}*\n"
        f"Type: {counter.type}\n"
        f"Increase step: {counter.increase}"
    )
    bot.edit_message_text(
        text=text,
        chat_id=cid,
        message_id=call.message.message_id,
        parse_mode="markdown",
        reply_markup=get_counter_keyboard(name),
    )


@bot.callback_query_handler(
    lambda call: call.data.startswith("decrease_counter")
)
def decrease_counter(call):
    cid = call.message.chat.id
    name, value = get_callback_arguments(call.data)
    value = -int(value)

    counter = get_counter_by_name(cid, name)
    counter.decrease(value)
    update_counter(cid, counter)

    text = (
        f"*{counter.name}: {counter.value}*\n"
        f"Type: {counter.type}\n"
        f"Increase step: {counter.increase}"
    )
    bot.edit_message_text(
        text=text,
        chat_id=cid,
        message_id=call.message.message_id,
        parse_mode="markdown",
        reply_markup=get_counter_keyboard(name),
    )


@bot.callback_query_handler(lambda call: call.data.startswith("set_counter"))
def set_counter(call):
    cid = call.message.chat.id
    name = get_callback_arguments(call.data)[0]

    def callback(answers):
        if answers[0].isdigit():
            counter = get_counter_by_name(cid, name)
            counter.value = int(answers[0])
            update_counter(cid, counter)

            # Update counter message
            reprint_counter(cid, call.message.message_id, counter)
        else:
            bot.send_message(cid, "🛑 The new value must be an integer!")

    send_chained_questions(
        cid,
        callback,
        f"What is the new value for {name}?",
        delete_all=True,
    )


@bot.callback_query_handler(lambda call: call.data == "remove_a_counter")
def remove_a_counter(call):
    cid = call.message.chat.id

    text = "*Select counter to remove*\n"
    keyboard = InlineKeyboardMarkup()
    for counter in get_counters(cid):
        keyboard.add(
            InlineKeyboardButton(
                text="🗑 " + str(counter),
                callback_data=f"remove_counter:{counter.name}",
            ),
        )
    keyboard.add(
        InlineKeyboardButton(
            text="<<",
            callback_data="back_to_list",
        )
    )

    bot.edit_message_text(
        text=text,
        chat_id=cid,
        message_id=call.message.message_id,
        parse_mode="markdown",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(
    lambda call: call.data.startswith("remove_counter")
)
def remove_counter(call):
    cid = call.message.chat.id
    name = get_callback_arguments(call.data)[0]

    # Overwrite data
    counters = get_counters(cid)
    with open(f"{DATA_DIR_PATH}/counters_{cid}.csv", "w") as f:
        for c in counters:
            if c.name != name:
                f.write(repr(c)+"\n")

    # Update counters list
    reprint_list(cid, call.message.message_id)


@bot.callback_query_handler(lambda call: call.data == "back_to_list")
def back_to_list(call):
    reprint_list(call.message.chat.id, call.message.message_id)


@bot.message_handler(commands=["git", "github", "source", "src"])
def command_github(message):
    """Display a link to this bot"s code repository."""

    cid = message.chat.id

    bot.send_message(
        cid,
        text=(
            "You can find the source code of this bot in "
            "[GitHub](https://github.com/Pablo-Davila/TrainCounterBot/)"
        ),
        parse_mode="markdown",
    )


@bot.message_handler(commands=["id"])
def command_id(message):
    """Display current chat"s id."""

    cid = message.chat.id
    bot.send_message(cid, f"Your chat id is {cid}")


try:
    print("Running TrainCounterBot")
    bot.polling()
except Exception as e:
    log_write(f"CRITICAL ERROR: {e}")
    raise e
