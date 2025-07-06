import streamlit as st
import pandas as pd
import re
import spacy
import time
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Product name extractor
def extract_product_name(text):
    text = re.sub(r"\s+", " ", text.strip())
    lowered_text = text.lower()
    last_from_index = lowered_text.rfind(" from ")
    if last_from_index == -1:
        return None
    pre_from_chunk = text[:last_from_index]
    keyword_match = re.search(r"(.*)\b(for|of|on)\b\s+(.*)$", pre_from_chunk, re.IGNORECASE)
    if keyword_match:
        return keyword_match.group(3).strip(" ,.")
    return None

# Country extractor
def extract_country(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "GPE":
            return re.sub(r"^the\s+", "", ent.text, flags=re.IGNORECASE)
    return None

# Core extractor using Selenium
def process_message_ids(df):
    driver = webdriver.Chrome()
    driver.get("https://trade.cbp.dhs.gov/ace/adcvd/adcvd-public/#")
    wait = WebDriverWait(driver, 20)
    all_data = []

    def extract_field(label):
        try:
            xpath = f"//table[@id='detailsMessageHeaderTables']//th[contains(normalize-space(), '{label}')]/following-sibling::td"
            return wait.until(EC.presence_of_element_located((By.XPATH, xpath))).text
        except TimeoutException:
            return "Not found"

    def extract_body():
        try:
            return wait.until(EC.presence_of_element_located((By.XPATH, "//textarea[@id='msg-text-body']"))).get_attribute("value")
        except TimeoutException:
            return "Not found"

    pattern = re.compile(
        r"Exporter:\s*(?P<Exporter>.*?)\s*"
        r"(?:Producer:\s*(?P<Producer>.*?)\s*)?"
        r"Case number:\s*(?P<CaseNumber>A-\d{3}-\d{3}-\d{3})\s*"
        r"Cash deposit rate:\s*(?P<CashRate>\d+(\.\d+)?%)",
        re.DOTALL
    )

    for msg_id in df["Message_ID"]:
        try:
            search_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Message #/Case #']")))
            search_input.clear()
            search_input.send_keys(str(msg_id))

            search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Search']")))
            search_btn.click()

            time.sleep(5)

            category = extract_field("Category")
            effective_date = extract_field("Effective Date")
            message_title = extract_field("Message Title")
            message_body = extract_body()

            country = extract_country(message_title)
            product_name = extract_product_name(message_title)

            for match in pattern.finditer(message_body):
                all_data.append({
                    "Message_ID": msg_id,
                    "Exporter": match.group("Exporter").strip(),
                    "Producer": match.group("Producer").strip() if match.group("Producer") else "Not mentioned",
                    "Case number": match.group("CaseNumber").strip(),
                    "Cash deposit rate": match.group("CashRate").strip(),
                    "Product Name": product_name,
                    "Country": country,
                    "Category": category,
                    "Effective Date": effective_date
                })
        except Exception as e:
            all_data.append({
                "Message_ID": msg_id,
                "Error": str(e)
            })

    driver.quit()
    return pd.DataFrame(all_data)

# Streamlit frontend
st.set_page_config(page_title="CBP ACE Extractor", layout="wide")
st.title("📦 CBP ACE ADCVD Message Extractor")

uploaded_file = st.file_uploader("Upload Excel with Message_ID column", type=["xlsx"])

if uploaded_file:
    df_input = pd.read_excel(uploaded_file)
    st.write("Uploaded File Preview:")
    st.dataframe(df_input)

    if st.button("🔍 Extract Data"):
        with st.spinner("Processing... This may take some time."):
            result_df = process_message_ids(df_input)

        st.success("✅ Extraction Complete")
        st.dataframe(result_df)

        # Prepare for download
        output = BytesIO()
        result_df.to_excel(output, index=False)
        output.seek(0)

        st.download_button("⬇️ Download Excel", data=output, file_name="extracted_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")