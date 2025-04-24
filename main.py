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
openai.api_key = os.getenv('OPENAI_API_KEY')

# Set up Google Cloud credentials (removed as not needed for pytesseract)

def extract_text_from_image(image):
    # Convert uploaded file to PIL Image
    img = Image.open(image)
    # Extract text using pytesseract
    text = pytesseract.image_to_string(img)
    return text if text else ""

def analyze_legal_document(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a legal document analyzer. Provide a clear summary and highlight key points."},
            {"role": "user", "content": f"Analyze this legal document:\n\n{text}"}
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
    st.write("Upload your legal document for AI-powered analysis and recommendations")

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

                st.subheader("Ask a Question")
                user_question = st.text_input("What would you like to know about this document?")
                if user_question:
                    response = openai.ChatCompletion.create(
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

    # Disclaimer
    st.markdown("---")
    st.caption("⚠️ Disclaimer: LexiGuide provides document analysis and recommendations but does not constitute legal advice. Always consult with a qualified legal professional for legal matters.")

if __name__ == "__main__":
    main()