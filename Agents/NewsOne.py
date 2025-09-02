import os
import re
import json
import requests
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image
# -----------------------------
# 2. Extract pages of PDF as a PIL image
# -----------------------------
def get_page_image(pdf_path, page_num):
    images = convert_from_path(
        pdf_path,
        first_page=page_num,
        last_page=page_num,
        # poppler_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\poppler\Library\bin"
    )
    if images:
        return images[0]
    return None

# -----------------------------
# 3. Run OCR using Gemini
# -----------------------------
def ocr_with_gemini(pil_image, query):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([query, pil_image])
    return response.text.strip()

# -----------------------------
# 4. Prompt builder for event details
# -----------------------------
def build_prompt(first_page_text):
    return f""" You are given News image extract .

Rules:
0. For the text field, it is critical to accurately represent any superscripts (e.g., ¹, ², ³, ™) or subscripts (e.g., ₁, ₂, ₃, ₘ).
1. category: The primary classification or section of the article, typically found at the very top (e.g., "RESEARCH").
2. title: The main headline of the article.
3. short_description: A brief, introductory summary or subtitle, usually located immediately below the title or date. It should capture the essence of the article in one or two sentences.
4. date: The publication or last updated date of the article. Please extract the exact string as it appears.
5. long_description: The complete body text of the article, excluding the category, title, short description, and date. Preserve all paragraphs and their original order, joining them into a single string.

JSON template:
{{
  "Category": " ",
  "title": " ",
  "short_description": " ",
  "date": " ",
  "long_description": " "
}}

First page text:
---
{first_page_text}
---

Now return ONLY valid JSON with the filled details.
"""

# -----------------------------
# 5. Main workflow function
# -----------------------------
def main(pdf_path: str, API_KEY: str, website_url: str):
    """Takes a PDF path, extracts news details, saves JSON & payload, 
    sends to API, and returns the API response (or None if failed)."""
    for i in range(1,11):
        genai.configure(api_key=API_KEY)

        # 1. Extract first page
        first_page_img = get_page_image(pdf_path, i+9)

        if not first_page_img:
            print("❌ Could not extract images from PDF.")
            return None

        # 2. OCR
        first_page_text = ocr_with_gemini(first_page_img, "Extract all the text exactly as shown from this page. For the text field, it is critical to accurately represent any superscripts (e.g., ¹, ², ³, ™) or subscripts (e.g., ₁, ₂, ₃, ₘ).")

        # 3. Build prompt
        prompt = build_prompt(first_page_text)

        # 4. Run Gemini for structured JSON
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([prompt])

        # 5. Save raw Gemini JSON
        output_json = r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\NewsOne.json"
        with open(output_json, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✅ Raw JSON saved to {output_json}")

        # 6. Clean JSON → dict
        clean_content = re.sub(r"^```[a-zA-Z]*\n", "", response.text.strip())
        clean_content = re.sub(r"\n```$", "", clean_content)
        event_data = json.loads(clean_content)

        # 7. Map → API payload
        description= event_data.get("long_description", "")
        paragraphs = description.split("\n\n")
        description_html = "".join(
            f"<p>{p_clean}</p>" for p in paragraphs if (p_clean := p.replace("\n", "<br><br>").strip())
        )
        payload = {
            "title": event_data.get("title", ""),
        # static field from your spec
            "topnews": 0,  # numeric flag
            "description": description_html,
            "shortdescription": event_data.get("short_description", ""),
            "categoryId": i,  # fixed category (or map dynamically if needed)
            "image": "",  # leave empty or attach later
            "previewImage": "",
            "publishdate": event_data.get("date", "")
        }

        output_payload = r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\NewsOne_payload.json"
        with open(output_payload, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"✅ Payload saved to {output_payload}")

        # 8. Send payload → API
        url = website_url.rstrip("/") + "/api/news"
        print(f"🌐 Sending to {url}")
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            print("✅ API call success")
            # return response
        except requests.exceptions.RequestException as e:
            print("❌ Request failed:", e)
            # return None

# -----------------------------
# CLI entry point
# -----------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract news details from PDF")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("API_KEY", help="API Key for Gemini")
    parser.add_argument("website_url", help="Website base URL")
    args = parser.parse_args()

    result = main(args.pdf_path, args.API_KEY, args.website_url)
