import os
from typing import List
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import matplotlib.pyplot as plt
from io import BytesIO
import pandas as pd
from app.data_types import DataProfileState, SheetState
from app.summary_tables import generate_summary_tables
from app.format_insights import format_insights_flowables



BASE_DIR = os.path.dirname(__file__)
REPORT_DIR = os.path.join(BASE_DIR, "generated_reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def make_pdf_report(state: DataProfileState) -> DataProfileState:
    updated_sheets: List[SheetState] = []
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]

    desc_style = ParagraphStyle(
    name="Description",
    parent=normal_style,
    alignment=TA_LEFT,
    wordWrap="CJK",
    leading=12,
    fontName="Helvetica",
    fontSize=8,   
)

    for sheet in state.get("sheets", []):
        df = sheet.get("df")
        images_with_descriptions = []

        # Generate charts
        for chart_name, chart in sheet.get("visuals", {}).items():
            plot_code = chart.get("plot", "").replace("plt.show()", "")
            description = chart.get("description", "")
            local_scope = {"df": df, "plt": plt, "pd": pd}
            try:
                exec(plot_code, {}, local_scope)
            except Exception as e:
                print(f"[ERROR] Executing plot code for {chart_name}: {e}")
                continue

            fig = plt.gcf()
            if fig is not None and plt.get_fignums():
                buf = BytesIO()
                try:
                    fig.savefig(buf, format="png", bbox_inches="tight")
                    buf.seek(0)
                    images_with_descriptions.append((buf, description))
                except Exception as e:
                    print(f"[ERROR] Saving figure for {chart_name}: {e}")
                finally:
                    plt.close(fig)
            else:
                print(f"[WARNING] No figure generated for {chart_name} in {sheet.get('sheet_name')}")

        # Create PDF
        pdf_filename = os.path.join(REPORT_DIR, f"{sheet.get('sheet_name')}.pdf")
        c = canvas.Canvas(pdf_filename, pagesize=A4)
        width, height = A4

        # Business Insights page
        c.setFont("Helvetica-Bold", 13)
        c.drawString(50, height - 50, "Business Insights")
        insights_raw = sheet.get("insights", "")
        flowables = format_insights_flowables(insights_raw, styles)
        frame_x = 50
        frame_width = width - 100
        frame_height = height - 140
        frame_y = 50
        insights_frame = Frame(frame_x, frame_y, frame_width, frame_height, showBoundary=0)
        insights_frame.addFromList(flowables, c)
        c.showPage()

        # Summary Tables
        summary_flowables = generate_summary_tables(df)
        summary_frame = Frame(50, 50, width - 100, height - 100, showBoundary=0)
        summary_frame.addFromList(summary_flowables, c)
        c.showPage()

        # Charts and their Descriptions
        if images_with_descriptions:

            margin_x = 18
            margin_y = 24 
            grid_cols = 2
            grid_rows = 2
            charts_per_page = grid_cols * grid_rows
            cell_w = (width - 2 * margin_x) / grid_cols
            cell_h = (height - 2 * margin_y) / grid_rows
            padding = 6      
            desc_gap = 6     
            image_area_ratio = 0.62 
            image_area_h = cell_h * image_area_ratio - padding 
            desc_area_h = cell_h - image_area_h - desc_gap - 2 * padding  

            for i, (img_buf, description) in enumerate(images_with_descriptions):

                # New page every 4 charts (except before the first)
                if i > 0 and i % charts_per_page == 0:
                    c.showPage()

               
                local_index = i % charts_per_page
                col = local_index % grid_cols
                row = local_index // grid_cols
                x_left = margin_x + col * cell_w
                y_top = height - margin_y - row * cell_h 

                # Load image
                try:
                    img = ImageReader(img_buf)
                except Exception as e:
                    print(f"[ERROR] ImageReader failed: {e}")
                    continue

                iw, ih = img.getSize()

                # Max drawable size for the image inside the cell
                max_img_w = cell_w - 2 * padding
                max_img_h = image_area_h
                scale = min(max_img_w / iw, max_img_h / ih, 1.0)
                img_w = iw * scale
                img_h = ih * scale
                img_x = x_left + (cell_w - img_w) / 2
                img_y = y_top - padding - img_h 

                c.drawImage(
                    img, img_x, img_y,
                    width=img_w, height=img_h,
                    preserveAspectRatio=True, anchor='sw'
                )

                desc_html = (description or " ").replace("\n", "<br/>")
                desc_para = Paragraph(desc_html, desc_style)
                desc_frame_x = x_left + padding
                desc_frame_y = img_y - desc_gap - desc_area_h
                desc_frame_w = cell_w - 2 * padding
                desc_frame_h = desc_area_h
                desc_frame = Frame(
                    desc_frame_x, desc_frame_y,
                    desc_frame_w, desc_frame_h,
                    showBoundary=0
                )
                desc_frame.addFromList([desc_para], c)
            c.showPage()

        c.save()
        sheet["pdf_path"] = os.path.basename(pdf_filename)
        updated_sheets.append(sheet)

    state["sheets"] = updated_sheets
    print("PDFAgent is done")
    return state
