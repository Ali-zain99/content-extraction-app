import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")  # make sure .env has GEMINI_API_KEY

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")

# 2. Configure Gemini API
genai.configure(api_key=api_key.strip())

# 3. Build prompt for Panel Discussion speaker extraction
def build_panel_prompt():
    return """
You are given the content of a PDF document.

Your task:
- Focus ONLY on the "Panel Discussion" session.
- Extract every speaker's full name and their company/organization.
- If the company is missing, leave it as an empty string "".
- Do not include any other sessions.
- Return the result strictly in valid JSON format.

The JSON format must follow this structure:
[
  {
    "speaker #01 name": "John Doe",
    "speaker #01 company": "ABC Energy"
  },
  {
    "speaker #02 name": "Jane Smith",
    "speaker #02 company": "XYZ Geothermal"
  }
]
"""

# 4. Main script
if __name__ == "__main__":
    # Path to your PDF
    pdf_path = r"C:\Users\ali.zain\Desktop\Content_Extraction\THZ25 (H) Final Agenda 250225.pdf"

    print("📄 Sending PDF to Gemini for panel discussion extraction...")
    model = genai.GenerativeModel("gemini-2.0-flash")

    # Build prompt
    prompt = build_panel_prompt()

    # Open PDF and send as input
    with open(pdf_path, "rb") as f:
        response = model.generate_content(
            [prompt, {"mime_type": "application/pdf", "data": f.read()}]
        )

    # Parse and save JSON safely
    try:
        # Remove markdown fences if present
        cleaned_text = re.sub(r"^```(?:json)?|```$", "", response.text.strip(), flags=re.MULTILINE).strip()
        speakers_json = json.loads(cleaned_text)
    except json.JSONDecodeError:
        print("⚠️ Model response was not valid JSON. Saving raw response.")
        speakers_json = {"raw_response": response.text}

    output_file = "panel_discussion_speakers.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(speakers_json, f, indent=2, ensure_ascii=False)

    print(f"✅ Speaker data saved to {output_file}")
