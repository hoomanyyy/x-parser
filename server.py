import asyncio
import html
import json
import logging
import os
import re
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from ai import translate
from auth import Auth
from posts import GetPosts, find_new_posts, merge_seen
from sqlCommand import SqlCommand

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))
MAX_TEXT_LENGTH = 3500
MAX_CAPTION_LENGTH = 1024
MAX_MEDIA_GROUP = 10

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")
PROFILE_URL_RE = re.compile(r"^(?:https?://)?(?:www\.|mobile\.)?(?:x|twitter)\.com/", re.IGNORECASE)
IMG_SRC_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("xmonitor")

translator = translate.Translator(first_language="English", language_to="Persian")

WELCOME_TEXT = (
    "WELCOME TO X MONITOR BOT!\n\n"
    "USE THE COMMANDS BELOW:\n\n"
    "/addusername - ADD USERNAME TO MONITOR\n"
    "/removeusername - REMOVE USERNAME\n"
    "/myusernames - VIEW MONITORED USERNAMES\n"
    "/help - HELP"
)

MAIN_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("ADD USERNAME", callback_data="addusername"),
        InlineKeyboardButton("REMOVE USERNAME", callback_data="removeusername"),
        InlineKeyboardButton("LISTS", callback_data="myusernames"),
    ]
])


def normalize_username(text):
    value = PROFILE_URL_RE.sub("", (text or "").strip())
    value = value.split("?")[0].split("/")[0].strip().lstrip("@")
    return value if USERNAME_RE.match(value) else None


def parse_seen(raw):
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(item) for item in data]
    except Exception:
        pass
    return []


def extract_images(post):
    images = []
    description = post.get("description") or ""
    matches = IMG_SRC_RE.findall(description)
    for match in matches:
        url = html.unescape(match).strip()
        if url.startswith("http") and url not in images:
            images.append(url)
    return images[:MAX_MEDIA_GROUP]


def format_post(username, post):
    text = post["text"]
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH].rstrip() + " ..."

    parts = [f"NEW POST FROM @{username}"]
    if text:
        parts.append(text)
    if post["link"]:
        parts.append(post["link"])
    return "\n\n".join(parts)


def fetch_posts(username):
    try:
        bot_posts = GetPosts(username)
        return bot_posts.posts()
    except Exception:
        logger.exception("FETCHING POSTS FOR @%s FAILED", username.upper())
        return None


async def send_post(bot, chat_id, username, post):
    text = format_post(username, post)
    images = extract_images(post)

    translated_text = await translator.translate_async(text)

    if not images:
        await bot.send_message(chat_id=chat_id, text=translated_text)
        return

    caption = translated_text if len(translated_text) <= MAX_CAPTION_LENGTH else None

    try:
        if len(images) == 1:
            await bot.send_photo(chat_id=chat_id, photo=images[0], caption=caption)
        else:
            media = []
            for img in images:
                media.append(InputMediaPhoto(img))
            if caption is not None:
                media[0] = InputMediaPhoto(images[0], caption=caption)
            await bot.send_media_group(chat_id=chat_id, media=media)
    except BadRequest as e:
        logger.warning("FAILED TO SEND IMAGE FOR POST %s, SENDING TEXT ONLY: %s", str(post["key"]).upper(), str(e).upper())
        await bot.send_message(chat_id=chat_id, text=translated_text)
        return

    if caption is None:
        await bot.send_message(chat_id=chat_id, text=translated_text)


async def reply(update: Update, text, reply_markup=None):
    await update.effective_chat.send_message(text, reply_markup=reply_markup)


async def check_posts(context: ContextTypes.DEFAULT_TYPE):
    db = SqlCommand()

    try:
        rows = db.select_all()
    except Exception:
        logger.exception("FAILED TO READ USERNAMES FROM DATABASE")
        return

    if not rows:
        return

    for row in rows:
        username = row["x_username"]
        user_id = row["user_id"]

        posts = fetch_posts(username)
        if not posts:
            continue

        seen = parse_seen(row["seen_ids"])

        if seen:
            new_posts = find_new_posts(posts, seen)
            if new_posts:
                logger.info("FOUND %s NEW POSTS FROM @%s FOR USER %s", len(new_posts), username.upper(), user_id)
                failed = set()
                for index, post in enumerate(new_posts):
                    try:
                        await send_post(context.bot, user_id, username, post)
                    except Forbidden:
                        logger.warning("USER %s HAS BLOCKED THE BOT", user_id)
                        break
                    except BadRequest as e:
                        logger.warning("SKIPPED POST %s FOR USER %s: %s", str(post["key"]).upper(), user_id, str(e).upper())
                    except TelegramError as e:
                        logger.warning("FAILED SENDING TO USER %s, RETRYING NEXT CHECK: %s", user_id, str(e).upper())
                        for item in new_posts[index:]:
                            failed.add(item["key"])
                        break

                updated = merge_seen(posts, seen, failed)
                if updated != seen:
                    db.update_seen(row["id"], updated)
        else:
            updated = merge_seen(posts, seen)
            if updated != seen:
                db.update_seen(row["id"], updated)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "step" in context.user_data:
        del context.user_data["step"]

    user = update.effective_user
    auth = Auth(
        telegram_user_id=user.id,
        user_chat_id=update.effective_chat.id,
        username=user.username,
        first_name=user.first_name
    )

    if not auth.user_exists():
        auth.add_user()

    await reply(update, WELCOME_TEXT, MAIN_KEYBOARD)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "step" in context.user_data:
        del context.user_data["step"]
    await reply(update, WELCOME_TEXT, MAIN_KEYBOARD)


async def add_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["step"] = "addUsername"
    await reply(update, "PLEASE ENTER THE X/TWITTER USERNAME:")


async def my_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "step" in context.user_data:
        del context.user_data["step"]
    usernames = SqlCommand(update.effective_user.id).select_usernames()

    if not usernames:
        await reply(update, "YOU ARE NOT MONITORING ANY USERNAME YET.")
        return

    text_list = []
    for name in usernames:
        text_list.append(f"@{name}")

    await reply(update, "MONITORED USERNAMES:\n\n" + "\n".join(text_list))


async def remove_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "step" in context.user_data:
        del context.user_data["step"]
    usernames = SqlCommand(update.effective_user.id).select_usernames()

    if not usernames:
        await reply(update, "YOU ARE NOT MONITORING ANY USERNAME YET.")
        return

    keyboard = []
    for name in usernames:
        keyboard.append([InlineKeyboardButton(f"@{name}", callback_data=f"rm:{name}")])

    await reply(update, "SELECT A USERNAME TO REMOVE:", InlineKeyboardMarkup(keyboard))


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "addusername":
        await add_username(update, context)
    elif data == "removeusername":
        await remove_username(update, context)
    elif data == "myusernames":
        await my_usernames(update, context)
    elif data.startswith("rm:"):
        username = data[3:]
        removed = SqlCommand(update.effective_user.id).remove_username(username)
        if removed:
            text = f"USERNAME @{username} REMOVED."
        else:
            text = f"USERNAME @{username} IS NOT IN YOUR LIST."
        await query.edit_message_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") != "addUsername":
        await reply(update, "USE /addusername TO ADD A USERNAME OR /help FOR HELP.")
        return

    if "step" in context.user_data:
        del context.user_data["step"]

    username = normalize_username(update.effective_message.text)
    if not username:
        await reply(update, "INVALID USERNAME. SEND /addusername AND TRY AGAIN.")
        return

    db = SqlCommand(update.effective_user.id)

    if db.username_exists(username):
        await reply(update, f"USERNAME @{username} IS ALREADY IN YOUR LIST.")
        return

    await reply(update, f"CHECKING @{username} ...")

    posts = fetch_posts(username)
    if posts is None:
        await reply(update, f"COULD NOT LOAD POSTS FOR @{username}. CHECK USERNAME OR TRY AGAIN LATER.")
        return

    db.add_username(username, merge_seen(posts, []))
    await reply(update, f"USERNAME SUCCESSFULLY ADDED\nUSERNAME: @{username}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("AN UNEXPECTED ERROR OCCURRED", exc_info=context.error)

    if isinstance(update, Update) and update.effective_chat:
        try:
            await update.effective_chat.send_message("AN ERROR OCCURRED. PLEASE TRY AGAIN.")
        except TelegramError:
            pass


def main():
    if not API_TOKEN:
        raise ValueError("API_TOKEN IS NOT SET IN ENVIRONMENT VARIABLES")

    app = Application.builder().token(API_TOKEN).build()

    if app.job_queue is None:
        raise RuntimeError('JOBQUEUE IS MISSING, RUN: pip install "python-telegram-bot[job-queue]"')

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("addusername", add_username))
    app.add_handler(CommandHandler("removeusername", remove_username))
    app.add_handler(CommandHandler("myusernames", my_usernames))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_message)
    )
    app.add_error_handler(error_handler)

    app.job_queue.run_repeating(
        check_posts,
        interval=CHECK_INTERVAL,
        first=5,
        name="check_posts"
    )

    logger.info("BOT IS RUNNING, CHECKING EVERY %s SECONDS", CHECK_INTERVAL)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()