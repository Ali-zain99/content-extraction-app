import streamlit as st
import time
import tempfile

# Import agents
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

# Streamlit setup
st.set_page_config(page_title="Event Detail Extractor", layout="wide")
st.title("📄 Event Detail Extraction & Chatbot App")

# Upload PDF + inputs
uploaded_pdf = st.file_uploader("Upload a PDF file", type=["pdf"])
API_KEY = st.text_input("Enter your API Key", type="password")
website_url = st.text_input("Enter your Website URL", placeholder="https://example.com")

# Agent list
agents = {
    "News Category": news_category,
    "News One": news_one,
    "Event Details": event_detail,
    "Homepage": page_home,
    "Key Points": key_points,
    "Statistics": statistics,
    "Expert Speakers": expert_speakers,
    "Past Attendees": past_attendees,
    "Testimonials": testimonials,
    "Upcoming Events": upcoming_events,
}

# Selection controls
st.subheader("⚙️ Select Agents to Run")
select_all = st.checkbox("Select All")

selected_agents = []
for agent_name in agents.keys():
    if select_all:
        checked = True
    else:
        checked = st.checkbox(agent_name)
    if checked:
        selected_agents.append(agent_name)

# Run selected agents
if uploaded_pdf is not None and st.button("🔍 Process PDF with Selected Agents"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_pdf.read())
        temp_pdf_path = tmp_file.name

    st.info(f"Running {len(selected_agents)} agent(s)...")

    results = {}
    start_time = time.time()

    for agent_name in selected_agents:
        with st.spinner(f"⏳ Extracting {agent_name}..."):
            try:
                result = agents[agent_name].main(temp_pdf_path, API_KEY, website_url)
                results[agent_name] = result
                st.success(f"✅ {agent_name} extraction complete!")
            except Exception as e:
                st.error(f"⚠️ Error in {agent_name}: {str(e)}")

    end_time = time.time()
    st.snow()
    st.success(f"❄️ PDF processing completed in {end_time - start_time:.2f} seconds!")

    # Store results in session for chatbots
    st.session_state["agent_results"] = results

# Chatbot Section
if "agent_results" in st.session_state and st.session_state["agent_results"]:
    st.subheader("💬 Chat with Agents")
    agent_choice = st.selectbox("Choose an agent to chat with", list(st.session_state["agent_results"].keys()))
    user_input = st.text_input("Ask a question to the selected agent:")

   
