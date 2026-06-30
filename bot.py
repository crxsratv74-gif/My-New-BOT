import asyncio
import logging
import os
from typing import List

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 1. Read all bot tokens from environment (BOT_TOKENS_1, BOT_TOKENS_2, ...)
# ----------------------------------------------------------------------
BOT_TOKENS = []
for key, value in os.environ.items():
    if key.startswith("BOT_TOKENS_") and value.strip():
        BOT_TOKENS.append(value.strip())

if not BOT_TOKENS:
    raise ValueError(
        "No BOT_TOKENS_* found in environment. "
        "Please add at least one token like BOT_TOKENS_1=your_token"
    )

logger.info(f"Loaded {len(BOT_TOKENS)} bot token(s).")

# ----------------------------------------------------------------------
# 2. Build the inline keyboard menu
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

# ----------------------------------------------------------------------
# 3. Handlers
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# 4. Create a bot application
# ----------------------------------------------------------------------
def create_bot_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    return app

# ----------------------------------------------------------------------
# 5. Run all bots – FIXED (no explicit initialize)
# ----------------------------------------------------------------------
async def run_bots() -> None:
    running_apps: List[Application] = []

    for i, token in enumerate(BOT_TOKENS, start=1):
        try:
            app = create_bot_app(token)
            # Start the bot – this internally calls initialize() and starts polling
            await app.start()
            # Verify by getting the bot's username
            username = (await app.bot.get_me()).username
            logger.info(f"✅ Bot #{i} (@{username}) started successfully.")
            running_apps.append(app)
        except Exception as e:
            logger.error(f"❌ Bot #{i} failed to start: {e}. Skipping.")

    if not running_apps:
        logger.error("No bots could be started. Exiting.")
        return

    logger.info(f"All {len(running_apps)} bot(s) are now running. Press Ctrl+C to stop.")

    # Keep the event loop alive
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("Shutdown signal received. Stopping bots...")
    finally:
        for app in running_apps:
            await app.stop()
            await app.shutdown()
        logger.info("All bots stopped.")

# ----------------------------------------------------------------------
# 6. Entry point
# ----------------------------------------------------------------------
def main() -> None:
    try:
        asyncio.run(run_bots())
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")

if __name__ == "__main__":
    main()
