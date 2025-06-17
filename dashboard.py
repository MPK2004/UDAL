import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def get_dashboard_data(db_path):
    conn = sqlite3.connect(db_path)
    
    # Today's waste
    today = datetime.now().strftime("%Y-%m-%d")
    df_today = pd.read_sql_query(f"""
        SELECT material, SUM(weight) as total 
        FROM waste_records 
        WHERE date = '{today}' 
        GROUP BY material
    """, conn)
    
    # Weekly trend
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    df_weekly = pd.read_sql_query(f"""
        SELECT date, SUM(weight) as total 
        FROM waste_records 
        WHERE date BETWEEN '{start_date.strftime("%Y-%m-%d")}' AND '{end_date.strftime("%Y-%m-%d")}'
        GROUP BY date
    """, conn)
    
    # Material distribution
    df_materials = pd.read_sql_query("""
        SELECT material, SUM(weight) as total 
        FROM waste_records 
        GROUP BY material
    """, conn)
    
    # Destination summary
    df_destinations = pd.read_sql_query("""
        SELECT destination, SUM(weight) as total 
        FROM waste_records 
        GROUP BY destination
    """, conn)
    
    conn.close()
    
    # Revenue calculation
    material_rates = {
        "PET": 28, "HDPE": 28, "Paper": 11, "Glass": 2, 
        "MLP": -4, "Rubber": -4
    }
    revenue = sum(row['total'] * material_rates.get(row['material'], 0) 
                 for _, row in df_materials.iterrows())
    
    return {
        "today": {
            "date": today,
            "materials": df_today.to_dict('records'),
            "total": df_today['total'].sum()
        },
        "weekly": {
            "labels": df_weekly['date'].tolist(),
            "data": df_weekly['total'].tolist()
        },
        "materials": {
            "labels": df_materials['material'].tolist(),
            "data": df_materials['total'].tolist()
        },
        "destinations": {
            "labels": df_destinations['destination'].tolist(),
            "data": df_destinations['total'].tolist()
        },
        "kpis": {
            "total_waste": df_materials['total'].sum(),
            "total_revenue": revenue,
            "avg_daily": df_weekly['total'].mean() if not df_weekly.empty else 0
        }
    }