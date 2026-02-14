import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
import sqlite3
from datetime import datetime, timedelta

from dashboard import get_dashboard_data
from report_generator import init_db, load_sample_data, import_csv_data, generate_reports

st.set_page_config(page_title="DK ZP - MRF Digital Suite", page_icon="♻️", layout="wide")
DB_PATH = "mrf_data.db"
REPORT_FOLDER = "reports"

if not os.path.exists(REPORT_FOLDER):
    os.makedirs(REPORT_FOLDER)
init_db(DB_PATH)

st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1a3a6c; font-weight: 700;}
    .sub-header {font-size: 1.5rem; color: #2e7d32;}
    .metric-card {background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32;}
    .welcome-container {
        background-color: #e8f5e9; 
        padding: 40px; 
        border-radius: 15px; 
        text-align: center; 
        border: 2px dashed #2e7d32;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966486.png", width=50) # Placeholder icon
    st.title("MRF Operator")
    st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
    
    page = st.radio("Navigation", ["Dashboard", "Data Management", "Reports"])
    
    st.divider()
    st.info("Dakshina Kannada Zilla Panchayat")

if page == "Dashboard":
    st.markdown('<div class="main-header">♻️ MRF Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Load Data
    data = get_dashboard_data(DB_PATH)
    kpis = data['kpis']
    
    if kpis['total_waste'] == 0:
        st.markdown("""
        <div class="welcome-container">
            <h2>👋 Welcome to the MRF Digital Suite!</h2>
            <p style="font-size: 1.1rem; color: #555;">
                It looks like your database is empty. To see the dashboard in action, 
                you can generate realistic sample data instantly.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.write("")
            if st.button("🚀 Load Sample Data (100 Records)", use_container_width=True, type="primary"):
                with st.spinner("Generating sample records..."):
                    load_sample_data(DB_PATH)
                    time.sleep(1)
                    st.rerun()
            st.caption("Or go to the 'Data Management' tab to upload your own CSV.")

    else:
        
        # KPI Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Waste Processed", f"{kpis['total_waste']:.2f} kg")
        col2.metric("Revenue Potential", f"₹{kpis['total_revenue']:,.2f}")
        col3.metric("Avg Daily Waste", f"{kpis['avg_daily']:.2f} kg")
        col4.metric("Today's Batches", kpis['today_loads'])
        
        st.markdown("---")
        

        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("Weekly Waste Trend")
            if not data['df_weekly'].empty:
                fig_trend = px.line(data['df_weekly'], x='date', y='total', markers=True, 
                                    line_shape='spline', template='plotly_white')
                fig_trend.update_traces(line_color='#1a3a6c', line_width=3)
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.warning("No data available for trend.")

        with col_right:
            st.subheader("Material Composition")
            if not data['df_materials'].empty:
                fig_mat = px.pie(data['df_materials'], values='total', names='material', hole=0.4)
                st.plotly_chart(fig_mat, use_container_width=True)
            else:
                st.warning("No data.")

        col_l, col_r = st.columns(2)
        
        with col_l:
            st.subheader("Destination Breakdown")
            if not data['df_destinations'].empty:
                fig_dest = px.pie(data['df_destinations'], values='total', names='destination')
                st.plotly_chart(fig_dest, use_container_width=True)
                
        with col_r:
            st.subheader("Revenue by Material")
            if not data['df_materials'].empty:
                fig_rev = px.bar(data['df_materials'], x='revenue', y='material', orientation='h',
                                 text_auto='.2s', color='revenue', color_continuous_scale='Greens')
                st.plotly_chart(fig_rev, use_container_width=True)

elif page == "Data Management":
    st.markdown('<div class="main-header">📂 Data Import & Export</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Import Data", "System Actions"])
    
    with tab1:
        st.write("Upload CSV files containing waste records.")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            # Save temporarily
            temp_path = os.path.join("uploads", "temp_import.csv")
            if not os.path.exists("uploads"): os.makedirs("uploads")
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if st.button("Process Import"):
                with st.spinner("Importing data..."):
                    try:
                        import_csv_data(DB_PATH, temp_path)
                        st.success("Data imported successfully!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error importing data: {e}")
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Sample Data")
            if st.button("Load Mock Data (100 records)"):
                load_sample_data(DB_PATH)
                st.success("Sample data loaded!")
                st.rerun()
                
        with col2:
            st.subheader("Export Database")
            conn = sqlite3.connect(DB_PATH)
            df_export = pd.read_sql_query("SELECT * FROM waste_records", conn)
            conn.close()
            
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download All Data (CSV)",
                csv,
                "mrf_full_export.csv",
                "text/csv",
                key='download-csv'
            )

elif page == "Reports":
    st.markdown('<div class="main-header">📄 Report Generation</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
        
    if st.button("Generate Report"):
        with st.spinner("Generating PDF & CSV reports..."):
            csv_path, pdf_path = generate_reports(DB_PATH, str(start_date), str(end_date), REPORT_FOLDER)
            
            if csv_path and pdf_path:
                st.success("Reports ready!")
                
                c1, c2 = st.columns(2)
                with c1:
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button("Download PDF Report", pdf_file, os.path.basename(pdf_path), "application/pdf")
                with c2:
                    with open(csv_path, "rb") as csv_file:
                        st.download_button("Download CSV Data", csv_file, os.path.basename(csv_path), "text/csv")
            else:
                st.warning("No data found for the selected date range.")