from reportlab.platypus import Paragraph, Spacer, ListItem, ListFlowable
from typing import List, Dict
import re
from reportlab.lib.styles import ParagraphStyle


def parse_insights_blocks(raw: str) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []

    # Match headings like "Insight 1:"
    heading_pat = re.compile(r"Insight\s*(\d+)\s*:", re.IGNORECASE)

    # Match fields, stopping at the next marker
    field_pat = {
        "insight": re.compile(
            r"Insight:\s*(.+?)(?=\s*Takeaway:|\s*Visualization|\Z)",
            re.IGNORECASE | re.DOTALL,
        ),
        "takeaway": re.compile(
            r"Takeaway:\s*(.+?)(?=\s*Visualization|\Z)",
            re.IGNORECASE | re.DOTALL,
        ),
    }

    headings = list(heading_pat.finditer(raw))
    for idx, m in enumerate(headings):
        start = m.start()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(raw)
        chunk = raw[start:end].strip()

        num = m.group(1).strip()
        title = f"Insight {num}"

        insight = ""
        takeaway = ""

        mi = field_pat["insight"].search(chunk)
        if mi:
            insight = mi.group(1).strip()

        mt = field_pat["takeaway"].search(chunk)
        if mt:
            takeaway = mt.group(1).strip()

        results.append({
            "num": num,
            "title": title,
            "insight": insight,
            "takeaway": takeaway,
        })
    
    return results


def format_insights_flowables(insights_raw: str, styles) -> List:
    """
    Convert parsed insights into ReportLab flowables:
    - Heading: "N: Title" (bold)
    - Bullets: "Insight: ..." and "Takeaway: ..." (bold labels)
    Returns a list of flowables for insertion into a Frame.
    """
    flowables = []
    parsed = parse_insights_blocks(insights_raw)

    # Styles
    heading_style = ParagraphStyle(
        name="InsightHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        name="InsightBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        leftIndent=12,   
        bulletIndent=0,
    )

    for block in parsed:
        
        heading_text = f"<b>{block['num']}: {block['title']}</b>"
        flowables.append(Paragraph(heading_text, heading_style))

        # Bulleted items
        bullets = []

        # Keep labels bold; content is plain. 
        def md_bold_to_html(s: str) -> str:
            return re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", s or "")

        insight_html = f"<b>Insight:</b> {md_bold_to_html(block['insight'])}"
        takeaway_html = f"<b>Takeaway:</b> {md_bold_to_html(block['takeaway'])}"

        bullets.append(Paragraph(insight_html, bullet_style))
        bullets.append(Paragraph(takeaway_html, bullet_style))

        flowables.append(ListFlowable(
            [ListItem(b, leftIndent=0) for b in bullets],
            bulletType='bullet',       
            leftIndent=0,
            bulletFontName="Helvetica",
            bulletFontSize=8,
            bulletOffsetY=0,
            spaceBefore=0,
            spaceAfter=8               
        ))

        # small spacer to avoid crowding between headings
        flowables.append(Spacer(1, 2))

    if not parsed:
        flowables.append(Paragraph("No insights available", styles["Normal"]))

    return flowables


