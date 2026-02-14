import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import random
import csv
import os

def init_db(db_path):
    """
    Initializes the SQLite database with the required table.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS waste_records (
                 id INTEGER PRIMARY KEY,
                 date TEXT NOT NULL,
                 vehicle_id TEXT,
                 weight REAL,
                 material TEXT,
                 destination TEXT)''')
    conn.commit()
    conn.close()

def import_csv_data(db_path, csv_path):
    """
    Imports data from a CSV file into the database.
    Includes robust column mapping to handle different header names.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
        
        for row in reader:
            date_val = row.get('date', row.get('Date'))
            
            vehicle = row.get('vehicle_id', row.get('vehicle_no', row.get('Vehicle No')))
            
            weight_val = row.get('weight', row.get('weight_kg', row.get('Weight')))
            
            material_val = row.get('material', row.get('waste_type', row.get('Waste Type')))
            
            dest_val = row.get('destination', row.get('source_panchayat', row.get('Source')))

            if date_val and weight_val:
                try:
                    c.execute(
                        "INSERT INTO waste_records (date, vehicle_id, weight, material, destination) VALUES (?, ?, ?, ?, ?)",
                        (
                            date_val, 
                            vehicle, 
                            float(weight_val), 
                            material_val, 
                            dest_val
                        )
                    )
                except ValueError:
                    print(f"Skipping row due to invalid data: {row}")
    
    conn.commit()
    conn.close()
    print(f"Imported data from {csv_path}")

def load_sample_data(db_path):
    """
    Generates 100 records of mock data for testing purposes.
    """
    materials = ["PET", "HDPE", "Paper", "Glass", "MLP", "Rubber"]
    destinations = ["Reliance Recycling", "ACC Cement", "ITC Paper Mill"]
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Clear existing data to avoid duplicates when loading sample data
    c.execute("DELETE FROM waste_records")
    
    # Generate data for last 30 days
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(100):  # 100 sample records
        days_offset = random.randint(0, 29)
        record_date = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        record = (
            record_date,
            f"KA19MJ{random.randint(1000,9999)}",
            round(50 + (i * 1.5), 2),
            random.choice(materials),
            random.choice(destinations)
        )
        c.execute("INSERT INTO waste_records (date, vehicle_id, weight, material, destination) VALUES (?,?,?,?,?)", record)
    
    conn.commit()
    conn.close()
    print("Loaded 100 sample records")

def generate_reports(db_path, start_date, end_date, report_folder):
    """
    Generates CSV and PDF reports for the specified date range.
    """
    if not os.path.exists(report_folder):
        os.makedirs(report_folder)

    conn = sqlite3.connect(db_path)
    query = f"""
        SELECT date, vehicle_id, weight, material, destination 
        FROM waste_records 
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print(f"No records found between {start_date} and {end_date}")
        return None, None
    
    # Material rates from DK ZP data
    material_rates = {
        "PET": 28, "HDPE": 28, "Paper": 11, "Glass": 2, 
        "MLP": -4, "Rubber": -4
    }
    
    csv_filename = f"MRF_Report_{start_date}_to_{end_date}.csv"
    csv_filepath = os.path.join(report_folder, csv_filename)
    df.to_csv(csv_filepath, index=False)
    
    pdf_filename = f"MRF_Report_{start_date}_to_{end_date}.pdf"
    pdf_filepath = os.path.join(report_folder, pdf_filename)
    
    doc = SimpleDocTemplate(pdf_filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph("Dakshina Kannada Zilla Panchayat", styles['Title']))
    elements.append(Paragraph("Swachh Bharat Mission (G) - MRF Report", styles['Heading2']))
    elements.append(Paragraph(f"Report Period: {start_date} to {end_date}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Summary Statistics
    total_weight = df['weight'].sum()
    summary_data = [
        ["Total Waste Processed", f"{total_weight:.2f} kg"],
        ["Number of Loads", str(len(df))],
        ["Avg Load Weight", f"{df['weight'].mean():.2f} kg"]
    ]
    
    # Add top material and destination
    top_material = df['material'].mode()[0] if not df['material'].mode().empty else "N/A"
    top_destination = df['destination'].mode()[0] if not df['destination'].mode().empty else "N/A"
    summary_data.extend([
        ["Top Material", top_material],
        ["Main Destination", top_destination]
    ])
    
    summary_table = Table(summary_data, colWidths=[200, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (1,0), (1,-1), 'RIGHT')
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 24))
    
    material_table = [["Material", "Weight (kg)", "Rate (₹/kg)", "Revenue (₹)"]]
    material_totals = df.groupby('material')['weight'].sum()
    
    total_revenue = 0
    for material, total in material_totals.items():
        rate = material_rates.get(material, 0)
        revenue = total * rate
        total_revenue += revenue
        material_table.append([
            material, 
            f"{total:.2f}",
            f"{rate}",
            f"₹{revenue:,.2f}"
        ])
    
    # Add total row
    material_table.append(["TOTAL", f"{total_weight:.2f}", "", f"₹{total_revenue:,.2f}"])
    
    mat_table = Table(material_table, colWidths=[120, 80, 80, 100])
    mat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgreen),
        ('FONTSIZE', (0,-1), (-1,-1), 12),
        ('BOLD', (0,-1), (-1,-1), True)
    ]))
    elements.append(Paragraph("Material Distribution & Revenue", styles['Heading3']))
    elements.append(mat_table)
    
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Destination Summary", styles['Heading3']))
    
    dest_table = [["Destination", "Waste (kg)", "% of Total"]]
    dest_totals = df.groupby('destination')['weight'].sum()
    
    for destination, total in dest_totals.items():
        dest_table.append([
            destination, 
            f"{total:.2f}",
            f"{(total / total_weight) * 100:.1f}%"
        ])
    
    dest_table.append(["TOTAL", f"{total_weight:.2f}", "100%"])
    
    dest_table_view = Table(dest_table, colWidths=[180, 80, 80])
    dest_table_view.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgreen)
    ]))
    elements.append(dest_table_view)
    
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                             styles['Italic']))
    
    doc.build(elements)
    
    return csv_filepath, pdf_filepath