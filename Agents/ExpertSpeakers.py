import io
import os
import re
import json
import requests
from PIL import Image
from pdf2image import convert_from_path
import google.generativeai as genai


# --------------------------
# Prompt Builder
# --------------------------
def build_prompt():
    return """
As a data extraction task, meticulously examine the provided image.  
The objective is to precisely identify the value associated with the Expert Speakers within the visual:
- Speaker name 
- Company name

There are total 3 expert speakers and their company names.  
Write a proper name if there is any typo in the image.  

Output only valid JSON in this format:

{
  "expert_speakers": [
    {
      "name": "",
      "company": ""
    },
    {
      "name": "",
      "company": ""
    },
    {
      "name": "",
      "company": ""
    }
  ]
}
    """


# --------------------------
# Extract page image from PDF
# --------------------------
def get_page_image(pdf_path, page_num):
    images = convert_from_path(
        pdf_path,
        first_page=page_num,
        last_page=page_num,
    )
    if images:
        return images[0]  # Return PIL.Image.Image object
    return None


# --------------------------
# Crop region for speakers
# --------------------------
def crop_speakers(img, crop_box, save_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\crop_image.png"):
    cropped = img.crop(crop_box)
    cropped.save(save_path)
    print(f"📸 Cropped image saved at {os.path.abspath(save_path)}")
    return save_path


# --------------------------
# Extract JSON with Gemini
# --------------------------
def extract_speakers(image_path, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    with Image.open(image_path) as img:
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

    query = build_prompt()
    response = model.generate_content([
        {
            "mime_type": "image/png",
            "data": img_bytes.read()
        },
        query
    ])

    return response.text


# --------------------------
# Clean & Load JSON
# --------------------------
def load_clean_json(raw_text, save_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\Expert_Speaker.json"):
    raw_text = raw_text.strip()

    # Remove markdown fences
    if raw_text.startswith("```json"):
        raw_text = raw_text[len("```json"):].strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3].strip()

    # Ensure JSON keys quoted
    raw_text = re.sub(r"(\w+):", r'"\1":', raw_text)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        debug_file = save_path.replace(".json", "_raw.txt")
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(raw_text)
        raise ValueError(f"❌ Invalid JSON. Raw response saved to {debug_file}")

    # Save cleaned JSON
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON saved to {save_path}")
    return data


# --------------------------
# Send to API
# --------------------------
def send_to_api(data, api_url):
    count=20
    for speaker in data.get("expert_speakers", []):
        url = api_url
        payload = {
            "name": speaker.get("name", ""),
            "company": speaker.get("company", "")
        }
        url = f"{url}/{count}"
        print(url)
        count+=1
        response = requests.post(url, json=payload)

        print(f"Sending: {payload}")
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:", response.json())
        except:
            print("Response Text:", response.text)
        print("-" * 50)


# --------------------------
# Main Function
# --------------------------
def main(pdf_path, API_KEY, website_url):
    crop_box = (886, 11100, 3250, 12347)
    api_key = API_KEY
    api_url = f"{website_url}/api/expert-speakers/update"
    # api_url = "https://ai-demo.genetechz.com/api/expert-speakers/update"  # Replace

    # Step 1: Get page image
    img = get_page_image(pdf_path, 2)
    if not img:
        raise FileNotFoundError("❌ Could not extract page image from PDF")

    # Step 2: Crop region
    cropped_path = crop_speakers(img, crop_box, save_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\crop_image.png")

    # Step 3: Extract speakers with Gemini
    raw_text = extract_speakers(cropped_path, api_key)

    # Step 4: Clean + Save JSON
    data = load_clean_json(raw_text, save_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\Expert_Speaker.json")

    # Step 5: Send to API
    send_to_api(data, api_url)


# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    PAGE_NUM = 2
    CROP_BOX = (886, 11100, 3250, 12347)  # left, top, right, bottom
    API_KEY = "AIzaSyDDoos-ITDh0hl694HB2um_iqdu36jREAw"
    import argparse
    parser = argparse.ArgumentParser(description="Extract homepage section from PDF and send to API")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("API_KEY", help="API Key for Gemini")
    parser.add_argument("website_url", help="Website URL for API endpoint")
    args = parser.parse_args()
    main(args.pdf_path, args.API_KEY, args.website_url)
