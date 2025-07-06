# 📦 CBP ACE ADCVD Streamlit Extraction App

This Streamlit app automates the extraction of key fields like Product Name, Country, Exporter, Case Number, and more from the [CBP ACE ADCVD Public Search Portal](https://trade.cbp.dhs.gov/ace/adcvd/adcvd-public/#) using `Message_ID`s from an Excel file.

---

## ✅ Features

- Upload Excel file with `Message_ID` column
- Automates scraping using Selenium
- Extracts:
  - Category
  - Effective Date
  - Message Title & Body
  - Product Name (via regex + NLP)
  - Country (via spaCy)
  - Exporter, Producer, Case Number, Cash Rate (via regex)
- Preview extracted data in-app
- Download results as an Excel file

---

## 📁 Input Format

Your input Excel file should have a column like this:

| Message_ID |
|------------|
| 2115402    |
| 2110403    |
| 2104441    |

---

## 💻 Run Locally

### 1. Clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/cbp-ace-streamlit-app.git
cd cbp-ace-streamlit-app

2. Install dependencies
pip install -r requirements.txt

3. Run the app
streamlit run app.py

📦 Technologies Used
🐍 Python 3

🧠 spaCy (NLP)

🔍 Selenium WebDriver

📊 Streamlit

🧾 Regex

📄 Excel + Pandas

