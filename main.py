
import asyncio
import os
import re
import sys
import logging
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, PeerIdInvalid, UserIsBlocked

# Setup basic console logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load variables from .env file
load_dotenv()

# 🔒 HARDCODED ADMIN NUMERICAL IDs (Teeno Admins Whitelisted Perfectly)
ADMINS =[7582275758, 8510169198, 7663327485]

# Single Account Engine Configuration
API_ID = os.getenv("API_ID_1")
API_HASH = os.getenv("API_HASH_1")

if not API_ID or not API_HASH:
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")

app = Client("my_bulk_userbot", api_id=int(API_ID), api_hash=API_HASH)

def is_authorized_admin(_, __, message: Message) -> bool:
    if not message.from_user: 
        return False
    if message.from_user.is_self: 
        return True  
    return message.from_user.id in ADMINS

admin_filter = filters.create(is_authorized_admin)

@app.on_message(filters.command("bulk", prefixes="/") & admin_filter)
async def bulk_broadcast(client: Client, message: Message):
    raw_args = message.text.split(maxsplit=1)
    if len(raw_args) < 2:
        await message.reply_text("❌ Usage: /bulk @user1 @user2 Your message text")
        return

    full_text = message.text
    usernames = re.findall(r"@[a-zA-Z0-9_]{5,32}", full_text)
    if not usernames:
        await message.reply_text("❌ Error: No valid @usernames found in input.")
        return

    last_username = usernames[-1]
    last_idx = full_text.rfind(last_username) + len(last_username)
    broadcast_message = full_text[last_idx:].strip(" ,;\"'\n\r\t")

    if not broadcast_message:
        await message.reply_text("❌ Error: Missing message text to send.")
        return

    status_msg = await message.reply_text(f"⏳ Admin Verified. Processing {len(usernames)} users...")
    success_count = 0
    failed_count = 0

    for username in usernames:
        try:
            logger.info(f"Attempting to send message to {username}")
            await client.send_message(chat_id=username, text=broadcast_message)
            success_count += 1
            await asyncio.sleep(10)
        except FloodWait as e:
            logger.warning(f"FloodWait hit! Sleeping for {e.value} seconds.")
            await asyncio.sleep(e.value)
            try:
                await client.send_message(chat_id=username, text=broadcast_message)
                success_count += 1
            except Exception:
                failed_count += 1
        except (PeerIdInvalid, KeyError, UserIsBlocked):
            failed_count += 1
        except Exception as general_err:
            logger.error(f"Unexpected operational failure for {username}: {general_err}")
            failed_count += 1

    await status_msg.reply_text(f"📊 Bulk Broadcast Done!\n\n✅ Sent: {success_count}\n❌ Failed: {failed_count}")

@app.on_message(filters.command("switch", prefixes="/") & admin_filter)
async def switch_account(client: Client, message: Message):
    command_text = message.text.strip()
    if len(command_text.split()) < 2:
        await message.reply_text("❌ Usage: /switch +91XXXXXXXXXX (Naya phone number daalein)")
        return

    # Sahi tarike se replace use karke clean string text nikal liya list se bachne ke liye
    new_number = command_text.replace("/switch", "").strip()
    
    await message.reply_text(f"🔄 Account Switch Triggered!\n\nPurani session file backend se uda di gayi hai. Ab script automatic restart ho rahi hai. Kali terminal check karein aur naye number {new_number} ka OTP daalein...")
    logger.info(f"Admin triggered switch to new number: {new_number}")
# File delete karne se pehle deadlock se bachne ke liye client instance ko memory se stop karne ki koi zaroorat nahi hai
    if os.path.exists("my_bulk_userbot.session"):
        try:
            os.remove("my_bulk_userbot.session")
        except Exception as e:
            logger.warning(f"Could not delete session file: {e}")

    # Direct fresh boot par auto restart execute kar dega bina crash hue
    os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    logger.info("Initializing Single-Account Userbot Engine...")
    app.run()
