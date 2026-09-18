# 🐦 X Monitor Bot (x-parser)

A Telegram bot that monitors X (Twitter) accounts and sends new posts (with translation to Persian + images) to users in real-time.

ربات تلگرام برای مانیتور کردن اکانت‌های X (توییتر). پست‌های جدید را به صورت خودکار دریافت می‌کند، به فارسی ترجمه می‌کند و همراه با عکس‌ها برای کاربر ارسال می‌کند.

---

## ✨ Features / ویژگی‌ها

- Add / remove / list X usernames to monitor
- Automatic checking of new posts at regular intervals
- Persian translation of posts
- Support for images / media groups
- Docker-based deployment (MariaDB + RSSHub + Bot in one container)
- Simple one-command installation scripts for Linux & Windows

- افزودن / حذف / مشاهده لیست یوزرنیم‌های مانیتور شده
- بررسی خودکار پست‌های جدید در بازه زمانی مشخص
- ترجمه خودکار پست‌ها به فارسی
- پشتیبانی از عکس و مدیا گروپ
- استقرار کامل با داکر (MariaDB + RSSHub + ربات در یک کانتینر)
- اسکریپت‌های نصب یک‌مرحله‌ای برای لینوکس و ویندوز

---

## 📋 Requirements / پیش‌نیازها

- Docker (must be installed and running)
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A Twitter/X Auth Token (for RSSHub to fetch posts)

- داکر باید نصب و در حال اجرا باشد
- توکن ربات تلگرام (از [@BotFather](https://t.me/BotFather))
- توکن احراز هویت توییتر/X (برای کارکرد صحیح RSSHub)

---

## 🚀 Quick Installation / نصب سریع

### Linux / macOS

```bash
git clone https://github.com/hoomanyyy/x-parser.git
cd x-parser
chmod +x install.sh
./install.sh
