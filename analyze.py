from flask import Flask, request, jsonify
from flask_cors import CORS          # <-- added: allows browser to POST from local HTML file
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io, base64, os
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)
CORS(app)   # <-- added: permits cross-origin requests from the browser


#  ROUTE 1 — Receive CSV from n8n, run statistics, return JSON
@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Receives a CSV file from n8n (field name: csv_file),
    performs statistical analysis, generates charts,
    and returns JSON with stats + base64-encoded chart image.
    """
    if 'csv_file' not in request.files:
        return jsonify({
            "error": "No file found. Make sure the n8n 'Send to Python via Flask' node "
                     "uses Binary Property name 'csv_file'."
        }), 400

    file = request.files['csv_file']

    try:
        df = pd.read_csv(file)

        #  Core statistics 
        analysis_results = {
            "total_rows":    len(df),
            "total_columns": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "column_types":   {col: str(dtype) for col, dtype in df.dtypes.items()}
        }

        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            analysis_results["numerical_summary"] = numeric_df.describe().to_dict()
            analysis_results["correlations"]       = numeric_df.corr().to_dict()

        #  Generate multi-chart dashboard 
        plt.figure(figsize=(12, 14))

        if not numeric_df.empty:
            # Chart 1: Correlation Heatmap
            plt.subplot(2, 1, 1)
            sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm',
                        fmt=".2f", linewidths=0.5)
            plt.title("Automated Correlation Analysis",
                       fontsize=16, fontweight='bold', pad=15)

            # Chart 2: Average Values Bar Chart
            plt.subplot(2, 1, 2)
            means = numeric_df.mean().sort_values(ascending=False)
            sns.barplot(x=means.values, y=means.index, palette="viridis")
            plt.title("Average Values by Metric",
                       fontsize=16, fontweight='bold', pad=15)
            plt.xlabel("Mean Value")

            plt.tight_layout(pad=5.0)
        else:
            plt.text(0.5, 0.5, "No numeric data available for charts",
                     ha='center', fontsize=14)

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=150)
        img.seek(0)
        chart_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close()

        return jsonify({
            "status":     "success",
            "stats":      analysis_results,
            "chart_data": chart_base64
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


#  ROUTE 2 — Receive Gemini text + chart, return base64 PDF
@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """
    Receives:
      - gemini_text  : string — Gemini's business report
      - chart_data   : string — base64-encoded PNG dashboard

    Returns JSON:
      - pdf_data     : string — base64-encoded PDF
    """
    chart_path = "final_dashboard.png"
    data = request.json or {}

    gemini_text = data.get('gemini_text', 'No summary provided.')
    chart_data  = data.get('chart_data', '')

    # Sanitize encoding and strip stray markdown artefacts
    gemini_text  = gemini_text.encode('latin-1', 'replace').decode('latin-1')
    current_date = datetime.now().strftime("%B %d, %Y")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Blue branded header 
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(0, 20, "  AI DATA ANALYST", ln=True, align='L', fill=True)

    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(100, 116, 139)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10,
             f"   BUSINESS INTELLIGENCE REPORT  |  GENERATED: {current_date.upper()}",
             ln=True, align='L', fill=True)
    pdf.ln(8)

    # Body text 
    pdf.set_text_color(30, 41, 59)
    lines = gemini_text.split('\n')

    for line in lines:
        line = line.strip().replace('\\', '')
        if not line:
            pdf.ln(4)
            continue
        if line.startswith('---') or line == '--':
            continue

        # Section headers  (# Header)
        if line.startswith('#'):
            pdf.ln(4)
            pdf.set_font("Arial", 'B', 15)
            pdf.set_text_color(37, 99, 235)
            pdf.multi_cell(0, 8, txt=line.replace('#', '').replace('*', '').strip())
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
            pdf.ln(2)
            pdf.set_text_color(30, 41, 59)

        # Numbered sub-headers  (1. Title)
        elif len(line) > 2 and line[0].isdigit() and line[1:3] in ('. ', ') '):
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 7, txt=line.replace('*', '').strip())
            pdf.set_text_color(30, 41, 59)

        # Bullet points
        elif line.startswith(('*', '-', '•')):
            pdf.set_font("Arial", '', 11)
            pdf.set_x(20)
            clean_b = line.lstrip('*-• ').strip()
            pdf.multi_cell(0, 6, txt=chr(149) + " " + clean_b)
            pdf.set_x(10)

        # Normal paragraphs
        else:
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 6, txt=line.replace('*', ''))

    #  Dashboard page 
    if chart_data:
        try:
            img_bytes = base64.b64decode(chart_data)
            with open(chart_path, "wb") as f:
                f.write(img_bytes)

            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.set_text_color(37, 99, 235)
            pdf.cell(0, 12, "Visual Data Dashboard", ln=True, align='L')
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
            pdf.ln(10)
            pdf.image(chart_path, x=15, w=180)
        except Exception as e:
            print(f"Error embedding dashboard: {e}")

    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str):
        pdf_output = pdf_output.encode('latin-1', errors='replace')

    pdf_b64 = base64.b64encode(pdf_output).decode('utf-8')
    if os.path.exists(chart_path):
        os.remove(chart_path)

    return jsonify({"pdf_data": pdf_b64})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
