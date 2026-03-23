"""
Inbound Inspection Section - فحص المواد الواردة
Handles incoming goods inspection with camera + GPS watermarking
"""
import flet as ft
import sqlite3
import base64
import os
from datetime import datetime
from pathlib import Path

from modules.database import get_db_connection, search_items
from modules.watermark import apply_watermark


class InboundSection:
    def __init__(self, db_path: str, colors: dict, show_snack, assets_dir: Path):
        self.db_path   = db_path
        self.C         = colors
        self.snack     = show_snack
        self.assets    = assets_dir
        self.photo_dir = assets_dir / "photos" / "inbound"
        self.photo_dir.mkdir(parents=True, exist_ok=True)

        # Form state
        self.selected_code   = ft.Ref[ft.Dropdown]()
        self.supplier_field  = ft.Ref[ft.TextField]()
        self.qty_recv_field  = ft.Ref[ft.TextField]()
        self.qty_acc_field   = ft.Ref[ft.TextField]()
        self.qty_rej_field   = ft.Ref[ft.TextField]()
        self.spec_field      = ft.Ref[ft.TextField]()
        self.notes_field     = ft.Ref[ft.TextField]()
        self.status_dd       = ft.Ref[ft.Dropdown]()
        self.photo_preview   = ft.Ref[ft.Image]()
        self.photo_container = ft.Ref[ft.Container]()
        self.search_field    = ft.Ref[ft.TextField]()

        self._current_photo_path = None
        self._records_col = ft.Column(spacing=6)

        # File pickers
        self.img_picker = ft.FilePicker(on_result=self._on_photo_picked)
        self.cam_picker = ft.FilePicker(on_result=self._on_cam_result)

    def build(self) -> ft.Control:
        self._load_records()

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    # ── Section Header ──────────────────────────────
                    ft.Row([
                        ft.Icon(ft.Icons.INBOX_ROUNDED, color=self.C["neon_blue"], size=22),
                        ft.Text("فحص المواد الواردة", size=16, weight=ft.FontWeight.BOLD,
                                color=self.C["text_primary"], font_family="Cairo"),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH_ROUNDED,
                            icon_color=self.C["neon_blue"],
                            icon_size=18,
                            on_click=lambda e: self._refresh_records(e),
                        ),
                    ], spacing=10),
                    ft.Divider(color=self.C["border"]),

                    # ── Search Bar ──────────────────────────────────
                    ft.TextField(
                        ref=self.search_field,
                        hint_text="بحث بالكود أو الوصف...",
                        hint_style=ft.TextStyle(color=self.C["text_muted"], size=12),
                        prefix_icon=ft.Icons.SEARCH_ROUNDED,
                        border_color=self.C["border"],
                        focused_border_color=self.C["neon_blue"],
                        color=self.C["text_primary"],
                        bgcolor=self.C["surface"],
                        text_size=12,
                        height=44,
                        on_submit=lambda e: self._search_item(e),
                        on_change=lambda e: self._search_item(e),
                    ),

                    # ── Inspection Form ─────────────────────────────
                    ft.Container(
                        content=ft.Column([
                            ft.Text("نموذج الفحص", size=12, color=self.C["text_secondary"],
                                    font_family="Cairo", weight=ft.FontWeight.W_600),

                            # Item Code Dropdown
                            ft.Dropdown(
                                ref=self.selected_code,
                                label="كود الصنف",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                options=self._get_item_options(),
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_blue"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"],
                                text_size=12,
                                on_change=self._on_item_selected,
                            ),

                            # Supplier
                            ft.TextField(
                                ref=self.supplier_field,
                                label="المورد",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_blue"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"],
                                text_size=12,
                                height=48,
                            ),

                            # Quantities Row
                            ft.Row([
                                ft.TextField(
                                    ref=self.qty_recv_field,
                                    label="المستلم",
                                    label_style=ft.TextStyle(color=self.C["text_secondary"], size=10),
                                    border_color=self.C["border"],
                                    focused_border_color=self.C["neon_blue"],
                                    color=self.C["text_primary"],
                                    bgcolor=self.C["surface"],
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    text_size=12,
                                    height=48,
                                    expand=True,
                                    on_change=self._auto_calc,
                                ),
                                ft.TextField(
                                    ref=self.qty_acc_field,
                                    label="المقبول",
                                    label_style=ft.TextStyle(color=self.C["text_secondary"], size=10),
                                    border_color=self.C["border"],
                                    focused_border_color=self.C["neon_green"],
                                    color=self.C["neon_green"],
                                    bgcolor=self.C["surface"],
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    text_size=12,
                                    height=48,
                                    expand=True,
                                    on_change=self._auto_calc,
                                ),
                                ft.TextField(
                                    ref=self.qty_rej_field,
                                    label="المرفوض",
                                    label_style=ft.TextStyle(color=self.C["text_secondary"], size=10),
                                    border_color=self.C["border"],
                                    focused_border_color=self.C["neon_red"],
                                    color=self.C["neon_red"],
                                    bgcolor=self.C["surface"],
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    text_size=12,
                                    height=48,
                                    expand=True,
                                ),
                            ], spacing=8),

                            # Specification
                            ft.TextField(
                                ref=self.spec_field,
                                label="المواصفة الفنية",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_blue"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"],
                                text_size=12,
                                height=48,
                            ),

                            # Status
                            ft.Dropdown(
                                ref=self.status_dd,
                                label="حالة الفحص",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                value="معلق",
                                options=[
                                    ft.dropdown.Option("مقبول",   text_style=ft.TextStyle(color=self.C["neon_green"])),
                                    ft.dropdown.Option("مرفوض",   text_style=ft.TextStyle(color=self.C["neon_red"])),
                                    ft.dropdown.Option("معلق",    text_style=ft.TextStyle(color=self.C["neon_orange"])),
                                    ft.dropdown.Option("قيد الفحص"),
                                ],
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_blue"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"],
                                text_size=12,
                            ),

                            # Notes
                            ft.TextField(
                                ref=self.notes_field,
                                label="ملاحظات",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                multiline=True,
                                min_lines=2,
                                max_lines=3,
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_blue"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"],
                                text_size=12,
                            ),

                            # ── Photo Capture ───────────────────────
                            ft.Text("توثيق بالصورة", size=11, color=self.C["text_secondary"],
                                    font_family="Cairo"),
                            ft.Row([
                                ft.ElevatedButton(
                                    "التقاط صورة",
                                    icon=ft.Icons.CAMERA_ALT_ROUNDED,
                                    on_click=self._capture_photo,
                                    style=ft.ButtonStyle(
                                        bgcolor=self.C["bg_glass"],
                                        color=self.C["neon_blue"],
                                        side=ft.BorderSide(1, self.C["neon_blue"]),
                                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                                    ),
                                    expand=True,
                                ),
                                ft.ElevatedButton(
                                    "رفع صورة",
                                    icon=ft.Icons.UPLOAD_ROUNDED,
                                    on_click=self._upload_photo,
                                    style=ft.ButtonStyle(
                                        bgcolor=self.C["bg_glass"],
                                        color=self.C["text_secondary"],
                                        side=ft.BorderSide(1, self.C["border"]),
                                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                                    ),
                                    expand=True,
                                ),
                            ], spacing=8),

                            # Photo Preview
                            ft.Container(
                                ref=self.photo_container,
                                content=ft.Column([
                                    ft.Icon(ft.Icons.ADD_A_PHOTO_ROUNDED,
                                            color=self.C["text_muted"], size=30),
                                    ft.Text("لا توجد صورة", color=self.C["text_muted"],
                                            size=10, font_family="Cairo"),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=self.C["surface"],
                                border=ft.border.all(1, self.C["border"]),
                                border_radius=10,
                                height=120,
                                alignment=ft.alignment.center,
                                visible=True,
                            ),

                            # Submit Button
                            ft.ElevatedButton(
                                "حفظ سجل الفحص",
                                icon=ft.Icons.SAVE_ROUNDED,
                                on_click=self._save_record,
                                style=ft.ButtonStyle(
                                    bgcolor=self.C["neon_blue"],
                                    color=self.C["bg_dark"],
                                    padding=ft.padding.symmetric(horizontal=20, vertical=14),
                                    text_style=ft.TextStyle(
                                        size=13, weight=ft.FontWeight.BOLD, font_family="Cairo"
                                    ),
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

                    # ── Records List ────────────────────────────────
                    ft.Row([
                        ft.Text("سجلات الوارد", size=12, color=self.C["text_secondary"],
                                font_family="Cairo", weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                    ]),
                    self._records_col,
                ], spacing=12),
                padding=16,
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    # ── Helpers ──────────────────────────────────────────────────────
    def _get_item_options(self):
        conn = get_db_connection(self.db_path)
        c = conn.cursor()
        c.execute("SELECT item_code, description FROM items ORDER BY item_code LIMIT 200")
        opts = [ft.dropdown.Option(r[0], f"{r[0]} - {r[1] or ''}") for r in c.fetchall()]
        conn.close()
        return opts if opts else [ft.dropdown.Option("-- لا توجد بنود --")]

    def _on_item_selected(self, e):
        code = e.control.value
        if not code or code.startswith("--"):
            return
        conn = get_db_connection(self.db_path)
        c = conn.cursor()
        c.execute("SELECT specification, supplier FROM items WHERE item_code=?", (code,))
        row = c.fetchone()
        conn.close()
        if row:
            if self.spec_field.current:
                self.spec_field.current.value = row[0] or ""
            if self.supplier_field.current:
                self.supplier_field.current.value = row[1] or ""
            e.page.update()

    def _auto_calc(self, e):
        try:
            recv = float(self.qty_recv_field.current.value or 0)
            acc  = float(self.qty_acc_field.current.value or 0)
            rej  = recv - acc
            if self.qty_rej_field.current and rej >= 0:
                self.qty_rej_field.current.value = str(rej)
                e.page.update()
        except (ValueError, AttributeError):
            pass

    def _search_item(self, e):
        q = e.control.value
        if not q or len(q) < 2:
            return
        results = search_items(self.db_path, q)
        if results and self.selected_code.current:
            self.selected_code.current.value = results[0]["item_code"]
            e.page.update()

    def _capture_photo(self, e):
        """Use device camera via FilePicker capture."""
        e.page.overlay.append(self.cam_picker)
        self.cam_picker.pick_files(
            dialog_title="التقاط صورة",
            allowed_extensions=["jpg", "jpeg", "png"],
        )
        e.page.update()

    def _upload_photo(self, e):
        e.page.overlay.append(self.img_picker)
        self.img_picker.pick_files(
            dialog_title="اختر صورة",
            allowed_extensions=["jpg", "jpeg", "png", "webp"],
        )
        e.page.update()

    def _on_cam_result(self, e: ft.FilePickerResultEvent):
        self._process_photo(e)

    def _on_photo_picked(self, e: ft.FilePickerResultEvent):
        self._process_photo(e)

    def _process_photo(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return
        src_path = e.files[0].path
        code = ""
        if self.selected_code.current:
            code = self.selected_code.current.value or "UNKNOWN"

        # Apply watermark
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        gps_text = "GPS: يتطلب صلاحية الموقع"

        dest_name = f"{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        dest_path = str(self.photo_dir / dest_name)

        try:
            apply_watermark(src_path, dest_path, code, ts, gps_text)
            self._current_photo_path = dest_path
        except Exception:
            # Fallback: just copy without watermark
            import shutil
            shutil.copy2(src_path, dest_path)
            self._current_photo_path = dest_path

        # Update preview
        if self.photo_container.current:
            self.photo_container.current.content = ft.Image(
                src=dest_path,
                fit=ft.ImageFit.COVER,
                border_radius=10,
                height=120,
                width=float("inf"),
            )
            e.page.update()

    def _save_record(self, e):
        code = self.selected_code.current.value if self.selected_code.current else None
        if not code or code.startswith("--"):
            self.snack("⚠️ يرجى اختيار كود الصنف", self.C["neon_orange"])
            return

        try:
            qty_r = float(self.qty_recv_field.current.value or 0)
            qty_a = float(self.qty_acc_field.current.value or 0)
            qty_j = float(self.qty_rej_field.current.value or 0)
        except ValueError:
            self.snack("⚠️ الكميات يجب أن تكون أرقاماً", self.C["neon_orange"])
            return

        status    = self.status_dd.current.value if self.status_dd.current else "معلق"
        supplier  = self.supplier_field.current.value if self.supplier_field.current else ""
        spec      = self.spec_field.current.value if self.spec_field.current else ""
        notes     = self.notes_field.current.value if self.notes_field.current else ""
        ts        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection(self.db_path)
        conn.execute("""
            INSERT INTO inbound_records
              (item_code, supplier, quantity_received, quantity_accepted, quantity_rejected,
               specification, status, inspection_date, photo_path, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (code, supplier, qty_r, qty_a, qty_j, spec, status, ts,
              self._current_photo_path, notes))
        conn.execute(
            "UPDATE items SET status=?, updated_at=? WHERE item_code=?",
            (status, ts, code)
        )
        conn.commit()
        conn.close()

        self.snack(f"✅ تم حفظ فحص {code} - {status}", self.C["neon_green"])
        self._reset_form(e.page)
        self._refresh_records(e)

    def _reset_form(self, page):
        for ref in [self.supplier_field, self.qty_recv_field, self.qty_acc_field,
                    self.qty_rej_field, self.spec_field, self.notes_field]:
            if ref.current:
                ref.current.value = ""
        if self.status_dd.current:
            self.status_dd.current.value = "معلق"
        self._current_photo_path = None
        if self.photo_container.current:
            self.photo_container.current.content = ft.Column([
                ft.Icon(ft.Icons.ADD_A_PHOTO_ROUNDED, color=self.C["text_muted"], size=30),
                ft.Text("لا توجد صورة", color=self.C["text_muted"], size=10, font_family="Cairo"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        page.update()

    def _load_records(self):
        conn = get_db_connection(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT id, item_code, supplier, quantity_received, quantity_accepted,
                   quantity_rejected, status, inspection_date, photo_path
            FROM inbound_records
            ORDER BY id DESC LIMIT 30
        """)
        rows = c.fetchall()
        conn.close()
        self._records_col.controls.clear()

        if not rows:
            self._records_col.controls.append(
                ft.Container(
                    content=ft.Text("لا توجد سجلات بعد", color=self.C["text_muted"],
                                    font_family="Cairo", size=11),
                    padding=16, alignment=ft.alignment.center,
                )
            )
            return

        for row in rows:
            rid, code, sup, qr, qa, qj, status, date, photo = row
            status_color = (self.C["neon_green"] if status == "مقبول"
                            else self.C["neon_red"] if status == "مرفوض"
                            else self.C["neon_orange"])
            self._records_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(code, size=12, weight=ft.FontWeight.BOLD,
                                    color=self.C["text_primary"], font_family="JetBrainsMono"),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(status, size=9, color=status_color, font_family="Cairo"),
                                bgcolor=f"{status_color}1A",
                                border_radius=6,
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            ),
                        ]),
                        ft.Row([
                            ft.Text(f"المورد: {sup or '-'}", size=10, color=self.C["text_secondary"], font_family="Cairo"),
                            ft.Container(expand=True),
                            ft.Text(f"م:{qr or 0} | ق:{qa or 0} | ر:{qj or 0}",
                                    size=10, color=self.C["text_secondary"], font_family="JetBrainsMono"),
                        ]),
                        ft.Text(date or "", size=9, color=self.C["text_muted"], font_family="JetBrainsMono"),
                    ], spacing=4),
                    bgcolor=self.C["bg_card"],
                    border=ft.border.all(1, self.C["border"]),
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                )
            )

    def _refresh_records(self, e):
        self._load_records()
        if hasattr(e, "page") and e.page:
            e.page.update()
