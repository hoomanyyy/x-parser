# x-parser

ربات تلگرام برای مانیتور کردن اکانت‌های X (توییتر)  
پست‌های جدید را می‌گیرد، به فارسی ترجمه می‌کند و ارسال می‌کند.

---

## پیش‌نیازها

- سرور لینوکس با Docker
- توکن ربات تلگرام (از @BotFather)
- Auth Token توییتر
- Google API Key (برای ترجمه)
- یک دیتابیس MySQL (ترجیحاً خارجی مثل FreeMySQLHosting)

---

## نصب روی سرور لینوکس

```bash
# ۱. کلون کردن پروژه
git clone https://github.com/hoomanyyy/x-parser.git
cd x-parser

# ۲. دادن دسترسی اجرا
chmod +x install.sh start.sh

# ۳. اجرای نصب
./install.sh
