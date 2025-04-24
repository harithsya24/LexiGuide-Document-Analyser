import streamlit as st
import os
import requests
from PIL import Image
import pytesseract
import openai
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Page config
st.set_page_config(
    page_title="LexiGuide - Legal Document Analyzer",
    layout="wide"
)

# Check API keys
if not api_key or not maps_api_key:
    st.error("Please make sure both OpenAI and Google Maps API keys are set in your .env file")
    st.stop()

def extract_text_from_image(image):
    img = Image.open(image)
    text = pytesseract.image_to_string(img)
    return text if text else ""

def analyze_legal_document(text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a legal document analyzer. Provide a clear summary, highlight key points, and explain important legal terms used."},
            {"role": "user", "content": f"Analyze this legal document and provide: 1) A summary 2) Key points 3) Legal terms used with their explanations:\n\n{text}"}
        ]
    )
    return response.choices[0].message.content

def extract_legal_terms(text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a legal terminology expert. Extract and explain legal terms from the document."},
            {"role": "user", "content": f"Extract all legal terms from this document and provide their definitions in simple language:\n\n{text}"}
        ]
    )
    return response.choices[0].message.content

# RAG Implementation for Legal Dictionary
def fetch_definition_from_api(term):
    """Step 1: Retrieve - Fetch definition from a dictionary API"""
    try:
        # Using Free Dictionary API
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{term}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            # Extract relevant information
            definitions = []
            for entry in data:
                for meaning in entry.get('meanings', []):
                    for definition in meaning.get('definitions', []):
                        definitions.append({
                            'definition': definition.get('definition', ''),
                            'part_of_speech': meaning.get('partOfSpeech', ''),
                            'example': definition.get('example', '')
                        })
            return {
                'found': True,
                'definitions': definitions,
                'source': 'Dictionary API'
            }
        else:
            return {
                'found': False,
                'message': f"Term '{term}' not found in general dictionary."
            }
    except Exception as e:
        return {
            'found': False,
            'message': f"Error fetching definition: {str(e)}"
        }

def augment_definition_with_llm(term, api_result, is_legal_context=True):
    """Step 2: Augment - Use LLM to enhance, simplify, or add legal context"""
    
    # Prepare context from API result
    context = ""
    if api_result['found']:
        context = f"Definitions from dictionary:\n"
        for i, def_item in enumerate(api_result['definitions']):
            context += f"{i+1}. ({def_item['part_of_speech']}) {def_item['definition']}"
            if def_item['example']:
                context += f"\n   Example: {def_item['example']}"
            context += "\n"
    else:
        context = api_result['message']
    
    # Prepare prompt based on whether definition was found and if legal context is needed
    system_prompt = "You are a legal dictionary assistant that explains terms clearly and accurately."
    
    if is_legal_context:
        user_prompt = f"""For the term: '{term}'
        
{context}

Please provide:
1. A clear legal definition (or your best understanding if the term wasn't found in the dictionary)
2. The legal context where this term is commonly used
3. A simplified explanation in plain language
4. 1-2 example sentences showing how this term is used in legal documents"""
    else:
        user_prompt = f"""For the term: '{term}'
        
{context}

Please provide:
1. A clear definition (based on the dictionary or your knowledge)
2. A simplified explanation in plain language
3. 1-2 example sentences showing how this term is used"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return {
            'augmented_definition': response.choices[0].message.content,
            'source': 'API + LLM' if api_result['found'] else 'LLM only'
        }
    except Exception as e:
        return {
            'augmented_definition': f"Error generating definition: {str(e)}",
            'source': 'Error'
        }

def generate_definition_output(term, augmented_result):
    """Step 3: Generate - Format and display the final result"""
    st.subheader(f"Definition: {term}")
    st.caption(f"Source: {augmented_result['source']}")
    st.markdown(augmented_result['augmented_definition'])
    st.markdown("---")

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
        col1, col2 = st.columns([3, 1])
        
        with col1:
            term = st.text_input("Search for a legal term")
        
        with col2:
            is_legal_specific = st.checkbox("Legal context only", value=True, help="When checked, focuses on legal definitions specifically")
        
        if term:
            with st.spinner("Retrieving definition..."):
                api_result = fetch_definition_from_api(term)
                augmented_result = augment_definition_with_llm(term, api_result, is_legal_specific)
                generate_definition_output(term, augmented_result)
                if 'dictionary_history' not in st.session_state:
                    st.session_state.dictionary_history = []
                if term not in [item['term'] for item in st.session_state.dictionary_history]:
                    st.session_state.dictionary_history.append({
                        'term': term,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        if 'dictionary_history' in st.session_state and st.session_state.dictionary_history:
            st.subheader("Recent Searches")
            history_cols = st.columns(min(5, len(st.session_state.dictionary_history)))
            
            for i, hist_item in enumerate(st.session_state.dictionary_history[-5:]):  
                with history_cols[i % len(history_cols)]:
                    if st.button(hist_item['term'], key=f"hist_{hist_item['term']}"):
                        
                        term = hist_item['term']
                        st.experimental_rerun()
            
            if st.button("Clear History"):
                st.session_state.dictionary_history = []
                st.experimental_rerun()
                
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