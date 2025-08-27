import os
import json
import requests
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image

# -----------------------------
# 1. Configure Gemini API
# -----------------------------
genai.configure(api_key="AIzaSyDDoos-ITDh0hl694HB2um_iqdu36jREAw")

# -----------------------------
# 2. Prompt builder
# -----------------------------
def build_prompt():
    return """
You are an expert information extraction AI. Given the OCR text of a webpage, 
identify and extract the heading and descriptive text associated with the section featuring a video element. 
The heading and descriptive text are presented near the following lines:
Event Logo
EVENT DETAILS SPEAKERS
SPONSORS VENUE MEDIA CONTACT US
REGISTER
and a video element.

Return the extracted heading and description in JSON format, where the keys are 'heading' and 'description', 
and the values are the corresponding text strings from the document. 
Ensure the 'description' value includes all text intended to describe the video section, presented 
in a concise and readable manner with original linebreaks.

json format:
{
"heading": "Extracted Heading Text",
"description": "Extracted descriptive text with linebreaks preserved."
}

If a video section cannot be confidently identified, return an empty JSON object.
"""

# -----------------------------
# 3. Utils
# -----------------------------
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
    return pil_image

def get_page_image(pdf_path, page_num):
    """Extract a single page as image from PDF"""
    images = convert_from_path(
        pdf_path,
        first_page=page_num,
        last_page=page_num,
        poppler_path=r"C:\Users\ali.zain\Desktop\Content_Extraction\poppler-24.08.0\Library\bin"
    )
    return images[0] if images else None

def ocr_with_gemini(pil_image):
    """Run OCR + structured extraction"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    query = build_prompt()
    safe_img = resize_image(pil_image)
    response = model.generate_content([query, safe_img])
    return response.text.strip()

# -----------------------------
# 4. Main workflow
# -----------------------------
def main(pdf_path: str,API_KEY: str, website_url: str):
    """Extract homepage section, save JSON, build payload, send to API"""
    # 1. Extract page
    page_img = get_page_image(pdf_path, 2)
    if not page_img:
        print("❌ Could not extract page image.")
        return None

    # 2. Run OCR with Gemini
    extracted_json = ocr_with_gemini(page_img)
    print("Extracted JSON:\n", extracted_json)

    # 3. Save raw Gemini JSON
    json_file = r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\Page_home.json"
    with open(json_file, "w", encoding="utf-8") as f:
        f.write(extracted_json)
    print(f"✅ JSON saved to {json_file}")

    # 4. Clean JSON fences
    raw_text = extracted_json.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()
    data = json.loads(raw_text)
    print(data)

    heading = data.get("heading", "")
    description = data.get("description", "")

    # 5. Build description HTML
    paragraphs = description.split("\n\n")
    description_html = "".join(
        f"<p>{p_clean}</p>" for p in paragraphs if (p_clean := p.replace("\n", "<br>").strip())
    )

    # Example video embed
    video_html = '<figure class="media"><oembed url="https://player.vimeo.com/video/236701630"></oembed></figure>'

    # 6. Build payload
    payload = {
        "options": [
            {"id": 1, "option": "heading", "value": heading, "label": "Heading"},
            {"id": 2, "option": "paragraph", "value": description_html, "label": "Paragraph"},
            {"id": 3, "option": "Video", "value": video_html, "label": "Video Link"}
        ]
    }
    payload_file = r"C:\Users\ali.zain\Desktop\Content_Extraction\Files\Page_home_payload.json"
    with open(payload_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"✅ Payload saved to {payload_file}")

    # 7. Send payload → API
    url = "https://ai-demo.genetechz.com/api/home-page"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        print("✅ API call success")
        return response
    except requests.exceptions.RequestException as e:
        print("❌ API call failed:", e)
        return None

# -----------------------------
# CLI entry point
# -----------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract homepage section from PDF and send to API")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("API_KEY",help="API Key for authentication")
    parser.add_argument("website_url", help="Website URL for reference")
    parser.add_argument("--page", type=int, default=2, help="Page number to process (default=2)")
    args = parser.parse_args()

    result = main(args.pdf_path,args.API_KEY,args.website_url)
    if result:
        print("Response:", result)
