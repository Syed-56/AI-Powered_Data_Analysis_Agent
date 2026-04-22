# 🤖 AI-Powered Data Analysis Agent
> Automated Statistical Insights & Business Intelligence

An end-to-end AI agent that automates the entire data analysis pipeline — from raw data ingestion to natural-language business reporting. No manual steps. No deep technical expertise required.

> **Course:** Artificial Intelligence | FAST-NUCES, Karachi | 2026

---

## 👥 Team

| Name | Roll No |
|------|---------|
| Syed Sultan Ahmed | 24K-0585 |
| Hassaan Nasir | 24K-1031 |
| Asad Khan | 24K-0580 |

---

## 📌 Overview

The agent accepts **CSV files or Google Sheets** as input, performs rigorous statistical analysis using Python, and leverages **Google Gemini** to convert numeric output into concise, actionable executive summaries. The full pipeline is orchestrated by **n8n**, eliminating manual intervention at every stage.

**Target users:** Business analysts, students, researchers, and SMEs who need fast, repeatable data insights without deep technical expertise.

---

## 🔍 Problem Being Solved

- Manual data analysis is time-consuming and error-prone for non-technical stakeholders
- Existing BI tools (Power BI, Tableau) require licensing costs and significant setup time
- Translating statistical numbers into plain-language decisions requires domain expertise that isn't always available
- Recurring reports (daily/weekly) lack automation in most small-to-medium setups

---

## ✨ Features

- **Fully automated pipeline** — data upload to final report with zero manual steps
- **Statistical analysis** — descriptive stats, outlier detection, correlation matrix, distribution summary
- **LLM summarization** — Gemini converts raw stats into executive-level business narratives
- **Familiar output channels** — Google Sheets and email (no new tools for end users)
- **Scheduled runs** — cron-triggered workflows for recurring weekly/monthly reporting
- **Optional chart generation** — Matplotlib histograms and heatmaps encoded as base64

---

## 🛠️ Tech Stack

| Layer | Tool / Technology | Purpose |
|-------|-------------------|---------|
| Orchestration | n8n (self-hosted) | Visual workflow automation; connects all components |
| Analysis Engine | Python 3 + Flask | REST API exposing statistical computations via `/analyze` |
| Data Libraries | Pandas, SciPy, NumPy | Descriptive stats, correlation, outlier detection |
| LLM | Google Gemini 1.5 Flash | Translates statistics into business summaries |
| Data Sources | CSV / Google Sheets | Flexible input — file uploads and live sheet ingestion |
| Visualization | Matplotlib (optional) | Chart generation encoded as base64 |
| Output Channels | Gmail, Google Sheets | Automated delivery via n8n output nodes |
| Version Control | Git / GitHub | Source management and collaboration |

---

## 🔄 System Workflow

```
Trigger (webhook / cron / Sheets update)
        ↓
Data Ingestion (CSV file or Google Sheets API)
        ↓
Statistical Analysis (POST /analyze → Flask returns JSON stats)
        ↓
Prompt Construction (inject stats + metadata into Gemini template)
        ↓
LLM Summarization (Gemini returns structured business summary)
        ↓
Output Delivery (Google Sheets write-back OR email digest)
```

---

## 🧠 AI Methodology

### Statistical Analysis Layer (Python/Flask)

The `/analyze` endpoint computes:

- **Descriptive statistics** — mean, median, std deviation, quartiles (Q1/Q3), min, max for all numeric columns
- **Missing value audit** — percentage of nulls per column, flagging columns above a threshold
- **Outlier detection** — IQR-based method to identify anomalous data points
- **Correlation matrix** — Pearson correlation between all numeric feature pairs
- **Distribution summary** — skewness and kurtosis per column to characterize data shape

### LLM Business Summarization (Gemini API)

The structured JSON from the Python service is passed to Gemini with a prompt engineered to act as a **senior business analyst**, producing a narrative covering: key trends, notable anomalies, risk indicators, and top-3 actionable recommendations.

### Orchestration Layer (n8n)

n8n handles data routing, HTTP communication between services, conditional branching (e.g., skip chart generation for small datasets), and output delivery — all visually, without deep coding effort.

---

## ⚙️ System Constraints

- Dataset must contain at least one numeric column for analysis to proceed
- Files exceeding **50 MB** are rejected at ingestion with an error notification
- Gemini prompt is always prefixed with: *"respond only with structured analysis, no filler text"*
- All HTTP nodes apply a **retry policy of 3 attempts with exponential backoff**
- If the Python service is unreachable, a fallback notification is sent via email

---

## 🗓️ Implementation Timeline

| Phase | Deliverable |
|-------|-------------|
| Phase 1 | Python Flask API & statistical engine (Pandas, SciPy) — CSV & Sheets input |
| Phase 2 | n8n workflow setup — trigger nodes, HTTP calls to Python, data routing |
| Phase 3 | Gemini API integration with prompt engineering for business-grade summaries |
| Phase 4 | Output pipeline — Google Sheets write-back, email delivery, error handling |
| Phase 5 | End-to-end testing, edge case handling, documentation & demo preparation |

---

---

## 📁 Project Structure

```
ai-data-analysis-agent/
├── app.py                  # Flask entry point
├── analyzer.py             # Statistical analysis logic
├── requirements.txt        # Python dependencies
├── n8n_workflow.json       # Exported n8n workflow
├── prompts/
│   └── gemini_prompt.txt   # Gemini system prompt template
└── README.md
```

---

## 📚 References

- [n8n Documentation](https://docs.n8n.io)
- [Google Gemini API Docs](https://ai.google.dev/docs)
