from reportlab.platypus import Table, TableStyle, Spacer, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
from typing import List

def generate_summary_tables(df: pd.DataFrame) -> List:
    flowables = []
    styles = getSampleStyleSheet()
    title_style = styles["Heading4"]

    # Dataset-level summary
    mem_usage = df.memory_usage(deep=True).sum()
    avg_record_size = mem_usage / len(df) if len(df) > 0 else 0
    type_counts = {
        "Numeric": sum(df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x))),
        "Categorical": sum(df.dtypes == "category"),
        "Boolean": sum(df.dtypes == "bool"),
        "Text": sum(df.dtypes == "object"),
        "DateTime": sum(pd.api.types.is_datetime64_any_dtype(x) for x in df.dtypes),
    }

    dataset_stats = [
        ["Dataset statistics", ""],
        ["Number of variables", len(df.columns)],
        ["Number of observations", len(df)],
        ["Missing cells", df.isnull().sum().sum()],
        ["Missing cells (%)", f"{df.isnull().sum().sum() / df.size * 100:.1f}%"],
        ["Duplicate rows", df.duplicated().sum()],
        ["Duplicate rows (%)", f"{df.duplicated().mean() * 100:.1f}%"],
        ["Total size in memory", f"{mem_usage / 1024:.1f} KiB"],
        ["Average record size in memory", f"{avg_record_size / 1024:.1f} KiB"],
        ["", ""],  # spacer row
        ["Variable types", ""],
    ] + [[k, v] for k, v in type_counts.items()]

    heading_indices = [0, 10]

    dataset_table = Table(dataset_stats, hAlign="LEFT", colWidths=[180, 100])
    style_commands = [
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]
    for idx in heading_indices:
        style_commands.extend([
            ("BACKGROUND", (0, idx), (-1, idx), colors.lightgrey),
            ("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold"),
        ])
    dataset_table.setStyle(TableStyle(style_commands))

    flowables.append(Paragraph("📊 Dataset Summary", title_style))
    flowables.append(dataset_table)
    flowables.append(Spacer(1, 8))

    # Per-variable summary
    var_stats = [["Variable", "Distinct", "Distinct (%)", "Missing", "Missing (%)", "Memory", "Type"]]
    for col in df.columns:
        col_data = df[col]
        distinct = col_data.nunique(dropna=True)
        missing = col_data.isnull().sum()
        mem = col_data.memory_usage(deep=True)
        var_stats.append([
            col,
            distinct,
            f"{distinct / len(df) * 100:.1f}%" if len(df) > 0 else "0.0%",
            missing,
            f"{missing / len(df) * 100:.1f}%" if len(df) > 0 else "0.0%",
            f"{mem / 1024:.1f} KiB",
            str(col_data.dtype),
        ])

    var_table = Table(var_stats, repeatRows=1, hAlign="LEFT", colWidths=[80, 40, 50, 40, 50, 60, 60])
    var_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))
    flowables.append(Paragraph("📋 Variable Summary", title_style))
    flowables.append(var_table)

    return flowables
