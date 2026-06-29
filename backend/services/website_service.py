import os
import re
import shutil
import requests
import time
from bs4 import BeautifulSoup
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv

# Load env variables using absolute path
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=dotenv_path)

URL = "https://nnrg.edu.in"
CHROMA_WEBSITE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_website_db")
api_key = os.getenv("GEMINI_API_KEY")


def get_embeddings():
    """Returns the Google GenAI embedding function."""
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=api_key
    )


def get_website_store():
    """Returns the persistent Chroma vector store instance for website content."""
    os.makedirs(os.path.dirname(CHROMA_WEBSITE_PATH), exist_ok=True)
    return Chroma(
        collection_name="website_collection",
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_WEBSITE_PATH
    )


def clean_soup(soup):
    """Removes standard header, footer, navigation, scripts, and styling to prevent indexing boilerplate."""
    for tag in ["header", "footer", "nav", "aside", "script", "style", "noscript"]:
        for element in soup.find_all(tag):
            element.decompose()
    return soup


def normalize_text_for_matching(text):
    """Normalizes AI/ML abbreviation variations so they match synonymously."""
    text = text.lower()
    text = re.sub(r'\bai\s*&\s*ml\b', 'aiml', text)
    text = re.sub(r'\bai\s*and\s*ml\b', 'aiml', text)
    text = re.sub(r'ai&ml', 'aiml', text)
    text = re.sub(r'ai-ml', 'aiml', text)
    return text


def extract_keywords(query):
    """Extracts meaningful keywords from the query for post-filtering and reranking."""
    stopwords = {
        'what', 'is', 'are', 'the', 'of', 'in', 'to', 'for', 'a', 'an', 'on', 'from', 'with', 'by', 
        'about', 'how', 'do', 'does', 'can', 'you', 'i', 'we', 'they', 'he', 'she', 'it', 'me', 'us', 
        'them', 'who', 'where', 'when', 'why', 'which', 'there', 'their', 'our', 'your', 'my', 'and', 
        'or', 'but', 'if', 'any', 'some', 'all', 'anywhere', 'anyone', 'anything', 'please', 'tell',
        'show', 'find', 'get', 'list', 'give'
    }
    # Normalize query first
    query_norm = normalize_text_for_matching(query)
    words = []
    cleaned_query = "".join(char if char.isalnum() or char.isspace() else " " for char in query_norm)
    for word in cleaned_query.split():
        if word not in stopwords and len(word) > 2:
            words.append(word)
    return words


def score_document(doc, keywords):
    """Calculates keyword match relevance score for a document."""
    text = normalize_text_for_matching(doc.page_content)
    score = 0
    for kw in keywords:
        if kw in text:
            score += 2
            # Add bonus for whole word matches
            if re.search(rf"\b{re.escape(kw)}\b", text):
                score += 3
    return score


def scrape_website():
    """
    Crawls the NNRG website homepage along with essential subpages and indexes them in ChromaDB.
    Cleans up HTML boilerplate and creates context-prefixed chunks.
    Uses batch sleep intervals to prevent Google Gemini API rate limiting.
    """
    try:
        pages = [
            ("Home Page", "https://nnrg.edu.in"),
            ("Contact Us", "https://nnrg.edu.in/contact-us.php"),
            ("About Us", "https://nnrg.edu.in/about-us.php"),
            ("Admission Process", "https://nnrg.edu.in/admission-process.php"),
            ("Fee Structure", "https://nnrg.edu.in/admission-fee-structure.php"),
            ("Courses Offered", "https://nnrg.edu.in/courses-offered.php"),
            ("Placement Cell", "https://nnrg.edu.in/placement-cell.php"),
            ("Placement Records", "https://nnrg.edu.in/placement-records.php"),
        ]
        
        all_text_blocks = []
        docs = []
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150
        )
        
        for name, url in pages:
            try:
                print(f"Scraping {name}: {url}")
                response = requests.get(url, timeout=12)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    soup = clean_soup(soup)
                    
                    # Extract clean lines
                    lines = [line.strip() for line in soup.get_text(separator="\n").split("\n")]
                    clean_content = "\n".join([line for line in lines if line])
                    
                    # Store in text blocks for backup file
                    all_text_blocks.append(f"\n\n=== NNRG Website Page: {name} ({url}) ===\n\n{clean_content}")
                    
                    # Split and create document chunks with page title prefix
                    page_chunks = text_splitter.split_text(clean_content)
                    for chunk in page_chunks:
                        chunk_content = f"Page: {name}\nContent: {chunk}"
                        docs.append(Document(
                            page_content=chunk_content,
                            metadata={"source": name, "url": url}
                        ))
            except Exception as e:
                print(f"Error scraping subpage {url}: {e}")

        full_text = "\n".join(all_text_blocks)
        
        # Save raw copy as a backup fallback
        data_dir = os.path.dirname(CHROMA_WEBSITE_PATH)
        os.makedirs(data_dir, exist_ok=True)
        txt_path = os.path.join(data_dir, "nnrg_website.txt")
        with open(txt_path, "w", encoding="utf-8") as file:
            file.write(full_text)
            
        db = get_website_store()
        try:
            res = db.get()
            if res and res.get("ids"):
                db.delete(ids=res["ids"])
                print(f"Cleared {len(res['ids'])} existing website vector entries.")
        except Exception as e:
            print(f"Warning: Could not clear website collection: {e}")
            
        print(f"Total chunks to index: {len(docs)}")
        
        # Add chunks one-by-one with a sleep of 1.2 seconds to avoid rate limits
        for i, doc in enumerate(docs):
            db.add_documents([doc])
            print(f"Indexed chunk {i+1}/{len(docs)}. Sleeping to respect rate limit...")
            time.sleep(1.2)
            
        return "Website crawled (including admissions, placements, fees, and contact details) and vector index created successfully."
    except Exception as e:
        return f"Error scraping website: {str(e)}"


def search_website_fallback(question):
    """
    Fallback keyword search over nnrg_website.txt if Chroma database is empty, rate-limited, or fails.
    """
    try:
        data_dir = os.path.dirname(CHROMA_WEBSITE_PATH)
        txt_path = os.path.join(data_dir, "nnrg_website.txt")
        if not os.path.exists(txt_path):
            return "Sorry, I couldn't find that information in the available knowledge base."
            
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        # Parse page blocks using the regex delimiter
        page_blocks = re.split(r'=== NNRG Website Page: (.*?) \((.*?)\) ===', text)
        candidates = []
        
        # Clean query and extract keywords
        stopwords = {
            'what', 'is', 'are', 'the', 'of', 'in', 'to', 'for', 'a', 'an', 'on', 'from', 'with', 'by', 
            'about', 'how', 'do', 'does', 'can', 'you', 'i', 'we', 'they', 'he', 'she', 'it', 'me', 'us', 
            'them', 'who', 'where', 'when', 'why', 'which', 'there', 'their', 'our', 'your', 'my', 'and', 
            'or', 'but', 'if', 'any', 'some', 'all', 'please', 'tell', 'show', 'find', 'get', 'list', 'give'
        }
        words = []
        # Normalize question first
        question_norm = normalize_text_for_matching(question)
        cleaned_query = "".join(char if char.isalnum() or char.isspace() else " " for char in question_norm)
        for word in cleaned_query.split():
            if word not in stopwords and len(word) > 2:
                words.append(word)
                
        i = 1
        while i < len(page_blocks):
            name = page_blocks[i].strip()
            url = page_blocks[i+1].strip()
            content = page_blocks[i+2].strip()
            
            name_lower = name.lower()
            question_lower = question.lower()
            
            # Split page content into paragraphs
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            for p in paragraphs:
                p_norm = normalize_text_for_matching(p)
                matches = sum(1 for kw in words if kw in p_norm)
                if matches > 0:
                    score = matches
                    
                    # Boost specific sections matching exact query terms
                    if any(kw in question_lower for kw in ["placement", "recruit", "job", "career"]):
                        if "placement" in name_lower:
                            score += 15
                    if any(kw in question_lower for kw in ["admission", "apply", "join", "eligibility", "counseling"]):
                        if "admission" in name_lower or "fee" in name_lower:
                            score += 15
                    if any(kw in question_lower for kw in ["location", "contact", "address", "where is", "phone", "email", "located"]):
                        if "contact" in name_lower:
                            score += 15
                        
                    candidates.append((p, score, name, url))
            i += 3
            
        if not candidates:
            return "Sorry, I couldn't find that information in the available knowledge base."
            
        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 4 candidates and format them
        top_candidates = candidates[:4]
        formatted_chunks = []
        for p, score, name, url in top_candidates:
            formatted_chunks.append(f"Page: {name}\nContent: {p}")
            
        return "\n\n".join(formatted_chunks)
    except Exception as e:
        print(f"Error in search_website_fallback: {e}")
        return "Sorry, I couldn't find that information in the available knowledge base."


def search_website(question, top_k=5):
    """
    Performs hybrid vector + keyword search on the Website Chroma collection and local text backup.
    Reranks and filters matches using semantic similarity, synonym mapping, and page boosts.
    """
    try:
        candidates = []
        
        # 1. Try retrieving candidates from vector store
        db_docs = []
        try:
            db = get_website_store()
            res = db.get(limit=1)
            if res and res.get("ids"):
                docs_and_scores = db.similarity_search_with_score(question, k=10)
                if docs_and_scores:
                    for doc, distance in docs_and_scores:
                        # Convert L2 distance to similarity score
                        similarity = 1.0 - (distance / 2.0)
                        db_docs.append((doc, similarity))
        except Exception as e:
            print(f"Chroma retrieval failed: {e}. Relying on text search.")
            
        # 2. Retrieve candidates from local text fallback
        fallback_docs = []
        try:
            data_dir = os.path.dirname(CHROMA_WEBSITE_PATH)
            txt_path = os.path.join(data_dir, "nnrg_website.txt")
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()
                page_blocks = re.split(r'=== NNRG Website Page: (.*?) \((.*?)\) ===', text)
                
                i = 1
                while i < len(page_blocks):
                    name = page_blocks[i].strip()
                    url = page_blocks[i+1].strip()
                    content = page_blocks[i+2].strip()
                    
                    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                    for p in paragraphs:
                        fallback_docs.append(Document(
                            page_content=f"Page: {name}\nContent: {p}",
                            metadata={"source": name, "url": url}
                        ))
                    i += 3
        except Exception as e:
            print(f"Fallback reading failed: {e}")

        # 3. Extract keywords (synonym normalized)
        keywords = extract_keywords(question)
        question_lower = question.lower()
        
        # 4. Score and merge all candidates
        scored_candidates = []
        seen_contents = set()
        
        # Process database docs first
        for doc, similarity in db_docs:
            content_clean = doc.page_content.strip()
            if content_clean in seen_contents:
                continue
            seen_contents.add(content_clean)
            
            kw_score = score_document(doc, keywords)
            total_score = similarity + (kw_score * 0.25)
            
            # Apply page topic boosts
            name = doc.metadata.get("source", "").lower()
            if any(kw in question_lower for kw in ["placement", "recruit", "job", "career"]) and "placement" in name:
                total_score += 15
            if any(kw in question_lower for kw in ["admission", "apply", "join", "eligibility", "counseling"]) and ("admission" in name or "fee" in name):
                total_score += 15
            if any(kw in question_lower for kw in ["location", "contact", "address", "where is", "phone", "email", "located"]) and "contact" in name:
                total_score += 15
                
            scored_candidates.append((doc, total_score))
            
        # Process fallback docs
        for doc in fallback_docs:
            content_clean = doc.page_content.strip()
            if content_clean in seen_contents:
                continue
            seen_contents.add(content_clean)
            
            kw_score = score_document(doc, keywords)
            if kw_score > 0:
                # Default baseline similarity for matched text
                similarity = 0.5
                total_score = similarity + (kw_score * 0.25)
                
                # Apply page topic boosts
                name = doc.metadata.get("source", "").lower()
                if any(kw in question_lower for kw in ["placement", "recruit", "job", "career"]) and "placement" in name:
                    total_score += 15
                if any(kw in question_lower for kw in ["admission", "apply", "join", "eligibility", "counseling"]) and ("admission" in name or "fee" in name):
                    total_score += 15
                if any(kw in question_lower for kw in ["location", "contact", "address", "where is", "phone", "email", "located"]) and "contact" in name:
                    total_score += 15
                    
                scored_candidates.append((doc, total_score))
                
        # 5. Sort candidates by total score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 6. Return top 4 candidates
        top_candidates = scored_candidates[:4]
        if not top_candidates:
            return "Sorry, I couldn't find that information in the available knowledge base."
            
        results = [doc.page_content for doc, _ in top_candidates]
        return "\n\n".join(results)
        
    except Exception as e:
        print(f"Unexpected error in search_website: {e}")
        return "Sorry, I couldn't find that information in the available knowledge base."