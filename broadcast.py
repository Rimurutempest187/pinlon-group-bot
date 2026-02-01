from config import ADMIN_IDS
from telegram import Update
from telegram.ext import ContextTypes

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to broadcast messages.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    from main import get_all_users

    users = get_all_users()
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except:
            pass

    await update.message.reply_text("Broadcast sent!")
