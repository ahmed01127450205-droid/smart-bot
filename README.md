# بوت مساعد تعليمي على Telegram

بوت Python يجيب عن الأسئلة باستخدام Gemini، ويحلل ��لصور وبعض المستندات، ويحتفظ بسجل محادثة منفصل لكل مستخدم في SQLite.

## الميزات

- أوامر `/start` و`/help` و`/clear`.
- أسئلة نصية وصور وملفات PDF.
- استخراج محتوى TXT وMD وCSV وJSON وDOCX وXLSX وإرساله إلى Gemini.
- حفظ آخر الرسائل في SQLite لاستمرار سياق المحادثة.
- حد أقصى لحجم الملف قابل للتعديل، ورسائل خطأ لا تكشف الأسرار.

## تنبيه أمني مهم

المفاتيح التي أُرسلت سابقًا في المحادثة يجب اعتبارها مكشوفة: ألغِ مفتاح Gemini وأنشئ مفتاحًا جديدًا، وألغِ Telegram bot token من BotFather ثم أنشئ واحدًا جديدًا. لا تضع الأسرار داخل ملفات المشروع أو GitHub.

## التشغيل محليًا

يتطلب Python 3.10 أو أحدث.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

انسخ `.env.example` إلى `.env` وأدخل القيم الجديدة. لا يتم تحميل `.env` تلقائيًا؛ عيّن المتغيرات في الطرفية قبل تشغيل البوت:

```bash
export TELEGRAM_BOT_TOKEN="القيمة الجديدة من BotFather"
export GEMINI_API_KEY="مفتاح Gemini الجديد"
python bot.py
```

في PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN="القيمة الجديدة من BotFather"
$env:GEMINI_API_KEY="مفتاح Gemini الجديد"
python bot.py
```

## الإعدادات الاختيارية

- `GEMINI_MODEL`: النموذج، والافتراضي `gemini-2.5-flash`.
- `DATABASE_PATH`: موقع قاعدة البيانات، والافتراضي `data/bot.sqlite3`.
- `MAX_FILE_SIZE_MB`: أقصى حجم للملف بالميغابايت، والافتراضي 15.
- `HISTORY_MESSAGES`: عدد الرسائل السابقة المرسلة إلى النموذج، والافتراضي 10.

## ملاحظات

- لا تُشارك ملف قاعدة البيانات إن كان يحتوي على محادثات خاصة.
- قد تختلف الملفات التي يستطيع Gemini تحليلها وفقًا لحدود النموذج وإعدادات حساب Google.
- شغّل البوت على خادم دائم التشغيل إذا أردت أن يبقى متاحًا على مدار الساعة.
