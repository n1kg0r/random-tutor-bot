

#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.


"""
import random
import logging
from typing import Dict

from telegram import __version__ as TG_VER
from telegram import Chat, Update
try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


CHOOSING, TYPING_REPLY, TYPING_CHOICE, CUSTOM_TYPING_CHOICE = range(4)

start_keyboard = [
    ["I need some help with studies"],
    ["I can help with studies"],
    ["I want to meet for something else"],
    ["Subscribe me for extracurriculum calls"],
    ["Done"],
]
start_markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=True)


reply_keyboard = [
    ["Match my requests"],
    ["I need some help with studies", "I can help with studies"],
    ["I want to meet for something else"],
    ["Subscribe me for extracurriculum calls"],
    ["Show my requests"],
    ["Done"],
]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)








def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {', '.join(value)}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n\n", "\n"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation, display any stored data and ask user for input."""

    user_name = update.effective_user.full_name
    chat = update.effective_chat
    if chat.type != Chat.PRIVATE:
        return
    
    # context.bot_data.setdefault("user_ids", set()).add(chat.id)
    context.bot_data.setdefault("users", set()).add(update.effective_user)
    

    reply_text = f"Hi {user_name}! \n\nRandom Tutor Bot was designed to help students meet for sharing ideas and helping each other with studies."

    if context.user_data:
        reply_text += (
            f"\n\nThis is what you've told me so far: {facts_to_str(context.user_data)}" 
            "\nWould you like to get an instant match? Or add a new request"
        )
        await update.message.reply_text(reply_text, reply_markup=reply_markup)
    else:
        reply_text += (
            " \n\nHow can I help you?"
        )
        await update.message.reply_text(reply_text, reply_markup=start_markup)
    
    return CHOOSING













async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text.lower()
    context.user_data["choice"] = text
    if context.user_data.get(text):
        reply_text = (
            f"So far you've told me the following: \n{text} – {', '.join(context.user_data[text])}."
            f"\n\nIf you want to add a new request, please text the area of studies, e.g. physics."
            f"\n\nOtherwise, write Done."
        )
        await update.message.reply_text(reply_text)
    elif text in {'i need some help with studies', 'i can help with studies'}:
        reply_text = f"Please text me the area of studies, for example, maths"
        await update.message.reply_text(reply_text)
        

    return TYPING_REPLY






async def custom_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for a description of a custom category."""
    text = update.message.text.lower()
    context.user_data["choice"] = text
    
    await update.message.reply_text(
        "Alright, please text me what you'd like to meet with fellow students for, for example 'I'd like to form a group for the startup call'"
    )
    return CUSTOM_TYPING_CHOICE



async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store info provided by user and ask for the next category."""
    text = update.message.text
    if text == "Subscribe me for extracurriculum calls":
        context.user_data["subscription for extracurriculum meetings"] = {"active"}
        if context.bot_data.get("extracurriculum_subscribers"):
            context.bot_data["extracurriculum_subscribers"].add(update.effective_user.username)
        else:
            context.bot_data["extracurriculum_subscribers"] = {update.effective_user.username}


    if context.user_data.get("choice"):
        if context.user_data["choice"] in {'i need some help with studies', 'i can help with studies'}:
            category = context.user_data["choice"] 
        else:
            category = 'extracurriculum'
        if context.user_data.get(category):
            context.user_data[category].add(text.lower())
        else:
            context.user_data[category] = {text.lower()}
        del context.user_data["choice"]

        if context.bot_data.get(category):
            for subject in context.user_data[category]:
                if context.bot_data[category].get(subject):
                    context.bot_data[category][subject].add(update.effective_user.username)
                else:
                    context.bot_data[category][subject] = {update.effective_user.username}
        else:
            context.bot_data[category] = {}
            for subject in context.user_data[category]:
                context.bot_data[category][subject] = {update.effective_user.username}

            
        logger.info(context.user_data)
        logger.info(context.bot_data)


    await update.message.reply_text(
        "Neat! Just so you know, this is what you already told me:"
        f"{facts_to_str(context.user_data)}"
        "\nDo you want an instant match or you'd like to add something else?",
        reply_markup=reply_markup,
    )

    return CHOOSING





async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the gathered info."""
    await update.message.reply_text(
        f"This is what you already told me: {facts_to_str(context.user_data)}"
        "\nDo you want an instant match or you'd like to add something else?",
        reply_markup=reply_markup,
    )
    return CHOOSING




async def suggest_matches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the gathered info."""

    candidates = {
        'i need some help with studies': {},
        'i can help with studies': {},
        'extracurriculum': {},
    }

    reply_text = "Here are the results for your requests"

    if context.user_data.get('i need some help with studies'):
        non_empty_subjects = set()
        empty_subjects = set()
        for user_subject in context.user_data['i need some help with studies']:
            candidates["i need some help with studies"][user_subject] = None
            if context.bot_data.get('i can help with studies'):
                for compared_subject in context.bot_data['i can help with studies']:
                    if user_subject == compared_subject:
                        non_empty_subjects.add(user_subject)
                        candidates["i need some help with studies"][user_subject] = random.choice(list(context.bot_data['i can help with studies'][compared_subject].difference({update.effective_user.username})))
            if user_subject not in non_empty_subjects:
                empty_subjects.add(user_subject)
        if len(non_empty_subjects):
            reply_text += "\n\nThese fellow students will be glad to help you with studies:"
            for user_subject in context.user_data['i need some help with studies']:
                if candidates['i need some help with studies'][user_subject] is not None:
                    reply_text += f"\n{user_subject}: @{candidates['i need some help with studies'][user_subject]}"
        if len(empty_subjects):
            reply_text += f"\n\nUnfortunately, for {', '.join(list(empty_subjects))} there's nobody who could help yet, so keep in touch!"      


    if context.user_data.get('i can help with studies'):
        non_empty_subjects = set()
        empty_subjects = set()
        for user_subject in context.user_data['i can help with studies']:
            candidates["i can help with studies"][user_subject] = None
            if context.bot_data.get('i can help with studies'):
                for compared_subject in context.bot_data['i need some help with studies']:
                    if user_subject == compared_subject:
                        non_empty_subjects.add(user_subject)
                        candidates["i can help with studies"][user_subject] = random.choice(list(context.bot_data['i need some help with studies'][compared_subject].difference({update.effective_user.username})))
            if user_subject not in non_empty_subjects:
                empty_subjects.add(user_subject)
        if len(non_empty_subjects):
            reply_text += "\n\nThese fellow students asked for help with studies:"
            for user_subject in context.user_data['i can help with studies']:
                if candidates['i can help with studies'][user_subject] is not None:
                    reply_text += f"\n{user_subject}: @{candidates['i can help with studies'][user_subject]}"
        if len(empty_subjects):
            reply_text += f"\n\nFor the subjects {', '.join(list(empty_subjects))} there's nobody you could help yet, but we appreciate your proactivity, come back later!"   

    if context.user_data.get('subscription for extracurriculum meetings'):
        if context.bot_data.get('extracurriculum'):
            reply_text += "\n\nThese fellow students have ideas for non-curriculum meetings:"
            for xtra_key in context.bot_data['extracurriculum'].keys():
                reply_text += f"\n{xtra_key}: @{random.choice(list(context.bot_data['extracurriculum'][xtra_key].difference({update.effective_user.username})))}"

    await update.message.reply_text(reply_text)

    await update.message.reply_text(
        "\nDo you want an to add something else to your requests?",
        reply_markup=reply_markup,
    )
    return CHOOSING


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    if "choice" in context.user_data:
        del context.user_data["choice"]

    await update.message.reply_text(
        f"These are your current requests: {facts_to_str(context.user_data)}\nUntil next time!",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END





def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token("").persistence(persistence).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(I need some help with studies|I can help with studies)$"), regular_choice
                ),
                MessageHandler(filters.Regex("^I want to meet for something else$"), custom_choice),
                MessageHandler(filters.Regex("^Show my requests$"), show_data),
                MessageHandler(filters.Regex("^Subscribe me for extracurriculum calls$"), received_information),
                MessageHandler(filters.Regex("^Match my requests$"), suggest_matches),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^(Done|done)$")), regular_choice
                ),
            ],
            TYPING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^(Done|done)$")),
                    received_information,
                )
            ],
            CUSTOM_TYPING_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^(Done|done)$")), received_information
                ),
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^(Done|done)$"), done)],
        name="my_conversation",
        persistent=True,
    )

    application.add_handler(conv_handler)

    show_data_handler = CommandHandler("show_data", show_data)
    application.add_handler(show_data_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()