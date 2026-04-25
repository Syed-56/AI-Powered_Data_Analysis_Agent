from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io, base64, os
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Receives CSV, performs stats, and creates a multi-chart visual dashboard."""
    # Note: Ensure this matches the 'Binary Property' name in your n8n 'Send to Python' node
    if 'csv_file' not in request.files:
        return jsonify({"error": "No file uploaded. Check n8n field name."}), 400
    
    file = request.files['csv_file']
    
    try:
        df = pd.read_csv(file)
        
        analysis_results = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }

        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            analysis_results["numerical_summary"] = numeric_df.describe().to_dict()
            analysis_results["correlations"] = numeric_df.corr().to_dict()

        # --- GENERATE MULTI-CHART DASHBOARD ---
        plt.figure(figsize=(12, 14)) 
        
        if not numeric_df.empty:
            # Chart 1: Correlation Heatmap (Top)
            plt.subplot(2, 1, 1)
            sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
            plt.title("Automated Correlation Analysis", fontsize=16, fontweight='bold', pad=15)
            
            # Chart 2: Average Values Bar Chart (Bottom)
            plt.subplot(2, 1, 2)
            means = numeric_df.mean().sort_values(ascending=False)
            sns.barplot(x=means.values, y=means.index, palette="viridis")
            plt.title("Average Values by Metric", fontsize=16, fontweight='bold', pad=15)
            plt.xlabel("Mean Value")
            
            plt.tight_layout(pad=5.0) 
        else:
            plt.text(0.5, 0.5, "No numeric data available for charts", ha='center', fontsize=14)
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=150)
        img.seek(0)
        chart_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close()

        return jsonify({
            "status": "success",
            "stats": analysis_results,
            "chart_data": chart_base64
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """Formats Gemini text and charts into a professional executive report."""
    chart_path = "final_dashboard.png"
    data = request.json
    gemini_text = data.get('gemini_text', 'No summary provided.')
    chart_data = data.get('chart_data', '')
    
    # Fix encoding and strip common AI markdown artifacts
    gemini_text = gemini_text.encode('latin-1', 'replace').decode('latin-1')
    current_date = datetime.now().strftime("%B %d, %Y")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- BLUE BRANDED HEADER ---
    pdf.set_fill_color(37, 99, 235) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(0, 20, "  AI DATA ANALYST", ln=True, align='L', fill=True)
    
    # Sub-header Bar
    pdf.set_fill_color(241, 245, 249) 
    pdf.set_text_color(100, 116, 139)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, f"   BUSINESS INTELLIGENCE REPORT  |  GENERATED: {current_date.upper()}", ln=True, align='L', fill=True)
    pdf.ln(8)

    # --- BODY TEXT FORMATTING ---
    pdf.set_text_color(30, 41, 59) 
    lines = gemini_text.split('\n')
    
    for line in lines:
        # Remove stray backslashes that AI sometimes puts before symbols
        line = line.strip().replace('\\', '')
        if not line:
            pdf.ln(4)
            continue
            
        if line.startswith('---') or line == '--':
            continue
        
        # 1. SECTION HEADERS (# Header)
        if line.startswith('#'):
            pdf.ln(4)
            pdf.set_font("Arial", 'B', 15)
            pdf.set_text_color(37, 99, 235) 
            clean_h = line.replace('#', '').replace('*', '').strip()
            pdf.multi_cell(0, 8, txt=clean_h)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
            pdf.ln(2)
            pdf.set_text_color(30, 41, 59)
            
        # 2. NUMBERED SUB-HEADERS (e.g., 1. Marketing Trends)
        elif line[0].isdigit() and (line[1:3] == '. ' or line[2:4] == '. '):
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 7, txt=line.replace('*', '').strip())
            pdf.set_text_color(30, 41, 59)

        # 3. BULLET POINTS
        elif line.startswith('*') or line.startswith('-') or line.startswith('•'):
            pdf.set_font("Arial", '', 11)
            pdf.set_x(20) # Indent
            clean_b = line.replace('*', '').replace('-', '').replace('•', '').strip()
            pdf.multi_cell(0, 6, txt=chr(149) + " " + clean_b)
            pdf.set_x(10) # Reset indent
            
        # 4. NORMAL PARAGRAPHS
        else:
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 6, txt=line.replace('*', ''))

    # --- DASHBOARD PAGE ---
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
            
            # Place the dashboard image
            pdf.image(chart_path, x=15, w=180)
        except Exception as e:
            print(f"Error embedding dashboard: {e}")
        
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str):
        pdf_output = pdf_output.encode('latin-1', errors='replace')
    
    pdf_b64 = base64.b64encode(pdf_output).decode('utf-8')
    if os.path.exists(chart_path): os.remove(chart_path)

    return jsonify({"pdf_data": pdf_b64})

if __name__ == '__main__':
    # debug=True allows the server to auto-reload when you save changes
    app.run(host='0.0.0.0', port=5000, debug=True)