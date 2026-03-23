"""
Excel Import Module - reads .xlsx/.xls and populates the items table.
Expected columns (flexible header matching):
  Code/الكود | Description/الوصف | Quantity/الكمية | Unit/الوحدة |
  Specification/المواصفة | Status/الحالة | Category/الفئة | Supplier/المورد
"""
import sqlite3
import re
from pathlib import Path

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import xlrd
    XLRD_AVAILABLE = True
except ImportError:
    XLRD_AVAILABLE = False


# Column name aliases (Arabic + English)
COLUMN_ALIASES = {
    "item_code":     ["code", "الكود", "كود", "item code", "رمز", "رقم البند", "part no", "part number"],
    "description":   ["description", "الوصف", "وصف", "البيان", "item description", "اسم الصنف"],
    "quantity":      ["quantity", "الكمية", "كمية", "qty", "كم"],
    "unit":          ["unit", "الوحدة", "وحدة", "uom"],
    "specification": ["specification", "المواصفة", "مواصفة", "spec", "المواصفات", "standard"],
    "status":        ["status", "الحالة", "حالة", "حالة الفحص"],
    "category":      ["category", "الفئة", "فئة", "group", "المجموعة"],
    "supplier":      ["supplier", "المورد", "مورد", "vendor"],
    "notes":         ["notes", "ملاحظات", "ملاحظة", "remarks"],
}


def normalize(text: str) -> str:
    """Lowercase, strip whitespace, remove diacritics."""
    if not text:
        return ""
    text = str(text).strip().lower()
    # Remove Arabic diacritics
    text = re.sub(r'[\u0610-\u061A\u064B-\u065F]', '', text)
    return text


def match_column(header: str) -> str | None:
    norm = normalize(header)
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if norm == normalize(alias) or norm.startswith(normalize(alias)):
                return field
    return None


def read_excel(file_path: str) -> list[dict]:
    """Read Excel and return list of row dicts with normalized keys."""
    path = Path(file_path)
    ext = path.suffix.lower()
    rows = []

    if ext == ".xlsx" and OPENPYXL_AVAILABLE:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        data = list(ws.values)
        wb.close()
    elif ext in (".xls", ".xlsx") and XLRD_AVAILABLE:
        import xlrd
        wb = xlrd.open_workbook(file_path)
        ws = wb.sheet_by_index(0)
        data = [ws.row_values(i) for i in range(ws.nrows)]
    else:
        raise ImportError("يرجى تثبيت openpyxl أو xlrd: pip install openpyxl xlrd")

    if not data:
        return rows

    # Find header row (first row with >2 non-empty cells)
    header_row_idx = 0
    for i, row in enumerate(data):
        non_empty = sum(1 for c in row if c not in (None, "", 0))
        if non_empty >= 2:
            header_row_idx = i
            break

    headers = data[header_row_idx]
    col_map = {}  # col_index -> field_name
    for idx, h in enumerate(headers):
        if h:
            field = match_column(str(h))
            if field:
                col_map[idx] = field

    for row in data[header_row_idx + 1:]:
        if all(c in (None, "", 0) for c in row):
            continue
        record = {}
        for idx, field in col_map.items():
            val = row[idx] if idx < len(row) else None
            record[field] = str(val).strip() if val not in (None, "") else None
        if record.get("item_code"):
            rows.append(record)

    return rows


def import_excel_to_db(file_path: str, db_path: str) -> int:
    """Import Excel rows into SQLite items table. Returns count of inserted/updated rows."""
    rows = read_excel(file_path)
    if not rows:
        raise ValueError("لم يتم العثور على بيانات في الملف")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()
    count = 0

    for row in rows:
        code = row.get("item_code")
        if not code:
            continue
        try:
            qty = float(row["quantity"]) if row.get("quantity") else 0.0
        except (ValueError, TypeError):
            qty = 0.0

        c.execute("""
            INSERT INTO items (item_code, description, quantity, unit, specification, status, category, supplier, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_code) DO UPDATE SET
                description   = excluded.description,
                quantity      = excluded.quantity,
                unit          = excluded.unit,
                specification = excluded.specification,
                category      = excluded.category,
                supplier      = excluded.supplier,
                notes         = excluded.notes,
                updated_at    = datetime('now','localtime')
        """, (
            code,
            row.get("description"),
            qty,
            row.get("unit", "EA"),
            row.get("specification"),
            row.get("status", "معلق"),
            row.get("category"),
            row.get("supplier"),
            row.get("notes"),
        ))
        count += 1

    conn.commit()
    conn.close()
    return count


def generate_sample_excel(output_path: str):
    """Generate a sample Excel file with 153 items for testing."""
    if not OPENPYXL_AVAILABLE:
        raise ImportError("pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Items"

    # Headers
    headers = ["الكود", "الوصف", "الكمية", "الوحدة", "المواصفة", "الحالة", "الفئة", "المورد"]
    ws.append(headers)

    categories = ["هياكل", "أنابيب", "رؤوس ري", "موتورات", "مضخات", "كابلات", "صمامات", "لوحات تحكم"]
    statuses   = ["معلق", "مقبول", "مرفوض", "معلق", "معلق"]
    suppliers  = ["المورد الأول", "الشركة الهندية", "المورد الكندي", "الشركة الألمانية"]
    specs      = ["ASTM A36", "ISO 9001", "DIN 2448", "ASME B16.5", "API 6D", "EN 10025"]

    items = [
        ("PVT-001", "عمود محوري رئيسي", 12, "EA", "ASTM A36 Grade 50", "معلق", "هياكل"),
        ("PVT-002", "ذراع رش طول 6م",   24, "EA", "SS316L",             "معلق", "أنابيب"),
        ("PVT-003", "رأس رش دوار",       480,"EA", "ISO 7-1",            "معلق", "رؤوس ري"),
        ("PVT-004", "موتور كهربائي 15KW",6,  "EA", "IEC 60034",          "معلق", "موتورات"),
        ("PVT-005", "مضخة مياه 200m³/h", 3,  "EA", "ISO 9906",           "معلق", "مضخات"),
    ]

    for i, (code, desc, qty, unit, spec, status, cat) in enumerate(items):
        ws.append([code, desc, qty, unit, spec, status, cat, suppliers[i % len(suppliers)]])

    # Add remaining items up to 153
    import random
    parts = [
        "صامولة", "مسمار", "حلقة ختم", "وصلة", "كوع", "تيه", "فلنشة",
        "بلت", "غسالة", "رابط", "قاطع", "مانع تسرب", "إطار", "دعامة"
    ]
    for i in range(6, 154):
        code = f"PVT-{i:03d}"
        part = random.choice(parts)
        desc = f"{part} {random.randint(1,50)}{'ملم' if random.random()>0.5 else 'إنش'}"
        qty  = random.randint(10, 500)
        unit = random.choice(["EA", "KG", "M", "SET", "BOX"])
        spec = random.choice(specs)
        stat = random.choice(statuses)
        cat  = random.choice(categories)
        sup  = random.choice(suppliers)
        ws.append([code, desc, qty, unit, spec, stat, cat, sup])

    wb.save(output_path)
    return output_path
