# CBP ACE ADCVD Streamlit Automation App 🚀

This Streamlit web app allows users to extract message-level details like Category, Product Name, Exporter, Case Number, etc., from the CBP ACE ADCVD Public Search Portal using just Message_IDs from an Excel file.

## ✅ Features
- Upload Excel with Message_IDs
- Automate data scraping using Selenium
- Extract key fields using spaCy + regex
- Preview and download results in Excel

## 📦 Setup Locally

1. Clone this repo or download it
2. Create a virtual environment and install dependencies:
   ```bash
pip install -r requirements.txt
streamlit run app.py
