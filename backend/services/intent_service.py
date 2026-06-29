import os
from google import genai
from dotenv import load_dotenv

# Load env variables using absolute path
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=dotenv_path)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def detect_intent_fallback(question):
    """Fallback keyword-based intent classifier."""
    question = question.lower()
    
    # Check PDF RAG keywords
    pdf_keywords = ["pdf", "document", "prospectus", "brochure", "file", "uploaded", "dummy.pdf"]
    if any(word in question for word in pdf_keywords):
        return "pdf"
        
    # Check Website RAG keywords
    website_keywords = [
        "nnrg", "college", "admission", "admissions", "course", "courses",
        "placement", "placements", "faculty", "department", "hostel",
        "transport", "library", "fees", "contact", "principal", "chairman",
        "campus"
    ]
    if any(word in question for word in website_keywords):
        return "website"
        
    return "general"


def detect_intent(question: str) -> str:
    """
    Uses Google Gemini 2.5 Flash to dynamically classify the intent of a question
    into 'pdf', 'website', or 'general' for RAG routing. Falls back to keyword matching.
    """
    # 1. Quick greetings and short query checks to bypass API calls
    q_clean = question.strip().lower().rstrip("?").strip()
    greetings = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how are you", "help", "who are you", "test"}
    if q_clean in greetings or len(q_clean) < 4:
        return "general"
        
    # 2. Check for strong PDF indicators
    pdf_keywords = ["pdf", "document", "prospectus", "brochure", "file", "uploaded", "syllabus", "guidelines"]
    if any(word in q_clean for word in pdf_keywords):
        return "pdf"
        
    # 3. Check for strong NNRG website indicators
    website_keywords = [
        "nnrg", "nalla", "narasimha", "reddy", "admission", "admissions", "placement", "placements", 
        "hostel", "principal", "chairman", "campus", "course", "courses", "fee", "fees", "transport", "bus", "route", "library"
    ]
    if any(word in q_clean for word in website_keywords):
        return "website"

    if not client:
        return detect_intent_fallback(question)
        
    system_prompt = f"""
    You are an intent classifier for the NNRG Web Knowledge Bot.
    Your task is to classify the user's question into exactly one of three categories:
    
    1. "pdf": The user is asking about an uploaded PDF document, a file, a brochure, a prospectus, or specifically requesting details from the "uploaded document".
    2. "website": The user is asking about NNRG Group of Institutions (e.g., college details, admissions, courses, placement statistics, library, transport, fees, principal, chairman, campus facilities).
    3. "general": Greetings, small talk, general programming, technology, general knowledge, or any other query that does not concern NNRG college specifically or the uploaded PDF.
    
    Only output the category name ("pdf", "website", or "general") as a single word. Do not include any extra words, punctuation, or formatting.
    
    User Question:
    "{question}"
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt
        )
        
        intent = response.text.strip().lower()
        if intent in ["pdf", "website", "general"]:
            return intent
            
    except Exception as e:
        print(f"Error in Gemini intent detection: {e}")
        
    return detect_intent_fallback(question)