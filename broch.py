import streamlit as st
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from googlesearch import search
import unicodedata


# Step 1: Get URLs from Google Search
def get_company_urls(company_name, num_results=5):
    query = f"{company_name} official site"
    return list(search(query, num_results=num_results))


# Step 2: Scrape content from each URL
def scrape_website_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        return "\n".join(paragraphs)
    except Exception:
        return ""


# Step 3: Sanitize text
def sanitize_text(text):
    return unicodedata.normalize("NFKD", text).encode("latin-1", "ignore").decode("latin-1")


# Step 4: Generate brochure with Ollama LLM
def generate_brochure_with_llm(company_name, raw_content, model="mistral"):
    prompt = f"""
You are a professional brochure writer.

Based on the following scraped content for the company "{company_name}", write a detailed 5-page brochure.

Scraped content:
\"\"\"
{raw_content}
\"\"\"

Brochure format:
Page 1: Introduction and Vision
Page 2: Services and Products
Page 3: Company Culture and Work Environment
Page 4: Client Success Stories
Page 5: Careers and Contact

Make it professional and structured with headings.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )

    result = response.json()
    return result.get("response", "No response generated.")


# Step 5: Create PDF
def create_pdf(company_name, brochure_text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    sections = brochure_text.split("Page")[1:]
    for section in sections:
        pdf.add_page()
        lines = section.strip().split("\n", 1)
        title = f"Page {lines[0].strip()}"
        body = lines[1] if len(lines) > 1 else ""
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, txt=sanitize_text(title), ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        for para in body.split("\n"):
            pdf.multi_cell(0, 10, sanitize_text(para.strip()))

    filename = f"{company_name.replace(' ', '_')}_Brochure.pdf"
    pdf.output(filename)
    return filename


# --- Streamlit UI ---
st.set_page_config(page_title="📘 Web-Scraped LLM Brochure Generator", layout="centered")
st.title("📘 AI Brochure Generator (LLM + Web Scraping)")

company_name = st.text_input("Enter a company name")

if st.button("Generate Brochure"):
    if not company_name.strip():
        st.warning("Enter a valid company name.")
    else:
        with st.spinner("🔍 Scraping and generating brochure..."):
            try:
                urls = get_company_urls(company_name)
                scraped_data = [scrape_website_text(url) for url in urls]
                full_text = "\n".join(scraped_data)[:15000]
                brochure_text = generate_brochure_with_llm(company_name, full_text)
                pdf_path = create_pdf(company_name, brochure_text)
                st.success("✅ Brochure created!")

                with open(pdf_path, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name=pdf_path, mime="application/pdf")

            except Exception as e:
                st.error(f"❌ Error: {e}")
