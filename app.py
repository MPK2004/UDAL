from flask import Flask, render_template, send_file, jsonify, request, redirect, url_for
from report_generator import generate_reports, init_db, load_sample_data, import_csv_data
from dashboard import get_dashboard_data
import os
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import uuid

app = Flask(__name__)
DB_PATH = os.path.expanduser("~/mrf_data.db")
UPLOAD_FOLDER = 'uploads'
REPORT_FOLDER = 'reports'
STATIC_FOLDER = 'static'

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# Initialize database on startup
init_db(DB_PATH)

@app.route('/')
def dashboard():
    current_date = datetime.now().strftime("%A, %d %B %Y")
    return render_template('dashboard.html', current_date=current_date)

@app.route('/dashboard-data')
def dashboard_data():
    return jsonify(get_dashboard_data(DB_PATH))

@app.route('/generate-report')
def generate_report():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    csv_file, pdf_file = generate_reports(DB_PATH, start_date, end_date, REPORT_FOLDER)
    return jsonify({
        "csv": csv_file,
        "pdf": pdf_file
    })

@app.route('/view-report/<filename>')
def view_report(filename):
    return send_file(os.path.join(REPORT_FOLDER, filename), as_attachment=True)

@app.route('/load-sample-data')
def load_sample():
    load_sample_data(DB_PATH)
    return jsonify({"status": "Sample data loaded"})

@app.route('/import-data', methods=['POST'])
def import_data():
    if 'csv_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.csv'):
        filename = f"{uuid.uuid4()}.csv"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            import_csv_data(DB_PATH, filepath)
            return jsonify({"status": "Data imported successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type"}), 400

@app.route('/export-data')
def export_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM waste_records", conn)
    conn.close()
    
    filename = f"mrf_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    filepath = os.path.join(REPORT_FOLDER, filename)
    df.to_csv(filepath, index=False)
    
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)