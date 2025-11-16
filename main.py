from telebot import TeleBot, types
import requests
import logging
import json
from messages import start_message, help_message, reset_message
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
API_KEY = os.getenv('API_KEY')
API_URL = os.getenv('API_URL')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


user_context = {}

bot = TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_messages(message):
    user_id = message.chat.id
    user_context[user_id] = []
    bot.send_message(message.chat.id, start_message)

@bot.message_handler(commands=['help'])
def help_messages(message):
    bot.send_message(message.chat.id, help_message)

def chatgpt_response(user_id, user_message):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Формируем запрос к OpenRouter API
    data = {
        "model": "openai/gpt-oss-20b:free",
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "extra_body": {"reasoning": {"enabled": True}}
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Проверка на ошибки в ответе сервера
        response_data = response.json()
        
        answer = response_data['choices'][0]['message']['content']
        user_context[user_id].append(user_message)  # Сохраняем сообщение пользователя
        user_context[user_id].append(answer)  # Сохраняем ответ

        return answer
    except Exception as e:
        logger.error(f"Ошибка от OpenRouter API: {e}")
        return "Извините, произошла ошибка при обращении к ChatGPT."

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("Новый запрос")
    markup.add(button)
    user_id = message.chat.id
    user_message = message.text
    answer = chatgpt_response(user_id, user_message)
    bot.send_message(user_id, answer, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Новый запрос")
def reset_context(message):
    user_id = message.chat.id
    user_context[user_id] = []
    bot.send_message(message.chat.id, reset_message)

if __name__ == '__main__':
    bot.polling(non_stop=True)
