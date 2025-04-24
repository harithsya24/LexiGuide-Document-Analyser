import streamlit as st
import os
from PIL import Image
import pytesseract
import openai
from geopy.geocoders import Nominatim
from datetime import datetime

# Page config
st.set_page_config(
    page_title="LexiGuide - Legal Document Analyzer",
    layout="wide"
)

# Initialize APIs (keys should be set in Secrets)
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("Please set your OpenAI API key in Secrets")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# Set up Google Cloud credentials (removed as not needed for pytesseract)

def extract_text_from_image(image):
    # Convert uploaded file to PIL Image
    img = Image.open(image)
    # Extract text using pytesseract
    text = pytesseract.image_to_string(img)
    return text if text else ""

def analyze_legal_document(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a legal document analyzer. Provide a clear summary, highlight key points, and explain important legal terms used."},
            {"role": "user", "content": f"Analyze this legal document and provide: 1) A summary 2) Key points 3) Legal terms used with their explanations:\n\n{text}"}
        ]
    )
    return response.choices[0].message.content

def extract_legal_terms(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a legal terminology expert. Extract and explain legal terms from the document."},
            {"role": "user", "content": f"Extract all legal terms from this document and provide their definitions in simple language:\n\n{text}"}
        ]
    )
    return response.choices[0].message.content

def get_specialist_recommendations(location):
    geolocator = Nominatim(user_agent="lexiguide")
    try:
        location_data = geolocator.geocode(location)
        # In a real app, you would query a database of legal specialists
        return [
            "Law Firm A - Specialists in Contract Law",
            "Legal Consultant B - Corporate Law Expert",
            "Attorney C - General Practice"
        ]
    except:
        return ["Unable to find specialists in your area"]

def main():
    st.title("🔍 LexiGuide Legal Document Analyzer")
    
    # Create menu using radio buttons
    menu = st.sidebar.radio("Navigation", ["Upload Document", "My Documents", "Legal Dictionary", "Analysis History"])
    
    if menu == "Upload Document":
        st.write("Upload your legal document for AI-powered analysis and recommendations")
        show_document_upload()
    elif menu == "My Documents":
        st.subheader("My Documents")
        st.write("Your previously analyzed documents will appear here")
        # In a real app, you would fetch from a database
        st.info("Document history will be implemented in future updates")
    elif menu == "Legal Dictionary":
        st.subheader("Legal Dictionary")
        term = st.text_input("Search for a legal term")
        if term:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a legal dictionary. Explain legal terms in simple language."},
                    {"role": "user", "content": f"Define this legal term: {term}"}
                ]
            )
            st.write(response.choices[0].message.content)
    elif menu == "Analysis History":
        st.subheader("Analysis History")
        st.write("Your previous analyses will appear here")
        # In a real app, you would fetch from a database
        st.info("Analysis history will be implemented in future updates")

def show_document_upload():
    # Document Upload
    uploaded_file = st.file_uploader("Upload your legal document", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file:
        # Process document
        with st.spinner("Processing document..."):
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                text = extract_text_from_image(uploaded_file)
            else:
                # For PDF support, additional processing would be needed
                st.error("PDF support coming soon!")
                return

            # Analyze document
            analysis = analyze_legal_document(text)

            # Display results
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Document Summary")
                st.write(analysis)
                
                st.subheader("Legal Terms Glossary")
                legal_terms = extract_legal_terms(text)
                st.write(legal_terms)

                st.subheader("Ask a Question")
                user_question = st.text_input("What would you like to know about this document?")
                if user_question:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Answer questions about this legal document."},
                            {"role": "user", "content": f"Document: {text}\nQuestion: {user_question}"}
                        ]
                    )
                    st.write(response.choices[0].message.content)

            with col2:
                st.subheader("Find Legal Specialists")
                location = st.text_input("Enter your location")
                if location:
                    specialists = get_specialist_recommendations(location)
                    for specialist in specialists:
                        st.write(specialist)

                st.subheader("Feedback")
                feedback = st.slider("How helpful was this analysis?", 1, 5, 3)
                feedback_text = st.text_area("Additional comments")
                if st.button("Submit Feedback"):
                    # In a real app, you would store this feedback
                    st.success("Thank you for your feedback!")
                    st.session_state.radio = "Upload Document"
                    st.experimental_rerun()

    # Disclaimer
    st.markdown("---")
    st.caption("⚠️ Disclaimer: LexiGuide provides document analysis and recommendations but does not constitute legal advice. Always consult with a qualified legal professional for legal matters.")

if __name__ == "__main__":
    main()

    # Configure Streamlit to run on the correct host and port
    import os
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'