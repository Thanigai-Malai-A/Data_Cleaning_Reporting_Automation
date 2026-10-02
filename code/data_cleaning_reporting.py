from pathlib import Path
from io import StringIO
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "dataset"
OUTPUT_DIR = PROJECT_ROOT / "output"
CHART_DIR = OUTPUT_DIR / "charts"
REPORT_DIR = PROJECT_ROOT / "report"
RAW_CSV = DATASET_DIR / "raw_data.csv"
RAW_XLSX = DATASET_DIR / "raw_data.xlsx"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_COLUMNS = ["Record_ID", "Date", "Product", "Category", "Region", "Quantity", "Unit_Price", "Revenue"]
TEXT_COLUMNS = ["Product", "Category", "Region"]
NUMERIC_COLUMNS = ["Quantity", "Unit_Price", "Revenue"]

PRODUCT_ALIASES = {
    "plc": "PLC", "servo motor": "Servo Motor", "industrial sensor": "Industrial Sensor",
    "hmi panel": "HMI Panel", "robotic arm": "Robotic Arm", "vfd": "VFD",
}
CATEGORY_ALIASES = {
    "control systems": "Control Systems", "control system": "Control Systems",
    "motion control": "Motion Control", "sensors": "Sensors", "sensor": "Sensors",
    "robotics": "Robotics", "industrial drives": "Industrial Drives", "industrial drive": "Industrial Drives",
}
REGION_ALIASES = {
    "chennai": "Chennai", "bengaluru": "Bengaluru", "pune": "Pune",
    "hyderabad": "Hyderabad", "coimbatore": "Coimbatore",
}


def save_csv(df, path):
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    Path(path).write_text(buffer.getvalue(), encoding="utf-8")


def parse_mixed_dates(series):
    s = series.astype("string").str.strip()
    result = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    iso_mask = s.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
    slash_mask = s.str.match(r"^\d{2}/\d{2}/\d{4}$", na=False)
    dash_mask = s.str.match(r"^\d{2}-\d{2}-\d{4}$", na=False)
    named_mask = s.str.match(r"^[A-Za-z]{3} \d{1,2}, \d{4}$", na=False)
    result.loc[iso_mask] = pd.to_datetime(s.loc[iso_mask], format="%Y-%m-%d", errors="coerce")
    result.loc[slash_mask] = pd.to_datetime(s.loc[slash_mask], format="%d/%m/%Y", errors="coerce")
    result.loc[dash_mask] = pd.to_datetime(s.loc[dash_mask], format="%d-%m-%Y", errors="coerce")
    result.loc[named_mask] = pd.to_datetime(s.loc[named_mask], format="%b %d, %Y", errors="coerce")
    return result


def clean_currency_number(series):
    return pd.to_numeric(
        series.astype("string")
        .str.replace("₹", "", regex=False)
        .str.replace("INR", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False),
        errors="coerce",
    )


def standardize_text(series, aliases):
    normalized = series.astype("string").str.strip().str.lower()
    return normalized.map(aliases)


def create_pdf_report(metrics, cleaning_df, summary_stats, category_summary, monthly_summary):
    pdf_path = REPORT_DIR / "Data_Cleaning_Reporting_Automation_Report.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER, fontSize=20, leading=24, spaceAfter=16))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=11))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=13, leading=16, spaceBefore=10, spaceAfter=7))
    story = []
    story.append(Paragraph("Data Cleaning & Reporting Automation", styles["TitleCenter"]))
    story.append(Paragraph("Automated preprocessing, quality control, reporting, and visual summary pipeline", styles["Heading3"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Dataset note: This project uses a synthetic/illustrative dataset created specifically for demonstrating data-cleaning automation. It is not real company data.", styles["BodyText"]))

    story.append(Paragraph("1. Objective", styles["Section"]))
    story.append(Paragraph("Build a reproducible Python workflow that detects and handles common data-quality problems, produces cleaned data, and automatically generates summary reports and visualizations.", styles["BodyText"]))

    story.append(Paragraph("2. Data-quality issues addressed", styles["Section"]))
    issues = [
        "Missing values in region, category, quantity, unit price, and revenue fields.",
        "Exact duplicate rows.",
        "Inconsistent capitalization and whitespace in product, category, and region values.",
        "Mixed date formats and invalid dates.",
        "Currency symbols and thousands separators stored inside numeric fields.",
        "Invalid quantity/price values.",
        "Revenue values inconsistent with quantity multiplied by unit price.",
    ]
    for item in issues:
        story.append(Paragraph("- " + item, styles["BodyText"]))

    story.append(Paragraph("3. Cleaning methodology", styles["Section"]))
    rules = [
        "Strip whitespace and standardize known product, category, and region aliases.",
        "Parse mixed date formats and remove records with invalid essential dates.",
        "Convert quantities and prices to numeric values; remove non-positive quantities/prices.",
        "Impute missing quantity using the median quantity for the standardized product.",
        "Impute missing unit price using the median unit price for the standardized product, with a global median fallback.",
        "Fill missing region/category values with documented fallback rules where possible.",
        "Recalculate revenue as Quantity x Unit_Price to correct missing or inconsistent revenue values.",
        "Remove duplicate records before and after standardization.",
    ]
    for item in rules:
        story.append(Paragraph("- " + item, styles["BodyText"]))

    story.append(Paragraph("4. Cleaning results", styles["Section"]))
    metric_rows = [
        ["Metric", "Value"],
        ["Original rows", str(metrics["original_rows"])],
        ["Original columns", str(metrics["original_columns"])],
        ["Duplicate rows removed", str(metrics["duplicates_removed"])],
        ["Invalid/removed rows", str(metrics["invalid_rows_removed"])],
        ["Final rows", str(metrics["final_rows"])],
        ["Missing cells before", str(metrics["missing_cells_before"])],
        ["Missing cells after", str(metrics["missing_cells_after"])],
        ["Standardized text changes", str(metrics["text_changes"])],
        ["Revenue corrections", str(metrics["revenue_corrections"])],
    ]
    tbl = Table(metric_rows, colWidths=[3.4*inch, 1.6*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f4e78")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.HexColor("#eef4f8")]),
    ]))
    story.append(tbl)

    story.append(Paragraph("5. Automated visual summaries", styles["Section"]))
    chart_files = [
        ("Missing values before vs after cleaning", CHART_DIR/"missing_values_comparison.png"),
        ("Records before vs after cleaning", CHART_DIR/"records_before_after.png"),
        ("Category distribution", CHART_DIR/"category_distribution.png"),
        ("Monthly trend", CHART_DIR/"monthly_trend.png"),
    ]
    for title, path in chart_files:
        story.append(Paragraph(title, styles["Heading4"]))
        story.append(Image(str(path), width=6.6*inch, height=3.6*inch))
        story.append(Spacer(1, 8))

    story.append(PageBreak())
    story.append(Paragraph("6. Summary outputs", styles["Section"]))
    story.append(Paragraph("The workflow saves machine-readable outputs for further analysis and reproducibility: cleaned_data.csv, cleaning_summary.csv, summary_statistics.csv, category_summary.csv, monthly_summary.csv, and automated_report.txt.", styles["BodyText"]))

    story.append(Paragraph("7. Conclusion", styles["Section"]))
    story.append(Paragraph("The completed pipeline turns intentionally messy source data into a standardized dataset while documenting what was changed. The same script can be rerun on a compatible CSV or Excel input, making the cleaning and reporting process repeatable and efficient.", styles["BodyText"]))

    story.append(Paragraph("8. Future improvements", styles["Section"]))
    story.append(Paragraph("Possible extensions include configurable validation rules, automated email delivery of reports, scheduled execution, anomaly-detection checks, interactive dashboards, and database connectivity.", styles["BodyText"]))

    doc.build(story)
    return pdf_path


def generate_charts(cleaned, monthly_summary, category_summary, missing_before, missing_after, original_rows, final_rows):
    before_total = int(missing_before.sum())
    after_total = int(missing_after.sum())
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(["Before", "After"], [before_total, after_total])
    ax.set_title("Missing Values: Before vs After Cleaning")
    ax.set_ylabel("Missing cells")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHART_DIR/"missing_values_comparison.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(["Original", "Cleaned"], [original_rows, final_rows])
    ax.set_title("Records: Before vs After Cleaning")
    ax.set_ylabel("Rows")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHART_DIR/"records_before_after.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    cat_plot = category_summary.sort_values("Revenue", ascending=False)
    ax.bar(cat_plot["Category"], cat_plot["Revenue"])
    ax.set_title("Revenue by Category")
    ax.set_ylabel("Revenue")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHART_DIR/"category_distribution.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(monthly_summary["Month"], monthly_summary["Revenue"], marker="o")
    ax.set_title("Monthly Revenue Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHART_DIR/"monthly_trend.png", dpi=160)
    plt.close(fig)


def generate_report_text(metrics):
    lines = [
        "DATA CLEANING & REPORTING AUTOMATION - AUTOMATED REPORT",
        "Dataset: synthetic/illustrative internship dataset",
        "",
        f"Original rows: {metrics['original_rows']}",
        f"Original columns: {metrics['original_columns']}",
        f"Duplicate rows removed: {metrics['duplicates_removed']}",
        f"Invalid/removed rows: {metrics['invalid_rows_removed']}",
        f"Final rows: {metrics['final_rows']}",
        f"Missing cells before: {metrics['missing_cells_before']}",
        f"Missing cells after: {metrics['missing_cells_after']}",
        f"Text values standardized: {metrics['text_changes']}",
        f"Revenue values recalculated/corrected: {metrics['revenue_corrections']}",
        "",
        "Cleaning rules:",
        "- Standardize whitespace and text aliases.",
        "- Parse mixed dates and remove invalid dates.",
        "- Convert numeric fields and remove non-positive quantity/price rows.",
        "- Impute missing quantity and unit price using product medians.",
        "- Fill missing region/category values with documented fallbacks.",
        "- Recalculate revenue as Quantity * Unit_Price.",
        "- Remove duplicates.",
    ]
    (OUTPUT_DIR/"automated_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run():
    parser = argparse.ArgumentParser(description="Automated data cleaning and reporting")
    parser.add_argument("--input", default=None, help="Path to CSV or XLSX. Defaults to dataset/raw_data.csv or raw_data.xlsx")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else (RAW_CSV if RAW_CSV.exists() else RAW_XLSX)
    if not input_path.exists():
        raise FileNotFoundError("No input dataset found. Put raw_data.csv or raw_data.xlsx in dataset/.")

    if input_path.suffix.lower() == ".xlsx":
        raw = pd.read_excel(input_path)
    else:
        raw = pd.read_csv(input_path)

    print(f"Original shape: {raw.shape}")
    print("Columns:", raw.columns.tolist())
    print("Missing values before:\n", raw.isna().sum())
    duplicates_before = int(raw.duplicated().sum())
    print("Duplicate rows:", duplicates_before)

    missing_before = raw.isna().sum().copy()
    original_rows, original_columns = raw.shape

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df = raw[REQUIRED_COLUMNS].copy()

    # First duplicate removal
    df = df.drop_duplicates().copy()
    duplicates_removed = original_rows - len(df)

    # Preserve raw string forms for comparison.
    original_text_snapshot = df[TEXT_COLUMNS].astype("string").copy()

    # Standardize text
    for col in TEXT_COLUMNS:
        aliases = PRODUCT_ALIASES if col == "Product" else CATEGORY_ALIASES if col == "Category" else REGION_ALIASES
        df[col] = standardize_text(df[col], aliases)

    # Fill category from product where missing; otherwise leave unknown.
    product_to_category = {
        "PLC": "Control Systems", "Servo Motor": "Motion Control", "Industrial Sensor": "Sensors",
        "HMI Panel": "Control Systems", "Robotic Arm": "Robotics", "VFD": "Industrial Drives",
    }
    df["Category"] = df["Category"].fillna(df["Product"].map(product_to_category))
    df["Product"] = df["Product"].fillna("Unknown Product")
    df["Category"] = df["Category"].fillna("Unknown")
    df["Region"] = df["Region"].fillna("Unknown")

    text_changes = int((original_text_snapshot != df[TEXT_COLUMNS].astype("string")).fillna(False).sum().sum())

    # Dates
    df["Date"] = parse_mixed_dates(df["Date"])
    invalid_date_mask = df["Date"].isna()

    # Numerics
    for col in NUMERIC_COLUMNS:
        df[col] = clean_currency_number(df[col])

    # Remove invalid essential numerical records (non-positive quantity/price)
    invalid_numeric_mask = (df["Quantity"] <= 0) | (df["Unit_Price"] <= 0)
    invalid_mask = invalid_date_mask | invalid_numeric_mask
    invalid_rows_removed = int(invalid_mask.sum())
    df = df.loc[~invalid_mask].copy()

    # Median imputation by product
    for col in ["Quantity", "Unit_Price"]:
        med = df.groupby("Product")[col].transform("median")
        df[col] = df[col].fillna(med)
        df[col] = df[col].fillna(df[col].median())
    df["Quantity"] = df["Quantity"].round().astype("int64")
    df["Unit_Price"] = df["Unit_Price"].round(2)

    # Keep track of revenue mismatches before recalc
    old_revenue = df["Revenue"].copy()
    recalculated_revenue = df["Quantity"] * df["Unit_Price"]
    revenue_corrections = int(((old_revenue - recalculated_revenue).abs() > 0.01).fillna(old_revenue.isna()).sum())
    df["Revenue"] = recalculated_revenue.round(2)

    # Canonical formatting
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df["Record_ID"] = pd.to_numeric(df["Record_ID"], errors="coerce")
    df = df.dropna(subset=["Record_ID", "Date"]).copy()
    df["Record_ID"] = df["Record_ID"].astype("int64")

    # Final dedupe after standardization
    before_final_dedupe = len(df)
    df = df.drop_duplicates().copy()
    duplicates_after_standardization = before_final_dedupe - len(df)

    # Ensure no missing values remain in reporting fields.
    for col in REQUIRED_COLUMNS:
        if df[col].isna().any():
            if col in ["Product", "Category", "Region"]:
                df[col] = df[col].fillna("Unknown")
            else:
                df[col] = df[col].fillna(0)

    final_rows = len(df)
    missing_after = df[REQUIRED_COLUMNS].isna().sum()

    # Outputs
    save_csv(df, OUTPUT_DIR/"cleaned_data.csv")
    summary_stats = df[["Quantity", "Unit_Price", "Revenue"]].describe().round(2).reset_index()
    save_csv(summary_stats, OUTPUT_DIR/"summary_statistics.csv")

    category_summary = df.groupby("Category", dropna=False).agg(
        Records=("Record_ID", "count"), Quantity=("Quantity", "sum"), Revenue=("Revenue", "sum")
    ).reset_index().sort_values("Revenue", ascending=False)
    save_csv(category_summary, OUTPUT_DIR/"category_summary.csv")

    monthly = df.copy()
    monthly["Date"] = pd.to_datetime(monthly["Date"])
    monthly_summary = monthly.groupby(monthly["Date"].dt.to_period("M")).agg(
        Records=("Record_ID", "count"), Quantity=("Quantity", "sum"), Revenue=("Revenue", "sum")
    ).reset_index()
    monthly_summary["Month"] = monthly_summary["Date"].astype(str)
    monthly_summary = monthly_summary[["Month", "Records", "Quantity", "Revenue"]]
    save_csv(monthly_summary, OUTPUT_DIR/"monthly_summary.csv")

    cleaning_summary = pd.DataFrame([{
        "Original_Rows": original_rows,
        "Original_Columns": original_columns,
        "Missing_Cells_Before": int(missing_before.sum()),
        "Duplicate_Rows_Removed": duplicates_removed,
        "Duplicates_After_Standardization_Removed": duplicates_after_standardization,
        "Invalid_Rows_Removed": invalid_rows_removed,
        "Rows_Removed_Total": original_rows - final_rows,
        "Final_Rows": final_rows,
        "Final_Columns": df.shape[1],
        "Missing_Cells_After": int(missing_after.sum()),
        "Text_Values_Standardized": text_changes,
        "Revenue_Values_Corrected": revenue_corrections,
    }])
    save_csv(cleaning_summary, OUTPUT_DIR/"cleaning_summary.csv")

    metrics = cleaning_summary.iloc[0].to_dict()
    metrics = {
        "original_rows": int(metrics["Original_Rows"]), "original_columns": int(metrics["Original_Columns"]),
        "duplicates_removed": int(metrics["Duplicate_Rows_Removed"]), "invalid_rows_removed": int(metrics["Invalid_Rows_Removed"]),
        "final_rows": int(metrics["Final_Rows"]), "missing_cells_before": int(metrics["Missing_Cells_Before"]),
        "missing_cells_after": int(metrics["Missing_Cells_After"]), "text_changes": int(metrics["Text_Values_Standardized"]),
        "revenue_corrections": int(metrics["Revenue_Values_Corrected"]),
    }
    generate_report_text(metrics)
    generate_charts(df, monthly_summary, category_summary, missing_before, missing_after, original_rows, final_rows)
    create_pdf_report(metrics, cleaning_summary, summary_stats, category_summary, monthly_summary)

    print("\nCleaning complete.")
    print(f"Final shape: {df.shape}")
    print("Missing after:\n", missing_after)
    print("Outputs written to:", OUTPUT_DIR)


if __name__ == "__main__":
    run()
