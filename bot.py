import asyncio
import logging
import os
from typing import List

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 1. Read tokens from environment (BOT_TOKENS_1, BOT_TOKENS_2, ...)
# ----------------------------------------------------------------------
BOT_TOKENS = []
for key, value in os.environ.items():
    if key.startswith("BOT_TOKENS_") and value.strip():
        BOT_TOKENS.append(value.strip())

if not BOT_TOKENS:
    raise ValueError("No BOT_TOKENS_* found in environment. Add at least one.")

logger.info(f"Loaded {len(BOT_TOKENS)} bot token(s).")

# ----------------------------------------------------------------------
# 2. Menu and handlers (unchanged)
# ----------------------------------------------------------------------
def build_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🔹 Trial v4.6", callback_data="trial")],
        [InlineKeyboardButton("🔹 Premium License", callback_data="premium")],
        [InlineKeyboardButton("🔹 Tools Download", callback_data="tools")],
        [InlineKeyboardButton("🔹 Setup Guide", callback_data="setup")],
        [InlineKeyboardButton("🔹 My Stats", callback_data="stats")],
        [InlineKeyboardButton("🔹 Support", callback_data="support")],
        [InlineKeyboardButton("🌐 Language", callback_data="language")],
    ]
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        "👋 *Welcome Back, Legend — Ready to dominate?*\n\n"
        "Select an option below to continue."
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=build_menu_keyboard(),
        parse_mode="Markdown",
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    responses = {
        "trial": "⚡ *Trial v4.6*\nYou are currently using the trial version. Upgrade to Premium for full features.",
        "premium": "💎 *Premium License*\nPurchase a premium license to unlock all tools and receive priority support.",
        "tools": "🛠️ *Tools Download*\nDownload the latest tools from our official repository:\n[Link to tools]",
        "setup": "📖 *Setup Guide*\nFollow the step-by-step guide to get started:\n[Link to guide]",
        "stats": "📊 *My Stats*\nYour usage statistics:\n- Total requests: 42\n- Active sessions: 3\n- Trial days left: 12",
        "support": "💬 *Support*\nContact our support team:\nEmail: support@devil.com\nTelegram: @DevilSupport",
        "language": "🌐 *Language*\nChoose your language:\n🇬🇧 English\n🇪🇸 Spanish\n🇫🇷 French\n(More coming soon)",
    }
    text = responses.get(data, "Unknown option.")
    await query.edit_message_text(
        text,
        reply_markup=build_menu_keyboard(),
        parse_mode="Markdown",
    )

def create_bot_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    return app

# ----------------------------------------------------------------------
# 3. Run all bots using run_polling() – works correctly with asyncio
# ----------------------------------------------------------------------
async def run_bots() -> None:
    apps: List[Application] = []
    for i, token in enumerate(BOT_TOKENS, start=1):
        try:
            app = create_bot_app(token)
            apps.append(app)
            logger.info(f"✅ Bot #{i} created.")
        except Exception as e:
            logger.error(f"❌ Bot #{i} creation failed: {e}")

    if not apps:
        logger.error("No bots to run. Exiting.")
        return

    # Start each bot's polling loop concurrently
    # run_polling() will handle initialization, start, and cleanup
    tasks = []
    for app in apps:
        # We use return_exceptions so one failure doesn't stop others
        tasks.append(asyncio.create_task(app.run_polling()))

    logger.info(f"Starting {len(tasks)} bot(s). Press Ctrl+C to stop.")
    try:
        # Wait for all tasks, but don't raise on first exception
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Bot #{i+1} stopped with error: {result}")
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received. Stopping bots...")
    finally:
        # Cleanly stop all apps
        for app in apps:
            await app.stop()
            await app.shutdown()
        logger.info("All bots stopped.")

# ----------------------------------------------------------------------
# 4. Entry point
# ----------------------------------------------------------------------
def main() -> None:
    try:
        asyncio.run(run_bots())
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")

if __name__ == "__main__":
    main()
