from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io, base64, os
from fpdf import FPDF
import re
from datetime import datetime

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. Catch the file from n8n
    if 'csv_file' not in request.files:
        return jsonify({"error": "No file uploaded. Check n8n field name."}), 400
    
    file = request.files['csv_file']
    
    try:
        # 2. Read the CSV (Generic: handles any column names)
        df = pd.read_csv(file)
        
        # 3. AUTOMATED ANALYSIS
        # Get basic metadata
        analysis_results = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }

        # Numeric Analysis (Generic: finds all number columns)
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            analysis_results["numerical_summary"] = numeric_df.describe().to_dict()
            analysis_results["correlations"] = numeric_df.corr().to_dict()

        # Categorical Analysis (Generic: finds all text columns)
        categorical_cols = df.select_dtypes(include=['object']).columns
        cat_summary = {}
        for col in categorical_cols:
            # We take the top 5 most common values for each category to keep JSON small
            cat_summary[col] = df[col].value_counts().head(5).to_dict()
        analysis_results["categorical_summary"] = cat_summary

        # 4. CHART GENERATION (Correlation Heatmap)
        plt.figure(figsize=(10, 8))
        if not numeric_df.empty:
            sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt=".2f")
            plt.title("Automated Correlation Analysis")
        else:
            plt.text(0.5, 0.5, "No numeric data for chart", ha='center')
        
        # Convert Plot to Base64 String for n8n
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        chart_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close()

        # 5. Return the full package
        return jsonify({
            "status": "success",
            "stats": analysis_results,
            "chart_data": chart_base64
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    chart_path = "final_chart.png"
    # 1. Get data from n8n (text from Gemini, chart from Python Node 1)
    data = request.json
    print(f"DEBUG: Data received from n8n: {data}")
    gemini_text = data.get('gemini_text', 'No summary provided.')
    chart_base64 = data.get('chart_data', '')
    gemini_text = gemini_text.encode("ascii", "ignore").decode("ascii")
    clean_text = re.sub(r'[#*_-]', '', gemini_text)
    clean_text = clean_text.replace('\n\n\n', '\n\n')
    current_date = datetime.now().strftime("%B %d, %Y")

    # 2. Initialize PDF
    pdf = FPDF()
    pdf.add_page()
    
    # 3. Add Header
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Report Date: {current_date}", ln=True, align='R')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Final AI Business Intelligence Report", ln=True, align='C')
    pdf.ln(10)

    # 4. Add Gemini's Analysis (The "Brain")
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Executive Summary & Insights:", ln=True)
    pdf.set_font("Arial", size=11)
    # Multi_cell handles long text and wraps it to the next line
    pdf.multi_cell(0, 8, txt=clean_text)
    
    pdf.ln(10)

    # 5. Add the Chart (The "Visuals")
    if chart_base64:
        try:
            img_data = base64.b64decode(chart_base64)
            with open(chart_path, "wb") as f:
                f.write(img_data)
            pdf.image(chart_path, x=10, w=180)
        except Exception as e:
            print(f"Image error: {e}")
        
    # 6. Convert PDF to Base64 to send back to n8n
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str):
        pdf_output = pdf_output.encode('latin-1', errors='replace')
    pdf_b64 = base64.b64encode(pdf_output).decode('utf-8')

    # Cleanup temp image file
    if os.path.exists(chart_path): os.remove(chart_path)

    return jsonify({"pdf_data": pdf_b64})

if __name__ == '__main__':
    # host 0.0.0.0 is critical for Docker connection
    app.run(host='0.0.0.0', port=5000, debug=True)