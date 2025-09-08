import streamlit as st
import time
import json
import requests
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import Agents.EventDetail as event_detail
import Agents.PageHome as page_home
import Agents.KeyPoints as key_points
import Agents.Statistics as statistics
import Agents.ExpertSpeakers as expert_speakers
import Agents.PastAttendees as past_attendees
import Agents.Testimonials as testimonials
import Agents.UpcomingEvents as upcoming_events
import Agents.NewsOne as news_one
import Agents.NewsCategory as news_category


st.set_page_config(page_title="Event Detail Extractor", layout="wide")
st.title("📄 Event Detail Extraction App")

# Upload PDF
uploaded_pdf = st.file_uploader("Upload a PDF file", type=["pdf"])
API_KEY = st.text_input("Enter your API Key", type="password")
website_url = st.text_input("Enter your Website URL", placeholder="https://example.com")

if uploaded_pdf is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_pdf.read())
        temp_pdf_path = tmp_file.name

    if st.button("🔍 Process PDF"):
        start_time = time.time()

        # Define tasks
        tasks = {
            "news_category": lambda: news_category.main(temp_pdf_path, API_KEY, website_url),
            "news_one": lambda: news_one.main(temp_pdf_path, API_KEY, website_url),
            "event_detail": lambda: event_detail.main(temp_pdf_path, API_KEY, website_url),
            "home_json": lambda: page_home.main(temp_pdf_path, API_KEY, website_url),
            "keypoints": lambda: key_points.main(temp_pdf_path, API_KEY, website_url),
            "statistics": lambda: statistics.main(temp_pdf_path, API_KEY, website_url),
            "expert_speakers": lambda: expert_speakers.main(temp_pdf_path, API_KEY, website_url),
            "past_attendees": lambda: past_attendees.main(temp_pdf_path, API_KEY, website_url),
            "testimonials": lambda: testimonials.main(temp_pdf_path, API_KEY, website_url),
            "upcoming_events": lambda: upcoming_events.main(temp_pdf_path, API_KEY, website_url),
        }

        results = {}

        # Run tasks in parallel
        with st.spinner("⏳ Extracting all sections in parallel..."):
            with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
                future_to_task = {executor.submit(func): name for name, func in tasks.items()}

                for future in as_completed(future_to_task):
                    task_name = future_to_task[future]
                    try:
                        results[task_name] = future.result()
                        st.success(f"✅ {task_name.replace('_', ' ').title()} extraction complete!")
                    except Exception as e:
                        st.error(f"❌ {task_name.replace('_', ' ').title()} failed: {e}")

        # Show final result
        end_time = time.time()
        elapsed_time = end_time - start_time
        st.snow()
        st.success(f"❄️ PDF processing completed in {elapsed_time:.2f} seconds!")
