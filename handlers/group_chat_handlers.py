# ============================= FILE: handlers/group_chat_handlers.py =============================
import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from filters.chat_type import ChatTypeFilter
from utils.text_extraction import extract_text_from_url_static, extract_text_from_url_dynamic
from utils.text_to_speech import synthesize_text_to_audio_edge

from config import AVAILABLE_LANGUAGES, MAX_MESSAGE_LENGTH

import chardet  # We might need this for group file handling if implemented.

# Create a router for group chats
group_router = Router()
group_router.message.filter(ChatTypeFilter(chat_type=["group", "supergroup"]))

@group_router.message(F.text.regexp(r'^\/vv\s+(help|h)\s*$'))
async def cmd_vv_help_in_group(message: Message, _: callable):
    """
    Sends usage help for the /vv command in group chats.
    """
    help_text = _(
        "📖 <b>Help for /vv command:</b>\n\n"
        "🔹 <b>/vv &lt;text&gt;</b> - Synthesize the provided text.\n"
        "🔹 <b>/vv &lt;link&gt;</b> - Extract text from the link and synthesize it.\n"
        "🔹 <b>/vv</b> (in reply to a message) - Synthesize text from the replied-to message.\n"
        "🔹 <b>/vv help</b> or <b>/vv h</b> - Shows this help.\n\n"
        "📂 <b>Supported formats:</b>\n"
        "- Text: any text\n"
        "- Links: HTTP/HTTPS\n\n"
        "⚙️ <b>Settings:</b>\n"
        "- The bot supports multiple languages: English, Russian, Ukrainian, Chinese.\n\n"
        "❓ <b>Questions or suggestions?</b>\n"
        "Contact the bot administrator @maksenro.\n\n"
        "[ @MKttsBOT | <a href=\"https://www.donationalerts.com/r/mkprod\">Support</a> | <a href=\"https://t.me/MKprodaction\">Group</a> ]"
    )
    logger.info(f"Group {message.chat.id} requested /vv help.")
    await message.reply(help_text, parse_mode='HTML')

@group_router.message(F.text.regexp(r'^\/vv(?:\s+.+)?$'))
async def cmd_vv_in_group(message: Message, _: callable):
    """
    Handles the /vv command in group chats. Either synthesizes text directly,
    or extracts from a provided link, or uses the text from the replied-to message.
    """
    if message.reply_to_message:
        text_to_speak = message.reply_to_message.text or message.reply_to_message.caption or ""
        if not text_to_speak.strip():
            await message.reply(_("No text to synthesize."))
            logger.warning(f"Group {message.chat.id} sent /vv command but no text was found in the replied message.")
            return
    else:
        splitted = message.text.split(' ', maxsplit=1)
        if len(splitted) > 1:
            text_to_speak = splitted[1].strip()
        else:
            await message.reply(_("Please provide text after /vv or reply to a message."))
            logger.warning(f"Group {message.chat.id} sent /vv command without additional text or a reply.")
            return

    if text_to_speak.startswith("http://") or text_to_speak.startswith("https://"):
        try:
            text_page = await extract_text_from_url_static(text_to_speak)
            if len(text_page) < 200:
                text_page = await extract_text_from_url_dynamic(text_to_speak)
            if not text_page.strip():
                await message.reply(_("Could not extract text."))
                logger.warning(f"Group {message.chat.id} provided a URL but no text was extracted.")
                return

            await synthesize_text_to_audio_edge(
                text_page,
                str(message.from_user.id),
                message,
                logger,
                _
            )
            logger.info(f"Group {message.chat.id} provided URL to synthesize: {text_to_speak}")

        except Exception as e:
            await message.reply(_("Failed to process link: {error}").format(error=str(e)))
            logger.error(f"Failed to process URL from group {message.chat.id}: {text_to_speak} | Error: {e}")
    else:
        if not text_to_speak.strip():
            await message.reply(_("Empty text."))
            logger.warning(f"Group {message.chat.id} sent /vv command with empty text.")
            return

        await synthesize_text_to_audio_edge(
            text_to_speak,
            str(message.from_user.id),
            message,
            logger,
            _
        )
        logger.info(f"Group {message.chat.id} provided text to synthesize: {text_to_speak}")