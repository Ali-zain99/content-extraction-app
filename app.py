import streamlit as st
import time
import json
import requests
import tempfile
import Agents.EventDetail as event_detail  # your eventdetail.py
import Agents.PageHome as page_home  # your pagehome.py
import Agents.KeyPoints as key_points  # your keypoints.py
import Agents.Statistics as statistics  # your statistics.py
import Agents.ExpertSpeakers as expert_speakers  # your expertspeakers.py
import Agents.PastAttendees as past_attendees  # your pastattendees.py
import Agents.Testimonials as testimonials  # your testimonials.py
import Agents.UpcomingEvents as upcoming_events  # your upcomingevents.py
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
            with st.spinner("⏳ Extracting event details..."):
                event_json = event_detail.main(temp_pdf_path,API_KEY,website_url)  # returns raw JSON text
            st.success("✅ Event Details Extraction complete!")
            with st.spinner("⏳ Extracting home_json..."):
                home_json= page_home.main(temp_pdf_path,API_KEY,website_url)  # returns raw JSON text
            st.success("✅ Homepage extraction complete!")
            with st.spinner("⏳ Extracting keypoints..."):
                keypoints_json = key_points.main(temp_pdf_path,API_KEY,website_url)  # returns raw JSON text
            st.success("✅ Key Topics extraction complete!")
            with st.spinner("⏳ Extracting statistics..."):
                statistics_json = statistics.main(temp_pdf_path,API_KEY,website_url)  # returns raw JSON text
            st.success("✅ Statistics extraction complete!")
            with st.spinner("⏳ Extracting expert_speakers..."):
                expert_speakers.main(temp_pdf_path,API_KEY,website_url)  # returns raw JSON text
            st.success("✅ Expert Speakers extraction complete!")
            with st.spinner("⏳ Extracting past_attendees..."):
              past_attendees.main(temp_pdf_path,API_KEY,website_url)
            st.success("✅ Past Attendees extraction complete!")
            with st.spinner("⏳ Extracting testimonials..."):
                testimonials.main(temp_pdf_path,API_KEY,website_url)
            st.success("✅ Testimonials extraction complete!")
            with st.spinner("⏳ Extracting upcoming_events..."):
                upcoming_events.main(temp_pdf_path,API_KEY,website_url)
            st.success("✅ Upcoming Events extraction complete!")
            end_time = time.time()
            elapsed_time = end_time - start_time
            st.snow()
            st.success(f"❄️ PDF processing completed in {elapsed_time:.2f} seconds!")




            
