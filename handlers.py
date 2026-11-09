import asyncio
import logging
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from database import clear_history, get_history, save_exchange
from document_utils import prepare_document
from gemini_service import GeminiService

logger = logging.getLogger(__name__)

START_TEXT = (
    "مرحبًا بك! أنا مساعدك الذكي للدراسة والإجابة عن الأسئلة.\n\n"
    "أرسل سؤالك نصًا، أو أرفق صورة/مستندًا وسأساعدك في فهمه.\n"
    "استخدم /help لعرض التعليمات، و /clear لمسح سجل محادثتك."
)
HELP_TEXT = (
    "طريقة الاستخدام:\n"
    "• أرسل سؤالًا نصيًا للحصول على إجابة وشرح.\n"
    "• أرسل صورة أو ملف PDF لتحليله.\n"
    "• الملفات النصية المدعومة: TXT وMD وCSV وJSON.\n"
    "• المستندات المدعومة: DOCX وXLSX.\n"
    "• الحد الأقصى لحجم الملف يُضبط عبر MAX_FILE_SIZE_MB.\n\n"
    "الأوامر:\n/start — بدء الاستخدام\n/help — عرض المساعدة\n/clear — مسح سجل المحادثة"
)


def _split_message(text: str, limit: int = 4000) -> list[str]:
    chunks = []
    remaining = text.strip()
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n", 0, limit)
        if split_at < limit // 2:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at < limit // 2:
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    return chunks or ["لم أتمكن من إنشاء إجابة."]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(START_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(HELP_TEXT)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return
    settings = context.application.bot_data["settings"]
    await asyncio.to_thread(clear_history, settings.database_path, chat.id, user.id)
    await message.reply_text("تم مسح سجل محادثتك.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return

    user_text = (message.text or message.caption or "").strip()
    attachment = None
    mime_type = None
    extracted_text = None
    filename = ""

    if message.photo:
        photo = await message.photo[-1].get_file()
        attachment = bytes(await photo.download_as_bytearray())
        mime_type = "image/jpeg"
        filename = "photo.jpg"
    elif message.document:
        document = message.document
        settings = context.application.bot_data["settings"]
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if document.file_size and document.file_size > max_bytes:
            await message.reply_text(f"حجم الملف يتجاوز الحد المسموح ({settings.max_file_size_mb} MB).")
            return
        file = await document.get_file()
        data = bytes(await file.download_as_bytearray())
        if len(data) > max_bytes:
            await message.reply_text(f"حجم الملف يتجاوز الحد المسموح ({settings.max_file_size_mb} MB).")
            return
        filename = document.file_name or "document"
        try:
            attachment, mime_type, extracted_text = prepare_document(
                filename, document.mime_type or "application/octet-stream", data
            )
        except (ValueError, Exception) as error:
            if isinstance(error, ValueError):
                await message.reply_text(str(error))
                return
            logger.exception("Could not read uploaded document")
            await message.reply_text("تعذر قراءة هذا الملف. تحقق من سلامته ثم أعد إرساله.")
            return

    if not user_text and not attachment and not extracted_text:
        await message.reply_text("أرسل سؤالًا نصيًا أو أرفق صورة/مستندًا مدعومًا.")
        return

    status = await message.reply_text("⏳ جارٍ إعداد إجابتك...")
    settings = context.application.bot_data["settings"]
    service: GeminiService = context.application.bot_data["gemini"]
    try:
        history = await asyncio.to_thread(
            get_history,
            settings.database_path,
            chat.id,
            user.id,
            settings.history_messages,
        )
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        answer = await asyncio.to_thread(
            service.answer,
            user_text,
            history,
            attachment,
            mime_type,
            extracted_text,
        )
        await asyncio.to_thread(
            save_exchange,
            settings.database_path,
            chat.id,
            user.id,
            user_text or f"تحليل الملف: {filename}",
            answer,
        )
        chunks = _split_message(answer)
        await status.edit_text(chunks[0])
        for chunk in chunks[1:]:
            await message.reply_text(chunk)
    except Exception:
        logger.exception("Failed to process a Telegram message")
        await status.edit_text("عذرًا، حدث خطأ أثناء معالجة طلبك. حاول مرة أخرى بعد قليل.")


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(
        MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, handle_message)
    )
