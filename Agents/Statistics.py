import os
import re
import json
import requests
from pdf2image import convert_from_path
from PIL import Image
import google.generativeai as genai


# --------------------------
# Prompt Builder
# --------------------------
def build_prompt():
    return """
As a data extraction task, meticulously examine the provided image (original and cropped segments). 
The objective is to precisely identify the count or value associated with the following specific metrics displayed within the visual:
- Total Industry Topics
- Number of Networking Events
- Quantity of Leading Experts
- Number of Q&A Sessions

Return only a valid JSON object in this format:
{
  "Total Industry Topics": "50+",
  "Number of Networking Events": "30+",
  "Quantity of Leading Experts": "100+",
  "Number of Q&A Sessions": "25+"
}
Do not include explanations, markdown, or text outside JSON.
    """


# --------------------------
# Image Resizing
# --------------------------
def resize_image(pil_image, max_size=2000):
    """Resize image to max_size while keeping aspect ratio. Save for inspection."""
    width, height = pil_image.size
    if max(width, height) > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)

    # pil_image.save(save_path)
    # print(f"📸 Resized image saved at {os.path.abspath(save_path)} ({pil_image.size[0]}x{pil_image.size[1]})")
    return pil_image


# --------------------------
# OCR with Gemini
# --------------------------
def ocr_with_gemini(pil_image):
    model = genai.GenerativeModel("gemma-3-4b-it")
    query = build_prompt()

    safe_img = resize_image(pil_image)
    response = model.generate_content([query, safe_img])
    return response.text


# --------------------------
# PDF to Image
# --------------------------
def get_page_image(pdf_path, page_num, poppler_path=None):
    images = convert_from_path(
        pdf_path,
        first_page=page_num,
        last_page=page_num,
        poppler_path=poppler_path
    )
    if images:
        return images[0]
    return None


# --------------------------
# JSON Loader with Cleaning
# --------------------------
def load_clean_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read().strip()

    # Strip Markdown fences if present
    raw_text = re.sub(r"^```[a-zA-Z]*\n", "", raw_text)
    raw_text = re.sub(r"\n```$", "", raw_text)

    # Ensure keys are quoted
    raw_text = re.sub(r"(\w+):", r'"\1":', raw_text)

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        debug_path = file_path.replace(".json", "_raw.txt")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(raw_text)
        raise ValueError(f"❌ Invalid JSON. Raw content saved to {debug_path}")


# --------------------------
# Transform JSON into Payload
# --------------------------
def transform_to_payload(data):
    payload = []
    for key, value in data.items():
        val_str = str(value)
        figure = val_str.replace("+", "")
        isplus = "yes" if "+" in val_str else "no"

        payload.append({
            "figure": figure,
            "caption": key.upper(),
            "isplus": isplus
        })
    return payload


# --------------------------
# Send to API
# --------------------------
def send_to_api(payload, base_url):
    for i, item in enumerate(payload, start=1):
        url = f"{base_url}{i}"
        print(f"Sending to {url}")
        response = requests.post(url, json=item)

        print(f"Request to {url}")
        print("Payload:", item)
        print("Status Code:", response.status_code)
        try:
            print("Response:", response.json())
        except:
            print("Response Text:", response.text)
        print("-" * 50)


# --------------------------
# Main Pipeline
# --------------------------
def main(pdf_path,API_KEY,website_url):
    poppler_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\poppler-24.08.0\Library\bin"
    # Configure Gemini API
    genai.configure(api_key=API_KEY)

    # Extract page image
    page_img = get_page_image(pdf_path, 2, poppler_path)
    if not page_img:
        print("❌ Could not extract page image")
        return

    # OCR with Gemini
    first_page_text = ocr_with_gemini(page_img)

    # Save raw output
    json_path = r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\Statistics.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(first_page_text)
    print(f"✅ Raw JSON saved to {json_path}")

    # Load & clean JSON
    data = load_clean_json(json_path)

    # Transform to payload
    payload = transform_to_payload(data)

    # Save transformed payload
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"✅ Updated payload saved to {json_path}")

    # Send to API
    base_url=website_url + "/api/statistics/update/"
    # base_url = "https://ai-demo.genetechz.com/api/statistics/update/"
    send_to_api(payload, base_url)


# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract homepage section from PDF and send to API")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("API_KEY", help="API Key for authentication")
    parser.add_argument("website_url", help="Website URL for context")
    args = parser.parse_args()

    result = main(args.pdf_path,args.API_KEY,args.website_url)
    if result:
        print("Response:", result)
