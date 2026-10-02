# Data Cleaning & Reporting Automation

## Project Overview

This internship project automates data cleaning, preprocessing, reporting, and visual summary generation using Python. The workflow is reproducible from raw input to final report.

> **Dataset note:** The included dataset is **synthetic/illustrative** and was created for demonstration. It does not represent real company data.

## Objective

Automate common data-quality checks and cleaning tasks, then generate machine-readable outputs, charts, and a PDF report.

## Features
- Missing-value detection and handling
- Duplicate detection and removal
- Text/whitespace standardization
- Category and region normalization
- Mixed-date parsing and invalid-date detection
- Numeric/currency cleanup
- Invalid quantity/price validation
- Revenue consistency correction
- Automated CSV reports
- Automated Matplotlib visualizations
- Automated PDF report generation

## Technologies
Python 3, pandas, NumPy, Matplotlib, openpyxl, ReportLab

## Folder Structure
```text
Data_Cleaning_Reporting_Automation/
├── code/data_cleaning_reporting.py
├── dataset/raw_data.csv
├── dataset/dataset_description.txt
├── output/
│   ├── cleaned_data.csv
│   ├── cleaning_summary.csv
│   ├── summary_statistics.csv
│   ├── category_summary.csv
│   ├── monthly_summary.csv
│   ├── automated_report.txt
│   └── charts/
│       ├── missing_values_comparison.png
│       ├── records_before_after.png
│       ├── category_distribution.png
│       └── monthly_trend.png
├── report/Data_Cleaning_Reporting_Automation_Report.pdf
├── .gitignore
├── README.md
├── requirements.txt
└── results_summary.txt
```

## Installation
```bash
python -m pip install -r requirements.txt
```

## Run
```bash
python code/data_cleaning_reporting.py
```

Use another CSV or Excel input:
```bash
python code/data_cleaning_reporting.py --input dataset/raw_data.csv
python code/data_cleaning_reporting.py --input dataset/raw_data.xlsx
```

Required columns: `Record_ID, Date, Product, Category, Region, Quantity, Unit_Price, Revenue`

## Cleaning Methodology
1. Detect missing values and duplicates.
2. Standardize whitespace and known text aliases.
3. Parse multiple date formats and remove invalid dates.
4. Convert numeric/currency fields.
5. Remove non-positive quantity or price rows.
6. Impute missing quantity and unit price with product medians and fallbacks.
7. Fill missing category/region values using documented rules.
8. Recalculate `Revenue = Quantity * Unit_Price`.
9. Remove duplicates after standardization.
10. Generate CSV reports, charts, and PDF report.

## Results
- Original records: **290**
- Duplicate rows removed: **10**
- Invalid rows removed: **9**
- Final cleaned records: **252**
- Missing cells before cleaning: **41**
- Missing cells after cleaning: **0**
- Standardized text values: **127**
- Revenue corrections: **22**

## Generated Reports
`output/cleaning_summary.csv`, `output/summary_statistics.csv`, `output/category_summary.csv`, `output/monthly_summary.csv`, `output/automated_report.txt`, and `report/Data_Cleaning_Reporting_Automation_Report.pdf`.

## Visual Summaries
Four PNG charts are generated inside `output/charts/`.

## Reproducibility
The raw dataset is preserved. Running the script regenerates the cleaned data, reports, charts, text report, and PDF.

## Limitations
Validation rules are designed for the included demonstration schema; production implementations would normally use configurable rules, logging, scheduling, databases, and domain-specific validation.

## Future Improvements
Scheduled execution, email delivery, database connectivity, anomaly detection, and interactive dashboards.
"# Data_Cleaning_Reporting_Automation" 
