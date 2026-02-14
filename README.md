# ♻️ MRF Digital Suite (Dakshina Kannada Zilla Panchayat)

A full-stack analytics and reporting platform designed for Material Recovery Facilities (MRFs) to streamline waste management operations. This application digitizes the tracking of daily waste processing, revenue generation, and operational efficiency using **Streamlit**, **Python**, and **SQLite**.

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-ff4b4b)

## 🎯 Project Overview
This tool solves the challenge of inconsistent data reporting in waste management. It allows operators to:
1.  **Ingest** daily waste records from various CSV formats (handling dirty data).
2.  **Visualize** key performance indicators (KPIs) like total waste, revenue, and material composition.
3.  **Generate** automated PDF & CSV reports for government compliance.

## ✨ Key Features

### 📊 Interactive Dashboard
* **Real-time Metrics:** Tracks Total Waste, Revenue Potential, and Daily Averages.
* **Visual Analytics:** Interactive Plotly charts for Weekly Trends, Material Composition (Donut Chart), and Destination Breakdown.
* **Smart "Empty State":** Guides new users to load sample data if the database is empty.

### 🛡️ Robust Data Pipeline (ETL)
* **Smart Column Mapping:** Automatically detects and maps mismatched headers (e.g., handles both `vehicle_id` and `vehicle_no`).
* **Data Validation:** Skips corrupt rows (non-numeric weights, missing dates) and logs errors without crashing.
* **Duplicate Protection:** Checks for existing records before insertion to prevent double-counting.
* **Append Mode:** Users can choose to **append** to historical data or **overwrite** for a fresh start.

### 📑 Automated Reporting
* Generates professional **PDF Reports** with summary tables and statistics.
* Exports clean, aggregated **CSV data** for further analysis.

## 🛠️ Tech Stack
* **Frontend:** Streamlit (Python)
* **Data Processing:** Pandas, SQLite3
* **Visualization:** Plotly Express
* **Reporting:** ReportLab (PDF Generation)

## 📂 Project Structure
```text
├── app.py       # Main Application UI & Logic
├── report_generator.py    # Backend: ETL logic, Validation, PDF Generation
├── dashboard.py           # Data Fetching & Aggregation Queries
├── mrf_data.db            # SQLite Database (Auto-created)
├── requirements.txt       # Project Dependencies
└── README.md              # Documentation
