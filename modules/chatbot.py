"""
AI Chatbot Section - المساعد الذكي
Natural language interface for querying items and issuing inspection commands
"""
import flet as ft
import re
from datetime import datetime
from modules.database import get_db_connection, search_items, get_item_by_code, update_item_status


class ChatbotSection:
    def __init__(self, db_path: str, colors: dict, show_snack):
        self.db_path = db_path
        self.C       = colors
        self.snack   = show_snack
        self._messages_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self.input_ref = ft.Ref[ft.TextField]()

    def build(self) -> ft.Control:
        self._load_history()
        self._add_bot_message(
            "مرحباً! أنا مساعدك الذكي لمراقبة الجودة 🤖\n\n"
            "يمكنني مساعدتك في:\n"
            "• البحث عن أي صنف بالكود أو الاسم\n"
            "• عرض المواصفة والكمية والحالة\n"
            "• تحديث حالة البنود (مثال: 'سجل PVT-001 مقبول')\n"
            "• إحصائيات المخزن والفحص\n\n"
            "ماذا تريد أن تعرف؟"
        )

        return ft.Column([
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Stack([
                            ft.Container(
                                width=36, height=36,
                                bgcolor=f"{self.C['neon_blue']}22",
                                border_radius=18,
                            ),
                            ft.Container(
                                content=ft.Icon(ft.Icons.SMART_TOY_ROUNDED,
                                                color=self.C["neon_blue"], size=20),
                                alignment=ft.alignment.center,
                                width=36, height=36,
                            ),
                        ]),
                    ),
                    ft.Column([
                        ft.Text("المساعد الذكي", size=14, weight=ft.FontWeight.BOLD,
                                color=self.C["text_primary"], font_family="Cairo"),
                        ft.Row([
                            ft.Container(width=6, height=6, bgcolor=self.C["neon_green"],
                                         border_radius=3),
                            ft.Text("متصل | يعمل أوفلاين", size=9,
                                    color=self.C["neon_green"], font_family="Cairo"),
                        ], spacing=4),
                    ], spacing=2, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_SWEEP_ROUNDED,
                        icon_color=self.C["text_secondary"],
                        icon_size=18,
                        tooltip="مسح المحادثة",
                        on_click=self._clear_chat,
                    ),
                ], spacing=10),
                bgcolor=self.C["bg_card"],
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                border=ft.border.only(bottom=ft.BorderSide(1, self.C["border"])),
            ),

            # Messages area
            ft.Container(
                content=self._messages_col,
                expand=True,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ),

            # Quick Suggestions
            ft.Container(
                content=ft.Row([
                    self._quick_chip("كشف الوارد اليوم"),
                    self._quick_chip("إحصائيات المخزن"),
                    self._quick_chip("البنود المرفوضة"),
                ], scroll=ft.ScrollMode.AUTO, spacing=6),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
            ),

            # Input Area
            ft.Container(
                content=ft.Row([
                    ft.TextField(
                        ref=self.input_ref,
                        hint_text="اكتب سؤالك أو أمر الفحص...",
                        hint_style=ft.TextStyle(color=self.C["text_muted"], size=12),
                        border_color=self.C["border"],
                        focused_border_color=self.C["neon_blue"],
                        color=self.C["text_primary"],
                        bgcolor=self.C["surface"],
                        text_size=12,
                        expand=True,
                        border_radius=24,
                        content_padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        on_submit=self._send_message,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.SEND_ROUNDED,
                        icon_color=self.C["neon_blue"],
                        icon_size=22,
                        bgcolor=f"{self.C['neon_blue']}22",
                        on_click=self._send_message,
                    ),
                ], spacing=8),
                bgcolor=self.C["bg_card"],
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border=ft.border.only(top=ft.BorderSide(1, self.C["border"])),
            ),
        ], expand=True, spacing=0)

    def _quick_chip(self, text: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(text, size=10, color=self.C["neon_blue"], font_family="Cairo"),
            bgcolor=f"{self.C['neon_blue']}1A",
            border=ft.border.all(1, f"{self.C['neon_blue']}44"),
            border_radius=16,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            on_click=lambda e, t=text: self._quick_send(e, t),
            ink=True,
        )

    def _quick_send(self, e, text: str):
        if self.input_ref.current:
            self.input_ref.current.value = text
        self._process_message(text, e.page)

    def _send_message(self, e):
        text = self.input_ref.current.value if self.input_ref.current else ""
        if not text.strip():
            return
        self._process_message(text, e.page)
        if self.input_ref.current:
            self.input_ref.current.value = ""
        e.page.update()

    def _process_message(self, text: str, page):
        # Add user message
        self._add_user_message(text)
        self._save_chat("user", text)

        # Parse intent
        response = self._parse_and_respond(text.strip())

        self._add_bot_message(response)
        self._save_chat("assistant", response)
        page.update()

    def _parse_and_respond(self, text: str) -> str:
        t = text.lower()

        # ── Command: Register inspection result ──────────────────────
        # "سجل PVT-001 مقبول" / "البند PVT-005 مرفوض"
        cmd_match = re.search(
            r"(سجل|ثبت|قيد|البند|حالة)\s+([A-Za-z0-9\-_]+)\s+(مقبول|مرفوض|معلق|قيد الفحص)",
            text, re.UNICODE
        )
        if cmd_match:
            code   = cmd_match.group(2).upper()
            status = cmd_match.group(3)
            item   = get_item_by_code(self.db_path, code)
            if item:
                update_item_status(self.db_path, code, status)
                sc = "✅" if status == "مقبول" else "❌" if status == "مرفوض" else "⏳"
                return (f"{sc} تم تحديث البند {code}\n"
                        f"الوصف: {item.get('description', '-')}\n"
                        f"الحالة الجديدة: {status}\n"
                        f"الوقت: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
            return f"⚠️ لم يتم العثور على البند: {code}\nتأكد من الكود وحاول مرة أخرى."

        # ── Query: Item by code ──────────────────────────────────────
        code_match = re.search(r'\b([A-Za-z]{2,6}-\d{2,6})\b', text, re.UNICODE)
        if code_match:
            code = code_match.group(1).upper()
            return self._get_item_info(code)

        # ── Statistics ───────────────────────────────────────────────
        if any(k in t for k in ["إحصاء", "إحصائيات", "إجمالي", "كم بند", "عدد"]):
            return self._get_statistics()

        # ── Inbound today ────────────────────────────────────────────
        if any(k in t for k in ["اليوم", "الوارد", "وارد اليوم", "كشف الوارد"]):
            return self._get_today_inbound()

        # ── Rejected items ───────────────────────────────────────────
        if any(k in t for k in ["مرفوض", "مرفوضة", "البنود المرفوضة"]):
            return self._get_rejected_items()

        # ── Accepted items ───────────────────────────────────────────
        if any(k in t for k in ["مقبول", "مقبولة", "البنود المقبولة"]):
            return self._get_accepted_items()

        # ── Pending items ─────────────────────────────────────────────
        if any(k in t for k in ["معلق", "قيد الفحص", "لم يفحص"]):
            return self._get_pending_items()

        # ── Search by name ────────────────────────────────────────────
        results = search_items(self.db_path, text)
        if results:
            if len(results) == 1:
                return self._format_item(results[0])
            lines = [f"🔍 وجدت {len(results)} نتائج لـ '{text}':\n"]
            for r in results[:5]:
                sc = "✅" if r["status"] == "مقبول" else "❌" if r["status"] == "مرفوض" else "⏳"
                lines.append(f"{sc} {r['item_code']} - {r['description'] or '-'}\n"
                              f"   الكمية: {r['quantity']} {r['unit'] or ''} | {r['status']}")
            if len(results) > 5:
                lines.append(f"\n... و{len(results)-5} نتائج أخرى")
            return "\n".join(lines)

        # ── Help ──────────────────────────────────────────────────────
        if any(k in t for k in ["مساعدة", "مساعد", "help", "كيف"]):
            return self._get_help()

        return (f"🤔 لم أفهم طلبك تماماً.\n\n"
                f"جرب:\n"
                f"• 'اعطني معلومات عن PVT-001'\n"
                f"• 'سجل PVT-005 مقبول'\n"
                f"• 'إحصائيات المخزن'\n"
                f"• 'البنود المرفوضة'")

    def _get_item_info(self, code: str) -> str:
        item = get_item_by_code(self.db_path, code)
        if not item:
            return f"❌ البند {code} غير موجود في قاعدة البيانات."
        return self._format_item(item)

    def _format_item(self, item: dict) -> str:
        sc = "✅" if item.get("status") == "مقبول" else "❌" if item.get("status") == "مرفوض" else "⏳"
        lines = [
            f"📦 **{item['item_code']}**",
            f"الوصف: {item.get('description') or '-'}",
            f"الكمية: {item.get('quantity', 0)} {item.get('unit', 'EA')}",
            f"المواصفة: {item.get('specification') or '-'}",
            f"المورد: {item.get('supplier') or '-'}",
            f"الفئة: {item.get('category') or '-'}",
            f"الحالة: {sc} {item.get('status', 'معلق')}",
        ]
        if item.get("notes"):
            lines.append(f"ملاحظات: {item['notes']}")
        lines.append(f"\nآخر تحديث: {item.get('updated_at', '-')}")
        return "\n".join(lines)

    def _get_statistics(self) -> str:
        conn = get_db_connection(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM items")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM items WHERE status='مقبول'")
        acc = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM items WHERE status='مرفوض'")
        rej = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM inbound_records")
        inb = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM rfi_records")
        rfi = c.fetchone()[0]
        conn.close()
        pending = total - acc - rej
        acc_pct  = round(acc/total*100) if total else 0
        return (f"📊 إحصائيات المخزن والجودة:\n\n"
                f"إجمالي البنود: {total}\n"
                f"✅ مقبول: {acc} ({acc_pct}%)\n"
                f"❌ مرفوض: {rej}\n"
                f"⏳ معلق: {pending}\n\n"
                f"سجلات الوارد: {inb}\n"
                f"سجلات RFI: {rfi}")

    def _get_today_inbound(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        conn  = get_db_connection(self.db_path)
        c     = conn.cursor()
        c.execute("""
            SELECT item_code, quantity_received, status, inspection_date
            FROM inbound_records
            WHERE inspection_date LIKE ?
            ORDER BY id DESC LIMIT 10
        """, (f"{today}%",))
        rows = c.fetchall()
        conn.close()
        if not rows:
            return f"📭 لا توجد سجلات وارد لليوم {today}"
        lines = [f"📥 الوارد اليوم ({today}) - {len(rows)} سجل:\n"]
        for r in rows:
            sc = "✅" if r[2] == "مقبول" else "❌" if r[2] == "مرفوض" else "⏳"
            lines.append(f"{sc} {r[0]} | الكمية: {r[1]} | {r[2]}")
        return "\n".join(lines)

    def _get_rejected_items(self) -> str:
        conn = get_db_connection(self.db_path)
        c    = conn.cursor()
        c.execute("""
            SELECT item_code, description, quantity
            FROM items WHERE status='مرفوض'
            ORDER BY item_code LIMIT 15
        """)
        rows = c.fetchall()
        conn.close()
        if not rows:
            return "✅ لا توجد بنود مرفوضة حالياً!"
        lines = [f"❌ البنود المرفوضة ({len(rows)}):\n"]
        for r in rows:
            lines.append(f"• {r[0]} - {r[1] or '-'} (الكمية: {r[2]})")
        return "\n".join(lines)

    def _get_accepted_items(self) -> str:
        conn = get_db_connection(self.db_path)
        c    = conn.cursor()
        c.execute("SELECT COUNT(*) FROM items WHERE status='مقبول'")
        count = c.fetchone()[0]
        c.execute("""
            SELECT item_code, description FROM items
            WHERE status='مقبول' ORDER BY item_code LIMIT 10
        """)
        rows = c.fetchall()
        conn.close()
        lines = [f"✅ البنود المقبولة: {count}\n\nآخر 10:\n"]
        for r in rows:
            lines.append(f"• {r[0]} - {r[1] or '-'}")
        return "\n".join(lines)

    def _get_pending_items(self) -> str:
        conn = get_db_connection(self.db_path)
        c    = conn.cursor()
        c.execute("""
            SELECT item_code, description FROM items
            WHERE status='معلق' ORDER BY item_code LIMIT 10
        """)
        rows = c.fetchall()
        conn.close()
        if not rows:
            return "🎉 لا توجد بنود معلقة!"
        lines = [f"⏳ بنود معلقة (عرض أول 10):\n"]
        for r in rows:
            lines.append(f"• {r[0]} - {r[1] or '-'}")
        return "\n".join(lines)

    def _get_help(self) -> str:
        return (
            "📖 دليل الاستخدام:\n\n"
            "🔍 البحث:\n"
            "  • 'PVT-001' أو 'صامولة'\n"
            "  • 'معلومات عن مضخة'\n\n"
            "✅ إصدار أمر فحص:\n"
            "  • 'سجل PVT-001 مقبول'\n"
            "  • 'ثبت PVT-005 مرفوض'\n\n"
            "📊 الإحصائيات:\n"
            "  • 'إحصائيات المخزن'\n"
            "  • 'كشف الوارد اليوم'\n"
            "  • 'البنود المرفوضة'\n"
            "  • 'البنود المقبولة'"
        )

    def _add_user_message(self, text: str):
        self._messages_col.controls.append(
            ft.Container(
                content=ft.Text(text, size=12, color=self.C["text_primary"],
                                font_family="Cairo", selectable=True),
                bgcolor=f"{self.C['neon_blue']}22",
                border=ft.border.all(1, f"{self.C['neon_blue']}44"),
                border_radius=ft.border_radius.only(
                    top_left=16, top_right=16, bottom_left=16, bottom_right=4),
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                margin=ft.margin.only(left=40),
                alignment=ft.alignment.center_right,
            )
        )

    def _add_bot_message(self, text: str):
        self._messages_col.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SMART_TOY_ROUNDED,
                                color=self.C["neon_blue"], size=14),
                        ft.Text("المساعد", size=9, color=self.C["neon_blue"],
                                font_family="Cairo"),
                    ], spacing=4),
                    ft.Text(text, size=11, color=self.C["text_primary"],
                            font_family="Cairo", selectable=True),
                ], spacing=6),
                bgcolor=self.C["bg_card"],
                border=ft.border.all(1, self.C["border"]),
                border_radius=ft.border_radius.only(
                    top_left=4, top_right=16, bottom_left=16, bottom_right=16),
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                margin=ft.margin.only(right=40),
            )
        )

    def _save_chat(self, role: str, message: str):
        try:
            conn = get_db_connection(self.db_path)
            conn.execute(
                "INSERT INTO chat_history (role, message) VALUES (?,?)",
                (role, message)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _load_history(self):
        try:
            conn = get_db_connection(self.db_path)
            c    = conn.cursor()
            c.execute("""
                SELECT role, message FROM chat_history
                ORDER BY id DESC LIMIT 20
            """)
            rows = list(reversed(c.fetchall()))
            conn.close()
            for role, msg in rows:
                if role == "user":
                    self._add_user_message(msg)
                else:
                    self._add_bot_message(msg)
        except Exception:
            pass

    def _clear_chat(self, e):
        self._messages_col.controls.clear()
        try:
            conn = get_db_connection(self.db_path)
            conn.execute("DELETE FROM chat_history")
            conn.commit()
            conn.close()
        except Exception:
            pass
        self._add_bot_message("تمت إعادة تعيين المحادثة. كيف يمكنني مساعدتك؟ 😊")
        e.page.update()
