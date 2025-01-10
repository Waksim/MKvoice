# ============================= FILE: handlers/private_chat_handlers.py =============================
"""
This file includes handlers for private chats:
- /start, /help, /change_lang, /settings
- Setting chunk size (with FSM for numeric input)
- Setting TTS speed (with inline buttons)
- Other existing logic for text/URL/document processing
"""

import asyncio
import os
import chardet
import sqlite3
from collections import deque
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from loguru import logger


from filters.chat_type import ChatTypeFilter
from utils.i18n import get_translator, get_user_lang, set_user_lang
from utils.text_extraction import extract_text_from_url_static, extract_text_from_url_dynamic
from utils.text_to_speech import synthesize_text_to_audio_edge
from utils.document_parsers import parse_docx, parse_fb2, parse_epub
from utils.user_settings import get_user_settings, save_user_chunk_size, save_user_speed
from states import SettingsState

from config import AUDIO_FOLDER, LOG_FILE, ADMIN_ID, AVAILABLE_LANGUAGES, MAX_MESSAGE_LENGTH, TOKEN
from project_structure.paths import DATABASE_PATH

private_router = Router()
private_router.message.filter(ChatTypeFilter(chat_type=["private"]))


@private_router.message(Command('start'))
async def cmd_start(message: Message, _: callable):
    """
    /start command handler in a private chat.
    Sends a greeting and initial help information.
    """
    user_id = message.from_user.id
    lang_code = get_user_lang(user_id)
    translator = get_translator(lang_code)
    __ = translator.gettext

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
        "<b>/change_lang</b> - Change interface language\n\n"
        "❓ <b>Questions or suggestions?</b>\n"
        "Contact the bot administrator @maksenro.\n\n"
        "[ <a href=\"https://www.donationalerts.com/r/mkprod\">Support</a> | <a href=\"https://t.me/MKprodaction\">Group</a> ]"
    )
    await message.answer(help_text, parse_mode='HTML')


@private_router.message(Command('help'))
async def cmd_help(message: Message, _: callable):
    """
    /help command handler in a private chat.
    Sends help info about available bot commands and usage.
    """
    help_text = _(
        "📖 <b>Available commands:</b>\n"
        "/start - Begin interaction with the bot\n"
        "/help - Show this message\n"
        "/change_lang - Change interface language\n"
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
        "- The bot supports multiple languages: English, Russian, Ukrainian, Chinese.\n\n"
        "👥 <b>Use in groups:</b>\n"
        "- Add the bot to a group.\n"
        "- Grant it the following permissions:\n"
        "  • Read messages\n"
        "  • Send messages\n"
        "  • Manage messages\n\n"
        "- <b>Available commands in groups:</b>\n"
        # ВАЖНО: заменяем <text> и <link> на &lt;text&gt; и &lt;link&gt;:
        "  • /vv &lt;text&gt; - Synthesize the provided text.\n"
        "  • /vv &lt;link&gt; - Extract text from the link and synthesize it.\n"
        "  • /vv (in reply to a message) - Synthesize text from the replied-to message.\n\n"
        "❓ <b>Questions or suggestions?</b>\n"
        "Contact the bot administrator @maksenro.\n\n"
        "[ <a href=\"https://www.donationalerts.com/r/mkprod\">Support</a> | <a href=\"https://t.me/MKprodaction\">Group</a> ]"
    )
    await message.answer(help_text, parse_mode='HTML')


@private_router.message(Command('settings'))
async def cmd_settings(message: Message, _: callable):
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
async def cb_set_chunk_size(callback_query: CallbackQuery, _: callable, state: FSMContext):
    """
    Inline button handler for "Set chunk size".
    Prompts the user to enter a number between 5000 and 80000.
    Moves user to FSM state: waiting_for_chunk_size.
    """
    await callback_query.message.answer(_("Please enter the chunk size (5,000 - 80,000):"))
    await state.set_state(SettingsState.waiting_for_chunk_size)
    await callback_query.answer()


@private_router.message(SettingsState.waiting_for_chunk_size, F.text)
async def handle_chunk_size_input(message: Message, _: callable, state: FSMContext):
    """
    Handles user input for chunk size while in FSM state waiting_for_chunk_size.
    """
    try:
        chunk_val = int(message.text.strip())
        if 5000 <= chunk_val <= 80000:
            # Save to DB
            save_user_chunk_size(message.from_user.id, chunk_val)
            await message.answer(_("Chunk size updated to: {size}").format(size=chunk_val))
            await state.clear()
        else:
            await message.answer(_("Value out of range (5,000–80,000). Please try again."))
    except ValueError:
        await message.answer(_("Invalid number. Please try again."))


@private_router.callback_query(F.data == "settings:set_speed")
async def cb_set_speed(callback_query: CallbackQuery, _: callable):
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
async def cb_speed_value(callback_query: CallbackQuery, _: callable):
    """
    Inline button handler for a specific speed value, e.g. speed:+25%.
    Saves the speed to DB and notifies the user.
    """
    speed_val = callback_query.data.split("speed:")[1]  # e.g. "+25%"
    save_user_speed(callback_query.from_user.id, speed_val)

    await callback_query.message.answer(_("Speed updated to: {spd}").format(spd=speed_val))
    await callback_query.answer()


# ===================== Existing language change handlers ======================
@private_router.message(Command('change_lang'))
async def cmd_change_lang(message: Message, _: callable):
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
async def process_change_lang(callback_query: CallbackQuery, _: callable):
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
    await callback_query.message.reply(_("Language updated!"))
    logger.info(f"User {callback_query.from_user.id} updated language to {lang_code}.")


@private_router.message(Command(commands=["s", "S", "ы", "Ы"]))
async def cmd_s(message: Message, _: callable):
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

        messages_list = []
        current_message = ""
        for line in last_lines.splitlines(keepends=True):
            if len(current_message) + len(line) > MAX_MESSAGE_LENGTH:
                messages_list.append(current_message)
                current_message = line
            else:
                current_message += line
        if current_message:
            messages_list.append(current_message)

        for msg in messages_list:
            await message.reply(_("📝 Last log lines:\n") + msg, parse_mode='HTML')
            await asyncio.sleep(0.1)
        logger.info(f"Admin {message.from_user.id} retrieved last log lines.")

    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        await message.reply(_("Failed to read log file: {error}").format(error=str(e)))


@private_router.message(F.text.regexp(r'^https?://'))
async def handle_url(message: Message, _: callable):
    """
    Handles a URL in a private chat. Tries static extraction,
    then dynamic extraction, then synthesizes the extracted text.
    """
    url = message.text
    try:
        text_page = await extract_text_from_url_static(url)
        if len(text_page) < 200:
            text_page = await extract_text_from_url_dynamic(url)
        if not text_page.strip():
            await message.reply(_("Could not extract text."))
            logger.warning(f"User {message.from_user.id} sent URL but no text extracted.")
            return

        await synthesize_text_to_audio_edge(
            text_page,
            str(message.from_user.id),
            message,
            logger,
            _
        )
        logger.info(f"Processed URL from user {message.from_user.id}: {url}")

    except Exception as e:
        await message.reply(_("Failed to process URL: {error}").format(error=str(e)))
        logger.error(f"Failed to process URL from user {message.from_user.id}: {url} | Error: {e}")


@private_router.message(F.text)
async def handle_text(message: Message, _: callable):
    """
    Handles any plain text sent by the user. Synthesizes the text to speech.
    """
    text = message.text
    if not text.strip():
        await message.reply(_("Empty text."))
        logger.warning(f"User {message.from_user.id} sent empty text.")
        return

    await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger, _)
    logger.info(f"Voiced text from user {message.from_user.id}: {text}")


@private_router.message(F.document)
async def handle_file(message: Message, _: callable):
    """
    Handles documents in private chat. Accepts .docx, .fb2, .epub, or text with encoding detection.
    Extracts text and synthesizes it.
    """

    bot = Bot(token=TOKEN)

    if message.document.file_size > 20 * 1024 * 1024:
        await message.reply(_("File is too large (max 20 MB)."))
        logger.warning(f"User {message.from_user.id} sent a file that is too large: {message.document.file_name}")
        return

    file_extension = os.path.splitext(message.document.file_name)[1].lower()
    local_file_path = os.path.join(AUDIO_FOLDER, message.document.file_name)

    try:
        # Correct approach in Aiogram 3.x
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, local_file_path)
        logger.info(f"Downloaded file from user {message.from_user.id}: {message.document.file_name}")

        # Detect encoding
        with open(local_file_path, 'rb') as f:
            raw_data = f.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']
        confidence = detected['confidence']
        logger.info(f"Detected encoding for {message.document.file_name}: {encoding} with confidence {confidence}")

        # Extract text
        if file_extension == ".docx":
            text = parse_docx(local_file_path)
        elif file_extension == ".fb2":
            text = parse_fb2(local_file_path)
        elif file_extension == ".epub":
            text = parse_epub(local_file_path)
        else:
            if encoding is None:
                encoding = 'utf-8'
            with open(local_file_path, "r", encoding=encoding, errors='replace') as txt_f:
                text = txt_f.read()

        # Remove file from local storage
        os.remove(local_file_path)
        logger.info(f"Processed and removed file {local_file_path}")

        if not text.strip():
            await message.reply(_("Could not extract text from the document."))
            logger.warning(f"No text extracted from document {message.document.file_name} by user {message.from_user.id}.")
            return

        # Synthesize text
        await synthesize_text_to_audio_edge(text, str(message.from_user.id), message, logger, _)
        logger.info(f"Synthesized document for user {message.from_user.id}: {message.document.file_name}")

    except Exception as e:
        logger.error(f"Failed to process document from user {message.from_user.id}: {e}")
        await message.reply(_("Failed to process document: {error}").format(error=str(e)))
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            logger.info(f"Removed corrupted file {local_file_path}")