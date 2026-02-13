import os
import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from motor.motor_asyncio import AsyncIOMotorClient

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

MONGO_URI = os.environ.get("DATABASE_URI")
DATABASE_NAME = os.environ.get("DATABASE_NAME")

BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL"))
GROUP_ID = int(os.environ.get("GROUP_ID"))

bot = Client("autofilter", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo[DATABASE_NAME]
files = db.files

print("Mongo Connected")

# START
@bot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    await message.reply_text("🎬 স্বাগতম!\n👉 Group e movie search korun")

# INDEX
@bot.on_message(filters.channel & filters.chat(BIN_CHANNEL))
async def index_files(client, message):
    if message.document or message.video:
        file = message.document or message.video
        
        data = {
            "file_name": file.file_name.lower(),
            "file_id": file.file_id
        }

        await files.update_one(
            {"file_id": file.file_id},
            {"$set": data},
            upsert=True
        )

# SEARCH
@bot.on_message(filters.group & filters.chat(GROUP_ID) & filters.text)
async def search(client, message):
    query = message.text.lower()
    results = files.find({"file_name": {"$regex": query}}).limit(10)

    buttons = []
    async for r in results:
        buttons.append([
            InlineKeyboardButton(
                r["file_name"][:40],
                callback_data=f"file#{r['file_id']}"
            )
        ])

    if buttons:
        await message.reply(
            "🔍 Result:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await message.reply("❌ Kichu pawa jayni")

# SEND FILE
@bot.on_callback_query(filters.regex("file#"))
async def send_file(client, callback):
    file_id = callback.data.split("#", 1)[1]

    msg = await client.send_document(
        callback.from_user.id,
        file_id,
        caption="📥 File pathano holo\n⏳ 5 minute por delete hobe"
    )

    await callback.answer("DM check korun")

    await asyncio.sleep(300)
    try:
        await msg.delete()
    except:
        pass

# WEB SERVER
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

def run():
    app.run(host="0.0.0.0", port=8080)

def start_bot():
    bot.run()

if __name__ == "__main__":
    Thread(target=start_bot).start()
    run()
