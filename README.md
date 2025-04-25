# LexiGuide - Legal Document Analyzer

## Overview
LexiGuide is an AI-powered legal document analysis tool that helps users understand legal documents by providing summaries, extracting key points, explaining legal terminology, and allowing interactive Q&A sessions about document content.

## Features

### Document Processing
- Upload and analyze legal documents in multiple formats (PDF, PNG, JPG, JPEG)
- Extract text from images and PDFs using OCR technology
- Save documents for future reference

### AI-Powered Analysis
- Get comprehensive document summaries
- Identify and explain key points in legal documents
- Extract and explain legal terminology used in documents
- Interactive Q&A about document content

### Legal Dictionary
- Search for legal terms and get plain-language explanations
- View terms in legal context or general context
- Access recently searched terms for quick reference

### Document Management
- Save and organize your legal documents
- View and manage previously analyzed documents
- Track analysis history with timestamps

### User Feedback System
- Rate the helpfulness of analysis
- Provide feedback and suggestions for improvement
- View feedback history for previous analyses

### AI Assistant
- Chat with an AI assistant about legal concepts
- Ask questions about loaded documents or general legal topics
- Get AI-powered guidance throughout the application

## Installation

### Prerequisites
- Python 3.8+
- Tesseract OCR (for image text extraction)
- OpenAI API key
- Google Maps API key

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lexiguide.git
   cd lexiguide
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Tesseract OCR:

Linux: sudo apt-get install tesseract-ocr
macOS: brew install tesseract
Windows: Download and install from GitHub

5. Create a .env file in the project root with your API keys:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```
## Usage

1. Start the application:
   ```bash
   streamlit run app.py
   ```

2. Navigate to http://localhost:8501 in your web browser
3. Use the sidebar menu to navigate between different features:
   Upload Document: Process and analyze new legal documents
   My Documents: Access previously saved documents
   Legal Dictionary: Look up and understand legal terminology
   Analysis History: Review previous document analyses

### Uploading Documents

1. Select "Upload Document" from the sidebar
2. Click "Browse files" and select your legal document (PDF or image)
3. Enter a name for your document
4. View the AI-generated analysis, including summary and legal terms
U5. se the Document Q&A feature to ask specific questions about the document

### Using the Legal Dictionary

Select "Legal Dictionary" from the sidebar
Enter a legal term in the search box
Toggle "Legal context only" to focus on legal-specific definitions
View the plain-language explanation and examples

### Accessing Saved Documents

Select "My Documents" from the sidebar
Browse your saved documents
Select a document to view or edit

### Using the AI Assistant

Click the "Chat Assistant" button in the sidebar
Ask questions about legal concepts or the currently loaded document
Get AI-powered responses in natural language

## Technical Details
### Architecture

* Built with Streamlit for the web interface
* Uses OpenAI's GPT models for document analysis and Q&A
* Implements OCR for extracting text from images
* Uses PyPDF2 for PDF text extraction

### RAG Implementation
The application uses a Retrieval-Augmented Generation (RAG) approach for the Legal Dictionary:

* Retrieve: Fetches definitions from a dictionary API
* Augment: Enhances definitions with legal context using LLMs
* Generate: Formats and presents the final result to users

### Data Privacy
LexiGuide processes all documents locally on your machine. Document content is sent to OpenAI's API for analysis but is not stored on their servers beyond the processing time. Your documents are stored only in your local session unless you explicitly save them.

## Team

LexiGuide was developed by a small but dedicated team of three:

- **Amrutha Kanakatte Ravishankar** - *Graduate Student at Stevens Institute of Technology*
- **Sneha Venkatesh** - *Graduate Student at Stevens Institute of Technology*
- **Nisha Thaluru Gopi** - *Graduate Student at Stevens Institute of Technology*

Our team combines expertise in legal document analysis, artificial intelligence, and user experience design to create a tool that makes legal documents more accessible and understandable for everyone.

## Disclaimer
⚠️ LexiGuide provides document analysis and recommendations but does not constitute legal advice. Always consult with a qualified legal professional for legal matters.
   
