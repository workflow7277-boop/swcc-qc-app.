"""
Library Section - مكتبة الوثائق الهندسية
PDF viewer and file manager for engineering drawings
"""
import flet as ft
import os
import shutil
from datetime import datetime
from pathlib import Path
from modules.database import get_db_connection


class LibrarySection:
    def __init__(self, library_dir: Path, colors: dict, show_snack):
        self.lib_dir  = library_dir
        self.C        = colors
        self.snack    = show_snack
        self._docs_col = ft.Column(spacing=8)
        self.title_ref = ft.Ref[ft.TextField]()
        self.type_ref  = ft.Ref[ft.Dropdown]()
        self.code_ref  = ft.Ref[ft.TextField]()
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self._pending_file = None

    def build(self) -> ft.Control:
        self._load_docs()
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=self.C["neon_blue"], size=22),
                        ft.Text("مكتبة الوثائق الهندسية", size=16, weight=ft.FontWeight.BOLD,
                                color=self.C["text_primary"], font_family="Cairo"),
                    ], spacing=10),
                    ft.Divider(color=self.C["border"]),

                    # Add new document
                    ft.Container(
                        content=ft.Column([
                            ft.Text("إضافة وثيقة / رسم هندسي", size=12,
                                    color=self.C["text_secondary"], font_family="Cairo",
                                    weight=ft.FontWeight.W_600),
                            ft.TextField(
                                ref=self.title_ref,
                                label="عنوان الوثيقة",
                                label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                border_color=self.C["border"],
                                focused_border_color=self.C["neon_blue"],
                                color=self.C["text_primary"], bgcolor=self.C["surface"],
                                text_size=12, height=48,
                            ),
                            ft.Row([
                                ft.Dropdown(
                                    ref=self.type_ref,
                                    label="نوع الوثيقة",
                                    label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                    value="رسم هندسي",
                                    options=[
                                        ft.dropdown.Option("رسم هندسي"),
                                        ft.dropdown.Option("مواصفة"),
                                        ft.dropdown.Option("دليل تشغيل"),
                                        ft.dropdown.Option("شهادة جودة"),
                                        ft.dropdown.Option("تقرير فحص"),
                                        ft.dropdown.Option("أخرى"),
                                    ],
                                    border_color=self.C["border"],
                                    focused_border_color=self.C["neon_blue"],
                                    color=self.C["text_primary"],
                                    bgcolor=self.C["surface"], text_size=12, expand=True,
                                ),
                                ft.TextField(
                                    ref=self.code_ref,
                                    label="الكود المرتبط",
                                    label_style=ft.TextStyle(color=self.C["text_secondary"], size=11),
                                    border_color=self.C["border"],
                                    focused_border_color=self.C["neon_blue"],
                                    color=self.C["text_primary"], bgcolor=self.C["surface"],
                                    text_size=12, height=48, expand=True,
                                ),
                            ], spacing=8),

                            ft.ElevatedButton(
                                "اختيار ملف PDF / صورة",
                                icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                                on_click=self._pick_file,
                                style=ft.ButtonStyle(
                                    bgcolor=self.C["bg_glass"],
                                    color=self.C["neon_blue"],
                                    side=ft.BorderSide(1, self.C["neon_blue"]),
                                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                                ),
                                width=float("inf"),
                            ),
                            ft.ElevatedButton(
                                "حفظ في المكتبة",
                                icon=ft.Icons.SAVE_ROUNDED,
                                on_click=self._save_doc,
                                style=ft.ButtonStyle(
                                    bgcolor=self.C["neon_blue"],
                                    color=self.C["bg_dark"],
                                    padding=ft.padding.symmetric(horizontal=20, vertical=14),
                                ),
                                width=float("inf"),
                            ),
                        ], spacing=10),
                        bgcolor=self.C["bg_card"],
                        border=ft.border.all(1, self.C["border"]),
                        border_radius=14, padding=16,
                    ),

                    ft.Divider(color=self.C["border"], height=20),
                    ft.Text("الوثائق المحفوظة", size=12, color=self.C["text_secondary"],
                            font_family="Cairo", weight=ft.FontWeight.W_600),
                    self._docs_col,
                ], spacing=12),
                padding=16,
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def _pick_file(self, e):
        e.page.overlay.append(self.file_picker)
        self.file_picker.pick_files(
            dialog_title="اختر ملفاً",
            allowed_extensions=["pdf", "png", "jpg", "jpeg", "dwg"],
        )
        e.page.update()

    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self._pending_file = e.files[0].path
            self.snack(f"📎 تم اختيار: {e.files[0].name}", self.C["neon_blue"])

    def _save_doc(self, e):
        if not self._pending_file:
            self.snack("⚠️ اختر ملفاً أولاً", self.C["neon_orange"])
            return
        title = self.title_ref.current.value if self.title_ref.current else ""
        if not title.strip():
            self.snack("⚠️ أدخل عنوان الوثيقة", self.C["neon_orange"])
            return

        src = Path(self._pending_file)
        dest = self.lib_dir / src.name
        shutil.copy2(src, dest)

        conn = get_db_connection(self._get_db_path())
        conn.execute("""
            INSERT INTO library_docs (title, file_path, doc_type, item_code)
            VALUES (?,?,?,?)
        """, (
            title,
            str(dest),
            self.type_ref.current.value if self.type_ref.current else "رسم هندسي",
            self.code_ref.current.value if self.code_ref.current else "",
        ))
        conn.commit()
        conn.close()

        self.snack(f"✅ تمت إضافة: {title}", self.C["neon_green"])
        self._pending_file = None
        self._load_docs()
        e.page.update()

    def _get_db_path(self):
        return str(self.lib_dir.parent.parent / "data" / "swcc_qc.db")

    def _load_docs(self):
        self._docs_col.controls.clear()
        try:
            conn = get_db_connection(self._get_db_path())
            c = conn.cursor()
            c.execute("SELECT id, title, file_path, doc_type, item_code, added_at FROM library_docs ORDER BY id DESC")
            rows = c.fetchall()
            conn.close()
        except Exception:
            rows = []

        if not rows:
            # Also scan library folder directly
            files = list(self.lib_dir.glob("*"))
            if not files:
                self._docs_col.controls.append(
                    ft.Text("لا توجد وثائق", color=self.C["text_muted"],
                            font_family="Cairo", size=11)
                )
                return
            for f in files[:20]:
                self._docs_col.controls.append(self._doc_card(f.stem, str(f), "ملف", "", ""))
            return

        for row in rows:
            rid, title, path, dtype, code, added = row
            self._docs_col.controls.append(self._doc_card(title, path, dtype, code, added))

    def _doc_card(self, title, path, dtype, code, added):
        icon = ft.Icons.PICTURE_AS_PDF_ROUNDED if str(path).endswith(".pdf") else ft.Icons.IMAGE_ROUNDED
        icon_color = self.C["neon_orange"] if str(path).endswith(".pdf") else self.C["neon_blue"]
        ext = Path(path).suffix.upper()

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=icon_color, size=22),
                    bgcolor=f"{icon_color}1A",
                    border_radius=8, padding=10,
                ),
                ft.Column([
                    ft.Text(title, size=11, weight=ft.FontWeight.W_600,
                            color=self.C["text_primary"], font_family="Cairo"),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(dtype, size=8, color=self.C["neon_blue_dim"],
                                            font_family="Cairo"),
                            bgcolor=f"{self.C['neon_blue']}1A",
                            border_radius=4, padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        ),
                        ft.Text(f"  {ext}", size=8, color=self.C["text_muted"],
                                font_family="JetBrainsMono"),
                        ft.Text(f"  {code or ''}", size=8, color=self.C["text_secondary"],
                                font_family="JetBrainsMono"),
                    ]),
                    ft.Text(added or "", size=8, color=self.C["text_muted"],
                            font_family="JetBrainsMono"),
                ], spacing=4, expand=True),
                ft.IconButton(
                    icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                    icon_color=self.C["text_secondary"],
                    icon_size=16,
                    tooltip="فتح الملف",
                    on_click=lambda e, p=path: self._open_file(e, p),
                ),
            ], spacing=10),
            bgcolor=self.C["bg_card"],
            border=ft.border.all(1, self.C["border"]),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
        )

    def _open_file(self, e, path: str):
        import subprocess, sys
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as ex:
            self.snack(f"❌ لا يمكن فتح الملف: {ex}", self.C["neon_red"])
