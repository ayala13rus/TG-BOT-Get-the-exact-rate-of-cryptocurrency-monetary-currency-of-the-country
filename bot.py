import telebot
from telebot import types
import requests
import json
from datetime import datetime
import time
import threading
import sys
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

telebot.apihelper.ENABLE_MIDDLEWARE = True

TOKEN = 'сюда свой приписюнить'

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=5)

subscriptions = {}

user_preferences = {}

POPULAR_CRYPTOS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'TON': 'the-open-network',
    'USDT': 'tether'
}

def get_rub_usd_rate():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        data = json.loads(response.text)
        return data["rates"]["RUB"]
    except Exception as e:
        logger.error(f"Ошибка при получении курса RUB/USD: {str(e)}")
        return 75.0  

def get_crypto_price(crypto_symbol, currency="USD"):
    try:
        coin_id = POPULAR_CRYPTOS.get(crypto_symbol, crypto_symbol.lower())
        
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = json.loads(response.text)
        
        if 'market_data' in data:
            if currency == "USD":
                price = data["market_data"]["current_price"]["usd"]
                market_cap = data["market_data"]["market_cap"]["usd"]
                volume_24h = data["market_data"]["total_volume"]["usd"]
                currency_symbol = "$"
            else:  
                price = data["market_data"]["current_price"]["rub"]
                market_cap = data["market_data"]["market_cap"]["rub"]
                volume_24h = data["market_data"]["total_volume"]["rub"]
                currency_symbol = "₽"
            
            change_24h = data["market_data"]["price_change_percentage_24h"]
            
            result = f"💰 *{crypto_symbol}* ({data['name']})\n\n"
            result += f"💵 Цена: {currency_symbol}{price:.4f}\n"
            
            if change_24h > 0:
                result += f"📈 Изменение (24ч): +{change_24h:.2f}%\n"
            else:
                result += f"📉 Изменение (24ч): {change_24h:.2f}%\n"
                
            result += f"🏦 Рыночная капитализация: {currency_symbol}{market_cap:.2f}\n"
            result += f"🔄 Объем торгов (24ч): {currency_symbol}{volume_24h:.2f}"
            
            return result
        else:
            if 'error' in data:
                logger.error(f"API CoinGecko вернул ошибку: {data['error']}")
                return f"Ошибка API CoinGecko. Пожалуйста, повторите запрос позже."
            return f"Криптовалюта {crypto_symbol} не найдена или недоступна."
    except Exception as e:
        logger.error(f"Ошибка при получении данных о {crypto_symbol}: {str(e)}")
        return f"Ошибка при получении данных о {crypto_symbol}. Пожалуйста, повторите запрос позже."

def get_crypto_price_short(crypto_symbol, currency="USD"):
    try:
        coin_id = POPULAR_CRYPTOS.get(crypto_symbol, crypto_symbol.lower())
        
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = json.loads(response.text)
        
        if 'market_data' in data:
            if currency == "USD":
                price = data["market_data"]["current_price"]["usd"]
                currency_symbol = "$"
            else:  
                price = data["market_data"]["current_price"]["rub"]
                currency_symbol = "₽"
            
            change_24h = data["market_data"]["price_change_percentage_24h"]
                
            return f"{crypto_symbol}: {currency_symbol}{price:.4f} (24ч: {change_24h:.2f}%)"
        else:
            if 'error' in data:
                logger.error(f"API CoinGecko вернул ошибку: {data['error']}")
                return f"Ошибка API при получении данных о {crypto_symbol}"
            return f"Криптовалюта {crypto_symbol} не найдена или недоступна."
    except Exception as e:
        logger.error(f"Ошибка при получении данных о {crypto_symbol}: {str(e)}")
        return f"Ошибка при получении данных о {crypto_symbol}"

def search_crypto(query):
    try:
        url = f"https://api.coingecko.com/api/v3/search?query={query}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = json.loads(response.text)
        
        if 'coins' in data and len(data['coins']) > 0:
            return data['coins'][0]['id']
        else:
            return None
    except Exception as e:
        logger.error(f"Ошибка при поиске криптовалюты: {str(e)}")
        return None

def get_currency_rate(currency_code, base_currency="USD"):
    try:
        url = f"https://open.er-api.com/v6/latest/{base_currency}"
        response = requests.get(url, timeout=10)
        data = json.loads(response.text)
        
        if currency_code in data["rates"]:
            rate = data["rates"][currency_code]
            
            if base_currency == "USD":
                return f"{currency_code}: {rate:.2f} за 1 USD"
            elif base_currency == "RUB":
                return f"{currency_code}: {rate:.2f} за 1 RUB"
        else:
            return f"Валюта {currency_code} не найдена."
    except Exception as e:
        logger.error(f"Ошибка при получении данных о {currency_code}: {str(e)}")
        return f"Ошибка при получении данных о {currency_code}. Пожалуйста, повторите запрос позже."

def get_user_currency(chat_id):
    if chat_id in user_preferences and "currency" in user_preferences[chat_id]:
        return user_preferences[chat_id]["currency"]
    return "USD"  

update_thread_running = True

def send_updates():
    while update_thread_running:
        try:
            for chat_id, symbols in subscriptions.items():
                try:
                    if symbols:
                        currency = get_user_currency(chat_id)
                        message = "Обновление курсов:\n\n"
                        for symbol in symbols:
                            if symbol.startswith("CRYPTO_"):
                                crypto_symbol = symbol[7:]
                                message += get_crypto_price_short(crypto_symbol, currency) + "\n"
                            else:
                                message += get_currency_rate(symbol) + "\n"
                        bot.send_message(chat_id, message)
                except Exception as e:
                    logger.error(f"Ошибка при отправке обновления для {chat_id}: {str(e)}")
            time.sleep(3600)  
        except Exception as e:
            logger.error(f"Ошибка в потоке обновлений: {str(e)}")
            time.sleep(60)  

update_thread = threading.Thread(target=send_updates, daemon=True)
update_thread.start()

def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    btn_crypto = types.InlineKeyboardButton("💰 Криптовалюты", callback_data="show_crypto_menu")
    btn_currency = types.InlineKeyboardButton("💱 Валюты", callback_data="show_currency_menu")
    btn_settings = types.InlineKeyboardButton("⚙️ Настройки", callback_data="show_settings")
    btn_subscriptions = types.InlineKeyboardButton("📊 Мои подписки", callback_data="show_subscriptions")
    
    keyboard.add(btn_crypto, btn_currency)
    keyboard.add(btn_settings, btn_subscriptions)
    
    return keyboard

def get_crypto_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    btn_btc = types.InlineKeyboardButton("Bitcoin (BTC)", callback_data="crypto_BTC")
    btn_eth = types.InlineKeyboardButton("Ethereum (ETH)", callback_data="crypto_ETH")
    btn_ton = types.InlineKeyboardButton("Toncoin (TON)", callback_data="crypto_TON")
    btn_usdt = types.InlineKeyboardButton("Tether (USDT)", callback_data="crypto_USDT")
    btn_search = types.InlineKeyboardButton("🔍 Поиск другой криптовалюты", callback_data="search_crypto")
    btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    
    keyboard.add(btn_btc, btn_eth)
    keyboard.add(btn_ton, btn_usdt)
    keyboard.add(btn_search)
    keyboard.add(btn_back)
    
    return keyboard

def get_currency_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    btn_eur = types.InlineKeyboardButton("Евро (EUR)", callback_data="currency_EUR")
    btn_rub = types.InlineKeyboardButton("Рубль (RUB)", callback_data="currency_RUB")
    btn_cny = types.InlineKeyboardButton("Юань (CNY)", callback_data="currency_CNY")
    btn_gbp = types.InlineKeyboardButton("Фунт (GBP)", callback_data="currency_GBP")
    btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    
    keyboard.add(btn_eur, btn_rub)
    keyboard.add(btn_cny, btn_gbp)
    keyboard.add(btn_back)
    
    return keyboard

def get_settings_keyboard(chat_id):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    currency = get_user_currency(chat_id)
    
    if currency == "USD":
        btn_currency = types.InlineKeyboardButton("💱 Валюта: USD", callback_data="switch_currency")
    else:
        btn_currency = types.InlineKeyboardButton("💱 Валюта: RUB", callback_data="switch_currency")
    
    btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    
    keyboard.add(btn_currency)
    keyboard.add(btn_back)
    
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        welcome_text = "Добро пожаловать! Я бот для отслеживания курсов валют и криптовалют."
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {str(e)}")
        bot.send_message(message.chat.id, "Произошла ошибка при запуске бота. Пожалуйста, повторите попытку позже.")

user_states = {}

@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id] == "waiting_for_crypto")
def handle_crypto_search(message):
    chat_id = message.chat.id
    try:
        user_states.pop(chat_id, None)  
        
        query = message.text.strip()
        bot.send_message(chat_id, f"🔍 Ищу криптовалюту: {query}...")
        
        coin_id = search_crypto(query)
        if coin_id:
            currency = get_user_currency(chat_id)
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            data = json.loads(response.text)
            
            if 'symbol' in data:
                symbol = data['symbol'].upper()
                
                if symbol not in POPULAR_CRYPTOS:
                    POPULAR_CRYPTOS[symbol] = coin_id
                
                result = get_crypto_price(symbol, currency)
                
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                btn_subscribe = types.InlineKeyboardButton("📈 Подписаться", callback_data=f"subscribe_crypto_{symbol}")
                btn_back = types.InlineKeyboardButton("🔙 К списку криптовалют", callback_data="show_crypto_menu")
                keyboard.add(btn_subscribe, btn_back)
                
                bot.send_message(chat_id, result, reply_markup=keyboard, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, "Не удалось получить информацию о криптовалюте. Попробуйте другой запрос.")
        else:
            bot.send_message(chat_id, "Криптовалюта не найдена. Попробуйте другой запрос.", reply_markup=get_crypto_keyboard())
    except Exception as e:
        logger.error(f"Ошибка при поиске криптовалюты: {str(e)}")
        bot.send_message(chat_id, "Произошла ошибка при поиске. Пожалуйста, попробуйте позже.", reply_markup=get_crypto_keyboard())
        user_states.pop(chat_id, None)  

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_preferences:
        user_preferences[chat_id] = {"currency": "USD"}
    
    try:
        if call.data == "main_menu":
            bot.edit_message_text("Выберите действие:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
        
        elif call.data == "show_crypto_menu":
            bot.edit_message_text("Выберите криптовалюту:", chat_id, call.message.message_id, reply_markup=get_crypto_keyboard())
        
        elif call.data == "search_crypto":
            user_states[chat_id] = "waiting_for_crypto"
            keyboard = types.InlineKeyboardMarkup()
            btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data="show_crypto_menu")
            keyboard.add(btn_cancel)
            bot.edit_message_text("Введите название или символ криптовалюты для поиска:", chat_id, call.message.message_id, reply_markup=keyboard)
        
        elif call.data == "show_currency_menu":
            bot.edit_message_text("Выберите валюту:", chat_id, call.message.message_id, reply_markup=get_currency_keyboard())
        
        elif call.data == "show_settings":
            bot.edit_message_text("Настройки:", chat_id, call.message.message_id, reply_markup=get_settings_keyboard(chat_id))
        
        elif call.data == "switch_currency":
            currency = user_preferences[chat_id].get("currency", "USD")
            new_currency = "RUB" if currency == "USD" else "USD"
            user_preferences[chat_id]["currency"] = new_currency
            bot.answer_callback_query(call.id, f"Валюта изменена на {new_currency}")
            bot.edit_message_text("Настройки:", chat_id, call.message.message_id, reply_markup=get_settings_keyboard(chat_id))
        
        elif call.data == "show_subscriptions":
            if chat_id in subscriptions and subscriptions[chat_id]:
                message_text = "Ваши подписки:\n\n"
                for symbol in subscriptions[chat_id]:
                    if symbol.startswith("CRYPTO_"):
                        message_text += f"Криптовалюта: {symbol[7:]}\n"
                    else:
                        message_text += f"Валюта: {symbol}\n"
            else:
                message_text = "У вас нет активных подписок"
                
            keyboard = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
            keyboard.add(btn_back)
            
            bot.edit_message_text(message_text, chat_id, call.message.message_id, reply_markup=keyboard)
        
        elif call.data.startswith("crypto_"):
            crypto_symbol = call.data.split("_")[1]
            currency = get_user_currency(chat_id)
            result = get_crypto_price(crypto_symbol, currency)
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            btn_subscribe = types.InlineKeyboardButton("📈 Подписаться", callback_data=f"subscribe_crypto_{crypto_symbol}")
            btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data="show_crypto_menu")
            keyboard.add(btn_subscribe, btn_back)
            
            bot.edit_message_text(result, chat_id, call.message.message_id, reply_markup=keyboard, parse_mode="Markdown")
        
        elif call.data.startswith("currency_"):
            currency_code = call.data.split("_")[1]
            base_currency = "USD"  
            result = get_currency_rate(currency_code, base_currency)
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            btn_subscribe = types.InlineKeyboardButton("📈 Подписаться", callback_data=f"subscribe_currency_{currency_code}")
            btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data="show_currency_menu")
            keyboard.add(btn_subscribe, btn_back)
            
            bot.edit_message_text(result, chat_id, call.message.message_id, reply_markup=keyboard)
        
        elif call.data.startswith("subscribe_crypto_"):
            crypto_symbol = call.data.split("_")[2]
            subscription_key = f"CRYPTO_{crypto_symbol}"
            
            if chat_id not in subscriptions:
                subscriptions[chat_id] = []
                
            if subscription_key in subscriptions[chat_id]:
                bot.answer_callback_query(call.id, f"Вы уже подписаны на {crypto_symbol}")
            else:
                subscriptions[chat_id].append(subscription_key)
                bot.answer_callback_query(call.id, f"Вы успешно подписались на обновления {crypto_symbol}")
        
        elif call.data.startswith("subscribe_currency_"):
            currency_code = call.data.split("_")[2]
            
            if chat_id not in subscriptions:
                subscriptions[chat_id] = []
                
            if currency_code in subscriptions[chat_id]:
                bot.answer_callback_query(call.id, f"Вы уже подписаны на {currency_code}")
            else:
                subscriptions[chat_id].append(currency_code)
                bot.answer_callback_query(call.id, f"Вы успешно подписались на обновления {currency_code}")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке callback: {e}")
        try:
            bot.answer_callback_query(call.id, "Произошла ошибка при обработке запроса")
        except:
            pass

@bot.message_handler(commands=['crypto'])
def get_crypto(message):
    try:
        command_parts = message.text.split(' ')
        if len(command_parts) < 2:
            bot.reply_to(message, "Пожалуйста, укажите символ криптовалюты. Например: /crypto BTC")
            return
            
        crypto_symbol = command_parts[1].upper()
        currency = get_user_currency(message.chat.id)
        result = get_crypto_price(crypto_symbol, currency)
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        btn_subscribe = types.InlineKeyboardButton("📈 Подписаться", callback_data=f"subscribe_crypto_{crypto_symbol}")
        btn_menu = types.InlineKeyboardButton("🔍 Другие криптовалюты", callback_data="show_crypto_menu")
        keyboard.add(btn_subscribe, btn_menu)
        
        bot.send_message(message.chat.id, result, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /crypto: {str(e)}")
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['ton'])
def get_ton(message):
    try:
        currency = get_user_currency(message.chat.id)
        result = get_crypto_price('TON', currency)
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        btn_subscribe = types.InlineKeyboardButton("📈 Подписаться", callback_data="subscribe_crypto_TON")
        btn_menu = types.InlineKeyboardButton("🔍 Другие криптовалюты", callback_data="show_crypto_menu")
        keyboard.add(btn_subscribe, btn_menu)
        
        bot.send_message(message.chat.id, result, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /ton: {str(e)}")
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['usdt'])
def get_usdt(message):
    try:
        currency = get_user_currency(message.chat.id)
        result = get_crypto_price('USDT', currency)
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        btn_subscribe = types.InlineKeyboardButton("📈 Подписаться", callback_data="subscribe_crypto_USDT")
        btn_menu = types.InlineKeyboardButton("🔍 Другие криптовалюты", callback_data="show_crypto_menu")
        keyboard.add(btn_subscribe, btn_menu)
        
        bot.send_message(message.chat.id, result, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /usdt: {str(e)}")
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['currency'])
def get_currency(message):
    try:
        command_parts = message.text.split(' ')
        if len(command_parts) < 2:
            bot.reply_to(message, "Пожалуйста, укажите код валюты. Например: /currency EUR")
            return
            
        currency_code = command_parts[1].upper()
        result = get_currency_rate(currency_code)
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        btn_subscribe = types.InlineKeyboardButton("📈 Подписаться", callback_data=f"subscribe_currency_{currency_code}")
        btn_menu = types.InlineKeyboardButton("🔍 Другие валюты", callback_data="show_currency_menu")
        keyboard.add(btn_subscribe, btn_menu)
        
        bot.send_message(message.chat.id, result, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /currency: {str(e)}")
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    try:
        command_parts = message.text.split(' ')
        if len(command_parts) < 2:
            bot.reply_to(message, "Пожалуйста, укажите символ/код для подписки. Например: /subscribe BTC или /subscribe EUR")
            return
            
        symbol = command_parts[1].upper()
        chat_id = message.chat.id
        
        if chat_id not in subscriptions:
            subscriptions[chat_id] = []
            
        if any(c.isdigit() for c in symbol) or len(symbol) > 5:
            bot.reply_to(message, f"Неверный формат символа: {symbol}")
            return
            
        subscription_key = f"CRYPTO_{symbol}" if len(symbol) <= 4 else symbol
        
        if subscription_key in subscriptions[chat_id]:
            bot.reply_to(message, f"Вы уже подписаны на {symbol}")
        else:
            subscriptions[chat_id].append(subscription_key)
            bot.reply_to(message, f"Вы успешно подписались на обновления {symbol}")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /subscribe: {str(e)}")
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    try:
        command_parts = message.text.split(' ')
        if len(command_parts) < 2:
            bot.reply_to(message, "Пожалуйста, укажите символ/код для отписки. Например: /unsubscribe BTC")
            return
            
        symbol = command_parts[1].upper()
        chat_id = message.chat.id
        
        if chat_id not in subscriptions:
            bot.reply_to(message, "У вас нет активных подписок")
            return
            
        subscription_key = f"CRYPTO_{symbol}" if len(symbol) <= 4 else symbol
        
        if subscription_key in subscriptions[chat_id]:
            subscriptions[chat_id].remove(subscription_key)
            bot.reply_to(message, f"Вы успешно отписались от обновлений {symbol}")
        else:
            bot.reply_to(message, f"Вы не подписаны на {symbol}")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /unsubscribe: {str(e)}")
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['list'])
def list_subscriptions(message):
    try:
        chat_id = message.chat.id
        
        if chat_id not in subscriptions or not subscriptions[chat_id]:
            bot.reply_to(message, "У вас нет активных подписок")
            return
            
        message_text = "Ваши подписки:\n\n"
        for symbol in subscriptions[chat_id]:
            if symbol.startswith("CRYPTO_"):
                message_text += f"Криптовалюта: {symbol[7:]}\n"
            else:
                message_text += f"Валюта: {symbol}\n"
        
        keyboard = types.InlineKeyboardMarkup()
        btn_menu = types.InlineKeyboardButton("🔙 В меню", callback_data="main_menu")
        keyboard.add(btn_menu)
        
        bot.send_message(chat_id, message_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /list: {str(e)}")
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.middleware_handler(update_types=['message', 'callback_query'])
def handle_middleware(bot_instance, update):
    try:
        return update
    except Exception as e:
        logger.error(f"Middleware error: {e}")
        
def shutdown_bot():
    global update_thread_running
    logger.info("Завершение работы бота...")
    update_thread_running = False
    
    time.sleep(1)
    
    try:
        bot.stop_polling()
    except:
        pass
    
    logger.info("Бот остановлен")

if __name__ == "__main__":
    try:
        logger.info("Бот запущен...")
        try:
            import signal
            signal.signal(signal.SIGINT, lambda sig, frame: shutdown_bot())
            signal.signal(signal.SIGTERM, lambda sig, frame: shutdown_bot())
        except:
            pass
        
        while True:
            try:
                logger.info("Запуск бота в режиме опроса...")
                bot.infinity_polling(timeout=60, long_polling_timeout=60, allowed_updates=None)
            except telebot.apihelper.ApiException as e:
                if "terminated by other getUpdates request" in str(e):
                    logger.warning("Обнаружен конфликт getUpdates. Ожидание 10 секунд перед повторной попыткой...")
                    time.sleep(10)
                    continue
                logger.error(f"Ошибка API Telegram: {str(e)}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Ошибка при опросе Telegram API: {str(e)}")
                time.sleep(5)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {str(e)}")
        shutdown_bot()
    finally:
        shutdown_bot()
