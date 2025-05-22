import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import pandas as pd
import ta

API_TOKEN = '7809359933:AAEmozd3svKCGAzXxo5OqifmOhe2aMZL0Gc'
CHAT_ID = 7098638994
COINS = [
    'dogecoin', 'shiba-inu', 'floki', 'pepe', 'dogelon-mars', 'baby-doge-coin',
    'akita-inu', 'samoyedcoin', 'kishu-inu', 'pitbull', 'doge-killer',
    'tama', 'mong', 'ladys', 'jejudoge', 'hoge-finance', 'catecoin', 'volt-inu',
    'kabosu', 'saitama', 'vita-inu', 'dogira', 'yummy', 'elondoge',
    'bone-shibaswap', 'bonk', 'wojak', 'arbinu', 'feg-token', 'dogpad'
]

bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

async def fetch_chart(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": 3, "interval": "hourly"}
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
    except:
        return None

def analyze(df):
    df["rsi"] = ta.momentum.RSIIndicator(close=df["price"]).rsi()
    macd = ta.trend.MACD(close=df["price"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    bb = ta.volatility.BollingerBands(close=df["price"])
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()

    latest = df.iloc[-1]
    price = latest["price"]
    rsi = latest["rsi"]
    macd_val = latest["macd"]
    macd_sig = latest["macd_signal"]
    bb_upper = latest["bb_upper"]
    bb_lower = latest["bb_lower"]

    msg = f"قیمت: {price:.4f} دلار | RSI: {rsi:.2f} | MACD: {macd_val:.4f} | Signal: {macd_sig:.4f}\n"
    suggestion = ""

    if rsi < 30 and macd_val > macd_sig and price <= bb_lower:
        suggestion = "خرید ✅ (احتمال رشد تا ۲ روز آینده)"
    elif rsi > 70 and macd_val < macd_sig and price >= bb_upper:
        suggestion = "فروش ❌ (احتمال افت در ۱ روز آینده)"
    else:
        suggestion = "صبر ⏳ (نوسان یا شرایط نامشخص)"

    return msg + " → " + suggestion

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply("در حال تحلیل حدود ۳۰ میم‌کوین محبوب... لطفاً صبر کنید.")
    results = []

    for coin in COINS:
        df = await fetch_chart(coin)
        if df is not None and len(df) > 50:
            analysis = analyze(df)
            results.append(f"*{coin.upper()}*\n{analysis}\n")
        await asyncio.sleep(1.2)  # برای جلوگیری از محدودیت کوین‌گکو

    full_message = "\n".join(results)
    # تقسیم پیام اگه خیلی طولانی بود
    if len(full_message) < 4000:
        await bot.send_message(CHAT_ID, full_message)
    else:
        chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
        for chunk in chunks:
            await bot.send_message(CHAT_ID, chunk)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
