import streamlit as st
from gradio_client import Client, handle_file
# Custom CSS for better aesthetics
st.markdown(
    """
    <style>
    /* Gradient button for regular Streamlit buttons */
    .stButton button {
        background: linear-gradient(90deg, #2563EB, #9333EA);
        color: white !important;
        border-radius: 6px;
        border: none;
    }
    .stButton button:hover {
        background: linear-gradient(90deg, #1D4ED8, #7E22CE);
        color: white !important;
    }

    /* Gradient style for the file upload button */
    input[type="file"]::file-selector-button {
        background: linear-gradient(90deg, #2563EB, #9333EA);
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        cursor: pointer;
        transition: background 0.3s ease;
    }
    input[type="file"]::file-selector-button:hover {
        background: linear-gradient(90deg, #1D4ED8, #7E22CE);
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Connect to the Hugging Face Space once
client = Client("girishwangikar/ResumeATS")

st.title("Smart ATS")
st.text("Improve Your Resume ATS")

# -----------------------
# Upload Resume + JD
# -----------------------
st.header("📄 ATS Resume Analyzer")

jd = st.text_area("Paste the Job Description")
uploaded_file = st.file_uploader("Upload Your Resume", type="pdf", help="Please upload a PDF resume")

analyze_button = st.button("Analyze Resume")
cover_letter_button = st.button("Generate Cover Letter")

# We’ll store parsed resume in session_state so both buttons can use it
if "parsed_resume" not in st.session_state:
    st.session_state.parsed_resume = None

# ---------- Analyze Resume ----------
if analyze_button:
    if uploaded_file is not None and jd.strip():
        # Save uploaded file to a temp file
        with open("temp_resume.pdf", "wb") as f:
            f.write(uploaded_file.read())

        # Parse resume
        parsed_resume = client.predict(
            file=handle_file("temp_resume.pdf"),
            api_name="/process_resume"
        )
        st.session_state.parsed_resume = parsed_resume  # save for later use

        

        # Analyze resume with job description
        analysis = client.predict(
            resume_text=parsed_resume,
            job_description=jd,
            with_job_description=True,
            temperature=0.5,
            max_tokens=1024,
            api_name="/analyze_resume"
        )
        st.subheader("Analysis Result:")
        st.write(analysis)
    else:
        st.warning("Please upload a resume and paste a Job Description before analyzing.")

# ---------- Generate Cover Letter ----------
if cover_letter_button:
    if st.session_state.parsed_resume is not None and jd.strip():
        cover_letter = client.predict(
            resume_text=st.session_state.parsed_resume,
            job_description=jd,
            temperature=0.5,
            max_tokens=1024,
            api_name="/generate_cover_letter"
        )
        st.subheader("Generated Cover Letter:")
        st.write(cover_letter)
    else:
        st.warning("Please first analyze the resume (or upload JD) before generating cover letter.")
# -----------------------
# Section 2: Rephrase Text
# -----------------------
st.header("✍️ Rephrase Any Text")

text_to_rephrase = st.text_area("Enter text to rephrase:")
temp = st.slider("Temperature", 0.0, 1.0, 0.5)
tokens = st.number_input("Max tokens", min_value=1, max_value=2048, value=1024)
rephrase_button = st.button("Rephrase Text")

if rephrase_button:
    if text_to_rephrase.strip():
        rephrased = client.predict(
            text=text_to_rephrase,
            temperature=temp,
            max_tokens=tokens,
            api_name="/rephrase_text"
        )
        st.subheader("Rephrased Text:")
        st.write(rephrased)
    else:
        st.warning("Please enter some text to rephrase.")