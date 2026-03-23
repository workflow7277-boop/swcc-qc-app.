#!/usr/bin/env python3
"""
Setup Script - تهيئة بيانات تجريبية
Run this once to initialize the database and create sample Excel file
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from modules.database import init_db
from modules.excel_import import generate_sample_excel, import_excel_to_db

DB_PATH     = str(BASE_DIR / "data" / "swcc_qc.db")
EXCEL_PATH  = str(BASE_DIR / "data" / "sample_items.xlsx")

print("⬡  SWCC QC Assistant - Setup")
print("=" * 40)

# 1. Init DB
print("1. تهيئة قاعدة البيانات...")
init_db(DB_PATH)
print(f"   ✅ قاعدة البيانات: {DB_PATH}")

# 2. Generate sample Excel
print("2. توليد ملف Excel تجريبي (153 بنداً)...")
try:
    generate_sample_excel(EXCEL_PATH)
    print(f"   ✅ ملف Excel: {EXCEL_PATH}")
except ImportError as e:
    print(f"   ⚠️  {e}")
    print("      قم بتشغيل: pip install openpyxl")
    sys.exit(1)

# 3. Import into DB
print("3. استيراد البيانات إلى SQLite...")
count = import_excel_to_db(EXCEL_PATH, DB_PATH)
print(f"   ✅ تم استيراد {count} بنداً")

# 4. Verify
import sqlite3
conn = sqlite3.connect(DB_PATH)
c    = conn.cursor()
c.execute("SELECT COUNT(*) FROM items")
n = c.fetchone()[0]
c.execute("SELECT item_code, description, quantity, status FROM items LIMIT 5")
rows = c.fetchall()
conn.close()

print(f"\n✅ إجمالي البنود في قاعدة البيانات: {n}")
print("\nأمثلة:")
for r in rows:
    print(f"  {r[0]:12} | {str(r[1] or '')[:30]:30} | {r[2]:6} | {r[3]}")

print("\n" + "=" * 40)
print("🚀 التطبيق جاهز للتشغيل!")
print("   python main.py")
print("\n📱 للتحويل إلى APK:")
print("   pip install flet[build]")
print("   flet build apk --project 'SWCC QC'")
