# import streamlit as st
# from gradio_client import Client, handle_file
# # Custom CSS for better aesthetics
# st.markdown(
#     """
#     <style>
#     /* Gradient button for regular Streamlit buttons */
#     .stButton button {
#         background: linear-gradient(90deg, #2563EB, #9333EA);
#         color: white !important;
#         border-radius: 6px;
#         border: none;
#     }
#     .stButton button:hover {
#         background: linear-gradient(90deg, #1D4ED8, #7E22CE);
#         color: white !important;
#     }

#     /* Gradient style for the file upload button */
#     input[type="file"]::file-selector-button {
#         background: linear-gradient(90deg, #2563EB, #9333EA);
#         color: white;
#         border-radius: 6px;
#         border: none;
#         padding: 0.5rem 1rem;
#         font-size: 1rem;
#         cursor: pointer;
#         transition: background 0.3s ease;
#     }
#     input[type="file"]::file-selector-button:hover {
#         background: linear-gradient(90deg, #1D4ED8, #7E22CE);
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )
# # Connect to the Hugging Face Space once
# client = Client("girishwangikar/ResumeATS")

# st.title("Smart ATS")
# st.text("Improve Your Resume ATS")

# # -----------------------
# # Upload Resume + JD
# # -----------------------
# st.header("📄 ATS Resume Analyzer")

# jd = st.text_area("Paste the Job Description")
# uploaded_file = st.file_uploader("Upload Your Resume", type="pdf", help="Please upload a PDF resume")

# analyze_button = st.button("Analyze Resume")
# cover_letter_button = st.button("Generate Cover Letter")

# # We’ll store parsed resume in session_state so both buttons can use it
# if "parsed_resume" not in st.session_state:
#     st.session_state.parsed_resume = None

# # ---------- Analyze Resume ----------
# if analyze_button:
#     if uploaded_file is not None and jd.strip():
#         # Save uploaded file to a temp file
#         with open("temp_resume.pdf", "wb") as f:
#             f.write(uploaded_file.read())

#         # Parse resume
#         parsed_resume = client.predict(
#             file=handle_file("temp_resume.pdf"),
#             api_name="/process_resume"
#         )
#         st.session_state.parsed_resume = parsed_resume  # save for later use

        

#         # Analyze resume with job description
#         analysis = client.predict(
#             resume_text=parsed_resume,
#             job_description=jd,
#             with_job_description=True,
#             temperature=0.5,
#             max_tokens=1024,
#             api_name="/analyze_resume"
#         )
#         st.subheader("Analysis Result:")
#         st.write(analysis)
#     else:
#         st.warning("Please upload a resume and paste a Job Description before analyzing.")

# # ---------- Generate Cover Letter ----------
# if cover_letter_button:
#     if st.session_state.parsed_resume is not None and jd.strip():
#         cover_letter = client.predict(
#             resume_text=st.session_state.parsed_resume,
#             job_description=jd,
#             temperature=0.5,
#             max_tokens=1024,
#             api_name="/generate_cover_letter"
#         )
#         st.subheader("Generated Cover Letter:")
#         st.write(cover_letter)
#     else:
#         st.warning("Please first analyze the resume (or upload JD) before generating cover letter.")
# # -----------------------
# # Section 2: Rephrase Text
# # -----------------------
# st.header("✍️ Rephrase Any Text")

# text_to_rephrase = st.text_area("Enter text to rephrase:")
# temp = st.slider("Temperature", 0.0, 1.0, 0.5)
# tokens = st.number_input("Max tokens", min_value=1, max_value=2048, value=1024)
# rephrase_button = st.button("Rephrase Text")

# if rephrase_button:
#     if text_to_rephrase.strip():
#         rephrased = client.predict(
#             text=text_to_rephrase,
#             temperature=temp,
#             max_tokens=tokens,
#             api_name="/rephrase_text"
#         )
#         st.subheader("Rephrased Text:")
#         st.write(rephrased)
#     else:
#         st.warning("Please enter some text to rephrase.")


from flask import Flask, request, jsonify
from flask_cors import CORS
from gradio_client import Client, handle_file
from dotenv import load_dotenv
import tempfile
import os

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])  # Enable CORS for all routes
load_dotenv(dotenv_path=".env")
HF_TOKEN = os.getenv("HF_TOKEN")
print("Loaded HF_TOKEN:", HF_TOKEN) 
if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not set in environment. Run: export HF_TOKEN=your_token")

# Connect to the Hugging Face Space once
client = Client("girishwangikar/ResumeATS", hf_token=HF_TOKEN)
@app.before_request
def log_request_info():
    print("Incoming request:", request.method, request.url)
    print("Headers:", request.headers)
    print("Files:", request.files)
@app.route('/process_resume', methods=['POST'])
def process_resume():
    """
    Process a resume PDF file and return the parsed text
    """
    print("Hit /process_resume")
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        print("Request files:", request.files)
        file = request.files['file']
        print("Received files:", request.files)
        # Check if the file is a PDF
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400
        
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            
            # Parse resume
            parsed_resume = client.predict(
                file=handle_file(temp_file.name),
                api_name="/process_resume"
            )
            
            # Clean up temporary file
            os.unlink(temp_file.name)
            
            return jsonify({'parsed_resume': parsed_resume})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_resume', methods=['POST'])
def analyze_resume():
    """
    Analyze a resume against a job description
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        resume_text = data.get('resume_text')
        job_description = data.get('job_description')
        temperature = data.get('temperature', 0.5)
        max_tokens = data.get('max_tokens', 1024)
        
        if not resume_text or not job_description:
            return jsonify({'error': 'resume_text and job_description are required'}), 400
        
        # Analyze resume with job description
        analysis = client.predict(
            resume_text=resume_text,
            job_description=job_description,
            with_job_description=True,
            temperature=temperature,
            max_tokens=max_tokens,
            api_name="/analyze_resume"
        )
        
        return jsonify({'analysis': analysis})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_cover_letter', methods=['POST'])
def generate_cover_letter():
    """
    Generate a cover letter based on resume and job description
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        resume_text = data.get('resume_text')
        job_description = data.get('job_description')
        temperature = data.get('temperature', 0.5)
        max_tokens = data.get('max_tokens', 1024)
        
        if not resume_text or not job_description:
            return jsonify({'error': 'resume_text and job_description are required'}), 400
        
        # Generate cover letter
        cover_letter = client.predict(
            resume_text=resume_text,
            job_description=job_description,
            temperature=temperature,
            max_tokens=max_tokens,
            api_name="/generate_cover_letter"
        )
        
        return jsonify({'cover_letter': cover_letter})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/rephrase_text', methods=['POST'])
def rephrase_text():
    """
    Rephrase the given text
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        text = data.get('text')
        temperature = data.get('temperature', 0.5)
        max_tokens = data.get('max_tokens', 1024)
        
        if not text:
            return jsonify({'error': 'text is required'}), 400
        
        # Rephrase text
        rephrased = client.predict(
            text=text,
            temperature=temperature,
            max_tokens=max_tokens,
            api_name="/rephrase_text"
        )
        
        return jsonify({'rephrased_text': rephrased})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, port=8000)