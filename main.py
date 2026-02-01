from bot import start, help_command, verse
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scheduler import daily_verse
import config, asyncio, logging
import nest_asyncio

nest_asyncio.apply()  # Fix event loop already running

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("verse", verse))
    # TODO: add remaining commands

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(daily_verse(app.bot)), "cron", hour=8, minute=0)
    scheduler.start()
    logger.info("Scheduler started.")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
