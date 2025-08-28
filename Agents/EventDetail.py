import os
import re
import json
import requests
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image

# -----------------------------
# 1. Configure Gemini API
# -----------------------------

# -----------------------------
# 2. Extract pages of PDF as a PIL image
# -----------------------------
def get_page_image(pdf_path, page_num):
    images = convert_from_path(
        pdf_path,
        first_page=page_num,
        last_page=page_num
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
def build_prompt(first_page_text, industry_name):
    return f""" You are given text from the first page of a PDF (event details) and an extracted "Industry Name".

Rules:
1. "Event name" – Use the event name , after removing first word and last word year.
2. "Event code" – Use the event code exactly as shown.
3. "Event Tagline" – Use the full event name except year .
3. "Event Dates" – Format as "Month, Date1 - Date2, YYYY".
4. "Event Location" – Full location (City, State/Region, Country).
5. "Event year" – 4-digit year from the event date.
6. "Event Currency" – Based on country (USA →  USD, Canada → CAD, Eurozone → EUR).
7. "Event Short Dates" – Format as "Month(In short form), Date1 - Date2, YYYY".
8. "Event Short Location" – Abbreviated form of Event Location contain only state (remove city and country if present, keep state short form).
9. "Event Color Name" – first word of the event name.
10. "Event City Shortcode" – First three letters of the city in uppercase.
11. "Event Postponed" – False unless stated otherwise.
12. Add an extra field called "Industry Name" – value is "{industry_name}".
13. "Previous Agenda" – True unless stated otherwise.
14. "Hubspot Disposition" – Format: disposition_<EventCode in lowercase>_<EventYear>
15. "Hubspot Email Status" – Format: email_status_<EventCode in lowercase>_<EventYear>
16. "Custom Currency Symbol" – leave it blank.
17. "Currency Position" – Always "Top left".


JSON template:
{{
  "Event name": "",  
  "Event code": "",  
  "Event Tagline": "",
  "Event Dates": "",  
  "Event Location": "",  
  "Event year": "",  
  "Event Currency": "", 
  "Event Short Dates": "", 
  "Event Short Location": "", 
  "Event Color Name": "", 
  "Event City Shortcode": "",  
  "Event Postponed": false,  
  "Industry Name": "",
  "Previous Agenda": false,  
  "Hubspot Disposition": "",  
  "Hubspot Email Status": "",  
  "Custom Currency Symbol": "",
  "Currency Position": "Top left"
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
    """Takes a PDF path, extracts event details, saves JSON & payload, 
    sends to API, and returns the API response (or None if failed)."""
    genai.configure(api_key=API_KEY)

    # 1. Extract pages
    first_page_img = get_page_image(pdf_path, 1)
    industry_page_img = get_page_image(pdf_path, 20)

    if not first_page_img or not industry_page_img:
        print("❌ Could not extract images from PDF.")
        return None

    # 2. OCR
    first_page_text = ocr_with_gemini(first_page_img, "Extract all the text exactly as shown from this page.")
    industry_name = ocr_with_gemini(industry_page_img, "From the provided form image, identify the industry option that is marked or checked. Return only the industry name (e.g., 'Clean Energy').")

    # 3. Build prompt
    prompt = build_prompt(first_page_text, industry_name)

    # 4. Run Gemini
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([prompt])

    # 5. Save raw Gemini JSON
    output_json = r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\EventDetail.json"
    with open(output_json, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"✅ JSON saved to {output_json}")

    # 6. Clean JSON → dict
    clean_content = re.sub(r"^```[a-zA-Z]*\n", "", response.text.strip())
    clean_content = re.sub(r"\n```$", "", clean_content)
    event_data = json.loads(clean_content)

    # 7. Map → payload
    mapping = [
        ("Event name", "event_name", "Event Name"),
        ("Event code", "event_code", "Event Code"),
        ("Event Tagline", "event_tagline", "Event Tagline"),
        ("Event Dates", "event_dates", "Event Dates"),
        ("Event Location", "event_Location", "Event Location"),
        ("Event year", "event_year", "Event Year"),
        ("Event Currency", "event_currency", "Event Currency"),
        ("Event Short Dates", "event_short_date", "Event Short Date"),
        ("Event Short Location", "event_short_location", "Event Short Location"),
        ("Event Color Name", "event_color_name", "Event Color Name"),
        ("Event City Shortcode", "event_city_shortcode", "Event City Shortcode"),
        ("Event Postponed", "event_postponed", "Event Postponed"),
        ("Industry Name", "industry_name", "Industry Name"),
        ("Previous Agenda", "previous_agenda", "Previous Agenda"),
        ("Hubspot Disposition", "hubspot_disposition", "Hubspot Disposition"),
        ("Hubspot Email Status", "hubspot_email_status", "Hubspot Email Status"),
        ("Custom Currency Symbol", "custom_currency_symbol", "Custom Currency Symbol"),
        ("Currency Position", "currency_postion", "Currency Postion"),
    ]

    payload = {"options": []}
    for idx, (json_key, option, label) in enumerate(mapping, start=1):
        value = event_data.get(json_key, None)
        if isinstance(value, bool):
            value = str(value).lower()
        payload["options"].append({
            "id": idx,
            "option": option,
            "value": value,
            "label": label
        })

    output_payload = r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\EventDetail_payload.json"
    with open(output_payload, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"✅ Payload saved to {output_payload}")

    # 8. Send payload → API
    url=website_url+"/api/event-details"
    # url = "https://ai-demo.genetechz.com/api/event-details"
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        print("✅ API call success")
        return response
    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", e)
        return None

# -----------------------------
# CLI entry point
# -----------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract event details from PDF")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("API_KEY", help="API Key for authentication")
    parser.add_argument("website_url", help="Website URL for reference")
    args = parser.parse_args()

    result = main(args.pdf_path, args.API_KEY, args.website_url)
