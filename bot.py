import json
import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ========== НАСТРОЙКИ ==========
TOKEN = "8693007147:AAHqyn8Aekty-r8TJB86miVPDVe9cObYejM"
ADMIN_ID = 1595538164
COMMISSION = 5  # ✅ ТВОЯ КОМИССИЯ 5%
PAYMENT_DETAILS = "💳 2200 1536 8048 9946\n🏦 Альфа-Банк"
BOT_USERNAME = "garantnoflixx_bot"  # ✅ ТВОЙ БОТ (без @)
REVIEW_TAG = "@noflixx"
# ================================

# Отключаем логи
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

# Файлы для хранения данных
DEALS_FILE = "deals.json"
CHATS_FILE = "chats.json"
USER_DATA_FILE = "user_data.json"
USERS_FILE = "users.json"
REVIEWS_FILE = "reviews.json"
MESSAGES_FILE = "messages.json"

# ========== ПРОВЕРКА ФАЙЛОВ ==========
def ensure_files_exist():
    """Создает файлы данных, если их нет"""
    files = [DEALS_FILE, CHATS_FILE, USER_DATA_FILE, USERS_FILE, REVIEWS_FILE, MESSAGES_FILE]
    for file in files:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    print("✅ Файлы данных проверены/созданы")

# ========== РАБОТА С JSON ==========
def load_data(filename):
    try:
        with open(filename, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_data(filename, data):
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
# ====================================

# ========== РАБОТА С USER_DATA ==========
def load_user_data():
    return load_data(USER_DATA_FILE)

def save_user_data(data):
    save_data(USER_DATA_FILE, data)

def get_user_step(user_id):
    data = load_user_data()
    return data.get(str(user_id), {}).get('step')

def set_user_step(user_id, step, **kwargs):
    data = load_user_data()
    if str(user_id) not in data:
        data[str(user_id)] = {}
    data[str(user_id)]['step'] = step
    for key, value in kwargs.items():
        data[str(user_id)][key] = value
    save_user_data(data)

def clear_user_step(user_id):
    data = load_user_data()
    if str(user_id) in data:
        del data[str(user_id)]
        save_user_data(data)
# =========================================

# ========== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ==========
def load_users():
    return load_data(USERS_FILE)

def save_user_info(user_id, username, full_name):
    users = load_users()
    users[str(user_id)] = {
        'user_id': user_id,
        'username': username.lower() if username else None,
        'full_name': full_name
    }
    save_data(USERS_FILE, users)

def user_exists(username):
    """Проверить, существует ли пользователь в базе"""
    users = load_users()
    username_clean = username.replace('@', '').lower().strip()
    
    for user_data in users.values():
        stored_username = user_data.get('username', '')
        if stored_username and stored_username.replace('@', '').lower() == username_clean:
            return user_data['user_id']
    return None
# =============================================

# ========== РАБОТА С ОТЗЫВАМИ ==========
def load_reviews():
    return load_data(REVIEWS_FILE)

def save_review(deal_id, from_user, to_user, text):
    """Сохранить отзыв"""
    reviews = load_reviews()
    if deal_id not in reviews:
        reviews[deal_id] = []
    
    reviews[deal_id].append({
        'from': from_user,
        'to': to_user,
        'text': text,
        'date': str(datetime.now())
    })
    save_data(REVIEWS_FILE, reviews)

def get_deal_reviews(deal_id):
    """Получить отзывы по сделке"""
    reviews = load_reviews()
    return reviews.get(deal_id, [])
# =========================================

# ========== ЛИЧНЫЕ СООБЩЕНИЯ АДМИНУ ==========
def load_messages():
    return load_data(MESSAGES_FILE)

def save_message(user_id, username, message_text):
    """Сохранить сообщение админу"""
    messages = load_messages()
    if str(user_id) not in messages:
        messages[str(user_id)] = []
    
    messages[str(user_id)].append({
        'text': message_text,
        'date': str(datetime.now()),
        'username': username
    })
    save_data(MESSAGES_FILE, messages)

def get_user_messages(user_id):
    """Получить сообщения пользователя"""
    messages = load_messages()
    return messages.get(str(user_id), [])
# =============================================

# ========== КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт - показывает меню и сохраняет пользователя"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name
    save_user_info(user_id, username, full_name)
    
    await show_main_menu(update, context)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /menu - открыть меню"""
    await show_main_menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - помощь"""
    text = (
        "❓ **Помощь по боту**\n\n"
        "🔹 **Как создать сделку?**\n"
        "• Нажми «Создать сделку» в меню\n\n"
        "🔹 **Как присоединиться к сделке?**\n"
        "Если вас пригласили, нажмите кнопку «Присоединиться»\n\n"
        "🔹 **Как проходит сделка?**\n"
        "1. Оба подтверждают участие\n"
        "2. Покупатель оплачивает и отправляет скриншот\n"
        "3. Продавец подтверждает передачу товара\n"
        "4. Продавец указывает карту и данные товара\n"
        "5. Админ подтверждает завершение\n"
        f"6. Гарант получает {COMMISSION}% от сделки\n\n"
        f"🔹 **Твоя комиссия:** {COMMISSION}%\n"
        f"🔹 **Тег для отзывов:** {REVIEW_TAG}\n\n"
        "⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
        "📋 **Команды:**\n"
        "/start - Главное меню\n"
        "/menu - Открыть меню\n"
        "/help - Эта помощь\n"
        "/mydeals - Мои сделки\n"
        "/reviews - Мои отзывы\n"
        "/messages - Сообщения админу\n"
        "/cancel - Отменить действие"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
    
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь из меню"""
    query = update.callback_query
    await query.answer()
    await help_command(update, context)

async def mydeals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mydeals - мои сделки"""
    await show_my_deals(update, context)

async def reviews_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /reviews - мои отзывы"""
    await show_my_reviews(update, context)

async def messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /messages - мои сообщения админу"""
    await show_my_messages(update, context)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel - отменить действие"""
    user_id = update.effective_user.id
    clear_user_step(user_id)
    
    await update.message.reply_text(
        "✅ Действие отменено.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")
        ]])
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    keyboard = [
        [InlineKeyboardButton("🤝 Создать сделку", callback_data="new_deal")],
        [InlineKeyboardButton("📋 Мои сделки", callback_data="my_deals")],
        [InlineKeyboardButton("📝 Мои отзывы", callback_data="my_reviews")],
        [InlineKeyboardButton("💬 Написать админу", callback_data="write_to_admin")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 Админ панель", callback_data="admin_panel")])
    
    if update.message:
        await update.message.reply_text(
            "🔹 **Главное меню** 🔹\n\n"
            "⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "🔹 **Главное меню** 🔹\n\n"
            "⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    query = update.callback_query
    await query.answer()
    await show_main_menu(update, context)

# ========== ПРОСМОТР СВОИХ СДЕЛОК ==========
async def show_my_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр своих сделок"""
    user_id = update.effective_user.id
    deals = load_data(DEALS_FILE)
    chats = load_data(CHATS_FILE)
    
    user_deals = []
    if str(user_id) in chats:
        for deal_id in chats[str(user_id)]:
            if deal_id in deals:
                deal = deals[deal_id]
                status_text = {
                    'waiting_for_second_user': '⏳ Ожидание второго',
                    'waiting_confirmation': '⏳ Ждём подтверждения',
                    'waiting_for_payment': '💰 Ожидание оплаты',
                    'waiting_screenshot': '📸 Ждём скриншот оплаты',
                    'screenshot_received': '📸 Скриншот оплаты получен',
                    'waiting_for_card': '💳 Ждём карту',
                    'waiting_for_item_data': '📦 Ждём данные товара',
                    'waiting_admin_confirm': '👑 Ждём админа',
                    'completed': '✅ Завершена'
                }.get(deal['status'], deal['status'])
                
                user_role = "продавец" if user_id == deal.get('seller_id') else "покупатель"
                
                deal_text = f"🔹 **Сделка #{deal_id}**\nРоль: {user_role}\nСтатус: {status_text}\nПредмет: {deal['product']}\n"
                
                if user_role == "продавец" and deal.get('card_number'):
                    deal_text += f"💳 Ваша карта: {deal['card_number']} ({deal.get('bank_name', '?')})\n"
                
                if deal.get('item_data') and deal['status'] == 'completed':
                    deal_text += f"📦 Данные товара: {deal['item_data']}\n"
                
                user_deals.append(deal_text)
    
    text = "📋 **Ваши сделки:**\n\n" + "\n".join(user_deals) if user_deals else "📭 Нет активных сделок."
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ========== ПРОСМОТР ОТЗЫВОВ ==========
async def show_my_reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр своих отзывов"""
    user_id = update.effective_user.id
    username = f"@{update.effective_user.username}" if update.effective_user.username else "NoUsername"
    reviews = load_reviews()
    
    my_reviews = []
    for deal_id, deal_reviews in reviews.items():
        for review in deal_reviews:
            if review['to'] == username:
                my_reviews.append(f"🔹 **Сделка #{deal_id}**\nОт: {review['from']}\nОтзыв: {review['text']}\n")
    
    text = "📝 **Ваши отзывы:**\n\n" + "\n".join(my_reviews) if my_reviews else "📭 У вас пока нет отзывов."
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ========== НАПИСАТЬ АДМИНУ ==========
async def write_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Написать сообщение админу"""
    query = update.callback_query
    await query.answer()
    
    set_user_step(query.from_user.id, 'writing_to_admin')
    
    await query.edit_message_text(
        f"✍️ Напишите сообщение для администратора. {REVIEW_TAG}\n/cancel - отмена"
    )

async def handle_message_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщения админу"""
    user_id = update.effective_user.id
    if get_user_step(user_id) != 'writing_to_admin':
        return
    
    message_text = update.message.text
    username = f"@{update.effective_user.username}" if update.effective_user.username else "NoUsername"
    
    save_message(user_id, username, message_text)
    clear_user_step(user_id)
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📨 **Сообщение от {username}**\n\n{message_text}\n\n{REVIEW_TAG}",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text("✅ Сообщение отправлено!", reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")
    ]]))

async def show_my_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр своих сообщений админу"""
    user_id = update.effective_user.id
    messages = get_user_messages(user_id)
    
    if not messages:
        text = "📭 У вас пока нет сообщений админу."
    else:
        text = "💬 **Ваши сообщения:**\n\n"
        for msg in messages[-5:]:
            text += f"• {msg['text']}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ========== СОЗДАНИЕ СДЕЛКИ ==========
async def new_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания сделки"""
    query = update.callback_query
    await query.answer()
    
    set_user_step(query.from_user.id, 'waiting_for_username')
    await query.edit_message_text("📝 Введите @username второго участника:")

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение username"""
    user_id = update.effective_user.id
    if get_user_step(user_id) != 'waiting_for_username':
        return
    
    username = update.message.text.strip()
    if not username.startswith('@'):
        username = '@' + username
    
    # Проверка на самого себя
    if username.replace('@', '').lower() == (update.effective_user.username or '').lower():
        await update.message.reply_text("❌ Нельзя создать сделку с самим собой!")
        return
    
    second_user_id = user_exists(username)
    
    set_user_step(user_id, 'waiting_for_role', second_username=username, second_user_id=second_user_id)
    
    keyboard = [
        [InlineKeyboardButton("💰 Я продавец", callback_data="role_seller")],
        [InlineKeyboardButton("🛒 Я покупатель", callback_data="role_buyer")]
    ]
    
    await update.message.reply_text("Выберите вашу роль:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор роли"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = load_user_data().get(str(user_id), {})
    
    if user_data.get('step') != 'waiting_for_role':
        return
    
    role = "seller" if query.data == "role_seller" else "buyer"
    
    set_user_step(user_id, 'waiting_for_product', 
                  second_username=user_data['second_username'],
                  second_user_id=user_data['second_user_id'],
                  role=role)
    
    await query.edit_message_text("📦 Напишите, что передаётся:")

async def handle_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение товара и отправка приглашения второму участнику"""
    user_id = update.effective_user.id
    user_data = load_user_data().get(str(user_id), {})
    
    if user_data.get('step') != 'waiting_for_product':
        return
    
    product = update.message.text
    second_username = user_data['second_username']
    second_user_id = user_data['second_user_id']
    creator_role = user_data['role']
    
    deals = load_data(DEALS_FILE)
    deal_id = str(len(deals) + 1)
    
    # Определяем роли
    if creator_role == "seller":
        seller_id = user_id
        seller_username = update.effective_user.username
        seller_name = update.effective_user.full_name
        buyer_id = None
        buyer_username = None
        buyer_name = None
    else:
        seller_id = None
        seller_username = None
        seller_name = None
        buyer_id = user_id
        buyer_username = update.effective_user.username
        buyer_name = update.effective_user.full_name
    
    deals[deal_id] = {
        'product': product,
        'seller_id': seller_id,
        'seller_username': seller_username,
        'seller_name': seller_name,
        'buyer_id': buyer_id,
        'buyer_username': buyer_username,
        'buyer_name': buyer_name,
        'second_username': second_username,
        'second_user_id': second_user_id,
        'seller_confirm': False,
        'buyer_confirm': False,
        'buyer_paid': False,
        'seller_ready': False,
        'status': 'waiting_for_second_user',
        'created_by': user_id,
        'card_number': None,
        'bank_name': None,
        'screenshot': None,
        'item_data': None
    }
    save_data(DEALS_FILE, deals)
    
    chats = load_data(CHATS_FILE)
    if str(user_id) not in chats:
        chats[str(user_id)] = []
    chats[str(user_id)].append(deal_id)
    save_data(CHATS_FILE, chats)
    
    clear_user_step(user_id)
    
    await update.message.reply_text(f"✅ Сделка #{deal_id} создана!\n\n💰 Твоя комиссия: {COMMISSION}%")
    
    # Отправка уведомления второму участнику
    if second_user_id:
        try:
            role_for_second = "покупатель" if creator_role == "seller" else "продавец"
            
            await context.bot.send_message(
                chat_id=second_user_id,
                text=f"🔔 **Вас пригласили в сделку #{deal_id}!**\n\n"
                     f"👤 Пригласил: {update.effective_user.full_name} (@{update.effective_user.username})\n"
                     f"📦 Предмет: {product}\n"
                     f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
                     f"Ваша роль: **{role_for_second}**\n\n"
                     f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
                     f"Чтобы присоединиться, нажмите кнопку ниже:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Присоединиться к сделке", callback_data=f"join_{deal_id}")
                ]]),
                parse_mode="Markdown"
            )
            logger.info(f"Уведомление отправлено {second_user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
            await update.message.reply_text(
                f"⚠️ Не удалось отправить уведомление {second_username}\n"
                f"Пользователь должен написать боту: @{BOT_USERNAME}\n\n"
                f"👉 **Дайте попробовать отправить другому участнику сделки предложение о участии**"
            )
    else:
        await update.message.reply_text(
            f"⚠️ Пользователь {second_username} ещё не писал боту.\n"
            f"Ему нужно написать: @{BOT_USERNAME}\n\n"
            f"👉 **Дайте попробовать отправить другому участнику сделки предложение о участии**"
        )

# ========== ПРИСОЕДИНЕНИЕ К СДЕЛКЕ ==========
async def join_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присоединение к сделке"""
    query = update.callback_query
    await query.answer()
    
    deal_id = query.data.replace('join_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal or deal['status'] != 'waiting_for_second_user':
        await query.edit_message_text("❌ Сделка не найдена или уже недоступна")
        return
    
    username = f"@{query.from_user.username}" if query.from_user.username else "NoUsername"
    if username.lower() != deal['second_username'].lower():
        await query.edit_message_text("❌ Это не ваша сделка")
        return
    
    # Проверка на повторное присоединение
    if (deal['seller_id'] is not None and query.from_user.id == deal['seller_id']) or \
       (deal['buyer_id'] is not None and query.from_user.id == deal['buyer_id']):
        await query.edit_message_text("❌ Вы уже присоединились к этой сделке")
        return
    
    # Определяем роль второго участника
    if deal['seller_id'] is None:
        deal['seller_id'] = query.from_user.id
        deal['seller_username'] = query.from_user.username
        deal['seller_name'] = query.from_user.full_name
        role = "seller"
        role_text = "продавец"
    else:
        deal['buyer_id'] = query.from_user.id
        deal['buyer_username'] = query.from_user.username
        deal['buyer_name'] = query.from_user.full_name
        role = "buyer"
        role_text = "покупатель"
    
    deal['status'] = 'waiting_confirmation'
    save_data(DEALS_FILE, deals)
    
    # Сохраняем в чаты
    chats = load_data(CHATS_FILE)
    if str(query.from_user.id) not in chats:
        chats[str(query.from_user.id)] = []
    chats[str(query.from_user.id)].append(deal_id)
    save_data(CHATS_FILE, chats)
    
    # Кнопка для присоединившегося участника
    keyboard = [[InlineKeyboardButton(f"✅ Подтвердить участие как {role_text}", callback_data=f"confirm_{role}_{deal_id}")]]
    
    await query.edit_message_text(
        f"✅ Вы присоединились к сделке #{deal_id}!\n\n"
        f"📦 Предмет: {deal['product']}\n"
        f"👤 Продавец: @{deal['seller_username'] or '?'}\n"
        f"👤 Покупатель: @{deal['buyer_username'] or '?'}\n"
        f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
        f"**Ваша роль:** {role_text}\n\n"
        f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
        f"Нажмите кнопку ниже для подтверждения участия:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Кнопка для первого участника (создателя)
    first_user_id = deal['created_by']
    if first_user_id == deal.get('seller_id'):
        first_role = "seller"
        first_role_text = "продавец"
    else:
        first_role = "buyer"
        first_role_text = "покупатель"
    
    first_keyboard = [[InlineKeyboardButton(f"✅ Подтвердить участие как {first_role_text}", callback_data=f"confirm_{first_role}_{deal_id}")]]
    
    try:
        await context.bot.send_message(
            chat_id=first_user_id,
            text=f"👤 **{role_text.capitalize()}** присоединился к сделке #{deal_id}!\n\n"
                 f"📦 Предмет: {deal['product']}\n"
                 f"👤 Продавец: @{deal['seller_username'] or '?'}\n"
                 f"👤 Покупатель: @{deal['buyer_username'] or '?'}\n"
                 f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
                 f"**Ваша роль:** {first_role_text}\n\n"
                 f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
                 f"Теперь вам нужно подтвердить участие:",
            reply_markup=InlineKeyboardMarkup(first_keyboard),
            parse_mode="Markdown"
        )
    except:
        pass
    
    # Уведомление админу
    await send_admin_update(context, deal_id, deal)

# ========== ПОДТВЕРЖДЕНИЕ УЧАСТИЯ ==========
async def send_admin_update(context, deal_id, deal):
    """Отправить обновление админу"""
    try:
        text = (
            f"🔄 **Сделка #{deal_id}**\n\n"
            f"📦 Предмет: {deal['product']}\n"
            f"👤 Продавец: @{deal['seller_username'] or '?'}\n"
            f"👤 Покупатель: @{deal['buyer_username'] or '?'}\n"
            f"💰 Твоя комиссия: {COMMISSION}%\n\n"
            f"**Статус подтверждения:**\n"
            f"Продавец: {'✅' if deal.get('seller_confirm') else '❌'}\n"
            f"Покупатель: {'✅' if deal.get('buyer_confirm') else '❌'}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")
    except:
        pass

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Общий обработчик подтверждения"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    if len(data) < 3:
        return
    
    role = data[1]  # seller или buyer
    deal_id = data[2]
    
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    user_id = query.from_user.id
    
    # Проверяем права
    if role == "seller" and user_id != deal['seller_id'] and user_id != ADMIN_ID:
        await query.edit_message_text("❌ Вы не продавец в этой сделке")
        return
    if role == "buyer" and user_id != deal['buyer_id'] and user_id != ADMIN_ID:
        await query.edit_message_text("❌ Вы не покупатель в этой сделке")
        return
    
    # Устанавливаем подтверждение
    if role == "seller":
        deal['seller_confirm'] = True
    else:
        deal['buyer_confirm'] = True
    
    save_data(DEALS_FILE, deals)
    
    await query.edit_message_text(f"✅ Вы подтвердили участие как {role}!")
    await send_admin_update(context, deal_id, deal)
    
    # Проверяем, подтвердили ли оба
    if deal.get('seller_confirm') and deal.get('buyer_confirm'):
        deal['status'] = 'waiting_for_payment'
        save_data(DEALS_FILE, deals)
        
        # Покупателю - кнопка оплаты
        if deal['buyer_id']:
            try:
                await context.bot.send_message(
                    chat_id=deal['buyer_id'],
                    text=f"✅ **Оба подтвердили сделку #{deal_id}!**\n\n"
                         f"📦 Предмет: {deal['product']}\n"
                         f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
                         f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
                         f"Теперь оплатите:",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("💳 Оплатить", callback_data=f"pay_{deal_id}")
                    ]]),
                    parse_mode="Markdown"
                )
            except:
                pass
        
        # Продавцу - уведомление
        if deal['seller_id']:
            try:
                await context.bot.send_message(
                    chat_id=deal['seller_id'],
                    text=f"✅ **Оба подтвердили сделку #{deal_id}!**\n\n"
                         f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
                         f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
                         f"Ожидание оплаты от покупателя..."
                )
            except:
                pass

# ========== ОПЛАТА ==========
async def handle_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплата"""
    query = update.callback_query
    await query.answer()
    
    deal_id = query.data.replace('pay_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    deal['status'] = 'waiting_screenshot'
    save_data(DEALS_FILE, deals)
    
    await query.edit_message_text(
        f"💳 **Реквизиты для оплаты:**\n\n"
        f"{PAYMENT_DETAILS}\n\n"
        f"📦 Сделка #{deal_id}\n"
        f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
        f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
        f"После оплаты **отправьте скриншот** (фото):",
        parse_mode="Markdown"
    )

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение скриншота оплаты от покупателя"""
    if not update.message.photo:
        return
    
    user_id = update.effective_user.id
    deals = load_data(DEALS_FILE)
    
    # Ищем сделку, где этот пользователь является покупателем и статус ожидания скриншота
    for deal_id, deal in deals.items():
        if deal.get('buyer_id') == user_id and deal['status'] == 'waiting_screenshot':
            photo = update.message.photo[-1]
            deal['screenshot'] = photo.file_id
            deal['status'] = 'screenshot_received'
            deal['buyer_paid'] = True
            save_data(DEALS_FILE, deals)
            
            await update.message.reply_text("✅ Скриншот оплаты получен и отправлен продавцу!")
            
            # Отправляем скриншот продавцу с кнопкой
            if deal['seller_id']:
                try:
                    await context.bot.send_photo(
                        chat_id=deal['seller_id'],
                        photo=photo.file_id,
                        caption=f"🖼️ Скриншот оплаты по сделке #{deal_id}\n💰 Комиссия гаранта: {COMMISSION}%\n\n"
                                f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
                                f"👉 **Укажите свой номер карты, администратор отправит вам деньги, если сделка пройдет верно**",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("📦 Я передал товар", callback_data=f"delivered_{deal_id}")
                        ]])
                    )
                    
                    # Уведомляем покупателя, что продавец уведомлен
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"✅ Скриншот доставлен продавцу. Ожидайте, когда продавец подтвердит передачу товара."
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки скриншота продавцу: {e}")
                    await update.message.reply_text(
                        f"⚠️ Скриншот получен, но не удалось уведомить продавца.\n"
                        f"Продавец скоро получит уведомление."
                    )
            return
    
    # Если не нашли подходящую сделку
    await update.message.reply_text(
        "❌ Не удалось найти активную сделку, ожидающую скриншот оплаты.\n"
        "Убедитесь, что вы создали сделку и нажали кнопку оплаты."
    )

# ========== ПРОДАВЕЦ ПЕРЕДАЛ ТОВАР ==========
async def handle_delivered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Продавец нажал кнопку 'Я передал товар'"""
    query = update.callback_query
    await query.answer()
    
    deal_id = query.data.replace('delivered_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    if query.from_user.id != deal['seller_id']:
        await query.edit_message_text("❌ Только продавец может подтвердить передачу")
        return
    
    # Сразу переходим к вводу карты (без запроса скриншота)
    set_user_step(query.from_user.id, 'waiting_for_card', deal_id=deal_id)
    
    await query.edit_message_text(
        "💳 **Введите номер карты для получения денег:**\n\n"
        "Например: `2200 1234 5678 9012`\n\n"
        "⚠️ Деньги поступят только после подтверждения администратора!",
        parse_mode="Markdown"
    )

async def handle_card_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение карты"""
    user_id = update.effective_user.id
    user_data = load_user_data().get(str(user_id), {})
    
    if user_data.get('step') != 'waiting_for_card':
        return
    
    card = update.message.text.strip()
    if len(card) < 10:  # Простая проверка
        await update.message.reply_text("❌ Слишком короткий номер карты. Попробуйте снова:")
        return
    
    deal_id = user_data['deal_id']
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await update.message.reply_text("❌ Сделка не найдена")
        clear_user_step(user_id)
        return
    
    # Проверяем, что это продавец
    if deal.get('seller_id') != user_id:
        await update.message.reply_text("❌ Вы не продавец в этой сделке")
        clear_user_step(user_id)
        return
    
    deal['card_number'] = card
    save_data(DEALS_FILE, deals)
    
    set_user_step(user_id, 'waiting_for_bank', deal_id=deal_id)
    await update.message.reply_text("🏦 Введите название банка (например, Сбербанк, Тинькофф):")

async def handle_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение банка"""
    user_id = update.effective_user.id
    user_data = load_user_data().get(str(user_id), {})
    
    if user_data.get('step') != 'waiting_for_bank':
        return
    
    bank = update.message.text
    deal_id = user_data['deal_id']
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await update.message.reply_text("❌ Сделка не найдена")
        clear_user_step(user_id)
        return
    
    # Проверяем, что это продавец
    if deal.get('seller_id') != user_id:
        await update.message.reply_text("❌ Вы не продавец в этой сделке")
        clear_user_step(user_id)
        return
    
    deal['bank_name'] = bank
    deal['status'] = 'waiting_for_item_data'
    deal['seller_ready'] = True
    save_data(DEALS_FILE, deals)
    clear_user_step(user_id)
    
    await update.message.reply_text(
        "✅ Карта сохранена!\n\n"
        "📦 **Теперь отправьте данные товара** (логин, пароль, код и т.д.):\n"
        "Эти данные получит покупатель после подтверждения админа.\n\n"
        "⚠️ Без данных товара сделка не будет завершена!"
    )
    
    # Устанавливаем следующий шаг - ввод данных товара
    set_user_step(user_id, 'waiting_for_item_data', deal_id=deal_id)

async def handle_item_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение данных товара от продавца"""
    user_id = update.effective_user.id
    user_data = load_user_data().get(str(user_id), {})
    
    if user_data.get('step') != 'waiting_for_item_data':
        return
    
    item_data = update.message.text
    deal_id = user_data['deal_id']
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await update.message.reply_text("❌ Сделка не найдена")
        clear_user_step(user_id)
        return
    
    # Проверяем, что это продавец
    if deal.get('seller_id') != user_id:
        await update.message.reply_text("❌ Вы не продавец в этой сделке")
        clear_user_step(user_id)
        return
    
    deal['item_data'] = item_data
    deal['status'] = 'waiting_admin_confirm'
    save_data(DEALS_FILE, deals)
    clear_user_step(user_id)
    
    await update.message.reply_text("✅ Данные товара сохранены! Ожидайте подтверждения администратора.")
    
    # Уведомление покупателю
    if deal['buyer_id']:
        try:
            await context.bot.send_message(
                chat_id=deal['buyer_id'],
                text=f"📦 Продавец подтвердил передачу товара по сделке #{deal_id}!\n\n"
                     f"💳 Карта продавца: {deal['card_number']} ({deal['bank_name']})\n"
                     f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
                     f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
                     f"⏳ Ожидайте подтверждения администратора.\n"
                     f"После подтверждения вы получите данные товара."
            )
        except:
            pass
    
    # Уведомление админу с кнопкой
    admin_keyboard = [[InlineKeyboardButton("✅ Завершить сделку", callback_data=f"approve_{deal_id}")]]
    
    # Отправляем админу скриншот оплаты
    if deal.get('screenshot'):
        try:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=deal['screenshot'],
                caption=f"✅ **Сделка #{deal_id} готова к завершению!**\n\n"
                        f"📦 Предмет: {deal['product']}\n"
                        f"👤 Продавец: @{deal['seller_username']}\n"
                        f"💳 Карта: {deal['card_number']} ({deal['bank_name']})\n"
                        f"👤 Покупатель: @{deal['buyer_username']}\n"
                        f"💰 Твоя комиссия: {COMMISSION}%\n\n"
                        f"📦 Данные товара:\n`{deal['item_data']}`\n\n"
                        f"🖼️ Скриншот оплаты (выше)\n"
                        f"Товар передан ✅",
                reply_markup=InlineKeyboardMarkup(admin_keyboard),
                parse_mode="Markdown"
            )
        except:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✅ **Сделка #{deal_id} готова к завершению!**\n\n"
                     f"📦 Предмет: {deal['product']}\n"
                     f"👤 Продавец: @{deal['seller_username']}\n"
                     f"💳 Карта: {deal['card_number']} ({deal['bank_name']})\n"
                     f"👤 Покупатель: @{deal['buyer_username']}\n"
                     f"💰 Твоя комиссия: {COMMISSION}%\n\n"
                     f"📦 Данные товара:\n{deal['item_data']}\n\n"
                     f"Покупатель оплатил ✅\n"
                     f"Товар передан ✅",
                reply_markup=InlineKeyboardMarkup(admin_keyboard),
                parse_mode="Markdown"
            )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ **Сделка #{deal_id} готова к завершению!**\n\n"
                 f"📦 Предмет: {deal['product']}\n"
                 f"👤 Продавец: @{deal['seller_username']}\n"
                 f"💳 Карта: {deal['card_number']} ({deal['bank_name']})\n"
                 f"👤 Покупатель: @{deal['buyer_username']}\n"
                 f"💰 Твоя комиссия: {COMMISSION}%\n\n"
                 f"📦 Данные товара:\n{deal['item_data']}\n\n"
                 f"Покупатель оплатил ✅\n"
                 f"Товар передан ✅",
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )

# ========== ПОДТВЕРЖДЕНИЕ АДМИНА ==========
async def handle_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ завершает сделку"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("⛔ Нет прав")
        return
    
    deal_id = query.data.replace('approve_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    deal['status'] = 'completed'
    save_data(DEALS_FILE, deals)
    
    # Уведомление продавцу
    if deal['seller_id']:
        try:
            await context.bot.send_message(
                chat_id=deal['seller_id'],
                text=f"✅ **Сделка #{deal_id} завершена!**\n\n"
                     f"📦 Предмет: {deal['product']}\n"
                     f"💰 Комиссия гаранта {COMMISSION}% удержана.\n\n"
                     f"💳 Деньги будут отправлены на карту {deal['card_number']} ({deal['bank_name']})\n\n"
                     f"Спасибо! {REVIEW_TAG}"
            )
        except:
            pass
    
    # Уведомление покупателю с данными товара
    if deal['buyer_id']:
        item_data_text = f"\n\n📦 **Данные товара:**\n`{deal['item_data']}`" if deal.get('item_data') else ""
        try:
            await context.bot.send_message(
                chat_id=deal['buyer_id'],
                text=f"✅ **Сделка #{deal_id} завершена!**\n\n"
                     f"📦 Предмет: {deal['product']}{item_data_text}\n\n"
                     f"💰 Комиссия гаранта {COMMISSION}% удержана.\n\n"
                     f"Спасибо за покупку! {REVIEW_TAG}",
                parse_mode="Markdown"
            )
        except:
            pass
    
    await query.edit_message_text(
        f"✅ Сделка #{deal_id} завершена!\n"
        f"💰 Твоя комиссия {COMMISSION}%"
    )

# ========== АДМИН ПАНЕЛЬ ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ панель"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    
    total = len(deals)
    waiting = sum(1 for d in deals.values() if d['status'] == 'waiting_confirmation')
    payment = sum(1 for d in deals.values() if d['status'] == 'waiting_for_payment')
    waiting_item = sum(1 for d in deals.values() if d['status'] == 'waiting_for_item_data')
    confirm = sum(1 for d in deals.values() if d['status'] == 'waiting_admin_confirm')
    
    # НЕОДОБРЕННЫЕ СДЕЛКИ - все, кроме завершенных и ожидающих второго участника
    not_approved = sum(1 for d in deals.values() 
                      if d['status'] not in ['completed', 'waiting_for_second_user'])
    
    keyboard = [
        [InlineKeyboardButton(f"⏳ Ожидают подтверждения ({waiting})", callback_data="admin_waiting")],
        [InlineKeyboardButton(f"💰 Ожидают оплату ({payment})", callback_data="admin_payment")],
        [InlineKeyboardButton(f"📦 Ожидают данные товара ({waiting_item})", callback_data="admin_item_data")],
        [InlineKeyboardButton(f"👑 Готовы к завершению ({confirm})", callback_data="admin_ready")],
        [InlineKeyboardButton(f"📋 НЕОДОБРЕННЫЕ СДЕЛКИ ({not_approved})", callback_data="admin_not_approved")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    
    text = (
        f"👑 **Админ панель**\n\n"
        f"📊 Всего сделок: {total}\n"
        f"⏳ Ожидают подтверждения: {waiting}\n"
        f"💰 Ожидают оплату: {payment}\n"
        f"📦 Ожидают данные товара: {waiting_item}\n"
        f"✅ Готовы к завершению: {confirm}\n"
        f"📋 Неодобренные сделки: {not_approved}\n"
        f"💵 Твоя комиссия: {COMMISSION}%"
    )
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_waiting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сделки, ожидающие подтверждения участников"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    waiting = []
    
    for deal_id, deal in deals.items():
        if deal['status'] == 'waiting_confirmation':
            waiting.append((deal_id, deal))
    
    if not waiting:
        await query.edit_message_text(
            "✅ Нет ожидающих",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
            ]])
        )
        return
    
    text = "⏳ **Сделки, ожидающие подтверждения:**\n\n"
    keyboard = []
    
    for deal_id, deal in waiting:
        status = (f"Продавец: {'✅' if deal.get('seller_confirm') else '❌'} | "
                  f"Покупатель: {'✅' if deal.get('buyer_confirm') else '❌'}")
        text += f"🔹 #{deal_id}: {deal['product']}\n   {status}\n   💰 Комиссия: {COMMISSION}%\n\n"
        
        # Кнопка для админа (подтвердить за двоих)
        keyboard.append([InlineKeyboardButton(f"✅ Подтвердить #{deal_id} (за двоих)", callback_data=f"admin_confirm_both_{deal_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сделки, ожидающие оплату"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    payment = []
    
    for deal_id, deal in deals.items():
        if deal['status'] == 'waiting_for_payment':
            payment.append((deal_id, deal))
    
    if not payment:
        await query.edit_message_text(
            "✅ Нет сделок, ожидающих оплату",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
            ]])
        )
        return
    
    text = "💰 **Сделки, ожидающие оплату:**\n\n"
    
    for deal_id, deal in payment:
        text += f"🔹 #{deal_id}: {deal['product']}\n"
        text += f"   Продавец: @{deal['seller_username']}\n"
        text += f"   Покупатель: @{deal['buyer_username']}\n"
        text += f"   💰 Комиссия: {COMMISSION}%\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_item_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сделки, ожидающие данные товара"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    item_waiting = []
    
    for deal_id, deal in deals.items():
        if deal['status'] == 'waiting_for_item_data':
            item_waiting.append((deal_id, deal))
    
    if not item_waiting:
        await query.edit_message_text(
            "✅ Нет сделок, ожидающих данные товара",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
            ]])
        )
        return
    
    text = "📦 **Сделки, ожидающие данные товара:**\n\n"
    
    for deal_id, deal in item_waiting:
        text += f"🔹 #{deal_id}: {deal['product']}\n"
        text += f"   Продавец: @{deal['seller_username']}\n"
        text += f"   💳 Карта: {deal.get('card_number', '?')}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сделки, готовые к завершению"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    ready = []
    
    for deal_id, deal in deals.items():
        if deal['status'] == 'waiting_admin_confirm':
            ready.append((deal_id, deal))
    
    if not ready:
        await query.edit_message_text(
            "✅ Нет готовых сделок",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
            ]])
        )
        return
    
    text = "👑 **Сделки, готовые к завершению:**\n\n"
    keyboard = []
    
    for deal_id, deal in ready:
        text += f"🔹 #{deal_id}: {deal['product']}\n"
        text += f"   💳 Карта: {deal.get('card_number', '?')} ({deal.get('bank_name', '?')})\n"
        text += f"   📦 Данные: {deal.get('item_data', '?')[:50]}...\n"
        text += f"   💰 Твоя комиссия: {COMMISSION}%\n\n"
        keyboard.append([InlineKeyboardButton(f"✅ Завершить #{deal_id}", callback_data=f"approve_{deal_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_not_approved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех неодобренных сделок (все, кроме завершенных и ожидающих второго)"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    not_approved = []
    
    # Собираем все сделки, кроме завершенных и ожидающих второго участника
    for deal_id, deal in deals.items():
        if deal['status'] not in ['completed', 'waiting_for_second_user']:
            not_approved.append((deal_id, deal))
    
    if not not_approved:
        await query.edit_message_text(
            "✅ Нет неодобренных сделок",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
            ]])
        )
        return
    
    # Группируем по статусам
    status_groups = {
        'waiting_confirmation': '⏳ Ожидают подтверждения',
        'waiting_for_payment': '💰 Ожидают оплату',
        'waiting_screenshot': '📸 Ждут скриншот оплаты',
        'screenshot_received': '📸 Скриншот получен',
        'waiting_for_card': '💳 Ждут карту',
        'waiting_for_item_data': '📦 Ждут данные товара',
        'waiting_admin_confirm': '👑 Готовы к завершению'
    }
    
    text = "📋 **НЕОДОБРЕННЫЕ СДЕЛКИ**\n\n"
    text += f"Всего: {len(not_approved)}\n\n"
    
    # Сортируем по статусам
    for status_code, status_text in status_groups.items():
        status_deals = [(did, d) for did, d in not_approved if d['status'] == status_code]
        if status_deals:
            text += f"**{status_text}** ({len(status_deals)}):\n"
            for deal_id, deal in status_deals:
                text += f"  🔹 #{deal_id}: {deal['product']}\n"
                text += f"    👤 Продавец: @{deal['seller_username'] or '?'}\n"
                text += f"    👤 Покупатель: @{deal['buyer_username'] or '?'}\n"
                if deal.get('card_number'):
                    text += f"    💳 Карта: {deal['card_number']}\n"
                text += "\n"
    
    # Добавляем кнопки для быстрого перехода к каждой категории
    keyboard = [
        [InlineKeyboardButton("⏳ К ожидающим подтверждения", callback_data="admin_waiting")],
        [InlineKeyboardButton("💰 К ожидающим оплату", callback_data="admin_payment")],
        [InlineKeyboardButton("📦 К данным товара", callback_data="admin_item_data")],
        [InlineKeyboardButton("👑 К готовым", callback_data="admin_ready")],
        [InlineKeyboardButton("🔙 Назад в админку", callback_data="admin_panel")]
    ]
    
    # Если текст слишком длинный, отправляем как файл
    if len(text) > 4000:
        # Сохраняем в файл
        filename = f"not_approved_deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Отправляем файлом
        with open(filename, 'rb') as f:
            await context.bot.send_document(
                chat_id=ADMIN_ID,
                document=f,
                filename=filename,
                caption="📋 Полный список неодобренных сделок",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Удаляем файл
        os.remove(filename)
        
        await query.edit_message_text(
            "✅ Список неодобренных сделок отправлен файлом (слишком большой для сообщения)",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
            ]])
        )
    else:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    
    total = len(deals)
    completed = sum(1 for d in deals.values() if d['status'] == 'completed')
    waiting_second = sum(1 for d in deals.values() if d['status'] == 'waiting_for_second_user')
    waiting_confirm = sum(1 for d in deals.values() if d['status'] == 'waiting_confirmation')
    waiting_payment = sum(1 for d in deals.values() if d['status'] == 'waiting_for_payment')
    waiting_screenshot = sum(1 for d in deals.values() if d['status'] == 'waiting_screenshot')
    waiting_card = sum(1 for d in deals.values() if d['status'] == 'waiting_for_card')
    waiting_item = sum(1 for d in deals.values() if d['status'] == 'waiting_for_item_data')
    waiting_admin = sum(1 for d in deals.values() if d['status'] == 'waiting_admin_confirm')
    
    # Неодобренные сделки (все, кроме завершенных и ожидающих второго)
    not_approved = total - completed - waiting_second
    
    # Примерный расчёт дохода (предположим средняя сумма 1000₽)
    estimated_income = completed * 1000 * COMMISSION / 100
    
    text = (
        f"📊 **Статистика**\n\n"
        f"📌 Всего: {total}\n"
        f"✅ Завершено: {completed}\n"
        f"⏳ Ожидание 2-го: {waiting_second}\n"
        f"⏳ Подтверждение: {waiting_confirm}\n"
        f"💰 Ожидание оплаты: {waiting_payment}\n"
        f"📸 Скриншот оплаты: {waiting_screenshot}\n"
        f"💳 Карта: {waiting_card}\n"
        f"📦 Данные товара: {waiting_item}\n"
        f"👑 Готово: {waiting_admin}\n"
        f"📋 **НЕОДОБРЕННЫЕ: {not_approved}**\n\n"
        f"💰 **Твой доход:**\n"
        f"• Комиссия: {COMMISSION}%\n"
        f"• Примерно: {estimated_income:.0f}₽ (при 1000₽/сделка)"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_confirm_both(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ подтверждает за двоих"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deal_id = query.data.replace('admin_confirm_both_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    # Подтверждаем за обоих
    deal['seller_confirm'] = True
    deal['buyer_confirm'] = True
    deal['status'] = 'waiting_for_payment'
    save_data(DEALS_FILE, deals)
    
    # Уведомление продавцу
    if deal['seller_id']:
        try:
            await context.bot.send_message(
                chat_id=deal['seller_id'],
                text=f"👑 **Администратор подтвердил ваше участие в сделке #{deal_id}!**\n\n"
                     f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
                     f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
                     f"Ожидайте оплаты от покупателя."
            )
        except:
            pass
    
    # Уведомление покупателю с кнопкой оплаты
    if deal['buyer_id']:
        try:
            await context.bot.send_message(
                chat_id=deal['buyer_id'],
                text=f"👑 **Администратор подтвердил сделку #{deal_id}!**\n\n"
                     f"📦 Предмет: {deal['product']}\n"
                     f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
                     f"⚠️ **Важно!** Деньги или товар не будут получены ни одной из сторон до подтверждения администратора!\n\n"
                     f"Теперь оплатите:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💳 Оплатить", callback_data=f"pay_{deal_id}")
                ]]),
                parse_mode="Markdown"
            )
        except:
            pass
    
    await query.edit_message_text(f"✅ Сделка #{deal_id} подтверждена за обоих!\n💰 Твоя комиссия {COMMISSION}%")

# ========== ОБЩИЙ ОБРАБОТЧИК ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Общий обработчик"""
    user_id = update.effective_user.id
    step = get_user_step(user_id)
    
    # Если это фото
    if update.message.photo:
        # Только покупатель может отправлять скриншот оплаты
        await handle_screenshot(update, context)
        return
    
    # Если это текст
    if step == 'writing_to_admin':
        await handle_message_to_admin(update, context)
    elif step == 'waiting_for_username':
        await handle_username(update, context)
    elif step == 'waiting_for_product':
        await handle_product(update, context)
    elif step == 'waiting_for_card':
        await handle_card_number(update, context)
    elif step == 'waiting_for_bank':
        await handle_bank_name(update, context)
    elif step == 'waiting_for_item_data':
        await handle_item_data(update, context)

# ========== ЗАПУСК ==========
def main():
    print("🚀 Запуск гарант-бота...")
    ensure_files_exist()
    print(f"✅ Твоя комиссия: {COMMISSION}%")
    print("✅ Бот работает! (логи отключены)")
    
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mydeals", mydeals_command))
    app.add_handler(CommandHandler("reviews", reviews_command))
    app.add_handler(CommandHandler("messages", messages_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    
    # Меню
    app.add_handler(CallbackQueryHandler(new_deal, pattern="^new_deal$"))
    app.add_handler(CallbackQueryHandler(show_my_deals, pattern="^my_deals$"))
    app.add_handler(CallbackQueryHandler(show_my_reviews, pattern="^my_reviews$"))
    app.add_handler(CallbackQueryHandler(write_to_admin, pattern="^write_to_admin$"))
    app.add_handler(CallbackQueryHandler(help_menu, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    
    # Админка
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(admin_waiting, pattern="^admin_waiting$"))
    app.add_handler(CallbackQueryHandler(admin_payment, pattern="^admin_payment$"))
    app.add_handler(CallbackQueryHandler(admin_item_data, pattern="^admin_item_data$"))
    app.add_handler(CallbackQueryHandler(admin_ready, pattern="^admin_ready$"))
    app.add_handler(CallbackQueryHandler(admin_not_approved, pattern="^admin_not_approved$"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_confirm_both, pattern="^admin_confirm_both_"))
    
    # Сделки
    app.add_handler(CallbackQueryHandler(join_deal, pattern="^join_"))
    app.add_handler(CallbackQueryHandler(handle_role, pattern="^role_"))
    app.add_handler(CallbackQueryHandler(handle_confirm, pattern="^confirm_seller_"))
    app.add_handler(CallbackQueryHandler(handle_confirm, pattern="^confirm_buyer_"))
    app.add_handler(CallbackQueryHandler(handle_pay, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(handle_delivered, pattern="^delivered_"))
    app.add_handler(CallbackQueryHandler(handle_approve, pattern="^approve_"))
    
    # Сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
