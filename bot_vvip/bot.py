import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import database
import backup
from datetime import time

# Load environment variables from .env file
load_dotenv()

# Get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Command Handlers ---
async def start(update: Update, context: CallbackContext) -> None:
    """Sends a message with three inline buttons attached."""
    user = update.effective_user
    database.get_or_create_user(user.id, user.username, user.full_name)

    start_text = database.get_setting('start_text') or "Selamat datang! Silahkan pilih menu di bawah ini."
    start_text = start_text.replace("{name}", user.full_name).replace("{id}", str(user.id))

    bantuan_url = database.get_setting('bantuan_url') or 't.me/ownerbot'

    keyboard = [
        [InlineKeyboardButton("Beli VVIP", callback_data='buy_vvip')],
        [InlineKeyboardButton("Bantuan", url=bantuan_url)],
    ]

    # Check if user is VIP
    db_user = database.get_or_create_user(user.id, user.username, user.full_name)
    if db_user and db_user['vip_status'] == 'active':
        keyboard[0].append(InlineKeyboardButton("Status VIP", callback_data='status_vip'))

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(start_text, reply_markup=reply_markup)

# --- Owner Command Handlers ---
async def addchvip(update: Update, context: CallbackContext) -> None:
    """Adds a VVIP channel."""
    if update.message.from_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("Gunakan format: /addchvip [channel_id/username]")
        return

    channel_input = context.args[0]
    try:
        chat = await context.bot.get_chat(channel_input)
        database.add_channel(chat.id, chat.title, chat.username)
        await update.message.reply_text(f"Channel VVIP '{chat.title}' berhasil ditambahkan.")
    except Exception as e:
        await update.message.reply_text(f"Gagal menambahkan channel. Error: {e}")


async def rmchvip(update: Update, context: CallbackContext) -> None:
    """Removes a VVIP channel."""
    if update.message.from_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Gunakan format: /rmchvip [channel_id]")
        return
    try:
        channel_id = int(context.args[0])
        if database.remove_channel(channel_id):
            await update.message.reply_text("Channel VVIP berhasil dihapus.")
        else:
            await update.message.reply_text("Gagal menghapus channel dari database.")
    except (IndexError, ValueError):
        await update.message.reply_text("Channel ID tidak valid.")

async def setharga(update: Update, context: CallbackContext) -> None:
    """Sets the price per month for VVIP."""
    if update.message.from_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Gunakan format: /setharga [harga]")
        return
    try:
        price = int(context.args[0])
        database.set_setting('price', str(price))
        await update.message.reply_text(f"Harga VVIP berhasil diatur ke Rp. {price}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Harga tidak valid.")

async def setqris(update: Update, context: CallbackContext) -> None:
    """Sets the QRIS Telegraph URL."""
    if update.message.from_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Gunakan format: /setqris [telegraph_url]")
        return
    qris_url = context.args[0]
    database.set_setting('qris_url', qris_url)
    await update.message.reply_text("URL QRIS berhasil diatur.")

async def setstarttext(update: Update, context: CallbackContext) -> None:
    """Sets the start text."""
    if update.message.from_user.id != OWNER_ID:
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Gunakan format: /setstarttext [text]")
        return
    database.set_setting('start_text', text)
    await update.message.reply_text("Teks /start berhasil diatur.")

async def setapprovalch(update: Update, context: CallbackContext) -> None:
    """Sets the approval channel ID."""
    if update.message.from_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Gunakan format: /setapprovalch [channel_id]")
        return
    channel_id = context.args[0]
    database.set_setting('approval_channel_id', channel_id)
    await update.message.reply_text(f"Channel approval berhasil diatur ke {channel_id}.")

async def setbantuanurl(update: Update, context: CallbackContext) -> None:
    """Sets the Bantuan button URL."""
    if update.message.from_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Gunakan format: /setbantuanurl [url]")
        return
    url = context.args[0]
    database.set_setting('bantuan_url', url)
    await update.message.reply_text("URL Bantuan berhasil diatur.")

async def dashboard_command(update: Update, context: CallbackContext) -> None:
    """Sends a link to the Mini App dashboard."""
    if update.message.from_user.id != OWNER_ID:
        return

    mini_app_url = os.getenv("MINI_APP_URL")
    if not mini_app_url:
        await update.message.reply_text("URL Mini App tidak diatur.")
        return

    keyboard = [[InlineKeyboardButton("Buka Dashboard", web_app={"url": f"{mini_app_url}/dashboard"})]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Klik tombol di bawah untuk membuka dashboard Mini App:", reply_markup=reply_markup)

async def vvip_command(update: Update, context: CallbackContext) -> None:
    """Displays the VVIP channel links to active VIP users."""
    user = update.effective_user
    db_user = database.get_or_create_user(user.id, user.username, user.full_name)

    if db_user and db_user['vip_status'] == 'active':
        channels = database.get_active_channels()
        if channels:
            keyboard = []
            for channel in channels:
                try:
                    invite_link = await context.bot.create_chat_invite_link(channel['channel_id'], member_limit=1)
                    keyboard.append([InlineKeyboardButton(channel['channel_title'], url=invite_link.invite_link)])
                except Exception as e:
                    logger.error(f"Failed to create invite link for channel {channel['channel_id']}: {e}")

            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Berikut adalah channel VVIP Anda:", reply_markup=reply_markup)
            else:
                await update.message.reply_text("Gagal membuat link channel. Silahkan hubungi admin.")
        else:
            await update.message.reply_text("Saat ini belum ada channel VVIP yang tersedia.")
    else:
        await update.message.reply_text("Langganan Anda telah berakhir. Silahkan perpanjang langganan Anda.")
        return

    mini_app_url = os.getenv("MINI_APP_URL")
    if not mini_app_url:
        await update.message.reply_text("URL Mini App tidak diatur.")
        return

    keyboard = [[InlineKeyboardButton("Buka Dashboard", web_app={"url": f"{mini_app_url}/dashboard"})]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Klik tombol di bawah untuk membuka dashboard Mini App:", reply_markup=reply_markup)

# --- Callback Query Handler ---
async def button_handler(update: Update, context: CallbackContext) -> None:
    """Handles inline button clicks."""
    query = update.callback_query
    await query.answer()

    # Initialize user data for purchase if it doesn't exist
    if 'purchase' not in context.user_data:
        context.user_data['purchase'] = {'months': 1}

    if query.data == 'buy_vvip':
        await show_cart(update, context)
    elif query.data == 'add_month':
        context.user_data['purchase']['months'] += 1
        await show_cart(update, context, is_edit=True)
    elif query.data == 'remove_month':
        if context.user_data['purchase']['months'] > 1:
            context.user_data['purchase']['months'] -= 1
            await show_cart(update, context, is_edit=True)
    elif query.data == 'cancel_purchase':
        context.user_data.pop('purchase', None)
        await query.edit_message_text("Pembelian dibatalkan.")
    elif query.data == 'proceed_payment':
        await proceed_to_payment(update, context)
    elif query.data.startswith('approve_'):
        payment_id = int(query.data.split('_')[1])
        await handle_approval(update, context, payment_id)
    elif query.data.startswith('reject_'):
        payment_id = int(query.data.split('_')[1])
        await handle_rejection(update, context, payment_id)

async def handle_approval(update: Update, context: CallbackContext, payment_id: int) -> None:
    """Handles the approval of a payment."""
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        await query.answer("You are not authorized to perform this action.", show_alert=True)
        return

    payment = database.get_payment(payment_id)
    if not payment or payment['approval_status'] != 'pending':
        await query.answer("This payment has already been processed.", show_alert=True)
        return

    user_id = payment['user_id']
    months = payment['duration_months']

    # Update user's VIP status
    database.activate_vip(user_id, months)

    # Update payment status
    database.update_payment_status(payment_id, 'approved')

    await query.edit_message_caption("Berhasil di approve")

    # Notify user
    # We will need to get the list of VVIP channels to show the buttons
    channels = database.get_active_channels()
    if channels:
        keyboard = []
        for channel in channels:
            try:
                invite_link = await context.bot.create_chat_invite_link(channel['channel_id'], member_limit=1)
                keyboard.append([InlineKeyboardButton(channel['channel_title'], url=invite_link.invite_link)])
            except Exception as e:
                logger.error(f"Failed to create invite link for channel {channel['channel_id']}: {e}")
                await context.bot.send_message(OWNER_ID, f"Gagal membuat link invite untuk channel {channel['channel_title']}. Pastikan bot adalah admin dengan hak 'Invite users'.")

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            user_id,
            "Pembayaran Anda telah disetujui! Silahkan gabung semua channel VVIP kami. Silahkan klik tombol di bawah:",
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_message(
            user_id,
            "Pembayaran Anda telah disetujui! Saat ini belum ada channel VVIP yang tersedia. Hubungi admin untuk info lebih lanjut."
        )

async def handle_rejection(update: Update, context: CallbackContext, payment_id: int) -> None:
    """Handles the rejection of a payment."""
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        await query.answer("You are not authorized to perform this action.", show_alert=True)
        return

    payment = database.get_payment(payment_id)
    if not payment or payment['approval_status'] != 'pending':
        await query.answer("This payment has already been processed.", show_alert=True)
        return

    user_id = payment['user_id']

    # Update payment status
    database.update_payment_status(payment_id, 'rejected')

    await query.message.delete()

    # Notify user
    await context.bot.send_message(
        user_id,
        "Pembayaran ditolak karena mengirim foto transaksi fake/palsu"
    )

async def show_cart(update: Update, context: CallbackContext, is_edit: bool = False) -> None:
    """Displays the shopping cart."""
    purchase_data = context.user_data['purchase']
    months = purchase_data['months']

    price_per_month = int(database.get_setting('price') or 10000)
    total_price = price_per_month * months

    from datetime import datetime, timedelta
    user_id = update.effective_user.id
    user_data = database.get_or_create_user(user_id, "", "")

    start_date = datetime.now()
    if user_data and user_data['vip_status'] == 'active' and user_data['vip_end_date']:
        start_date = datetime.fromisoformat(user_data['vip_end_date'])

    end_date = start_date + timedelta(days=30 * months)
    end_date_str = end_date.strftime('%d %B %Y')

    text = (
        "🛒 *Keranjang Belanja*\n\n"
        f"💎 VVIP Channel: {months} Bulan\n"
        f"🗓️ VVIP Anda akan berakhir pada: *{end_date_str}*\n\n"
        f"💰 *Total Harga: Rp. {total_price:,}*"
    )

    keyboard = [
        [
            InlineKeyboardButton("-", callback_data='remove_month'),
            InlineKeyboardButton(f"⏰ {months} Bulan", callback_data='noop'), # No operation
            InlineKeyboardButton("+", callback_data='add_month')
        ],
        [
            InlineKeyboardButton("❌ Batalkan", callback_data='cancel_purchase'),
            InlineKeyboardButton("✅ Lanjutkan", callback_data='proceed_payment')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_edit:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def proceed_to_payment(update: Update, context: CallbackContext) -> None:
    """Handles the payment process."""
    qris_url = database.get_setting('qris_url')
        f"💎 VVIP Channel: {months} Bulan\n"
        f"🗓️ VVIP Anda akan berakhir pada: {end_date}\n\n"
        f"💰 *Total Harga: Rp. {total_price:,}*"
    )

    keyboard = [
        [
            InlineKeyboardButton("-", callback_data='remove_month'),
            InlineKeyboardButton(f"⏰ {months} Bulan", callback_data='noop'), # No operation
            InlineKeyboardButton("+", callback_data='add_month')
        ],
        [
            InlineKeyboardButton("❌ Batalkan", callback_data='cancel_purchase'),
            InlineKeyboardButton("✅ Lanjutkan", callback_data='proceed_payment')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_edit:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def proceed_to_payment(update: Update, context: CallbackContext) -> None:
    """Handles the payment process."""
    qris_url = database.get_setting('qris_url')
    if not qris_url:
        await update.callback_query.message.reply_text("Pembayaran saat ini tidak tersedia. Silahkan hubungi admin.")
        return

    await update.callback_query.edit_message_text(
        f"Silahkan transfer ke QRIS di [link]({qris_url}) ini.\n\n"
        "Setelah transfer, kirim bukti transfer ke bot ini. "
        "Pembayaran Anda akan diproses dalam 15-20 menit setelah bukti transfer dikirim.",
        parse_mode='Markdown'
    )
    # Here, we need to add a handler to listen for the user's photo message
async def handle_payment_proof(update: Update, context: CallbackContext) -> None:
    """Handles the user's payment proof submission."""
    if 'purchase' not in context.user_data:
        # This might be a random photo, so we can either ignore it or reply with a message
        return

    user = update.effective_user
    purchase_data = context.user_data['purchase']
    months = purchase_data['months']
    price_per_month = int(database.get_setting('price') or 10000)
    total_price = price_per_month * months

    # Save payment to database
    payment_id = database.create_payment_record(user.id, total_price, months)

    if not payment_id:
        await update.message.reply_text("Terjadi kesalahan saat menyimpan pembayaran. Silahkan hubungi admin.")
        return

    approval_channel_id = database.get_setting('approval_channel_id')
    if not approval_channel_id:
        logger.error("Approval channel ID is not set.")
        await update.message.reply_text("Sistem approval sedang bermasalah. Silahkan hubungi admin.")
        # We should also notify the owner
        await context.bot.send_message(OWNER_ID, "PENTING: Approval Channel ID belum diatur! Tidak bisa memproses pembayaran.")
        return

    caption = (
        f"Informasi Pembayaran:\n"
        f"ID: `{user.id}`\n"
        f"Nama: {user.full_name}\n"
        f"Bulan: {months} Bulan\n"
        f"Harga: Rp. {total_price:,}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f'approve_{payment_id}'),
            InlineKeyboardButton("❌ Reject", callback_data=f'reject_{payment_id}')
        ]
    ])

    try:
        sent_message = await context.bot.send_photo(
            chat_id=approval_channel_id,
            photo=update.message.photo[-1].file_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        database.update_payment_approval_message_id(payment_id, sent_message.message_id)
        await update.message.reply_text("✅ Bukti transfer Anda telah diterima dan akan segera diproses. Mohon tunggu 15-20 menit untuk konfirmasi.")
        context.user_data.pop('purchase', None)
    except Exception as e:
        logger.error(f"Failed to send payment proof to approval channel: {e}")
        await update.message.reply_text("Gagal mengirim bukti pembayaran. Silahkan coba lagi atau hubungi admin.")


# --- Automatic Systems ---
async def check_expired_users(context: CallbackContext) -> None:
    """Checks for expired VIP users and removes them from channels."""
    expired_users = database.get_expired_vip_users()
    channels = database.get_active_channels()

    for user in expired_users:
        user_id = user['user_id']
        logger.info(f"Processing expired user: {user_id}")
        for channel in channels:
            try:
                await context.bot.ban_chat_member(chat_id=channel['channel_id'], user_id=user_id)
                # Unbanning immediately allows them to rejoin if they renew
                await context.bot.unban_chat_member(chat_id=channel['channel_id'], user_id=user_id)
            except Exception as e:
                logger.error(f"Failed to kick {user_id} from {channel['channel_id']}: {e}")

        database.update_user_vip_status(user_id, 'expired')

async def backup_command(update: Update, context: CallbackContext) -> None:
    """Performs a manual backup of the database."""
    if update.message.from_user.id != OWNER_ID:
        return
    await perform_backup(context, manual=True)

async def auto_backup_job(context: CallbackContext) -> None:
    """Performs an automatic backup of the database."""
    await perform_backup(context, manual=False)

async def perform_backup(context: CallbackContext, manual: bool = False) -> None:
    """Creates a backup and sends it to the owner."""
    backup_filepath, file_size = backup.create_backup()

    if backup_filepath:
        backup_type = 'manual' if manual else 'auto'
        database.add_backup_record(file_size, backup_filepath, backup_type)

        caption = (
            f"🔄 {'Manual' if manual else 'Auto'} Backup Database\n"
            f"📅 Tanggal: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"📦 Ukuran: {file_size / 1024:.2f} KB\n"
            f"✅ Backup berhasil"
        )
        try:
            await context.bot.send_document(
                chat_id=OWNER_ID,
                document=open(backup_filepath, 'rb'),
                caption=caption
            )
        except Exception as e:
            logger.error(f"Failed to send backup file to owner: {e}")
            await context.bot.send_message(OWNER_ID, f"Gagal mengirim file backup: {e}")
    else:
        await context.bot.send_message(OWNER_ID, "Gagal membuat file backup. Cek log untuk detail.")

# --- Main Bot Function ---
def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Add job queue for automatic tasks
    job_queue = application.job_queue
    job_queue.run_daily(check_expired_users, time=time(hour=0, minute=0)) # Run daily at midnight
    job_queue.run_repeating(auto_backup_job, interval=60*60*6, first=10) # Run every 6 hours

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(CommandHandler("addchvip", addchvip))
    application.add_handler(CommandHandler("rmchvip", rmchvip))
    application.add_handler(CommandHandler("setharga", setharga))
    application.add_handler(CommandHandler("setqris", setqris))
    application.add_handler(CommandHandler("setstarttext", setstarttext))
    application.add_handler(CommandHandler("setapprovalch", setapprovalch))
    application.add_handler(CommandHandler("setbantuanurl", setbantuanurl))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("vvip", vvip_command))

    # Add handler for inline button clicks
    application.add_handler(CallbackQueryHandler(button_handler))

    # Add handler for photo messages (payment proofs)
    application.add_handler(MessageHandler(filters.PHOTO, handle_payment_proof))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()
