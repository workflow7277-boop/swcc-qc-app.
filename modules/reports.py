"""
PDF Report Generator - توليد تقارير الجودة
Generates comprehensive inspection reports with embedded photos
"""
from datetime import datetime
from pathlib import Path
import os


def generate_pdf_report(db_path: str, output_path: str, assets_dir: str) -> str:
    """Generate a full QC inspection PDF report."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm, mm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         Table, TableStyle, Image as RLImage,
                                         HRFlowable, PageBreak)
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import sqlite3

        # Colors
        NEON_BLUE   = colors.HexColor("#00D4FF")
        DARK_BG     = colors.HexColor("#0D0F14")
        CARD_BG     = colors.HexColor("#13161E")
        TEXT_LIGHT  = colors.HexColor("#E8EDF5")
        TEXT_DIM    = colors.HexColor("#7A8499")
        GREEN       = colors.HexColor("#00FF88")
        RED         = colors.HexColor("#FF3366")
        ORANGE      = colors.HexColor("#FF6B35")
        WHITE       = colors.white

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=1.5*cm, leftMargin=1.5*cm,
            topMargin=2*cm, bottomMargin=2*cm,
            title="تقرير مراقبة الجودة - SWCC",
            author="SWCC QC Assistant",
        )

        styles = getSampleStyleSheet()
        story  = []

        # ── Styles ────────────────────────────────────────────────────
        title_style = ParagraphStyle(
            "Title", parent=styles["Normal"],
            fontSize=20, textColor=NEON_BLUE,
            alignment=TA_CENTER, spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle", parent=styles["Normal"],
            fontSize=11, textColor=TEXT_DIM,
            alignment=TA_CENTER, spaceAfter=2,
        )
        section_style = ParagraphStyle(
            "Section", parent=styles["Normal"],
            fontSize=13, textColor=NEON_BLUE,
            spaceBefore=12, spaceAfter=6,
            borderPad=4,
        )
        normal_style = ParagraphStyle(
            "Normal2", parent=styles["Normal"],
            fontSize=9, textColor=colors.HexColor("#333333"),
        )
        header_style = ParagraphStyle(
            "Header", parent=styles["Normal"],
            fontSize=10, textColor=WHITE, alignment=TA_CENTER,
        )

        # ── Report Header ─────────────────────────────────────────────
        now = datetime.now()
        story.append(Paragraph("⬡  SWCC Quality Control Report", title_style))
        story.append(Paragraph("الشركة السويدية الوطنية | أجهزة الري المحوري", subtitle_style))
        story.append(Paragraph(f"تاريخ التقرير: {now.strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=NEON_BLUE, spaceAfter=12))

        # ── Database Summary ──────────────────────────────────────────
        conn = sqlite3.connect(db_path)
        c    = conn.cursor()

        c.execute("SELECT COUNT(*) FROM items")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM items WHERE status='مقبول'")
        accepted = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM items WHERE status='مرفوض'")
        rejected = c.fetchone()[0]
        pending  = total - accepted - rejected

        story.append(Paragraph("ملخص الجودة", section_style))

        summary_data = [
            ["البيان", "القيمة"],
            ["إجمالي البنود", str(total)],
            ["مقبول", str(accepted)],
            ["مرفوض", str(rejected)],
            ["معلق", str(pending)],
            ["نسبة القبول", f"{round(accepted/total*100)}%" if total else "0%"],
        ]
        summary_table = Table(summary_data, colWidths=[9*cm, 6*cm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),  NEON_BLUE),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  DARK_BG),
            ("FONTSIZE",    (0, 0), (-1, 0),  10),
            ("FONTSIZE",    (0, 1), (-1, -1), 9),
            ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8F9FA"), WHITE]),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING",  (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # ── Inbound Records Table ────────────────────────────────────
        c.execute("""
            SELECT item_code, supplier, quantity_received, quantity_accepted,
                   quantity_rejected, status, inspection_date, notes
            FROM inbound_records
            ORDER BY id DESC
            LIMIT 50
        """)
        inbound_rows = c.fetchall()

        story.append(Paragraph(f"سجلات الوارد ({len(inbound_rows)} سجل)", section_style))

        if inbound_rows:
            ib_data = [["الكود", "المورد", "المستلم", "المقبول", "المرفوض", "الحالة", "التاريخ"]]
            for row in inbound_rows:
                code, sup, qr, qa, qj, status, date, notes = row
                ib_data.append([
                    str(code or ""),
                    str(sup or "")[:15],
                    str(qr or ""),
                    str(qa or ""),
                    str(qj or ""),
                    str(status or ""),
                    str(date or "")[:10],
                ])
            col_w = [3*cm, 3*cm, 2*cm, 2*cm, 2*cm, 2*cm, 3*cm]
            ib_table = Table(ib_data, colWidths=col_w)
            ib_table.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1A1E2A")),
                ("TEXTCOLOR",    (0, 0), (-1, 0),  NEON_BLUE),
                ("FONTSIZE",     (0, 0), (-1, 0),  8),
                ("FONTSIZE",     (0, 1), (-1, -1), 7),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1),[colors.HexColor("#F5F5F5"), WHITE]),
                ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                ("TOPPADDING",   (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ]))
            story.append(ib_table)
        else:
            story.append(Paragraph("لا توجد سجلات وارد.", normal_style))

        story.append(Spacer(1, 12))

        # ── Photos Section ────────────────────────────────────────────
        c.execute("""
            SELECT item_code, status, inspection_date, photo_path
            FROM inbound_records
            WHERE photo_path IS NOT NULL AND photo_path != ''
            ORDER BY id DESC LIMIT 12
        """)
        photos = c.fetchall()

        if photos:
            story.append(PageBreak())
            story.append(Paragraph("الصور الموثقة (Evidence Shield)", section_style))
            photo_pairs = []
            for code, status, date, photo_path in photos:
                if photo_path and Path(photo_path).exists():
                    try:
                        img = RLImage(photo_path, width=8.5*cm, height=6*cm)
                        caption = Paragraph(
                            f"{code} | {status} | {(date or '')[:10]}",
                            ParagraphStyle("Cap", fontSize=7, textColor=TEXT_DIM,
                                          alignment=TA_CENTER)
                        )
                        photo_pairs.append([img, caption])
                    except Exception:
                        pass

            if photo_pairs:
                # Arrange in 2 columns
                for i in range(0, len(photo_pairs), 2):
                    row_data = [[photo_pairs[i][0]], [photo_pairs[i][1]]]
                    if i + 1 < len(photo_pairs):
                        row_data[0].append(photo_pairs[i+1][0])
                        row_data[1].append(photo_pairs[i+1][1])
                    img_table = Table(
                        [[row_data[0][0], row_data[0][1] if len(row_data[0])>1 else ""],
                         [row_data[1][0], row_data[1][1] if len(row_data[1])>1 else ""]],
                        colWidths=[9*cm, 9*cm]
                    )
                    img_table.setStyle(TableStyle([
                        ("ALIGN", (0,0), (-1,-1), "CENTER"),
                        ("VALIGN",(0,0), (-1,-1), "MIDDLE"),
                        ("TOPPADDING",(0,0),(-1,-1), 6),
                        ("BOTTOMPADDING",(0,0),(-1,-1),6),
                    ]))
                    story.append(img_table)
                    story.append(Spacer(1, 8))

        # ── RFI Records ───────────────────────────────────────────────
        c.execute("SELECT rfi_no, item_code, inspection_type, result, inspection_date FROM rfi_records ORDER BY id DESC LIMIT 30")
        rfi_rows = c.fetchall()

        if rfi_rows:
            story.append(PageBreak())
            story.append(Paragraph(f"سجلات RFI ({len(rfi_rows)})", section_style))
            rfi_data = [["رقم RFI", "الكود", "نوع الفحص", "النتيجة", "التاريخ"]]
            for row in rfi_rows:
                rfi_data.append(list(str(x or "") for x in row))
            rfi_table = Table(rfi_data, colWidths=[3.5*cm, 3*cm, 4*cm, 3*cm, 3.5*cm])
            rfi_table.setStyle(TableStyle([
                ("BACKGROUND",  (0,0),(-1,0), colors.HexColor("#1A1E2A")),
                ("TEXTCOLOR",   (0,0),(-1,0), GREEN),
                ("FONTSIZE",    (0,0),(-1,-1), 8),
                ("ALIGN",       (0,0),(-1,-1), "CENTER"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#F5F5F5"), WHITE]),
                ("GRID",        (0,0),(-1,-1), 0.4, colors.HexColor("#DDDDDD")),
                ("TOPPADDING",  (0,0),(-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ]))
            story.append(rfi_table)

        conn.close()

        # ── Footer ────────────────────────────────────────────────────
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=1, color=TEXT_DIM))
        story.append(Paragraph(
            f"تم إنشاء هذا التقرير بواسطة SWCC QC Assistant | {now.strftime('%Y-%m-%d %H:%M')}",
            ParagraphStyle("Footer", fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER)
        ))

        doc.build(story)
        return output_path

    except ImportError:
        # Fallback: plain text report if reportlab not installed
        return _generate_text_report(db_path, output_path)


def _generate_text_report(db_path: str, output_path: str) -> str:
    """Fallback text report when reportlab is not available."""
    import sqlite3
    txt_path = output_path.replace(".pdf", ".txt")

    conn = sqlite3.connect(db_path)
    c    = conn.cursor()

    lines = [
        "=" * 60,
        "SWCC QC Report | تقرير مراقبة الجودة",
        f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
    ]

    c.execute("SELECT item_code, description, quantity, status FROM items ORDER BY item_code")
    rows = c.fetchall()
    lines.append(f"البنود ({len(rows)}):")
    lines.append("-" * 40)
    for r in rows:
        lines.append(f"{r[0]:15} | {str(r[1] or '')[:25]:25} | Qty:{r[2]:8} | {r[3]}")

    conn.close()
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return txt_path
