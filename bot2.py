from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

# قائمة تخزين قنوات الاشتراك الإجباري لكل جروب
group_forced_channels = {}

# التحقق من أن المستخدم هو مالك الجروب
async def is_group_owner(update: Update):
    chat = update.effective_chat
    user_id = update.message.from_user.id
    admins = await chat.get_administrators()
    for admin in admins:
        if admin.user.id == user_id and admin.status == "creator":
            return True
    return False

# تعيين قناة الاشتراك الإجباري باستخدام أمر /User ومعرف القناة كمعامل
async def set_forced_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_group_owner(update):
        await update.message.reply_text("فقط مالك الجروب يمكنه تعيين قناة الاشتراك الإجباري.")
        return

    if context.args and context.args[0].startswith('@'):
        username = context.args[0][1:]  # حذف '@' من بداية المعرف
        group_id = update.effective_chat.id
        group_forced_channels[group_id] = username
        await update.message.reply_text(f"تم تعيين قناة الاشتراك الإجباري لهذا الجروب: @{username}")
    else:
        await update.message.reply_text("الرجاء إرسال معرف القناة بالشكل الصحيح بعد الأمر /User، مثال: /User @channel_username")

# إزالة قناة الاشتراك الإجباري باستخدام أمر /Delete
async def delete_forced_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_group_owner(update):
        await update.message.reply_text("فقط مالك الجروب يمكنه إزالة قناة الاشتراك الإجباري.")
        return

    group_id = update.effective_chat.id
    if group_id in group_forced_channels:
        del group_forced_channels[group_id]
        await update.message.reply_text("تم إزالة قناة الاشتراك الإجباري لهذا الجروب.")
    else:
        await update.message.reply_text("لم يتم تعيين قناة اشتراك إجباري لهذا الجروب.")

# التحقق من اشتراك المستخدم في القناة المحددة قبل السماح له بإرسال الرسائل
async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id, channel_username):
    try:
        status = await context.bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
        return status.status in ["member", "administrator", "creator"]
    except BadRequest:
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

# فحص الرسائل ومنع الأعضاء غير المشتركين
async def restrict_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.full_name  # الحصول على الاسم الكامل

    if group_id in group_forced_channels:
        channel_username = group_forced_channels[group_id]

        is_subscribed = await check_subscription(context, user_id, channel_username)

        if not is_subscribed:
            await update.message.delete()

            # زر للاشتراك في القناة وزر يظهر اسم المستخدم
            keyboard = [
                [InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{channel_username}")],
                [InlineKeyboardButton(user_name, url=f"https://t.me/{update.message.from_user.username}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="يجب عليك الاشتراك في القناة المحددة لهذا الجروب قبل إرسال الرسائل هنا.",
                reply_markup=reply_markup
            )

# ترحيب عند استخدام أمر /start مع InlineKeyboardButtons
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 أهلاً بك في البوت\n\n"
        "📌 وظيفة البوت:\n"
        "- إدارة الاشتراك الإجباري في القناة الخاصة بكل جروب.\n"
        "- السماح للمدير بتعيين قناة للاشتراك الإجباري وإزالتها.\n"
        "- منع الأعضاء غير المشتركين من إرسال الرسائل.\n\n"
        "🔗 للبدء، يمكنك استخدام الأوامر التالية:\n"
        "- /User @channel_username لتعيين قناة اشتراك.\n"
        "- /Delete لإزالة قناة الاشتراك الإجباري."
    )

    # هروب الأحرف المحجوزة في MarkdownV2
    escaped_welcome_message = (
        welcome_message
        .replace("!", "\\!")
        .replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("~", "\\~")
        .replace("`", "\\`")
        .replace(">", "\\>")
        .replace("#", "\\#")
        .replace("+", "\\+")
        .replace("-", "\\-")
        .replace("=", "\\=")
        .replace("|", "\\|")
        .replace(".", "\\.")
    )

    keyboard = [
        [
            InlineKeyboardButton(text="𝒎𝒐𝒉𝒂𝒎𝒎𝒆𝒅", url="tg://user?id=6264668799"),
            InlineKeyboardButton(text="ملفات 𝐏𝐘𝐓𝐇𝐎𝐍", url="https://t.me/Your_uncle_Muhammad")
        ],
        [
            InlineKeyboardButton(text="Add me to a channel", url="https://t.me/Coffee_hacker_bot?startchannel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo="https://t.me/B_6ODA/2751",  # استخدم الرابط الصحيح للصورة
        caption=escaped_welcome_message,  # تأكد من تهريب جميع الشخصيات
        parse_mode="MarkdownV2",  # تأكد من استخدام التنسيق المناسب
        reply_markup=reply_markup
    )

# إعداد وتشغيل البوت
app = ApplicationBuilder().token("7304346400:AAEof_UTLs5jPbCeXBqWAeHdi0mxT1Zr38E").build()
app.add_handler(CommandHandler("User", set_forced_channel))
app.add_handler(CommandHandler("Delete", delete_forced_channel))
app.add_handler(CommandHandler("start", start))  # معالجة أمر /start
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, restrict_message))

app.run_polling()
