"""
RFI - Request For Inspection Section
نموذج الفحص الداخلي مع كاميرا وGPS
"""
import flet as ft
from datetime import datetime
from pathlib import Path
from modules.database import get_db_connection
from modules.watermark import apply_watermark


class RFISection:
    def __init__(self, db_path: str, colors: dict, show_snack, assets_dir: Path):
        self.db_path   = db_path
        self.C         = colors
        self.snack     = show_snack
        self.photo_dir = assets_dir / "photos" / "rfi"
        self.photo_dir.mkdir(parents=True, exist_ok=True)

        self._records_col     = ft.Column(spacing=6)
        self._current_photo   = None
        self.rfi_no_ref       = ft.Ref[ft.TextField]()
        self.item_code_ref    = ft.Ref[ft.TextField]()
        self.desc_ref         = ft.Ref[ft.TextField]()
        self.insp_type_ref    = ft.Ref[ft.Dropdown]()
        self.result_ref       = ft.Ref[ft.Dropdown]()
        self.notes_ref        = ft.Ref[ft.TextField]()
        self.photo_cont_ref   = ft.Ref[ft.Container]()
        self.img_picker = ft.FilePicker(on_result=self._on_photo)

    def build(self) -> ft.Control:
        self._load_records()
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.ASSIGNMENT_ROUNDED, color=self.C["neon_green"], size=22),
                        ft.Text("طلب فحص داخلي (RFI)", size=16, weight=ft.FontWeight.BOLD,
                                color=self.C["text_primary"], font_family="Cairo"),
                    ], spacing=10),
                    ft.Divider(color=self.C["border"]),

                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                self._tf("رقم RFI", self.rfi_no_ref),
                                self._tf("كود الصنف", self.item_code_ref),
                            ], spacing=8),
                            self._tf("الوصف", self.desc_ref),
                            ft.Dropdown(
                                ref=self.insp_type_ref,
                                label="نوع الفحص",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                value="فحص بصري",
                                options=[
                                    ft.dropdown.Option("فحص بصري"),
                                    ft.dropdown.Option("فحص أبعاد"),
                                    ft.dropdown.Option("فحص وظيفي"),
                                    ft.dropdown.Option("اختبار ضغط"),
                                    ft.dropdown.Option("فحص لحام"),
                                    ft.dropdown.Option("فحص شامل"),
                                ],
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_green"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"], text_size=12,
                            ),
                            ft.Dropdown(
                                ref=self.result_ref,
                                label="النتيجة",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                value="معلق",
                                options=[
                                    ft.dropdown.Option("مقبول",   text_style=ft.TextStyle(color=self.C["neon_green"])),
                                    ft.dropdown.Option("مرفوض",   text_style=ft.TextStyle(color=self.C["neon_red"])),
                                    ft.dropdown.Option("معلق",    text_style=ft.TextStyle(color=self.C["neon_orange"])),
                                    ft.dropdown.Option("يحتاج مراجعة"),
                                ],
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_green"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"], text_size=12,
                            ),
                            ft.TextField(
                                ref=self.notes_ref,
                                label="ملاحظات الفحص",
                                multiline=True, min_lines=2,
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_green"],
                                color=self.C["text_primary"],
                                bgcolor=self.C["surface"], text_size=12,
                            ),

                            # Camera
                            ft.ElevatedButton(
                                "توثيق بالصورة + GPS",
                                icon=ft.Icons.CAMERA_ALT_ROUNDED,
                                on_click=self._pick_photo,
                                style=ft.ButtonStyle(
                                    bgcolor=self.C["bg_glass"],
                                    color=self.C["neon_green"],
                                    side=ft.BorderSide(1, self.C["neon_green"]),
                                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                                ),
                                width=float("inf"),
                            ),
                            ft.Container(
                                ref=self.photo_cont_ref,
                                content=ft.Column([
                                    ft.Icon(ft.Icons.PHOTO_CAMERA_OUTLINED,
                                            color=self.C["text_muted"], size=28),
                                    ft.Text("لا توجد صورة", color=self.C["text_muted"],
                                            size=10, font_family="Cairo"),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=self.C["surface"],
                                border=ft.border.all(1, self.C["border"]),
                                border_radius=10, height=100,
                                alignment=ft.alignment.center,
                            ),
                            ft.ElevatedButton(
                                "حفظ RFI",
                                icon=ft.Icons.SAVE_ROUNDED,
                                on_click=self._save,
                                style=ft.ButtonStyle(
                                    bgcolor=self.C["neon_green"],
                                    color=self.C["bg_dark"],
                                    padding=ft.padding.symmetric(horizontal=20, vertical=14),
                                    text_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD,
                                                            font_family="Cairo"),
                                ),
                                width=float("inf"),
                            ),
                        ], spacing=10),
                        bgcolor=self.C["bg_card"],
                        border=ft.border.all(1, self.C["border"]),
                        border_radius=14, padding=16,
                    ),

                    ft.Divider(color=self.C["border"], height=20),
                    ft.Text("سجلات RFI", size=12, color=self.C["text_secondary"],
                            font_family="Cairo", weight=ft.FontWeight.W_600),
                    self._records_col,
                ], spacing=12),
                padding=16,
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def _tf(self, label, ref):
        return ft.TextField(
            ref=ref, label=label, expand=True,
            label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
            border_color=self.C["border"],
            focused_border_color=self.C["neon_green"],
            color=self.C["text_primary"], bgcolor=self.C["surface"],
            text_size=12, height=48,
        )

    def _pick_photo(self, e):
        e.page.overlay.append(self.img_picker)
        self.img_picker.pick_files(
            dialog_title="اختر صورة الفحص",
            allowed_extensions=["jpg", "jpeg", "png"],
        )
        e.page.update()

    def _on_photo(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return
        code = self.item_code_ref.current.value if self.item_code_ref.current else "RFI"
        ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dest = str(self.photo_dir / f"RFI_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        try:
            apply_watermark(e.files[0].path, dest, code, ts, "GPS: يتطلب صلاحية الموقع")
            self._current_photo = dest
        except Exception:
            import shutil
            shutil.copy2(e.files[0].path, dest)
            self._current_photo = dest

        if self.photo_cont_ref.current:
            self.photo_cont_ref.current.content = ft.Image(
                src=dest, fit=ft.ImageFit.COVER, border_radius=10, height=100, width=float("inf"),
            )
            e.page.update()

    def _save(self, e):
        rfi_no = self.rfi_no_ref.current.value if self.rfi_no_ref.current else ""
        if not rfi_no.strip():
            self.snack("⚠️ أدخل رقم RFI", self.C["neon_orange"])
            return
        conn = get_db_connection(self.db_path)
        conn.execute("""
            INSERT INTO rfi_records
              (rfi_no, item_code, description, inspection_type, result, inspection_date, photo_path, notes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            rfi_no,
            self.item_code_ref.current.value if self.item_code_ref.current else "",
            self.desc_ref.current.value if self.desc_ref.current else "",
            self.insp_type_ref.current.value if self.insp_type_ref.current else "فحص بصري",
            self.result_ref.current.value if self.result_ref.current else "معلق",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            self._current_photo,
            self.notes_ref.current.value if self.notes_ref.current else "",
        ))
        conn.commit()
        conn.close()
        self.snack(f"✅ تم حفظ RFI {rfi_no}", self.C["neon_green"])
        self._load_records()
        e.page.update()

    def _load_records(self):
        conn = get_db_connection(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT rfi_no, item_code, inspection_type, result, inspection_date
            FROM rfi_records ORDER BY id DESC LIMIT 30
        """)
        rows = c.fetchall()
        conn.close()
        self._records_col.controls.clear()
        if not rows:
            self._records_col.controls.append(
                ft.Text("لا توجد سجلات RFI", color=self.C["text_muted"],
                        font_family="Cairo", size=11)
            )
            return
        for row in rows:
            no, code, itype, result, date = row
            rc = (self.C["neon_green"] if result == "مقبول"
                  else self.C["neon_red"] if result == "مرفوض"
                  else self.C["neon_orange"])
            self._records_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(no, size=11, weight=ft.FontWeight.BOLD,
                                    color=self.C["text_primary"], font_family="JetBrainsMono"),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(result, size=9, color=rc, font_family="Cairo"),
                                bgcolor=f"{rc}1A", border_radius=6,
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            ),
                        ]),
                        ft.Text(f"الكود: {code} | نوع الفحص: {itype}",
                                size=10, color=self.C["text_secondary"], font_family="Cairo"),
                        ft.Text(date or "", size=9, color=self.C["text_muted"],
                                font_family="JetBrainsMono"),
                    ], spacing=4),
                    bgcolor=self.C["bg_card"],
                    border=ft.border.all(1, self.C["border"]),
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                )
            )
