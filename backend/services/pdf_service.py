import os
import re
import shutil
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader
from dotenv import load_dotenv

# Load env variables using absolute path
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=dotenv_path)

# Setup paths
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_pdf_db")
ACTIVE_PDF_PATH = os.path.join(DATA_DIR, "active_pdf.txt")

# Initialize API key
api_key = os.getenv("GEMINI_API_KEY")


def set_active_pdf(filename: str):
    """Sets the currently active PDF filename."""
    ensure_dirs()
    with open(ACTIVE_PDF_PATH, "w", encoding="utf-8") as f:
        f.write(filename)


def get_active_pdf() -> str:
    """Gets the currently active PDF filename."""
    if os.path.exists(ACTIVE_PDF_PATH):
        with open(ACTIVE_PDF_PATH, "r", encoding="utf-8") as f:
            filename = f.read().strip()
            # Verify the file actually exists in uploads directory
            if filename and os.path.exists(os.path.join(UPLOADS_DIR, filename)):
                return filename
                
    # Fallback to the most recently modified PDF in uploads directory
    pdf_files = [f for f in os.listdir(UPLOADS_DIR) if f.lower().endswith(".pdf")]
    if pdf_files:
        # Sort by modification time descending
        pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOADS_DIR, x)), reverse=True)
        set_active_pdf(pdf_files[0])
        return pdf_files[0]
        
    return ""


def ensure_dirs():
    """Ensure uploads and data directories exist."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


def get_embeddings():
    """Returns the Google GenAI embedding function."""
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=api_key
    )


def get_vector_store():
    """Returns the persistent Chroma vector store instance."""
    ensure_dirs()
    return Chroma(
        collection_name="pdf_collection",
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_PATH
    )


def extract_text_from_pdf(filepath):
    """Extracts text page-by-page from a PDF file."""
    pages = []
    try:
        reader = PdfReader(filepath)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages.append({"text": text, "page_num": page_num + 1})
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
    return pages


def add_pdf_to_index(filename):
    """Extracts, chunks, and indexes a PDF file into ChromaDB."""
    filepath = os.path.join(UPLOADS_DIR, filename)
    if not os.path.exists(filepath):
        return
    
    pages = extract_text_from_pdf(filepath)
    if not pages:
        return
    
    documents = []
    for page in pages:
        doc = Document(
            page_content=page["text"],
            metadata={
                "source": filename,
                "page": page["page_num"]
            }
        )
        documents.append(doc)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )
    split_docs = text_splitter.split_documents(documents)
    
    db = get_vector_store()
    try:
        res = db.get()
        if res and res.get("ids"):
            db.delete(ids=res["ids"])
            print(f"Cleared {len(res['ids'])} existing PDF vector entries.")
    except Exception as e:
        print(f"Warning: Could not clear Chroma PDF collection: {e}")
        
    db.add_documents(split_docs)


def delete_pdf_from_index(filename):
    """Deletes all chunks associated with a specific filename from ChromaDB."""
    try:
        db = get_vector_store()
        db.delete(where={"source": filename})
        return f"Successfully removed '{filename}' chunks from Chroma index."
    except Exception as e:
        print(f"Error deleting '{filename}' from Chroma index: {e}")
        return str(e)


def get_indexed_filenames():
    """Retrieves list of unique source filenames currently indexed in ChromaDB."""
    try:
        db = get_vector_store()
        result = db.get(include=["metadatas"])
        metadatas = result.get("metadatas", [])
        filenames = set()
        for meta in metadatas:
            if meta and "source" in meta:
                filenames.add(meta["source"])
        return filenames
    except Exception as e:
        print(f"Error getting indexed filenames: {e}")
        return set()


def sync_pdf_index(force=False):
    """
    Synchronizes the uploads directory with the ChromaDB vector index.
    Deletes index entries for files removed from disk, and indexes new files.
    """
    ensure_dirs()
    
    if force:
        # Clear database folder to rebuild from scratch
        if os.path.exists(CHROMA_PATH):
            try:
                # Close Chroma client lock if possible (shutil might fail if file locked, 
                # but standard script start is fine)
                shutil.rmtree(CHROMA_PATH)
            except Exception as e:
                print(f"Warning: Could not delete Chroma DB folder directly: {e}")
                # Alternative is to fetch and delete everything
                try:
                    db = get_vector_store()
                    result = db.get()
                    if result and result.get("ids"):
                        db.delete(ids=result["ids"])
                except Exception as ex:
                    print(f"Could not clear Chroma via API: {ex}")

    # Files currently in uploads folder
    pdf_files = [f for f in os.listdir(UPLOADS_DIR) if f.lower().endswith(".pdf")]
    
    # Files currently in vector store
    indexed_files = get_indexed_filenames() if not force else set()
    
    updated = False
    
    # 1. Remove deleted files from index
    for filename in indexed_files:
        if filename not in pdf_files or force:
            print(f"Sync: Removing '{filename}' from Chroma index...")
            delete_pdf_from_index(filename)
            updated = True
            
    # 2. Add new files to index
    for filename in pdf_files:
        if filename not in indexed_files or force:
            print(f"Sync: Indexing '{filename}' into Chroma DB...")
            add_pdf_to_index(filename)
            updated = True
            
    if updated:
        return "PDF vector index updated successfully."
    return "PDF vector index is up to date."


def search_pdf_fallback(question):
    """
    Fallback keyword search over the raw PDF file if Chroma DB fails.
    """
    try:
        active_pdf = get_active_pdf()
        if not active_pdf:
            return "No PDF documents have been uploaded yet."
            
        filepath = os.path.join(UPLOADS_DIR, active_pdf)
        if not os.path.exists(filepath):
            return "Active PDF file not found on server."
            
        pages = extract_text_from_pdf(filepath)
        if not pages:
            return "Failed to extract text from the active PDF."
            
        # Extract keywords
        stopwords = {
            'what', 'is', 'are', 'the', 'of', 'in', 'to', 'for', 'a', 'an', 'on', 'from', 'with', 'by', 
            'about', 'how', 'do', 'does', 'can', 'you', 'i', 'we', 'they', 'he', 'she', 'it', 'me', 'us', 
            'them', 'who', 'where', 'when', 'why', 'which', 'there', 'their', 'our', 'your', 'my', 'and', 
            'or', 'but', 'if', 'any', 'some', 'all', 'please', 'tell', 'show', 'find', 'get', 'list', 'give'
        }
        words = []
        cleaned_query = "".join(char if char.isalnum() or char.isspace() else " " for char in question.lower())
        for word in cleaned_query.split():
            if word not in stopwords and len(word) > 2:
                words.append(word)
                
        candidates = []
        for page in pages:
            text = page["text"]
            # Split page text into smaller paragraph blocks
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            for p in paragraphs:
                p_lower = p.lower()
                matches = sum(1 for kw in words if kw in p_lower)
                if matches > 0:
                    candidates.append((p, matches, page["page_num"]))
                    
        if not candidates:
            # Fallback to returning first few pages if no keyword match
            first_chunks = []
            for page in pages[:3]:
                first_chunks.append(f"Page: {page['page_num']}\nContent: {page['text'][:500]}")
            return "\n\n".join(first_chunks)
            
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = candidates[:4]
        formatted_chunks = []
        for p, score, page_num in top_candidates:
            formatted_chunks.append(f"Page: {page_num}\nContent: {p}")
            
        return "\n\n".join(formatted_chunks)
    except Exception as e:
        print(f"Error in search_pdf_fallback: {e}")
        return "Sorry, I couldn't find that information in the uploaded PDF."


def search_pdf(question, top_k=5):
    """
    Performs vector similarity search on the PDF Chroma collection.
    Automatically index-segments to retrieve chunks based on page position or keyword relevance.
    """
    ensure_dirs()
    active_pdf = get_active_pdf()
    if not active_pdf:
        return "No PDF documents have been uploaded yet. Please upload PDF files to search them."

    try:
        try:
            db = get_vector_store()
            res = db.get(limit=1)
        except Exception as e:
            print(f"Chroma get failed: {e}. Falling back to PDF text file search.")
            return search_pdf_fallback(question)
        
        # If collection is empty, trigger a sync
        if not res or not res.get("ids"):
            try:
                sync_pdf_index()
                db = get_vector_store()
                res = db.get(limit=1)
            except Exception as e:
                print(f"Chroma sync failed: {e}. Falling back to PDF text file search.")
                return search_pdf_fallback(question)
                
            if not res or not res.get("ids"):
                return search_pdf_fallback(question)

        question_lower = question.lower().strip()

        # Retrieve all chunks belonging to the active PDF to do smart segment filtering
        try:
            all_result = db.get(where={"source": active_pdf}, include=["documents", "metadatas"])
            all_docs = []
            if all_result and all_result.get("documents"):
                for doc_text, meta in zip(all_result["documents"], all_result["metadatas"]):
                    all_docs.append(Document(page_content=doc_text, metadata=meta))
        except Exception as e:
            print(f"Error getting all PDF docs: {e}. Falling back to PDF text search.")
            return search_pdf_fallback(question)

        if not all_docs:
            return search_pdf_fallback(question)

        # Sort all documents by page number to represent original document flow
        all_docs.sort(key=lambda d: d.metadata.get("page", 1))

        # Custom Retrieval Rules
        selected_docs = []

        # Rule 1: "Summarize this PDF" -> Retrieve from beginning, middle, and end
        if any(k in question_lower for k in ["summarize this pdf", "summarise this pdf", "summarize the pdf", "summarise the pdf", "summary of this pdf", "summary of the pdf"]):
            n = len(all_docs)
            if n <= 6:
                selected_docs = all_docs
            else:
                mid = n // 2
                selected_docs = all_docs[:2] + all_docs[mid-1:mid+1] + all_docs[-2:]
                
        # Rule 2: "What is the conclusion?" -> Retrieve heading "Conclusion" or final semantic sections
        elif any(k in question_lower for k in ["conclusion", "concluding", "conclude"]):
            conclusion_chunks = []
            for doc in all_docs:
                if "conclusion" in doc.page_content.lower():
                    conclusion_chunks.append(doc)
            if conclusion_chunks:
                selected_docs = conclusion_chunks[:3]
            else:
                selected_docs = all_docs[-3:] # Grab the final semantic section

        # Rule 3: "What are the key points?" -> Retrieve major headings or top page sections
        elif any(k in question_lower for k in ["key points", "major points", "main points", "important points"]):
            heading_chunks = []
            for doc in all_docs:
                if re.search(r'\b[0-9]\.\s+[A-Z]', doc.page_content) or any(h in doc.page_content.lower() for h in ["introduction", "objective", "milestone", "deliverables", "requirements", "evaluation"]):
                    heading_chunks.append(doc)
            if len(heading_chunks) >= 3:
                selected_docs = heading_chunks[:5]
            else:
                selected_docs = all_docs[:4]

        # Rule 4: "What is this document about?" or "explain this document" -> Retrieve introduction/title (page 1)
        elif any(k in question_lower for k in ["document about", "pdf about", "explain this document", "explain the document", "what is this document"]):
            intro_chunks = [d for d in all_docs if d.metadata.get("page", 1) <= 2]
            if intro_chunks:
                selected_docs = intro_chunks[:3]
            else:
                selected_docs = all_docs[:3]

        # Fallback: standard similarity search
        if not selected_docs:
            try:
                selected_docs = db.similarity_search(question, k=top_k, filter={"source": active_pdf})
            except Exception as e:
                print(f"Similarity search failed in search_pdf: {e}. Falling back to PDF text search.")
                return search_pdf_fallback(question)

        results = []
        for doc in selected_docs:
            filename = doc.metadata.get("source", "Unknown PDF")
            page = doc.metadata.get("page", "?")
            results.append(
                f"--- Context from PDF Source File: '{filename}' (Page {page}) ---\n"
                f"{doc.page_content}"
            )
        return "\n\n".join(results)
        
    except Exception as e:
        print(f"Error in search_pdf: {e}")
        return search_pdf_fallback(question)
