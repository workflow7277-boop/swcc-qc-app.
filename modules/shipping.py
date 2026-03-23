"""
Shipping Section - تتبع الشحن
"""
import flet as ft
from datetime import datetime
from modules.database import get_db_connection


class ShippingSection:
    def __init__(self, db_path: str, colors: dict, show_snack):
        self.db_path = db_path
        self.C = colors
        self.snack = show_snack
        self._records_col = ft.Column(spacing=6)
        self.ship_no_ref    = ft.Ref[ft.TextField]()
        self.item_code_ref  = ft.Ref[ft.TextField]()
        self.desc_ref       = ft.Ref[ft.TextField]()
        self.qty_ref        = ft.Ref[ft.TextField]()
        self.dest_ref       = ft.Ref[ft.TextField]()
        self.carrier_ref    = ft.Ref[ft.TextField]()
        self.status_ref     = ft.Ref[ft.Dropdown]()
        self.notes_ref      = ft.Ref[ft.TextField]()

    def build(self) -> ft.Control:
        self._load_records()
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.LOCAL_SHIPPING_ROUNDED, color=self.C["neon_orange"], size=22),
                        ft.Text("إدارة الشحن", size=16, weight=ft.FontWeight.BOLD,
                                color=self.C["text_primary"], font_family="Cairo"),
                    ], spacing=10),
                    ft.Divider(color=self.C["border"]),

                    ft.Container(
                        content=ft.Column([
                            ft.Text("إضافة شحنة جديدة", size=12, color=self.C["text_secondary"],
                                    font_family="Cairo", weight=ft.FontWeight.W_600),
                            ft.Row([
                                self._tf("رقم الشحنة", self.ship_no_ref),
                                self._tf("كود الصنف", self.item_code_ref),
                            ], spacing=8),
                            self._tf("وصف الشحنة", self.desc_ref),
                            ft.Row([
                                self._tf("الكمية", self.qty_ref, keyboard=ft.KeyboardType.NUMBER),
                                self._tf("الناقل / شركة الشحن", self.carrier_ref),
                            ], spacing=8),
                            self._tf("الوجهة", self.dest_ref),
                            ft.Dropdown(
                                ref=self.status_ref,
                                label="الحالة",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                value="جاري التحضير",
                                options=[
                                    ft.dropdown.Option("جاري التحضير"),
                                    ft.dropdown.Option("تم الشحن"),
                                    ft.dropdown.Option("في الطريق"),
                                    ft.dropdown.Option("تم التسليم"),
                                    ft.dropdown.Option("عائد"),
                                ],
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_orange"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"],
                                text_size=12,
                            ),
                            ft.TextField(
                                ref=self.notes_ref,
                                label="ملاحظات",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                multiline=True, min_lines=2,
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_orange"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"],
                                text_size=12,
                            ),
                            ft.ElevatedButton(
                                "حفظ الشحنة",
                                icon=ft.Icons.SAVE_ROUNDED,
                                on_click=self._save,
                                style=ft.ButtonStyle(
                                    bgcolor=self.C["neon_orange"],
                                    color=self.C["bg_dark"],
                                    padding=ft.padding.symmetric(horizontal=20, vertical=14),
                                ),
                                width=float("inf"),
                            ),
                        ], spacing=10),
                        bgcolor=self.C["bg_card"],
                        border=ft.border.all(1, self.C["border"]),
                        border_radius=14,
                        padding=16,
                    ),

                    ft.Divider(color=self.C["border"], height=20),
                    ft.Text("سجل الشحنات", size=12, color=self.C["text_secondary"],
                            font_family="Cairo", weight=ft.FontWeight.W_600),
                    self._records_col,
                ], spacing=12),
                padding=16,
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def _tf(self, label, ref, keyboard=ft.KeyboardType.TEXT):
        return ft.TextField(
            ref=ref, label=label, expand=True,
            label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
            border_color=self.C["border"],
            focused_border_color=self.C["neon_orange"],
            color=self.C["text_primary"],
            bgcolor=self.C["surface"],
            keyboard_type=keyboard,
            text_size=12, height=48,
        )

    def _save(self, e):
        ship_no = self.ship_no_ref.current.value if self.ship_no_ref.current else ""
        if not ship_no.strip():
            self.snack("⚠️ أدخل رقم الشحنة", self.C["neon_orange"])
            return
        conn = get_db_connection(self.db_path)
        conn.execute("""
            INSERT INTO shipping_records
              (shipment_no, item_code, description, quantity, destination, carrier, status, ship_date, notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            ship_no,
            self.item_code_ref.current.value if self.item_code_ref.current else "",
            self.desc_ref.current.value if self.desc_ref.current else "",
            float(self.qty_ref.current.value or 0) if self.qty_ref.current else 0,
            self.dest_ref.current.value if self.dest_ref.current else "",
            self.carrier_ref.current.value if self.carrier_ref.current else "",
            self.status_ref.current.value if self.status_ref.current else "جاري التحضير",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            self.notes_ref.current.value if self.notes_ref.current else "",
        ))
        conn.commit()
        conn.close()
        self.snack(f"✅ تم حفظ الشحنة {ship_no}", self.C["neon_green"])
        self._load_records()
        e.page.update()

    def _load_records(self):
        conn = get_db_connection(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT shipment_no, item_code, description, quantity, destination, status, ship_date
            FROM shipping_records ORDER BY id DESC LIMIT 30
        """)
        rows = c.fetchall()
        conn.close()
        self._records_col.controls.clear()

        if not rows:
            self._records_col.controls.append(
                ft.Text("لا توجد شحنات", color=self.C["text_muted"],
                        font_family="Cairo", size=11)
            )
            return

        status_colors = {
            "تم التسليم": self.C["neon_green"],
            "تم الشحن": self.C["neon_blue"],
            "في الطريق": self.C["neon_blue_dim"],
            "عائد": self.C["neon_red"],
        }
        for row in rows:
            sno, code, desc, qty, dest, status, date = row
            sc = status_colors.get(status, self.C["neon_orange"])
            self._records_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.LOCAL_SHIPPING_OUTLINED, color=sc, size=14),
                            ft.Text(sno, size=11, weight=ft.FontWeight.BOLD,
                                    color=self.C["text_primary"], font_family="JetBrainsMono"),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(status, size=9, color=sc, font_family="Cairo"),
                                bgcolor=f"{sc}1A", border_radius=6,
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            ),
                        ]),
                        ft.Text(f"{code} | {desc or '-'}", size=10,
                                color=self.C["text_secondary"], font_family="Cairo"),
                        ft.Row([
                            ft.Text(f"الكمية: {qty}", size=10, color=self.C["text_secondary"],
                                    font_family="JetBrainsMono"),
                            ft.Text(f"إلى: {dest or '-'}", size=10,
                                    color=self.C["text_secondary"], font_family="Cairo"),
                        ], spacing=10),
                        ft.Text(date or "", size=9, color=self.C["text_muted"],
                                font_family="JetBrainsMono"),
                    ], spacing=4),
                    bgcolor=self.C["bg_card"],
                    border=ft.border.all(1, self.C["border"]),
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                )
            )
