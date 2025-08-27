import json
import requests
from PyPDF2 import PdfReader
import os

# ---------------------------------------
# 1. Extract topics from PDF
# ---------------------------------------
def extract_key_topics(pdf_path: str, start: int = 19, end: int = 30):
    """Extract key topics (Title + Description) from AcroForm fields"""
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()

    text_fields = {}
    for name, data in fields.items():
        if name.startswith("Text"):
            try:
                num = int("".join(filter(str.isdigit, name)))
                text_fields[num] = data.get("/V")
            except ValueError:
                pass  # skip non-numeric suffix

    results = []
    for i in range(start, end + 1):
        value = text_fields.get(i, None)
        if i % 2 == 1:  # odd -> Title
            current_item = {"title": value, "description": None}
            results.append(current_item)
        else:  # even -> Description
            if results:
                results[-1]["description"] = value

    return {"key_topics": results}

# ---------------------------------------
# 2. Save to JSON
# ---------------------------------------
def save_json(data, filename=r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\output.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved results to {filename}")
    return filename

# ---------------------------------------
# 3. Send updates to API
# ---------------------------------------
def send_to_api(payload, website_url):
    base_url=website_url + "/api/key-topics/update"
    # base_url="https://ai-demo.genetechz.com/api/key-topics/update"
    headers = {"Content-Type": "application/json"}
    for i, topic in enumerate(payload["key_topics"], start=1):
        url = f"{base_url}/{i}"
        print(f"Sending to {url}")
        try:
            response = requests.post(url, json=topic, headers=headers, timeout=20)
            print(f"➡️ Updating ID {i}")
            print("   Title:", topic.get("title"))
            print("   Status:", response.status_code)
            try:
                print("   Response:", response.json())
            except:
                print("   Response:", response.text)
            print("-" * 50)
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to update ID {i}: {e}")

# ---------------------------------------
# 4. Main
# ---------------------------------------
def main(pdf_path: str, API_KEY: str, website_url: str):
    print(f"📄 Extracting key topics from: {pdf_path}")
    data = extract_key_topics(pdf_path)
    output_file = save_json(data)
    # Send to API
    send_to_api(data,website_url)   

# ---------------------------------------
# CLI Entry Point
# ---------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract Key Topics from PDF and send to API")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("API_KEY", help="API Key for authentication")
    parser.add_argument("website_url", help="Website URL for context")
    args = parser.parse_args()

    main(args.pdf_path, args.API_KEY, args.website_url)
