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
You are given an image that contains multiple testimonials. Each testimonial consists of three elements:

1. The testimonial text (inside quotes).
2. The name of the person.
3. The company/organization name (immediately below the name).

Your task:
- Extract all testimonials in the exact order specified below.
- The order of extraction is strictly top-right first → then middle section → then bottom-left last.
- Do not shuffle, reorder, or skip any testimonial. Follow the sequence exactly as it appears by position.

Output format (JSON only):

{
  "testimonial": [
    { "name": "Attendee 1", "company": "Company 1", "text": "Testimonial text 1" },
    { "name": "Attendee 2", "company": "Company 2", "text": "Testimonial text 2" },
    { "name": "Attendee 3", "company": "Company 3", "text": "Testimonial text 3" },
    { "name": "Attendee 4", "company": "Company 4", "text": "Testimonial text 4" },
    { "name": "Attendee 5", "company": "Company 5", "text": "Testimonial text 5" },
    { "name": "Attendee 6", "company": "Company 6", "text": "Testimonial text 6" }
  ]
}

Important:
- Preserve the exact spelling, formatting, and wording of names and companies as shown in the image.
- Do not modify or normalize text.
- Ensure every testimonial is included in the correct order.
    """


# --------------------------
# Extract Page Image from PDF
# --------------------------
def get_page_image(pdf_path, page_num):
    images = convert_from_path(
        pdf_path,
        first_page=page_num,
        last_page=page_num
    )
    if images:
        return images[0]
    return None


# --------------------------
# Crop Region for Testimonials
# --------------------------
def crop_testimonials(img, crop_box, save_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\Testimonial.png"):
    cropped = img.crop(crop_box)
    cropped.save(save_path)
    print(f"📸 Cropped testimonial image saved at {os.path.abspath(save_path)}")
    return save_path


# --------------------------
# Extract JSON with Gemini
# --------------------------
def extract_testimonials(image_path, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")  # ✅ use stable model

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
def load_clean_json(raw_text, save_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\Testimonial.json"):
    raw_text = raw_text.strip()

    # Remove markdown fences
    if raw_text.startswith("```json"):
        raw_text = raw_text[len("```json"):].strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3].strip()

    # Ensure JSON keys are quoted
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
# Send Testimonials to API
# --------------------------
def send_to_api(data, api_url):
    count = 1
    for speaker in data.get("testimonial", []):
        url = f"{api_url}/{count}"

        payload = {
            "name": speaker.get("name", ""),
            "company": speaker.get("company", ""),
            "testimonial": speaker.get("text", ""),
            "title": speaker.get("title", "Lorem"),   # optional field
            "ishome": speaker.get("ishome", "1")
        }

        response = requests.post(url, json=payload)

        print(f"Sending: {payload}")
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:", response.json())
        except:
            print("Response Text:", response.text)
        print("-" * 50)

        count += 1


# --------------------------
# Main Function
# --------------------------
def main(pdf_path,API_KEY, website):
    page_num=2
    api_url=f"{website}/api/testimonials/update"
    # api_url="https://ai-demo.genetechz.com/api/testimonials/update"
    crop_box = (974, 13078, 4347, 17505)
    api_key = API_KEY
    # Step 1: Get page image
    img = get_page_image(pdf_path, page_num)
    if not img:
        raise FileNotFoundError("❌ Could not extract page image from PDF")

    # Step 2: Crop region
    cropped_path = crop_testimonials(img, crop_box)

    # Step 3: Extract testimonials with Gemini
    raw_text = extract_testimonials(cropped_path, api_key)

    # Step 4: Clean + Save JSON
    data = load_clean_json(raw_text)

    # Step 5: Send to API
    send_to_api(data, api_url)


# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract homepage section from PDF and send to API")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("API_KEY", help="API Key for Gemini")
    parser.add_argument("website_url", help="Website URL for the event")
    args = parser.parse_args()
    main(args.pdf_path, args.API_KEY, args.website_url)

