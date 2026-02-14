import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def get_dashboard_data(db_path):
    conn = sqlite3.connect(db_path)
    
    # Today's waste
    today = datetime.now().strftime("%Y-%m-%d")
    df_today = pd.read_sql_query(f"SELECT material, SUM(weight) as total FROM waste_records WHERE date = '{today}' GROUP BY material", conn)
    
    # Weekly trend
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30) # Show 30 days by default
    df_weekly = pd.read_sql_query(f"SELECT date, SUM(weight) as total FROM waste_records WHERE date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}' GROUP BY date", conn)
    
    # Material distribution
    df_materials = pd.read_sql_query("SELECT material, SUM(weight) as total FROM waste_records GROUP BY material", conn)
    
    # Destination summary
    df_destinations = pd.read_sql_query("SELECT destination, SUM(weight) as total FROM waste_records GROUP BY destination", conn)
    
    conn.close()
    
    # Revenue calculation
    material_rates = {"PET": 28, "HDPE": 28, "Paper": 11, "Glass": 2, "MLP": -4, "Rubber": -4}

    df_materials['revenue'] = df_materials.apply(lambda x: x['total'] * material_rates.get(x['material'], 0), axis=1)
    
    total_revenue = df_materials['revenue'].sum()
    
    return {
        "df_today": df_today,
        "df_weekly": df_weekly,
        "df_materials": df_materials,
        "df_destinations": df_destinations,
        "kpis": {
            "total_waste": df_materials['total'].sum() if not df_materials.empty else 0,
            "total_revenue": total_revenue,
            "avg_daily": df_weekly['total'].mean() if not df_weekly.empty else 0,
            "today_loads": len(df_today) if not df_today.empty else 0 # Approximate based on material types for now
        }
    }