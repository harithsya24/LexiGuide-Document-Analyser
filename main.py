import streamlit as st
import os
import requests
from PIL import Image
import pytesseract
import openai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')

# Page config
st.set_page_config(
    page_title="LexiGuide - Legal Document Analyzer",
    layout="wide"
)

# Check API keys
if not api_key or not maps_api_key:
    st.error("Please make sure both OpenAI and Google Maps API keys are set in your .env file")
    st.stop()

openai.api_key = api_key

def extract_text_from_image(image):
    img = Image.open(image)
    text = pytesseract.image_to_string(img)
    return text if text else ""

def analyze_legal_document(text):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a legal document analyzer. Provide a clear summary, highlight key points, and explain important legal terms used."},
            {"role": "user", "content": f"Analyze this legal document and provide: 1) A summary 2) Key points 3) Legal terms used with their explanations:\n\n{text}"}
        ]
    )
    return response.choices[0].message.content

def extract_legal_terms(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a legal terminology expert. Extract and explain legal terms from the document."},
            {"role": "user", "content": f"Extract all legal terms from this document and provide their definitions in simple language:\n\n{text}"}
        ]
    )
    return response.choices[0].message.content

'''def get_specialist_recommendations(location):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={maps_api_key}"
        res = requests.get(url).json()
        if res['status'] == 'OK':
            return [
                "Law Firm A - Specialists in Contract Law",
                "Legal Consultant B - Corporate Law Expert",
                "Attorney C - General Practice"
            ]
        else:
            return ["Unable to geocode location. Please check the input."]
    except Exception as e:
        return [f"Error: {str(e)}"]'''

def main():
    st.title("🔍 LexiGuide Legal Document Analyzer")
    
    menu = st.sidebar.radio("Navigation", ["Upload Document", "My Documents", "Legal Dictionary", "Analysis History"])
    
    if menu == "Upload Document":
        st.write("Upload your legal document for AI-powered analysis and recommendations")
        show_document_upload()
    elif menu == "My Documents":
        st.subheader("My Documents")
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
        st.info("Analysis history will be implemented in future updates")

def show_document_upload():
    uploaded_file = st.file_uploader("Upload your legal document", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file:
        with st.spinner("Processing document..."):
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                text = extract_text_from_image(uploaded_file)
            else:
                st.error("PDF support coming soon!")
                return

            analysis = analyze_legal_document(text)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Document Summary")
                st.write(analysis)
                
                st.subheader("Legal Terms Glossary")
                legal_terms = extract_legal_terms(text)
                st.write(legal_terms)

                st.subheader("Chat with Document")
                if 'chat_history' not in st.session_state:
                    st.session_state.chat_history = []

                chat_container = st.container()
                with chat_container:
                    for chat in st.session_state.chat_history:
                        if chat["role"] == "user":
                            st.markdown(f"**You:** {chat['content']}")
                        else:
                            st.markdown(f"**Assistant:** {chat['content']}")
                
                user_question = st.text_input("Ask a question about your document", key="chat_input")
                if user_question:
                    st.session_state.chat_history.append({"role": "user", "content": user_question})
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Answer questions about this legal document clearly and concisely."},
                            {"role": "user", "content": f"Document: {text}\nQuestion: {user_question}"}
                        ]
                    )
                    assistant_response = response.choices[0].message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                    st.rerun()

                if st.button("Clear Chat"):
                    st.session_state.chat_history = []
                    st.rerun()

            with col2:
                #st.subheader("Find Legal Specialists")
                #location = st.text_input("Enter your location")
                #if location:
                    #specialists = get_specialist_recommendations(location)
                    #for specialist in specialists:
                        #st.write(specialist)

                st.subheader("Feedback")
                if 'feedback_submitted' not in st.session_state:
                    st.session_state.feedback_submitted = False

                if not st.session_state.feedback_submitted:
                    feedback_rating = st.slider("How helpful was this analysis?", 1, 5, 3)
                    feedback_text = st.text_area("What can we improve?")
                    feedback_satisfaction = st.radio("Would you recommend this tool to others?", ["Yes", "No", "Maybe"])
                    
                    if st.button("Submit Feedback"):
                        feedback_data = {
                            "rating": feedback_rating,
                            "text": feedback_text,
                            "satisfaction": feedback_satisfaction,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        if 'all_feedback' not in st.session_state:
                            st.session_state.all_feedback = []
                        st.session_state.all_feedback.append(feedback_data)
                        st.session_state.feedback_submitted = True
                        st.success("Thank you for your feedback! Your input helps us improve.")
                        st.rerun()
                else:
                    st.success("Thank you for your feedback!")
                    if st.button("Provide More Feedback"):
                        st.session_state.feedback_submitted = False
                        st.rerun()

    st.markdown("---")
    st.caption("⚠️ Disclaimer: LexiGuide provides document analysis and recommendations but does not constitute legal advice. Always consult with a qualified legal professional.")

if __name__ == "__main__":
    main()