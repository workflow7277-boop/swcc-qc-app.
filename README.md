# ⬡ SWCC QC Assistant — مساعد جودة ذكي
## الشركة السويدية الوطنية | أجهزة الري المحوري

> تطبيق موبايل احترافي لمراقبي الجودة، مبني بـ Python + Flet  
> واجهة **Dark Industrial Glassmorphism** | يعمل **أوفلاين** كاملاً

---

## 📦 هيكل المشروع

```
swcc_qc_app/
├── main.py                  # نقطة الدخول الرئيسية + App Bar + Nav
├── setup.py                 # تهيئة قاعدة البيانات + بيانات تجريبية
├── requirements.txt         # المكتبات المطلوبة
├── pubspec.yaml             # إعدادات بناء APK
├── modules/
│   ├── database.py          # SQLite init + CRUD helpers
│   ├── excel_import.py      # قراءة Excel → SQLite
│   ├── inbound.py           # قسم الوارد + كاميرا
│   ├── shipping.py          # قسم الشحن
│   ├── rfi.py               # نموذج RFI
│   ├── library.py           # مكتبة PDF + ملفات
│   ├── chatbot.py           # المساعد الذكي
│   ├── watermark.py         # علامة مائية GPS + وقت + كود
│   └── reports.py           # توليد PDF شامل
├── data/                    # SQLite DB + Excel files
├── assets/photos/           # صور الفحص الموثقة
├── library/                 # ملفات PDF المكتبة
└── reports/                 # التقارير المولدة
```

---

## 🚀 التشغيل السريع

```bash
# 1. تثبيت المكتبات
pip install -r requirements.txt

# 2. تهيئة البيانات (مرة واحدة)
python setup.py

# 3. تشغيل التطبيق
python main.py
```

---

## 📱 التحويل إلى APK

```bash
# تثبيت أدوات البناء
pip install "flet[build]"

# بناء APK (يتطلب Flutter SDK)
flet build apk \
  --project "SWCC QC Assistant" \
  --description "Smart Quality Control" \
  --org "com.swcc.qc" \
  --splash-color "#0D0F14"
```

**ملاحظات APK:**
- يتطلب Flutter SDK مثبت على الجهاز
- يتطلب Java JDK 17+
- ملف APK سيكون في: `build/apk/`
- أذونات الكاميرا والموقع تُضاف تلقائياً

---

## 🗄️ هيكل قاعدة البيانات

| الجدول | الوصف |
|--------|-------|
| `items` | البنود الرئيسية (من Excel) |
| `inbound_records` | سجلات فحص الوارد |
| `shipping_records` | سجلات الشحن |
| `rfi_records` | سجلات الفحص الداخلي |
| `library_docs` | وثائق PDF المكتبة |
| `chat_history` | تاريخ محادثات المساعد |

---

## 📋 ملف Excel المطلوب

الأعمدة المدعومة (عربي أو إنجليزي):

| العربي | الإنجليزي |
|--------|-----------|
| الكود | Code / Item Code |
| الوصف | Description |
| الكمية | Quantity / QTY |
| الوحدة | Unit / UOM |
| المواصفة | Specification / Spec |
| الحالة | Status |
| الفئة | Category |
| المورد | Supplier / Vendor |

---

## 🤖 أوامر المساعد الذكي

```
# البحث بالكود
PVT-001

# البحث بالاسم
مضخة مياه

# إصدار أمر فحص
سجل PVT-001 مقبول
ثبت PVT-050 مرفوض
قيد PVT-010 معلق

# الإحصائيات
إحصائيات المخزن
كشف الوارد اليوم
البنود المرفوضة
البنود المقبولة
```

---

## 🛡️ نظام Evidence Shield

كل صورة يلتقطها التطبيق تحمل:
- **كود الصنف** (كبير وواضح)
- **تاريخ ووقت الفحص** (دقيق)
- **إحداثيات GPS** (lat/lon)
- **علامة مائية قطرية** لمنع التلاعب
- **شعار SWCC QC** في أسفل الصورة

---

## 📊 التقارير

التقرير المولد يحتوي على:
1. ملخص إجمالي (قبول/رفض/معلق)
2. جدول كامل لسجلات الوارد
3. صور موثقة مرتبة (2 في الصف)
4. سجلات RFI
5. تذييل بالتاريخ والتوقيع الرقمي

---

## 🎨 الألوان

| اللون | الكود | الاستخدام |
|-------|-------|-----------|
| Dark BG | `#0D0F14` | خلفية رئيسية |
| Neon Blue | `#00D4FF` | النشط / العناوين |
| Neon Green | `#00FF88` | مقبول |
| Neon Red | `#FF3366` | مرفوض |
| Neon Orange | `#FF6B35` | معلق / شحن |

---

*Built with ❤️ for SWCC Quality Control Team*
