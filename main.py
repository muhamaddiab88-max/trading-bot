import imaplib
import email
import ccxt
import time
import os
from email.header import decode_header

# إعداد الاتصال بـ Bybit Testnet
bybit = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_SECRET'),
    'sandbox': True,  # **مهم جداً: يضمن أن التداول على حساب التجربة**
    'enableRateLimit': True,
})

def read_emails():
    try:
        # الاتصال بخادم Gmail
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
        mail.select('inbox')

        # البحث عن رسائل غير مقروءة
        _, data = mail.search(None, 'UNSEEN')
        email_ids = data[0].split()

        if not email_ids:
            print("لا توجد رسائل جديدة.")
            mail.close()
            mail.logout()
            return

        for num in email_ids:
            _, msg_data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_header(msg['Subject'])[0][0]

            if isinstance(subject, bytes):
                subject = subject.decode()

            print(f"تم العثور على رسالة بعنوان: {subject}")

            # التحقق من وجود أمر في الرسالة
            if 'BUY' in subject or 'SELL' in subject:
                try:
                    # تقسيم الرسالة لاستخراج التفاصيل
                    # صيغة الرسالة المتوقعة: "BUY BTCUSDT 0.01"
                    parts = subject.split()
                    action = parts[0].upper()
                    symbol = parts[1]
                    amount = float(parts[2])

                    # تنفيذ أمر السوق (Market Order)
                    order = bybit.create_market_order(symbol, action.lower(), amount)
                    print(f"✅ تم تنفيذ الأمر بنجاح: {action} {amount} {symbol}")
                    print(f"   تفاصيل الأمر: {order}")

                    # **مهم: تعليم الرسالة كمقروءة لتجنب تكرارها**
                    mail.store(num, '+FLAGS', '\\Seen')

                except (IndexError, ValueError) as e:
                    print(f"خطأ في تنسيق الرسالة: {subject}. الرجاء التأكد من الصيغة الصحيحة.")
                except Exception as e:
                    print(f"حدث خطأ أثناء تنفيذ الأمر: {e}")

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"فشل في قراءة البريد الإلكتروني: {e}")

# حلقة تشغيل لا نهائية للتحقق كل 30 ثانية
while True:
    read_emails()
    time.sleep(30)
