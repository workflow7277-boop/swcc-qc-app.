"""
مساعد جودة ذكي - الشركة السويدية الوطنية
Smart Quality Assistant - SWCC (Pivot Irrigation Systems)
Built with Flet | Dark Industrial Glassmorphism UI
"""

import flet as ft
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

# ─── Import local modules ───────────────────────────────────────────
from modules.database import init_db, get_db_connection
from modules.excel_import import import_excel_to_db
from modules.inbound import InboundSection
from modules.shipping import ShippingSection
from modules.rfi import RFISection
from modules.library import LibrarySection
from modules.chatbot import ChatbotSection
from modules.reports import generate_pdf_report

# ─── Constants & Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
REPORTS_DIR = BASE_DIR / "reports"
LIBRARY_DIR = BASE_DIR / "library"

for d in [DATA_DIR, ASSETS_DIR, REPORTS_DIR, LIBRARY_DIR]:
    d.mkdir(exist_ok=True)

DB_PATH = str(DATA_DIR / "swcc_qc.db")

# ─── Color Palette ──────────────────────────────────────────────────
COLORS = {
    "bg_dark":       "#0D0F14",
    "bg_card":       "#13161E",
    "bg_glass":      "#1A1E2A",
    "neon_blue":     "#00D4FF",
    "neon_blue_dim": "#0099BB",
    "neon_green":    "#00FF88",
    "neon_orange":   "#FF6B35",
    "neon_red":      "#FF3366",
    "text_primary":  "#E8EDF5",
    "text_secondary":"#7A8499",
    "text_muted":    "#3D4459",
    "border":        "#1E2535",
    "border_active": "#00D4FF",
    "surface":       "#161922",
}


def main(page: ft.Page):
    # ── Page Setup ──────────────────────────────────────────────────
    page.title = "مساعد الجودة الذكي | SWCC QC Assistant"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLORS["bg_dark"]
    page.padding = 0
    page.spacing = 0
    page.fonts = {
        "Cairo":       "https://fonts.gstatic.com/s/cairo/v28/SLXgc1nY6HkvalIhTps.woff2",
        "Rajdhani":    "https://fonts.gstatic.com/s/rajdhani/v15/LDI2apCSOBg7S-QT7pasEcOsc-bGkqIw.woff2",
        "JetBrainsMono":"https://fonts.gstatic.com/s/jetbrainsmono/v18/tDbY2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKxTPlOTk6OThhvAWV8.woff2",
    }
    page.theme = ft.Theme(
        font_family="Cairo",
        color_scheme=ft.ColorScheme(
            primary=COLORS["neon_blue"],
            on_primary=COLORS["bg_dark"],
            surface=COLORS["bg_card"],
            on_surface=COLORS["text_primary"],
        ),
    )

    # ── Initialize Database ──────────────────────────────────────────
    init_db(DB_PATH)

    # ── State ────────────────────────────────────────────────────────
    current_section = ft.Ref[str]()
    current_section.current = "home"

    # ── Content Area ─────────────────────────────────────────────────
    content_area = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
    )

    # ── Notification Snackbar ────────────────────────────────────────
    def show_snack(msg: str, color: str = COLORS["neon_blue"]):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color=COLORS["text_primary"], font_family="Cairo"),
            bgcolor=color,
            duration=3000,
        )
        page.snack_bar.open = True
        page.update()

    # ── Section Loader ───────────────────────────────────────────────
    def load_section(section_name: str):
        content_area.controls.clear()
        current_section.current = section_name

        if section_name == "home":
            content_area.controls.append(build_home_screen())
        elif section_name == "inbound":
            inbound = InboundSection(DB_PATH, COLORS, show_snack, ASSETS_DIR)
            content_area.controls.append(inbound.build())
        elif section_name == "shipping":
            shipping = ShippingSection(DB_PATH, COLORS, show_snack)
            content_area.controls.append(shipping.build())
        elif section_name == "rfi":
            rfi = RFISection(DB_PATH, COLORS, show_snack, ASSETS_DIR)
            content_area.controls.append(rfi.build())
        elif section_name == "library":
            library = LibrarySection(LIBRARY_DIR, COLORS, show_snack)
            content_area.controls.append(library.build())
        elif section_name == "chatbot":
            chatbot = ChatbotSection(DB_PATH, COLORS, show_snack)
            content_area.controls.append(chatbot.build())
        elif section_name == "reports":
            content_area.controls.append(build_reports_screen())

        update_nav_highlight(section_name)
        page.update()

    # ── Navigation Items ─────────────────────────────────────────────
    nav_refs = {}

    def nav_item(icon, label, section):
        ref = ft.Ref[ft.Container]()
        nav_refs[section] = ref

        def on_click(e):
            load_section(section)

        return ft.Container(
            ref=ref,
            content=ft.Column(
                [
                    ft.Icon(icon, size=22, color=COLORS["text_secondary"]),
                    ft.Text(label, size=9, color=COLORS["text_secondary"],
                            font_family="Cairo", text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            padding=ft.padding.symmetric(vertical=10, horizontal=6),
            border_radius=10,
            on_click=on_click,
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            tooltip=label,
        )

    def update_nav_highlight(section_name: str):
        for sec, ref in nav_refs.items():
            if ref.current:
                is_active = sec == section_name
                ref.current.bgcolor = f"{COLORS['neon_blue']}22" if is_active else "transparent"
                col = ref.current.content
                if col and col.controls:
                    col.controls[0].color = COLORS["neon_blue"] if is_active else COLORS["text_secondary"]
                    col.controls[1].color = COLORS["neon_blue"] if is_active else COLORS["text_secondary"]
        page.update()

    # ── Bottom Navigation Bar ────────────────────────────────────────
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                nav_item(ft.Icons.HOME_ROUNDED,         "الرئيسية",  "home"),
                nav_item(ft.Icons.INBOX_ROUNDED,        "الوارد",    "inbound"),
                nav_item(ft.Icons.LOCAL_SHIPPING_ROUNDED,"الشحن",   "shipping"),
                nav_item(ft.Icons.ASSIGNMENT_ROUNDED,   "RFI",       "rfi"),
                nav_item(ft.Icons.MENU_BOOK_ROUNDED,    "المكتبة",   "library"),
                nav_item(ft.Icons.SMART_TOY_ROUNDED,    "المساعد",   "chatbot"),
                nav_item(ft.Icons.SUMMARIZE_ROUNDED,    "التقارير",  "reports"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        bgcolor=COLORS["bg_card"],
        border=ft.border.only(top=ft.BorderSide(1, COLORS["border"])),
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
    )

    # ── Top App Bar ──────────────────────────────────────────────────
    def build_app_bar():
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row([
                        ft.Container(
                            content=ft.Text("⬡", size=20, color=COLORS["neon_blue"]),
                            margin=ft.margin.only(right=6),
                        ),
                        ft.Column([
                            ft.Text("SWCC Quality Assistant",
                                    size=13, weight=ft.FontWeight.BOLD,
                                    color=COLORS["text_primary"], font_family="Rajdhani"),
                            ft.Text("أجهزة الري المحوري | Pivot Systems",
                                    size=9, color=COLORS["text_secondary"], font_family="Cairo"),
                        ], spacing=0),
                    ]),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(
                                datetime.now().strftime("%d/%m/%Y"),
                                size=10, color=COLORS["text_secondary"], font_family="JetBrainsMono"
                            ),
                            margin=ft.margin.only(right=8),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                            icon_color=COLORS["neon_blue"],
                            icon_size=20,
                            tooltip="استيراد Excel",
                            on_click=lambda e: import_excel_dialog(e),
                        ),
                    ]),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=COLORS["bg_card"],
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, COLORS["border"])),
        )

    # ── Excel Import Dialog ──────────────────────────────────────────
    file_picker = ft.FilePicker(on_result=lambda e: handle_excel_upload(e))
    page.overlay.append(file_picker)

    def import_excel_dialog(e):
        file_picker.pick_files(
            dialog_title="اختر ملف Excel",
            allowed_extensions=["xlsx", "xls"],
            allow_multiple=False,
        )

    def handle_excel_upload(e: ft.FilePickerResultEvent):
        if e.files:
            path = e.files[0].path
            try:
                count = import_excel_to_db(path, DB_PATH)
                show_snack(f"✅ تم استيراد {count} بنداً بنجاح", COLORS["neon_green"])
                if current_section.current == "home":
                    load_section("home")
            except Exception as ex:
                show_snack(f"❌ خطأ في الاستيراد: {ex}", COLORS["neon_red"])

    # ── Home Screen ──────────────────────────────────────────────────
    def build_home_screen():
        conn = get_db_connection(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM items")
        total_items = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM items WHERE status='مقبول'")
        accepted = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM items WHERE status='مرفوض'")
        rejected = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM inbound_records")
        inbound_count = c.fetchone()[0]
        conn.close()

        def stat_card(icon, value, label, color):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=color, size=20),
                        ft.Text(str(value), size=26, weight=ft.FontWeight.BOLD,
                                color=color, font_family="Rajdhani"),
                    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Text(label, size=10, color=COLORS["text_secondary"],
                            font_family="Cairo", text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4),
                bgcolor=COLORS["bg_card"],
                border=ft.border.all(1, COLORS["border"]),
                border_radius=12,
                padding=16,
                expand=True,
                ink=True,
            )

        def quick_btn(icon, label, section, color):
            return ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=28),
                        bgcolor=f"{color}1A",
                        border_radius=14,
                        padding=14,
                        border=ft.border.all(1, f"{color}44"),
                    ),
                    ft.Text(label, size=11, color=COLORS["text_primary"],
                            font_family="Cairo", text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8),
                on_click=lambda e: load_section(section),
                border_radius=14,
                padding=12,
                ink=True,
                expand=True,
            )

        pending = max(0, total_items - accepted - rejected)

        return ft.Column([
            # Header Banner
            ft.Container(
                content=ft.Stack([
                    ft.Container(
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[f"{COLORS['neon_blue']}22", COLORS["bg_dark"]],
                        ),
                        border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
                        height=140,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("مرحباً، مراقب الجودة",
                                    size=18, weight=ft.FontWeight.BOLD,
                                    color=COLORS["text_primary"], font_family="Cairo"),
                            ft.Text(f"آخر تحديث: {datetime.now().strftime('%H:%M - %d/%m/%Y')}",
                                    size=10, color=COLORS["text_secondary"], font_family="JetBrainsMono"),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(width=6, height=6, bgcolor=COLORS["neon_green"],
                                                 border_radius=3),
                                    ft.Text("النظام يعمل - وضع أوفلاين", size=10,
                                            color=COLORS["neon_green"], font_family="Cairo"),
                                ], spacing=6),
                                margin=ft.margin.only(top=4),
                            ),
                        ], spacing=4),
                        padding=ft.padding.symmetric(horizontal=20, vertical=16),
                    ),
                ]),
            ),

            ft.Container(
                content=ft.Column([
                    # Stats Row
                    ft.Text("الإحصائيات", size=12, color=COLORS["text_secondary"],
                            font_family="Cairo", weight=ft.FontWeight.W_600),
                    ft.Row([
                        stat_card(ft.Icons.INVENTORY_2_ROUNDED, total_items, "إجمالي البنود", COLORS["neon_blue"]),
                        stat_card(ft.Icons.CHECK_CIRCLE_ROUNDED, accepted, "مقبول", COLORS["neon_green"]),
                        stat_card(ft.Icons.CANCEL_ROUNDED, rejected, "مرفوض", COLORS["neon_red"]),
                        stat_card(ft.Icons.PENDING_ROUNDED, pending, "معلق", COLORS["neon_orange"]),
                    ], spacing=8),

                    ft.Divider(color=COLORS["border"], height=24),

                    # Quick Actions
                    ft.Text("الوصول السريع", size=12, color=COLORS["text_secondary"],
                            font_family="Cairo", weight=ft.FontWeight.W_600),
                    ft.Row([
                        quick_btn(ft.Icons.INBOX_ROUNDED, "فحص الوارد", "inbound", COLORS["neon_blue"]),
                        quick_btn(ft.Icons.LOCAL_SHIPPING_ROUNDED, "الشحن", "shipping", COLORS["neon_orange"]),
                        quick_btn(ft.Icons.SMART_TOY_ROUNDED, "المساعد الذكي", "chatbot", COLORS["neon_green"]),
                        quick_btn(ft.Icons.SUMMARIZE_ROUNDED, "التقارير", "reports", COLORS["neon_blue_dim"]),
                    ], spacing=8),

                    ft.Divider(color=COLORS["border"], height=24),

                    # Recent Activity
                    ft.Text("آخر النشاطات", size=12, color=COLORS["text_secondary"],
                            font_family="Cairo", weight=ft.FontWeight.W_600),
                    build_recent_activity(),
                ], spacing=12),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ),
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    def build_recent_activity():
        conn = get_db_connection(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT item_code, description, status, inspection_date
            FROM inbound_records
            ORDER BY id DESC LIMIT 5
        """)
        rows = c.fetchall()
        conn.close()

        if not rows:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INBOX_OUTLINED, color=COLORS["text_muted"], size=40),
                    ft.Text("لا توجد نشاطات بعد", color=COLORS["text_muted"],
                            font_family="Cairo", size=12),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                alignment=ft.alignment.center,
            )

        items = []
        for row in rows:
            code, desc, status, date = row
            status_color = (COLORS["neon_green"] if status == "مقبول"
                            else COLORS["neon_red"] if status == "مرفوض"
                            else COLORS["neon_orange"])
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            width=4, height=40,
                            bgcolor=status_color,
                            border_radius=2,
                        ),
                        ft.Column([
                            ft.Text(f"{code} - {desc[:30]}{'...' if len(desc)>30 else ''}",
                                    size=11, color=COLORS["text_primary"], font_family="Cairo"),
                            ft.Text(date or "", size=9, color=COLORS["text_secondary"],
                                    font_family="JetBrainsMono"),
                        ], spacing=2, expand=True),
                        ft.Container(
                            content=ft.Text(status, size=9, color=status_color,
                                            font_family="Cairo"),
                            bgcolor=f"{status_color}1A",
                            border_radius=6,
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        ),
                    ], spacing=10),
                    bgcolor=COLORS["bg_card"],
                    border=ft.border.all(1, COLORS["border"]),
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                )
            )
        return ft.Column(items, spacing=6)

    # ── Reports Screen ───────────────────────────────────────────────
    def build_reports_screen():
        def on_generate(e):
            try:
                out_path = str(REPORTS_DIR / f"QC_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
                generate_pdf_report(DB_PATH, out_path, str(ASSETS_DIR))
                show_snack(f"✅ تم توليد التقرير: {os.path.basename(out_path)}", COLORS["neon_green"])
            except Exception as ex:
                show_snack(f"❌ خطأ في التوليد: {ex}", COLORS["neon_red"])

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SUMMARIZE_ROUNDED, color=COLORS["neon_blue"], size=22),
                        ft.Text("التقارير", size=16, weight=ft.FontWeight.BOLD,
                                color=COLORS["text_primary"], font_family="Cairo"),
                    ], spacing=10),
                    ft.Divider(color=COLORS["border"]),

                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED,
                                    color=COLORS["neon_orange"], size=50),
                            ft.Text("تقرير الفحص الشامل", size=14, font_family="Cairo",
                                    color=COLORS["text_primary"], weight=ft.FontWeight.BOLD),
                            ft.Text("يشمل جميع بنود الفحص مع الصور الموثقة وبيانات GPS",
                                    size=11, color=COLORS["text_secondary"], font_family="Cairo",
                                    text_align=ft.TextAlign.CENTER),
                            ft.ElevatedButton(
                                "توليد التقرير",
                                icon=ft.Icons.DOWNLOAD_ROUNDED,
                                on_click=on_generate,
                                style=ft.ButtonStyle(
                                    bgcolor=COLORS["neon_blue"],
                                    color=COLORS["bg_dark"],
                                    padding=ft.padding.symmetric(horizontal=30, vertical=14),
                                ),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12),
                        bgcolor=COLORS["bg_card"],
                        border=ft.border.all(1, COLORS["border"]),
                        border_radius=16,
                        padding=30,
                        margin=ft.margin.only(top=10),
                    ),

                    # Reports List
                    ft.Text("التقارير السابقة", size=12, color=COLORS["text_secondary"],
                            font_family="Cairo", weight=ft.FontWeight.W_600),
                    *build_reports_list(),
                ], spacing=12),
                padding=16,
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def build_reports_list():
        reports = sorted(REPORTS_DIR.glob("*.pdf"), reverse=True)
        if not reports:
            return [ft.Text("لا توجد تقارير سابقة", color=COLORS["text_muted"],
                            font_family="Cairo", size=11)]
        items = []
        for rpt in reports[:10]:
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED, color=COLORS["neon_orange"], size=18),
                        ft.Text(rpt.name, size=11, color=COLORS["text_primary"],
                                font_family="JetBrainsMono", expand=True),
                        ft.Text(
                            datetime.fromtimestamp(rpt.stat().st_mtime).strftime("%d/%m %H:%M"),
                            size=9, color=COLORS["text_secondary"], font_family="JetBrainsMono"
                        ),
                    ], spacing=8),
                    bgcolor=COLORS["surface"],
                    border=ft.border.all(1, COLORS["border"]),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                )
            )
        return items

    # ── Assemble Layout ───────────────────────────────────────────────
    load_section("home")

    page.add(
        ft.Column([
            build_app_bar(),
            ft.Container(
                content=content_area,
                expand=True,
            ),
            bottom_nav,
        ], spacing=0, expand=True)
    )


ft.app(target=main, assets_dir="assets")
