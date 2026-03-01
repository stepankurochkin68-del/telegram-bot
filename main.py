import logging
from typing import Dict, Any

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5068182519
CHANNEL_LINK = "https://t.me/+iU0AU04JtTdmMWEy"

# ===== РЕКВИЗИТЫ (копируются) =====
PAY_TEXT = (
    "💳 Реквизиты для оплаты:\n\n"
    "📱 Телефон: `+79680379906`\n"
    "💳 Карта: `2200701926416063`\n"
    "👤 Получатель: Степан К.\n"
    "🏦 Банк: Т-Банк\n\n"
    "После оплаты нажми «✅ Оплатил» и отправь скрин."
)

pending: Dict[int, Dict[str, Any]] = {}
approved: Dict[int, bool] = {}

MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("✅ Оплатил")],
    ],
    resize_keyboard=True,
)

def admin_kb(user_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve:{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{user_id}")
        ]
    ])

def channel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Войти в канал", url=CHANNEL_LINK)]
    ])

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет 👋\n\n" + PAY_TEXT,
        parse_mode="Markdown",
        reply_markup=MENU,
    )

# ===== TEXT =====
async def text_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if text == "✅ Оплатил":
        pending[user_id] = {"step": "wait_photo"}
        await update.message.reply_text("📸 Отправь скрин оплаты (ФОТО)")
        return

    if user_id not in pending:
        return

    step = pending[user_id]["step"]

    if step == "wait_photo":
        await update.message.reply_text("❌ Нужно фото, а не текст")
        return

    if step == "wait_nick":
        pending[user_id]["nick"] = text

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=pending[user_id]["photo"],
            caption=f"Новая заявка\nНик: {text}\nID: {user_id}",
            reply_markup=admin_kb(user_id)
        )

        await update.message.reply_text("Заявка отправлена админу")

# ===== PHOTO =====
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in pending:
        return

    if pending[user_id]["step"] != "wait_photo":
        return

    pending[user_id]["photo"] = update.message.photo[-1].file_id
    pending[user_id]["step"] = "wait_nick"

    await update.message.reply_text("✅ Фото получил. Теперь напиши ник")

# ===== ADMIN =====
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    action, user_id = query.data.split(":")
    user_id = int(user_id)

    if action == "approve":
        approved[user_id] = True
        pending.pop(user_id, None)

        await context.bot.send_message(
            chat_id=user_id,
            text="🚀 Доступ открыт.\n\nНажми кнопку ниже:",
            reply_markup=channel_kb()
        )

        await query.edit_message_caption("ОДОБРЕНО")

    elif action == "reject":
        pending.pop(user_id, None)

        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Отклонено"
        )

        await query.edit_message_caption("ОТКЛОНЕНО")

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_actions))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_flow))

    app.run_polling()

if __name__ == "__main__":
    main()
