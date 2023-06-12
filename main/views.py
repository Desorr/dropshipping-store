from django.shortcuts import render
from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError
import asyncio


def index(request):
    return render(request, 'index.html')


def about_us(request):
    return render(request, 'about-us.html')


async def send_telegram_message(chat_id, text):
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=text)


def contacts(request):
    if request.method == 'POST':
        # Получение данных из формы
        name = request.POST.get('first-name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        message = request.POST.get('message')

        try:
            # Отправка данных в Telegram
            chat_id = int(settings.TELEGRAM_CHAT_ID)
            text = f"Нужна помощь:\n\nИмя: {name}\nТелефон: {phone}\nE-mail: {email}\nСообщение: {message}"
            asyncio.run(send_telegram_message(chat_id, text))

        except TelegramError as e:
            print(f"Ошибка при отправке сообщения в Telegram: {e}")

    # Возвращение страницы с формой для GET-запроса
    return render(request, 'contacts.html')
