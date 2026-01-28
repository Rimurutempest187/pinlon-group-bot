import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TEAM_FILE = "team.json"

def load_team():
    if not os.path.exists(TEAM_FILE):
        return {}
    with open(TEAM_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- /ginfo ----------
async def ginfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    team = load_team()
    if not team:
        await update.message.reply_text("❌ No team data found.")
        return

    group_name = team.get("group_name", "Unknown Team")
    group_photo = team.get("group_photo")
    members = team.get("members", [])

    # Member buttons
    buttons = []
    for m in members:
        buttons.append([InlineKeyboardButton(m["name"], callback_data=f"member_{m['id']}")])

    reply_markup = InlineKeyboardMarkup(buttons)

    if group_photo:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=group_photo,
            caption=f"👥 {group_name}\nMembers: {len(members)}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"👥 {group_name}\nMembers: {len(members)}",
            reply_markup=reply_markup
        )

# ---------- Member Info ----------
# ---------- Member Info ----------
async def member_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    member_id = int(query.data.replace("member_", ""))
    team = load_team()
    members = team.get("members", [])
    member = next((m for m in members if m["id"] == member_id), None)

    if not member:
        await query.edit_message_text("❌ Member not found.")
        return

    text = (
        f"👤 {member['name']}\n"
        f"📞 Phone: {member['phone']}\n"
        f"🏠 Address: {member['address']}"
    )

    # Show profile photo + info
    if member.get("pfp"):
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=member["pfp"],
            caption=text
        )
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


# ---------- Main ----------
def main():
    token = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("ginfo", ginfo))
    app.add_handler(CallbackQueryHandler(member_info, pattern="^member_"))

    app.run_polling()

if __name__ == "__main__":
    main()

