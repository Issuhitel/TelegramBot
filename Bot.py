import asyncio
import random
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

# Замените 'YOUR_API_TOKEN' на ваш токен от @BotFather
API_TOKEN = '7561063983:AAFVetZjfYBIrCvdwpRdnBor0QVBl84GY94'

# Правила чата (настройте под себя)
CHAT_RULES = """
Привет новичок

🗓 Правила чата

1. Мастер Шип (автор) есть закон. Он будет карать и миловать по советам звёзд и мало, кто может предугадать его действия.
2. Инквизиция не дремлет. Запрещено распространять непристойные, запрещённые и шокирующие материалы (представьте, что чат 12+, как в мультиках Дисней). 
3. Все равны, но порядок превыше всего. Будьте рассудительны и ведите дискуссии порядочно, а так же не обсуждайте современную политику - это бесконечный спор.
4. Четыре равно три.
Слава Каштану! 🌰🐀
"""

# Словарь для хранения мутов (user_id: unmute_time)
MUTED_USERS = {}

# Приветствие нового участника
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        if new_member.is_bot:
            continue
            
        welcome_text = f"""
🌰 Добро пожаловать, {new_member.first_name}!

Ты попал в Частный Частный Чат! 
Здесь страждущие и жаждущие общения!

{CHAT_RULES}

Рады видеть тебя среди ореховых душ! 🎉
        """
        
        await update.message.reply_text(welcome_text)

# Команда /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(
        f"🌰 Привет, {user_name}! Я Страж каштана - хранитель этого чата!\n\n"
        f"Я слежу за порядком и приветствую новых участников.\n"
        f"Напиши /help чтобы узнать мои команды."
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🌰 Помощь по командам Стража каштана:

👮‍♂️ Команды модерации (только для модераторов):
/mute @username время_в_минутах [причина] - выдать мут
/unmute @username - снять мут
/mutelist - список заблокированных

📜 Правила:
/rules - показать правила чата

⚔️ Дуэль:
/duel @username - вызвать на дуэль

🎯 Прочие:
/start - начать работу
/help - показать справку

Служу ореховому сообществу! 🌰
    """
    await update.message.reply_text(help_text)

# Команда /rules - показать правила
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(CHAT_RULES)

# Команда /mute - выдать мут (только для модераторов)
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user = update.message.from_user
    
    # Проверяем права модератора
    if not await is_user_moderator(update, context, user.id):
        await update.message.reply_text("❌ Только модераторы могут выдавать мут!")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Используйте: /mute @username время_в_минутах [причина]")
        return
    
    # Парсим аргументы
    target_username = context.args[0].replace('@', '')
    try:
        mute_minutes = int(context.args[1])
        reason = ' '.join(context.args[2:]) if len(context.args) > 2 else "Нарушение правил чата"
    except ValueError:
        await update.message.reply_text("Укажите корректное время в минутах!")
        return
    
    try:
        # Получаем информацию о пользователе
        chat_member = await context.bot.get_chat_member(chat_id, target_username)
        target_user = chat_member.user
        
        # Выдаем мут
        until_date = int(asyncio.get_event_loop().time()) + (mute_minutes * 60)
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            ),
            until_date=until_date
        )
        
        # Сохраняем информацию о муте
        MUTED_USERS[target_user.id] = until_date
        
        await update.message.reply_text(
            f"🔇 Страж каштана выдал мут пользователю @{target_username} на {mute_minutes} минут.\n"
            f"🌰 Причина: {reason}\n"
            f"Соблюдайте ореховую гармонию! 🚫"
        )
        
    except BadRequest as e:
        if "user not found" in str(e).lower():
            await update.message.reply_text("❌ Пользователь не найден в чате!")
        else:
            await update.message.reply_text("❌ Ошибка при выдаче мута!")
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка!")

# Команда /unmute - снять мут (только для модераторов)
async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user = update.message.from_user
    
    if not await is_user_moderator(update, context, user.id):
        await update.message.reply_text("❌ Только модераторы могут снимать мут!")
        return
    
    if not context.args:
        await update.message.reply_text("Используйте: /unmute @username")
        return
    
    target_username = context.args[0].replace('@', '')
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id, target_username)
        target_user = chat_member.user
        
        # Снимаем ограничения
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        
        # Удаляем из списка мутов
        if target_user.id in MUTED_USERS:
            del MUTED_USERS[target_user.id]
        
        await update.message.reply_text(
            f"🌰 Страж каштана снял мут с пользователя @{target_username}!\n"
            f"Снова можно щелкать каштаны! ✅"
        )
        
    except BadRequest:
        await update.message.reply_text("❌ Пользователь не найден в чате!")
    except Exception:
        await update.message.reply_text("❌ Произошла ошибка!")

# Команда /mutelist - список заблокированных (только для модераторов)
async def mutelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_moderator(update, context, update.message.from_user.id):
        await update.message.reply_text("❌ Только модераторы могут просматривать список!")
        return
    
    if not MUTED_USERS:
        await update.message.reply_text("🌰 Нет пользователей в муте! Ореховый порядок! ✅")
        return
    
    mute_list = "🔇 Пользователи в муте:\n\n"
    
    for user_id, unmute_time in MUTED_USERS.items():
        try:
            user = await context.bot.get_chat_member(update.message.chat_id, user_id)
            time_left = int(unmute_time - asyncio.get_event_loop().time())
            minutes_left = max(0, time_left // 60)
            
            mute_list += f"👤 @{user.user.username} - осталось {minutes_left} минут\n"
        except:
            mute_list += f"👤 ID {user_id} - осталось {minutes_left} минут\n"
    
    await update.message.reply_text(mute_list)

# Мини-игра дуэль
async def duel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи противника: /duel @username")
        return
    
    target_username = context.args[0].replace('@', '')
    challenger = update.message.from_user
    
    # Простая дуэль с random
    winner = random.choice([challenger.first_name, target_username])
    weapons = ["каштаном", "орехом", "скорлупой", "веткой"]
    weapon = random.choice(weapons)
    
    await update.message.reply_text(
        f"⚔️ {challenger.first_name} вызывает на дуэль @{target_username}!\n\n"
        f"🌰 Дуэль начинается! Противники сражаются {weapon}!\n\n"
        f"🏆 Победитель: {winner}!\n"
        f"Слава ореховому герою! 👑"
    )

# Проверка является ли пользователь модератором
async def is_user_moderator(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    # Здесь можно добавить проверку по конкретным user_id модераторов
    # Например: return user_id in [123456789, 987654321]
    
    # Или проверять права в чате (админ/создатель)
    chat_id = update.message.chat_id
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ['administrator', 'creator']
    except:
        return False

# Обработчик ошибок
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Произошла ошибка: {context.error}')

def main():
    # Создаем Application объект
    application = Application.builder().token(API_TOKEN).build()

    # Обработчики для приветствия новых участников
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # Основные команды
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('rules', rules_command))
    application.add_handler(CommandHandler('mute', mute_command))
    application.add_handler(CommandHandler('unmute', unmute_command))
    application.add_handler(CommandHandler('mutelist', mutelist_command))
    application.add_handler(CommandHandler('duel', duel_command))

    # Обработчик ошибок
    application.add_error_handler(error)

    # Запускаем бота
    print('🌰 Страж каштана запущен! 🤖')
    print('Функции: приветствие новых участников, мут/анмут, правила чата, дуэль')
    application.run_polling()

if __name__ == '__main__':
    main()
