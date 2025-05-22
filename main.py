import asyncio
import aiohttp
import pandas as pd
import numpy as np
import ta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = '7809359933:AAEmozd3svKCGAzXxo5OqifmOhe2aMZL0Gc'
CHAT_ID = 7098638994
TOMAN_RATE = 58000

bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

MEME_COINS = [
    'dogecoin', 'shiba-inu', 'pepe', 'floki', 'baby-doge-coin', 'dogelon-mars',
    'akita-inu', 'kishu-inu', 'pitbull', 'samoyedcoin', 'vitoge', 'cumrocket',
    'wojak', 'doge-killer', 'catscoin', 'jejudoge', 'mongcoin', 'kabosu', 
    'poocoin', 'saitama-inu', 'hoge-finance', 'dogira', 'suka', 'doge-ceo', 
    'pug-ai', 'bonk', 'tosa-inu', 'arbdoge-ai', 'doggy', 'pork', 'turbodoge'
]

async def fetch_chart(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": 7, "interval": "hourly"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as res:
                if res.status != 200:
                    return None
                data = await res.json()
                prices = data.get("prices", [])
                df = pd.DataFrame(prices, columns=["timestamp", "price"])
                df['price'] = df['price'].astype(float)
                return df
    except Exception:
        return None

def analyze(df, name):
    df["rsi"] = ta.momentum.RSIIndicator(close=df["price"]).rsi()
    macd = ta.trend.MACD(close=df["price"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    bb = ta.volatility.BollingerBands(close=df["price"])
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()

    latest = df.iloc[-1]
    rsi = latest["rsi"]
    macd_val = latest["macd"]
    macd_sig = latest["macd_signal"]
    price = latest["price"]
    bb_upper = latest["bb_upper"]
    bb_lower = latest["bb_lower"]

    msg = f"*{name.upper()}*\nقیمت: {price:.4f} $\n"
    msg += f"RSI: {rsi:.2f}, MACD: {macd_val:.4f}, سیگنال: {macd_sig:.4f}\n"
    msg += f"بولینگر: بالا {bb_upper:.4f}, پایین {bb_lower:.4f}\n"

    if rsi < 30 and macd_val > macd_sig and price <= bb_lower:
        msg += "✅ مناسب خرید (احتمال رشد 1 تا 2 روزه)"
    elif rsi > 70 and macd_val < macd_sig and price >= bb_upper:
        msg += "❌ مناسب فروش (احتمال افت طی 1 روز)"
    else:
        msg += "⏳ هنوز شرایط مشخصی ندارد"
    msg += "\n\n"
    return msg

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("در حال تحلیل ۳۰+ میم‌کوین لطفاً منتظر بمانید...")
    result = ""
    for coin in MEME_COINS:
        df = await fetch_chart(coin)
        if df is not None and len(df) > 50:
            result += analyze(df, coin)
    if not result:
        await message.reply("❌ خطا در دریافت داده از CoinGecko.")
    else:
        await bot.send_message(chat_id=message.chat.id, text=result)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.run_forever()
