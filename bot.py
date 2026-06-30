import asyncio
import logging
import os
from typing import List

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# Load environment variables from .env (for local testing) or system env (for Render)
load_dotenv()

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 1. Read all bot tokens from environment variables
#    Variables should be named: BOT_TOKENS_1, BOT_TOKENS_2, ...
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
# 2. Build the inline keyboard menu (as seen in the screenshot)
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
# 3. Handlers for /start and button callbacks
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
# 4. Create a bot application for each token
# ----------------------------------------------------------------------
def create_bot_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    return app

# ----------------------------------------------------------------------
# 5. Run all bots concurrently – with graceful error handling
# ----------------------------------------------------------------------
async def run_bots() -> None:
    successful_apps: List[Application] = []

    # Initialize each bot (this validates the token)
    for i, token in enumerate(BOT_TOKENS, start=1):
        try:
            app = create_bot_app(token)
            await app.initialize()
            successful_apps.append(app)
            logger.info(f"✅ Bot #{i} initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Bot #{i} failed to initialize: {e}. Skipping.")

    if not successful_apps:
        logger.error("No bots could be initialized. Exiting.")
        return

    # Start each bot (polling in the background)
    for app in successful_apps:
        try:
            await app.start()
            username = (await app.bot.get_me()).username
            logger.info(f"✅ Bot @{username} started polling.")
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}. Removing from list.")
            successful_apps.remove(app)

    if not successful_apps:
        logger.error("No bots could be started. Exiting.")
        return

    logger.info(f"All {len(successful_apps)} bot(s) are now running. Press Ctrl+C to stop.")

    # Keep the event loop alive until interrupted
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()   # waits forever
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("Shutdown signal received. Stopping bots...")
    finally:
        for app in successful_apps:
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
