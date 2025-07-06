import re
import time
import pandas as pd
import spacy
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display
import streamlit as st

# Start virtual display for headless Chrome
display = Display(visible=0, size=(1024, 768))
display.start()

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Define Streamlit UI
st.title("📦 CBP ACE ADCVD Message Extractor")
uploaded_file = st.file_uploader("Upload Excel file with Message_ID column", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    results = []

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://trade.cbp.dhs.gov/ace/adcvd/adcvd-public/#")
    wait = WebDriverWait(driver, 20)

    def extract_field(label):
        try:
            xpath = f"//table[@id='detailsMessageHeaderTables']//th[contains(normalize-space(), '{label}')]/following-sibling::td"
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            return element.text
        except TimeoutException:
            return "Not found"

    def extract_message_body():
        try:
            body_element = wait.until(EC.presence_of_element_located((By.XPATH, "//textarea[@id='msg-text-body']")))
            return body_element.get_attribute("value")
        except TimeoutException:
            return "Not found"

    def extract_country(text):
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "GPE":
                return re.sub(r"^the\s+", "", ent.text, flags=re.IGNORECASE)
        return None

    def extract_product_between_last_from_and_nearest_keyword(text):
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

    for message_number in df["Message_ID"]:
        try:
            input_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Message #/Case #']")))
            input_box.clear()
            input_box.send_keys(str(message_number))

            search_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Search']")))
            search_button.click()

            time.sleep(5)

            category = extract_field("Category")
            effective_date = extract_field("Effective Date")
            message_title = extract_field("Message Title")
            message_body = extract_message_body()

            country = extract_country(message_title)
            product = extract_product_between_last_from_and_nearest_keyword(message_title)

            pattern = re.compile(
                r"Exporter:\s*(?P<Exporter>.*?)\s*"
                r"(?:Producer:\s*(?P<Producer>.*?)\s*)?"
                r"Case number:\s*(?P<CaseNumber>A-\d{3}-\d{3}-\d{3})\s*"
                r"Cash deposit rate:\s*(?P<CashRate>\d+(\.\d+)?%)",
                re.DOTALL
            )
            matches = pattern.finditer(message_body)
            for match in matches:
                results.append({
                    "Message_ID": message_number,
                    "Exporter": match.group("Exporter").strip(),
                    "Producer": match.group("Producer").strip() if match.group("Producer") else "Not mentioned",
                    "Case number": match.group("CaseNumber").strip(),
                    "Cash deposit rate": match.group("CashRate").strip(),
                    "Product Name": product,
                    "Country": country,
                    "Category": category,
                    "Effective Date": effective_date
                })
        except Exception as e:
            st.warning(f"Error processing message {message_number}: {e}")

    driver.quit()

    if results:
        final_df = pd.DataFrame(results)
        st.subheader("✅ Extracted Data Preview")
        st.dataframe(final_df)

        # Download button
        output = BytesIO()
        final_df.to_excel(output, index=False)
        st.download_button("📥 Download Excel", output.getvalue(), file_name="cbp_extracted_data.xlsx")
    else:
        st.warning("No results extracted.")
