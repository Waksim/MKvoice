# ============================= FILE: handlers/private_chat_handlers.py =============================
"""
This file includes handlers for private chats:
- /start, /help, /change_lang, /settings
- Setting chunk size (with FSM for numeric input)
- Setting TTS speed (with inline buttons)
- Other existing logic for text/URL/document processing
"""

import asyncio
import json
import os
from collections import deque
from pathlib import Path
from typing import Callable

import chardet
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, WebAppInfo)
from loguru import logger

from config import (ADMIN_ID, AUDIO_FOLDER, AVAILABLE_LANGUAGES, LOG_FILE,
                    MAX_MESSAGE_LENGTH, WEBAPP_URL)
from filters.chat_type import ChatTypeFilter
from states import SettingsState
from utils.document_parsers import parse_docx, parse_epub, parse_fb2
from utils.i18n import get_translator, get_user_lang, set_user_lang
from utils.text_extraction import (extract_text_from_url_dynamic,
                                   extract_text_from_url_static)
from utils.text_to_speech import synthesize_text_to_audio_edge
from utils.user_settings import get_user_settings, save_user_chunk_size, save_user_speed

private_router = Router()
private_router.message.filter(ChatTypeFilter(chat_type=["private"]))


# ===================== Web App Handler (MUST BE FIRST) =====================

@private_router.message(F.web_app_data)
async def handle_web_app_data(message: Message, _: Callable) -> None:
    """
    Handles data received from the Telegram Web App.
    This handler MUST be registered before any generic text handlers.
    """
    user_id = message.from_user.id
    logger.info(f"User {user_id} sent data from Web App. Raw data: {message.web_app_data.data}")

    # --- Немедленно отвечаем пользователю, что данные получены ---
    await message.answer(_("Received your text. Starting synthesis..."))

    try:
        data = json.loads(message.web_app_data.data)
        text_to_speak = data.get("text")

        if not text_to_speak or not isinstance(text_to_speak, str) or not text_to_speak.strip():
            logger.warning(f"Invalid or empty text from TWA for user {user_id}: {data}")
            await message.answer(_("Received empty text from the web app. Please try again."))
            return

        logger.info(f"Successfully parsed text from TWA for user {user_id}. Length: {len(text_to_speak)}.")
        await synthesize_text_to_audio_edge(text_to_speak, str(user_id), message, logger, _)

    except json.JSONDecodeError:
        logger.error(f"JSONDecodeError from TWA for user {user_id}: {message.web_app_data.data}")
        await message.answer(_("Failed to parse data from the web app. The data format is incorrect."))
    except Exception as e:
        logger.error(f"Error processing TWA data for user {user_id}: {e}", exc_info=True)
        await message.answer(_("An unexpected error occurred: {error}").format(error=str(e)))


# ===================== Standard Command Handlers =====================

@private_router.message(Command('webapp'))
async def cmd_webapp(message: Message, _: Callable) -> None:
    """
    /webapp command handler. Sends a message with a button to open the TWA.
    """
    if not WEBAPP_URL:
        await message.answer(_("Web App is not configured. Please contact the administrator."))
        logger.error("WEBAPP_URL is not set in the environment variables.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_("Open Text Input App"),
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])
    await message.answer(
        _("Click the button below to open the web app for entering large texts."),
        reply_markup=keyboard
    )


@private_router.message(Command('start'))
async def cmd_start(message: Message, _: Callable):
    user_id = message.from_user.id
    logger.info(f"User {user_id} started the bot in private chat.")
    help_text = _(
        "👋 Hi! I can help you convert text to speech in various ways.\n\n"
        "🔹 <b>What I can do:</b>\n"
        "- Send me a text message to synthesize speech.\n"
        "- Send a link to a website to extract text and synthesize it.\n"
        "- Send a file (<code>.docx</code>, <code>.fb2</code>, <code>.epub</code>) to extract text and synthesize it.\n"
        "- Add me to a group chat and use the command <b>/vv help</b> to see how to work with me in groups.\n\n"
        "📄 <b>Available commands:</b>\n"
        "<b>/help</b> - Show help\n"
        "<b>/change_lang</b> - Change interface language\n"
        "<b>/settings</b> - Configure TTS options (chunk size, speed)\n"
        "<b>/webapp</b> - Open web interface for large texts\n\n"
        "❓ <b>Questions or suggestions?</b>\n"
        "Contact the bot administrator @maksenro.\n\n"
        "[ <a href=\"https://www.donationalerts.com/r/mkprod\">Support</a> | <a href=\"https://t.me/MKprodaction\">Group</a> ]"
    )
    await message.answer(help_text)


@private_router.message(Command('help'))
async def cmd_help(message: Message, _: Callable) -> None:
    """
    /help command handler in a private chat.
    Sends help info about available bot commands and usage.
    """
    help_text = _(
        "📖 <b>Available commands:</b>\n"
        "/start - Begin interaction with the bot\n"
        "/help - Show this message\n"
        "/change_lang - Change interface language\n"
        "/settings - Configure TTS options (chunk size, speed)\n"
        "/webapp - Open web interface for large texts\n"
        "\n"
        "🤖 <b>Bot capabilities:</b>\n"
        "- Send text messages, and the bot will synthesize them using text-to-speech.\n"
        "- Send documents in <code>.docx</code>, <code>.fb2</code>, <code>.epub</code> formats, "
        "and the bot will extract and synthesize them.\n"
        "- Send links to web pages, and the bot will extract and synthesize the text.\n\n"
        "📂 <b>Supported formats:</b>\n"
        "- Text messages: any text\n"
        "- Documents: <code>.docx</code>, <code>.fb2</code>, <code>.epub</code>\n"
        "- Links: HTTP/HTTPS\n\n"
        "⚙️ <b>Settings:</b>\n"
        "- Use <b>/change_lang</b> command to change the interface language.\n"
        "- Use <b>/settings</b> command to adjust chunk size and TTS speed.\n"
        "- The bot supports multiple languages: English, Russian, Ukrainian, Chinese.\n\n"
        "👥 <b>Use in groups:</b>\n"
        "- Add the bot to a group.\n"
        "- Grant it the following permissions:\n"
        "  • Read messages\n"
        "  • Send messages\n"
        "  • Manage messages\n\n"
        "- <b>Available commands in groups:</b>\n"
        "  • /vv <text> - Synthesize the provided text.\n"
        "  • /vv <link> - Extract text from the link and synthesize it.\n"
        "  • /vv (in reply to a message) - Synthesize text from the replied-to message.\n\n"
        "❓ <b>Questions or suggestions?</b>\n"
        "Contact the bot administrator @maksenro.\n\n"
        "[ <a href=\"https://www.donationalerts.com/r/mkprod\">Support</a> | <a href=\"https://t.me/MKprodaction\">Group</a> ]"
    )
    await message.answer(help_text)


# ===================== Settings Handlers ======================

@private_router.message(Command('settings'))
async def cmd_settings(message: Message, _: Callable) -> None:
    """
    /settings command handler in a private chat.
    Shows an inline keyboard to update user settings (chunk size or TTS speed).
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("Set chunk size"), callback_data="settings:set_chunk")],
        [InlineKeyboardButton(text=_("Set TTS speed"), callback_data="settings:set_speed")],
    ])
    await message.answer(_("Choose a setting to update:"), reply_markup=keyboard)


@private_router.callback_query(F.data == "settings:set_chunk")
async def cb_set_chunk_size(callback_query: CallbackQuery, _: Callable, state: FSMContext) -> None:
    """
    Inline button handler for "Set chunk size".
    Prompts the user to enter a number between 5000 and 80000.
    Moves user to FSM state: waiting_for_chunk_size.
    """
    await callback_query.message.answer(_("Please enter the chunk size (5,000 - 80,000):"))
    await state.set_state(SettingsState.waiting_for_chunk_size)
    await callback_query.answer()


@private_router.message(SettingsState.waiting_for_chunk_size, F.text)
async def handle_chunk_size_input(message: Message, _: Callable, state: FSMContext) -> None:
    """
    Handles user input for chunk size while in FSM state waiting_for_chunk_size.
    """
    try:
        chunk_val = int(message.text.strip())
        if 5000 <= chunk_val <= 80000:
            save_user_chunk_size(message.from_user.id, chunk_val)
            await message.answer(_("Chunk size updated to: {size}").format(size=chunk_val))
            await state.clear()
        else:
            await message.answer(_("Value out of range (5,000–80,000). Please try again."))
    except ValueError:
        await message.answer(_("Invalid number. Please try again."))


@private_router.callback_query(F.data == "settings:set_speed")
async def cb_set_speed(callback_query: CallbackQuery, _: Callable) -> None:
    """
    Inline button handler for "Set TTS speed".
    Shows a second inline keyboard with possible speed options.
    """
    speed_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="-50%", callback_data="speed:-50%")],
        [InlineKeyboardButton(text="-25%", callback_data="speed:-25%")],
        [InlineKeyboardButton(text="0%",   callback_data="speed:+0%")],
        [InlineKeyboardButton(text="+25%", callback_data="speed:+25%")],
        [InlineKeyboardButton(text="+50%", callback_data="speed:+50%")],
    ])
    await callback_query.message.answer(_("Choose desired TTS speed:"), reply_markup=speed_keyboard)
    await callback_query.answer()


@private_router.callback_query(F.data.startswith("speed:"))
async def cb_speed_value(callback_query: CallbackQuery, _: Callable) -> None:
    """
    Inline button handler for a specific speed value, e.g. speed:+25%.
    Saves the speed to DB and notifies the user.
    """
    speed_val = callback_query.data.split("speed:")[1]
    save_user_speed(callback_query.from_user.id, speed_val)

    await callback_query.message.answer(_("Speed updated to: {spd}").format(spd=speed_val))
    await callback_query.answer()


# ===================== Language change handlers ======================
@private_router.message(Command('change_lang'))
async def cmd_change_lang(message: Message, _: Callable) -> None:
    """
    Command /change_lang to show available languages via inline keyboard.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{lang_info['flag']} {lang_info['name']}",
                    callback_data=f"change_lang:{lang_code}"
                )
            ] for lang_code, lang_info in AVAILABLE_LANGUAGES.items()
        ]
    )
    logger.info(f"User {message.from_user.id} requested language change.")
    await message.reply(_("Please choose your language:"), reply_markup=keyboard)


@private_router.callback_query(F.data.startswith("change_lang:"))
async def process_change_lang(callback_query: CallbackQuery, _: Callable) -> None:
    lang_code = callback_query.data.split(":")[1]

    if lang_code not in AVAILABLE_LANGUAGES:
        await callback_query.answer(_("Unsupported language."), show_alert=True)
        logger.warning(f"User {callback_query.from_user.id} tried to set unsupported language: {lang_code}")
        return

    set_user_lang(callback_query.from_user.id, lang_code)
    translator = get_translator(lang_code)
    __ = translator.gettext

    await callback_query.answer()
    await callback_query.message.edit_reply_markup()
    await callback_query.message.reply(__("Language updated!"))
    logger.info(f"User {callback_query.from_user.id} updated language to {lang_code}.")


# ===================== Other handlers (Specific before Generic) ======================
@private_router.message(Command(commands=["s", "S", "ы", "Ы"]))
async def cmd_s(message: Message, _: Callable) -> None:
    """
    An admin-only command to retrieve the last lines of the log file.
    """
    if message.from_user.id != ADMIN_ID:
        logger.warning(f"Access denied for user {message.from_user.id} to command 's'.")
        await message.reply(_("Access denied."))
        return

    try:
        log_file = Path(LOG_FILE)
        if not log_file.exists():
            logger.error(f"Log file {LOG_FILE} does not exist.")
            await message.reply(_("Log file does not exist."))
            return

        with log_file.open('r', encoding='utf-8') as f:
            last_n_lines = deque(f, 15)
        last_lines = ''.join(last_n_lines)

        if not last_lines.strip():
            await message.reply(_("No log messages."))
            return

        # Splitting logic remains the same
        current_message = ""
        for line in last_lines.splitlines(keepends=True):
            if len(current_message) + len(line) > MAX_MESSAGE_LENGTH:
                await message.answer(f"<pre>{current_message}</pre>")
                current_message = line
            else:
                current_message += line
        if current_message:
            await message.answer(f"<pre>{current_message}</pre>")

        logger.info(f"Admin {message.from_user.id} retrieved last log lines.")

    except Exception as e:
        logger.error(f"Failed to read log file: {e}", exc_info=True)
        await message.reply(_("Failed to read log file: {error}").format(error=str(e)))


@private_router.message(F.text.regexp(r'^https?://'))
async def handle_url(message: Message, _: Callable) -> None:
    """
    Handles a URL in a private chat. Tries static extraction,
    then dynamic extraction, then synthesizes the extracted text.
    """
    url = message.text
    try:
        await message.answer(_("Received a link. Starting text extraction..."))
        text_page = await extract_text_from_url_static(url)
        if len(text_page) < 200:
            await message.answer(_("Static extraction yielded little text. Trying dynamic extraction..."))
            text_page = await extract_text_from_url_dynamic(url)
        if not text_page.strip():
            await message.reply(_("Could not extract text from the link."))
            logger.warning(f"User {message.from_user.id} sent URL but no text extracted: {url}")
            return

        await synthesize_text_to_audio_edge(text_page, str(message.from_user.id), message, logger, _)
        logger.info(f"Processed URL from user {message.from_user.id}: {url}")

    except Exception as e:
        await message.reply(_("Failed to process URL: {error}").format(error=str(e)))
        logger.error(f"Failed to process URL from user {message.from_user.id}: {url} | Error: {e}", exc_info=True)


@private_router.message(F.document)
async def handle_file(message: Message, bot: Bot, _: Callable) -> None:
    """
    Handles documents in private chat. Accepts .docx, .fb2, .epub, or text with encoding detection.
    Extracts text and synthesizes it.
    """
    if not message.document:
        return

    if message.document.file_size > 20 * 1024 * 1024:
        await message.reply(_("File is too large (max 20 MB)."))
        logger.warning(f"User {message.from_user.id} sent a file that is too large: {message.document.file_name}")
        return

    file_extension = os.path.splitext(message.document.file_name)[1].lower()
    unique_filename = f"{message.from_user.id}_{message.document.file_unique_id}{file_extension}"
    local_file_path = os.path.join(AUDIO_FOLDER, unique_filename)

    try:
        await message.answer(_("Received file `{file_name}`. Downloading...").format(file_name=message.document.file_name), parse_mode="MarkdownV2")
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, destination=local_file_path)
        logger.info(f"Downloaded file from user {message.from_user.id}: {unique_filename}")

        with open(local_file_path, 'rb') as f:
            raw_data = f.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']
        logger.info(f"Detected encoding for {unique_filename}: {encoding} with confidence {detected['confidence']}")

        text = ""
        if file_extension == ".docx":
            text = parse_docx(local_file_path)
        elif file_extension == ".fb2":
            text = parse_fb2(local_file_path)
        elif file_extension == ".epub":
            text = parse_epub(local_file_path)
        else:
            encoding = encoding or 'utf-8'
            with open(local_file_path, "r", encoding=encoding, errors='replace') as txt_f:
                text = txt_f.read()

        if not text.strip():
            await message.reply(_("Could not extract text from the document."))
            logger.warning(f"No text extracted from {unique_filename} by user {message.from_user.id}.")
            return

        await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger, _)
        logger.info(f"Synthesized document for user {message.from_user.id}: {unique_filename}")

    except Exception as e:
        logger.error(f"Failed to process document from user {message.from_user.id}: {e}", exc_info=True)
        await message.reply(_("Failed to process document: {error}").format(error=str(e)))
    finally:
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            logger.info(f"Removed temporary file {local_file_path}")


# ===================== Generic Text Handler (MUST BE LAST) =====================

@private_router.message(F.text, F.web_app_data.is_(None))
async def handle_text(message: Message, _: Callable) -> None:
    """
    Handles any plain text sent by the user. Synthesizes the text to speech.
    This handler explicitly IGNORES messages that have web_app_data to prevent conflicts.
    It MUST be one of the last message handlers registered in this router.
    """
    text = message.text
    if not text or not text.strip():
        # This check is good practice to prevent reacting to empty messages
        return

    await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger, _)
    logger.info(f"Voiced text from user {message.from_user.id}: {text[:100]}...")