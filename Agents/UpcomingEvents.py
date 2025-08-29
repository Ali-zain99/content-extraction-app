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
You are an expert in extracting structured data from images. 

Task: Analyze the provided image, which shows a section of upcoming events displayed as cards. Extract all event cards and return the results strictly in JSON format.  

Each event must be represented as an object with these exact keys:
- "eventname": Full event name (e.g., "Direct Lithium Extraction USA 2025"). Donot use abrrevation.
- "eventlocation": Format "City, State, Country". If incomplete, use what is available.
- "eventlink": Hyperlink/URL if visible, otherwise null.
- "eventdate": Format "Month DD - DD, YYYY". Do not use ordinal indicators like "1st" or "2nd". Example: "December 1 - 2, 2025".
- "image": Image filename/path if visible, otherwise null.
- "hoverimage": Hover image filename/path if visible, otherwise null.

Output Format:
Return ONLY valid JSON. Do not include markdown, explanations, or any extra text.  
The JSON must follow this structure exactly:

{
  "upcomingEvent": [
    {
      "eventname": "",
      "eventlocation": "",
      "eventlink": null,
      "eventdate": "",
      "image": null,
      "hoverimage": null
    },
    {
      "eventname": "",
      "eventlocation": "",
      "eventlink": null,
      "eventdate": "",
      "image": null,
      "hoverimage": null
    }
  ]
}

Important Rules:
- Ensure JSON is valid and properly formatted.
- Do not wrap JSON in triple backticks or markdown.
- Use null (not "None") when a value is unavailable.
- Maintain the order of events from left to right.
    """


# --------------------------
# Extract Page Image from PDF
# --------------------------
def get_page_image(pdf_path, page_num):
    images = convert_from_path(
        pdf_path,
        first_page=page_num,
        last_page=page_num,
        
    )
    if images:
        return images[0]
    return None


# --------------------------
# Crop Region for Testimonials
# --------------------------
def crop_testimonials(img, crop_box, save_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\UpcomingEvents.png"):
    cropped = img.crop(crop_box)
    cropped.save(save_path)
    print(f"📸 Cropped testimonial image saved at {os.path.abspath(save_path)}")
    return save_path


# --------------------------
# Extract JSON with Gemini
# --------------------------
def extract_testimonials(image_path, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")  # ✅ use stable model

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
def load_clean_json(raw_text, save_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\UpcomingEvents.json"):
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
def send_to_api(data, api_url, start_index=1):
    count = start_index
    for event in data["upcomingEvent"]:  # event is each dict inside the list
        url = f"{api_url}/{count}"

        # Normalize date field if it contains "OR"

        payload = {
            "eventname": event["eventname"],
            "eventlocation": event["eventlocation"],
            "eventlink": event["eventlink"],
            "eventdate": event["eventdate"],
            "image": event["image"],
            "hoverimage": event["hoverimage"]
        }

        response = requests.post(url, json=payload)

        print(f"➡️ Sending to: {url}")
        print(f"Payload: {payload}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print("-" * 50)

        count += 1



# --------------------------
# Main Function
# --------------------------
def main(pdf_path,API_KEY,website_url):
    page_num=2
    api_url=website_url+"/api/upcoming-events/update"
    # api_url="https://ai-demo.genetechz.com/api/upcoming-events/update"
    crop_box = (955, 20260, 4413, 21854)
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
    parser.add_argument("API_KEY", help="API Key for authentication")
    parser.add_argument("website_url", help="Website URL for reference")
    args = parser.parse_args()
    main(args.pdf_path, args.API_KEY, args.website_url)

