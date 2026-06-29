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


def extract_keywords(query):
    """Extracts meaningful keywords from the query for post-filtering and reranking."""
    stopwords = {
        'what', 'is', 'are', 'the', 'of', 'in', 'to', 'for', 'a', 'an', 'on', 'from', 'with', 'by', 
        'about', 'how', 'do', 'does', 'can', 'you', 'i', 'we', 'they', 'he', 'she', 'it', 'me', 'us', 
        'them', 'who', 'where', 'when', 'why', 'which', 'there', 'their', 'our', 'your', 'my', 'and', 
        'or', 'but', 'if', 'any', 'some', 'all', 'anywhere', 'anyone', 'anything', 'please', 'tell',
        'show', 'find', 'get', 'list', 'give'
    }
    # Clean the query, convert to lowercase, and split
    words = []
    cleaned_query = "".join(char if char.isalnum() or char.isspace() else " " for char in query.lower())
    for word in cleaned_query.split():
        if word not in stopwords and len(word) > 2:
            words.append(word)
    return words


def score_document(doc, keywords):
    """Calculates keyword match relevance score for a document."""
    text = doc.page_content.lower()
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


def search_website(question, top_k=5):
    """
    Performs vector similarity search on the Website Chroma collection.
    Automatically indexes raw website text if the collection is empty.
    Reranks and filters matches using semantic similarity and keyword scores.
    """
    try:
        db = get_website_store()
        res = db.get(limit=1)
        
        # Auto-index raw file if vector store is empty but raw backup exists
        if not res or not res.get("ids"):
            data_dir = os.path.dirname(CHROMA_WEBSITE_PATH)
            txt_path = os.path.join(data_dir, "nnrg_website.txt")
            if os.path.exists(txt_path):
                print("Website Chroma empty. Building index from local nnrg_website.txt...")
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                page_blocks = re.split(r'=== NNRG Website Page: (.*?) \((.*?)\) ===', text)
                docs = []
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=800,
                    chunk_overlap=150
                )
                
                i = 1
                while i < len(page_blocks):
                    name = page_blocks[i].strip()
                    url = page_blocks[i+1].strip()
                    content = page_blocks[i+2].strip()
                    
                    cleaned_lines = [line.strip() for line in content.split("\n") if line.strip()]
                    clean_content = "\n".join(cleaned_lines)
                    
                    page_chunks = text_splitter.split_text(clean_content)
                    for chunk in page_chunks:
                        chunk_content = f"Page: {name}\nContent: {chunk}"
                        docs.append(Document(
                            page_content=chunk_content,
                            metadata={"source": name, "url": url}
                        ))
                    i += 3
                
                if docs:
                    db.add_documents(docs)
            else:
                # Crawl from scratch
                print("Website index and local text missing. Crawling nnrg.edu.in...")
                scrape_website()
                db = get_website_store()
                
        # 1. Retrieve a wider set of candidates
        docs_and_scores = db.similarity_search_with_score(question, k=15)
        if not docs_and_scores:
            return "Sorry, I couldn't find that information on the NNRG website."
            
        # 2. Extract keywords from user question
        keywords = extract_keywords(question)
        
        # 3. Score and filter candidates
        valid_candidates = []
        for doc, distance in docs_and_scores:
            similarity = 1.0 - (distance / 2.0)
            kw_score = score_document(doc, keywords)
            total_score = similarity + (kw_score * 0.1)
            
            # Filter completely unrelated pages: high distance and no keyword matches
            if distance > 0.95 and kw_score == 0:
                continue
                
            valid_candidates.append((doc, total_score, distance, kw_score))
            
        # 4. Sort candidates by total score descending
        valid_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 5. Return the top 3-5 most relevant chunks (we select top 4)
        final_candidates = valid_candidates[:4]
        
        if not final_candidates:
            return "Sorry, I couldn't find that information on the NNRG website."
            
        # Strict verification for unrelated topics
        if final_candidates[0][2] > 0.95 and final_candidates[0][3] == 0:
            return "Sorry, I couldn't find that information on the NNRG website."
            
        results = [doc.page_content for doc, _, _, _ in final_candidates]
        return "\n\n".join(results)
        
    except Exception as e:
        return f"Website data not found. Please run /scrape first. Error: {str(e)}"