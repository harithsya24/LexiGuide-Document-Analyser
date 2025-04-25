import streamlit as st
import os
import requests
from PIL import Image
import pytesseract
import openai
import PyPDF2  # Add PyPDF2 for PDF extraction
import io  # For handling byte streams
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

# Initialize session state variables
if 'show_chat' not in st.session_state:
    st.session_state.show_chat = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'dictionary_history' not in st.session_state:
    st.session_state.dictionary_history = []
if 'feedback_submitted' not in st.session_state:
    st.session_state.feedback_submitted = False
if 'current_document_text' not in st.session_state:
    st.session_state.current_document_text = ""
if 'doc_chat_history' not in st.session_state:
    st.session_state.doc_chat_history = []
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = {
        "rating": 3,
        "text": "",
        "satisfaction": "Yes"
    }
if 'all_feedback' not in st.session_state:
    st.session_state.all_feedback = []

# New session state variables for document storage
if 'my_documents' not in st.session_state:
    st.session_state.my_documents = []
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None
if 'current_document_name' not in st.session_state:
    st.session_state.current_document_name = ""

# Check API keys
if not api_key or not maps_api_key:
    st.error("Please make sure both OpenAI and Google Maps API keys are set in your .env file")
    st.stop()

def extract_text_from_image(image):
    img = Image.open(image)
    text = pytesseract.image_to_string(img)
    return text if text else ""

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file"""
    text = ""
    try:
        # Create a PDF reader object
        pdf_bytes = io.BytesIO(pdf_file.read())
        pdf_reader = PyPDF2.PdfReader(pdf_bytes)
        
        # Extract text from each page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"
        
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def analyze_legal_document(text):
    # Only call API if analysis doesn't exist or needs to be refreshed
    if st.session_state.current_analysis is None:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a legal document analyzer. Provide a clear summary, highlight key points, and explain important legal terms used."},
                {"role": "user", "content": f"Analyze this legal document and provide: 1) A summary 2) Key points 3) Legal terms used with their explanations:\n\n{text}"}
            ]
        )
        analysis_result = response.choices[0].message.content
        st.session_state.current_analysis = analysis_result
    
    return st.session_state.current_analysis

def extract_legal_terms(text):
    # Check if we need to extract terms or can use cached data
    if 'current_legal_terms' not in st.session_state:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a legal terminology expert. Extract and explain legal terms from the document."},
                {"role": "user", "content": f"Extract all legal terms from this document and provide their definitions in simple language:\n\n{text}"}
            ]
        )
        terms_result = response.choices[0].message.content
        st.session_state.current_legal_terms = terms_result
    
    return st.session_state.current_legal_terms

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
    
    # Check if we already have this definition cached
    term_key = f"{term}_{is_legal_context}"
    if 'cached_definitions' not in st.session_state:
        st.session_state.cached_definitions = {}
    
    if term_key in st.session_state.cached_definitions:
        return st.session_state.cached_definitions[term_key]
    
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
        result = {
            'augmented_definition': response.choices[0].message.content,
            'source': 'API + LLM' if api_result['found'] else 'LLM only'
        }
        
        # Cache the result
        st.session_state.cached_definitions[term_key] = result
        return result
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

def toggle_chat():
    st.session_state.show_chat = not st.session_state.show_chat

# Callback functions to avoid page refresh
def submit_doc_question():
    user_question = st.session_state.doc_question_input
    if user_question:
        # Add user question to doc chat history
        st.session_state.doc_chat_history.append({
            "role": "user", 
            "content": user_question
        })
        
        # Get AI response for document context
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful legal assistant. Answer questions about this document clearly and concisely."},
                    {"role": "user", "content": f"Document: {st.session_state.current_document_text}\nQuestion: {user_question}"}
                ]
            )
            assistant_response = response.choices[0].message.content
            
            # Add assistant response to doc chat history
            st.session_state.doc_chat_history.append({
                "role": "assistant", 
                "content": assistant_response
            })
        except Exception as e:
            st.session_state.doc_chat_history.append({
                "role": "assistant", 
                "content": f"Sorry, I encountered an error: {str(e)}"
            })
        
        # Clear the input
        st.session_state.doc_question_input = ""

def submit_chat_question():
    user_question = st.session_state.chat_input
    if user_question:
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user", 
            "content": user_question
        })
        
        # Generate context based on whether we have document text
        context = f"Document: {st.session_state.current_document_text}\n" if st.session_state.current_document_text else "No document is currently loaded. "
        
        # Get AI response
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful legal assistant. Answer questions clearly and concisely."},
                    {"role": "user", "content": f"{context}Question: {user_question}"}
                ]
            )
            assistant_response = response.choices[0].message.content
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": assistant_response
            })
        except Exception as e:
            # Handle API errors
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"Sorry, I encountered an error: {str(e)}"
            })
        
        # Clear the input
        st.session_state.chat_input = ""

def clear_doc_chat():
    st.session_state.doc_chat_history = []

def clear_chat():
    st.session_state.chat_history = []

def submit_feedback():
    if 'feedback_rating' in st.session_state and 'feedback_text' in st.session_state and 'feedback_satisfaction' in st.session_state:
        feedback_data = {
            "rating": st.session_state.feedback_rating,
            "text": st.session_state.feedback_text,
            "satisfaction": st.session_state.feedback_satisfaction,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.all_feedback.append(feedback_data)
        st.session_state.feedback_submitted = True
        
        # Add feedback to the current analysis history
        if st.session_state.current_analysis and st.session_state.current_document_name:
            for item in st.session_state.analysis_history:
                if item['document_name'] == st.session_state.current_document_name:
                    if 'feedback' not in item:
                        item['feedback'] = []
                    item['feedback'].append(feedback_data)
                    break

def reset_feedback():
    st.session_state.feedback_submitted = False

def save_document():
    """Save current document to My Documents"""
    if not st.session_state.current_document_text or not st.session_state.current_document_name:
        st.warning("No document to save or missing document name")
        return
    
    # Check if document already exists
    doc_exists = False
    for doc in st.session_state.my_documents:
        if doc['name'] == st.session_state.current_document_name:
            doc_exists = True
            doc['text'] = st.session_state.current_document_text
            doc['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"Updated document: {st.session_state.current_document_name}")
            break
    
    if not doc_exists:
        # Add new document
        st.session_state.my_documents.append({
            'name': st.session_state.current_document_name,
            'text': st.session_state.current_document_text,
            'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'last_modified': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        st.success(f"Saved document: {st.session_state.current_document_name}")
    
    # Also save to analysis history if we have an analysis
    if st.session_state.current_analysis:
        save_analysis()

def save_analysis():
    """Save current analysis to Analysis History"""
    if not st.session_state.current_analysis or not st.session_state.current_document_name:
        return
    
    # Check if analysis already exists
    analysis_exists = False
    for analysis in st.session_state.analysis_history:
        if analysis['document_name'] == st.session_state.current_document_name:
            analysis_exists = True
            analysis['analysis'] = st.session_state.current_analysis
            analysis['legal_terms'] = st.session_state.current_legal_terms if 'current_legal_terms' in st.session_state else ""
            analysis['last_analyzed'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    
    if not analysis_exists:
        # Add new analysis
        st.session_state.analysis_history.append({
            'document_name': st.session_state.current_document_name,
            'analysis': st.session_state.current_analysis,
            'legal_terms': st.session_state.current_legal_terms if 'current_legal_terms' in st.session_state else "",
            'date_analyzed': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'last_analyzed': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'feedback': []
        })

def load_document(document_name):
    """Load a document from My Documents"""
    for doc in st.session_state.my_documents:
        if doc['name'] == document_name:
            st.session_state.current_document_text = doc['text']
            st.session_state.current_document_name = doc['name']
            # Reset analysis to force reanalysis
            st.session_state.current_analysis = None
            if 'current_legal_terms' in st.session_state:
                del st.session_state.current_legal_terms
            # Clear document Q&A
            st.session_state.doc_chat_history = []
            return True
    return False

def render_chat_ui():
    # Chat header
    st.subheader("💬 LexiGuide Assistant")
    
    # Custom CSS for chat messages
    st.markdown("""
    <style>
    .user-message {
        background-color: #e1f5fe;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        text-align: right;
    }
    .assistant-message {
        background-color: #f0f0f0;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        text-align: left;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display chat messages in a scrollable container
    chat_container = st.container(height=400)
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.markdown(f"<div class='user-message'><strong>You:</strong> {chat['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='assistant-message'><strong>Assistant:</strong> {chat['content']}</div>", unsafe_allow_html=True)
    
    # Chat input and buttons
    st.text_input("Ask a question", key="chat_input", on_change=submit_chat_question)
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.button("Clear Chat", on_click=clear_chat)
    
    with col2:
        st.button("Close Chat", on_click=toggle_chat)

def main():
    st.title("🔍 LexiGuide Legal Document Analyzer")
    
    # Add chat button in the sidebar
    with st.sidebar:
        st.title("LexiGuide Menu")
        if st.button("💬 Chat Assistant", use_container_width=True, 
                     help="Open AI Assistant to ask questions"):
            toggle_chat()
    
    # Main navigation menu
    with st.sidebar:
        menu = st.radio("Navigation", ["Upload Document", "My Documents", "Legal Dictionary", "Analysis History"])
    
    # Show chat window if toggled
    if st.session_state.show_chat:
        with st.sidebar:
            st.markdown("---")
            render_chat_ui()
            st.markdown("---")
    
    if menu == "Upload Document":
        st.write("Upload your legal document for AI-powered analysis and recommendations")
        uploaded_file = st.file_uploader("Upload your legal document", type=["pdf", "png", "jpg", "jpeg"])
        
        # Document name input field
        document_name = st.text_input("Document Name", value=st.session_state.current_document_name)
        if document_name:
            st.session_state.current_document_name = document_name

        if uploaded_file:
            with st.spinner("Processing document..."):
                # Check file type and process accordingly
                if uploaded_file.type.startswith('image'):
                    text = extract_text_from_image(uploaded_file)
                    st.session_state.current_document_text = text
                    
                    # Show preview of the image
                    st.subheader("Document Preview")
                    image = Image.open(uploaded_file)
                    st.image(image, width=400)
                    
                elif uploaded_file.type == "application/pdf":
                    text = extract_text_from_pdf(uploaded_file)
                    st.session_state.current_document_text = text
                    
                    # Show notification that PDF was processed
                    st.subheader("Document Preview")
                    st.success(f"PDF document processed successfully")
                    # Display first 500 characters as preview
                    if len(text) > 0:
                        st.text_area("Document Content Preview", text[:500] + "...", height=200)
                    else:
                        st.warning("No text could be extracted from the PDF. It may be scanned or contain only images.")
                else:
                    st.error("Unsupported file type. Please upload a PDF or image file.")
                    st.session_state.current_document_text = ""

                # Set default name if not provided
                if not st.session_state.current_document_name and uploaded_file:
                    st.session_state.current_document_name = uploaded_file.name

                # Save document button
                if st.session_state.current_document_text and st.session_state.current_document_name:
                    if st.button("Save to My Documents"):
                        save_document()

                if st.session_state.current_document_text:
                    # Call analysis function - caching handled inside
                    analysis = analyze_legal_document(st.session_state.current_document_text)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Document Summary")
                        st.write(analysis)
                        
                        st.subheader("Legal Terms Glossary")
                        legal_terms = extract_legal_terms(st.session_state.current_document_text)
                        st.write(legal_terms)

                    with col2:
                        st.subheader("Document Q&A")
                        
                        # Document Q&A without page refresh using callbacks
                        st.text_input("Ask a question about this document", key="doc_question_input", on_change=submit_doc_question)
                        
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.button("Clear Conversation", on_click=clear_doc_chat)
                        
                        # Display document chat history
                        doc_chat_container = st.container(height=300)
                        with doc_chat_container:
                            for chat in st.session_state.doc_chat_history:
                                if chat["role"] == "user":
                                    st.markdown(f"<div class='user-message'><strong>You:</strong> {chat['content']}</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<div class='assistant-message'><strong>Assistant:</strong> {chat['content']}</div>", unsafe_allow_html=True)

                        st.subheader("Feedback")
                        if not st.session_state.feedback_submitted:
                            st.slider("How helpful was this analysis?", 1, 5, 3, key="feedback_rating")
                            st.text_area("What can we improve?", key="feedback_text")
                            st.radio("Would you recommend this tool to others?", ["Yes", "No", "Maybe"], key="feedback_satisfaction")
                            
                            st.button("Submit Feedback", on_click=submit_feedback)
                        else:
                            st.success("Thank you for your feedback!")
                            st.button("Provide More Feedback", on_click=reset_feedback)

    elif menu == "My Documents":
        st.subheader("My Documents")
        
        if not st.session_state.my_documents:
            st.info("No documents saved yet. Upload a document first.")
        else:
            # Display documents in a table
            doc_data = []
            for doc in st.session_state.my_documents:
                doc_data.append({
                    "Name": doc['name'],
                    "Date Added": doc['date_added'],
                    "Last Modified": doc['last_modified']
                })
            
            st.table(doc_data)
            
            # Document selection dropdown
            doc_names = [doc['name'] for doc in st.session_state.my_documents]
            selected_doc = st.selectbox("Select a document to view", [""] + doc_names)
            
            if selected_doc:
                if st.button(f"Load document: {selected_doc}"):
                    if load_document(selected_doc):
                        st.success(f"Document loaded: {selected_doc}")
                        st.rerun()  # This will refresh the page to show the loaded document
        
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
                
                if term not in [item['term'] for item in st.session_state.dictionary_history]:
                    st.session_state.dictionary_history.append({
                        'term': term,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        if st.session_state.dictionary_history:
            st.subheader("Recent Searches")
            # Use columns for displaying recent searches
            num_columns = min(5, len(st.session_state.dictionary_history))
            if num_columns > 0:  # Make sure we have at least one column
                history_cols = st.columns(num_columns)
                
                for i, hist_item in enumerate(st.session_state.dictionary_history[-5:]):  
                    with history_cols[i % len(history_cols)]:
                        # We need a unique callback for each history item
                        def create_term_callback(t):
                            def term_callback():
                                st.session_state.term_search = t
                            return term_callback
                        
                        st.button(hist_item['term'], key=f"hist_{hist_item['term']}", 
                                 on_click=create_term_callback(hist_item['term']))
            
            if st.button("Clear History"):
                st.session_state.dictionary_history = []
                
    elif menu == "Analysis History":
        st.subheader("Analysis History")
        
        if not st.session_state.analysis_history:
            st.info("No analyses saved yet. Upload and analyze a document first.")
        else:
            # Display analyses in a table
            analysis_data = []
            for analysis in st.session_state.analysis_history:
                feedback_count = len(analysis.get('feedback', []))
                avg_rating = 0
                if feedback_count > 0:
                    avg_rating = sum(fb.get('rating', 0) for fb in analysis.get('feedback', [])) / feedback_count
                
                analysis_data.append({
                    "Document": analysis['document_name'],
                    "Date Analyzed": analysis['date_analyzed'],
                    "Feedback Count": feedback_count,
                    "Avg. Rating": f"{avg_rating:.1f}/5" if feedback_count > 0 else "N/A"
                })
            
            st.table(analysis_data)
            
            # Analysis selection dropdown
            analysis_docs = [a['document_name'] for a in st.session_state.analysis_history]
            selected_analysis = st.selectbox("Select an analysis to view", [""] + analysis_docs)
            
            if selected_analysis:
                for analysis in st.session_state.analysis_history:
                    if analysis['document_name'] == selected_analysis:
                        st.subheader(f"Analysis for: {selected_analysis}")
                        
                        # Create tabs for different sections
                        tab1, tab2, tab3 = st.tabs(["Summary", "Legal Terms", "Feedback"])
                        
                        with tab1:
                            st.markdown(analysis['analysis'])
                        
                        with tab2:
                            if analysis.get('legal_terms'):
                                st.markdown(analysis['legal_terms'])
                            else:
                                st.info("No legal terms extracted for this document.")
                        
                        with tab3:
                            if analysis.get('feedback') and len(analysis['feedback']) > 0:
                                for i, fb in enumerate(analysis['feedback']):
                                    st.markdown(f"### Feedback #{i+1}")
                                    st.markdown(f"**Rating:** {fb.get('rating')}/5")
                                    st.markdown(f"**Would recommend:** {fb.get('satisfaction')}")
                                    st.markdown(f"**Comment:** {fb.get('text')}")
                                    st.markdown(f"**Date:** {fb.get('timestamp')}")
                                    st.markdown("---")
                            else:
                                st.info("No feedback submitted for this analysis.")
                        
                        # Option to load the document
                        if st.button(f"Load document for editing"):
                            if load_document(selected_analysis):
                                st.success(f"Document loaded: {selected_analysis}")
                                st.rerun()  # This will refresh the page
                        break

    st.markdown("---")
    st.caption("⚠️ Disclaimer: LexiGuide provides document analysis and recommendations but does not constitute legal advice. Always consult with a qualified legal professional.")

if __name__ == "__main__":
    main()