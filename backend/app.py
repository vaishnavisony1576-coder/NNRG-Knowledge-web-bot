import os
import re
import time
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from services.gemini_service import get_response
from services.intent_service import detect_intent
from services.website_service import scrape_website, search_website
from services.pdf_service import search_pdf, sync_pdf_index, UPLOADS_DIR, set_active_pdf, get_active_pdf
from services.context_service import filter_and_rank_chunks

app = FastAPI(title="NNRG RAG Backend")

# Conversational memory state
CHAT_HISTORY = []
PREVIOUS_RAG_MODE = "general"


def get_contextual_prompt(prompt: str) -> str:
    """Concatenates the previous user question to the current prompt to keep context highly focused."""
    if CHAT_HISTORY:
        for entry in reversed(CHAT_HISTORY):
            if entry["role"] == "user":
                return entry["content"] + " " + prompt
    return prompt

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nnrg-knowledge-web-bot.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_query_related_local(prompt: str) -> bool:
    """Determines whether a question is locally related by whitelist/blacklist keywords."""
    prompt_clean = prompt.lower().strip()
    
    # 1. Whitelist greetings/small talk to keep conversation natural
    greetings = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how are you", "who are you", "help", "test"}
    if prompt_clean in greetings or len(prompt_clean) < 4:
        return True
        
    # Get all words from the prompt using regex
    words = set(re.findall(r'\b[a-z0-9\-\.]+\b', prompt_clean))
    
    # 2. Check blacklist first (unrelated categories)
    blacklisted_keywords = {
        # General knowledge / sports / celebs / politics / weather
        "weather", "celebrity", "celebrities", "politics", "president", "prime minister", "governor",
        "sports", "cricket", "football", "tennis", "basketball", "olympics", "movie", "movies", "actor", "actress",
        # Programming & General tech
        "programming", "coding", "write a code", "write a function", "algorithm", "quicksort", "binary search",
        "bubble sort", "javascript", "python", "html", "css", "database", "sql", "java", "c++",
        # General non-NNRG info
        "capital of", "population of", "distance from",
        # Other colleges/universities
        "cbit", "vnr", "griet", "kmit", "vasavi", "mgit", "gokaraju", "chaitanya bharathi", "osmania university", "ou",
        "iit madras", "iit bombay", "iit delhi", "iit", "bits pilani"
    }
    
    for black in blacklisted_keywords:
        if " " in black:
            if black in prompt_clean:
                return False
        else:
            if black in words:
                return False
        
    # 3. Check whitelist (related to NNRG or PDF files)
    nnrg_keywords = {
        "nnrg", "nalla", "narasimha", "reddy", "korremula", "narapally", "chowdariguda", "ghatkesar", "medchal",
        "admissions", "admission", "placement", "placements", "hostel", "transport", "bus", "buses", "route", "routes",
        "canteen", "library", "fees", "fee", "principal", "chairman", "campus", "course", "courses", "syllabus", "curriculum",
        "b.tech", "btech", "pharmacy", "b.pharm", "bpharm", "mba", "m.tech", "mtech", "m.pharm", "mpharm",
        "pdf", "document", "file", "uploaded", "prospectus", "brochure", "enquiry", "college", "institutions", "institution",
        "aiml", "vaishnavi", "specialization", "better", "choose", "why"
    }
    
    for white in nnrg_keywords:
        if " " in white:
            if white in prompt_clean:
                return True
        else:
            if white in words:
                return True
                
    return False


def is_query_related(prompt: str) -> bool:
    """Combines local keyword check and database similarity scoring checks."""
    # 1. Quick local check first
    if is_query_related_local(prompt):
        return True
        
    # 2. Check PDF vector database similarity if active document is present
    try:
        from services.pdf_service import get_vector_store, UPLOADS_DIR
        active_pdf = get_active_pdf()
        if active_pdf:
            db = get_vector_store()
            res = db.get(limit=1)
            if res and res.get("ids"):
                # Search the PDF store for relevant matches filtering by active PDF
                docs_and_scores = db.similarity_search_with_score(prompt, k=3, filter={"source": active_pdf})
                for doc, score in docs_and_scores:
                    if score <= 0.80:
                        return True
    except Exception as e:
        print(f"Error checking PDF db relatedness: {e}")
        
    # 3. Check Website vector database similarity
    try:
        from services.website_service import get_website_store
        db_web = get_website_store()
        res_web = db_web.get(limit=1)
        if res_web and res_web.get("ids"):
            # Search the website store for relevant matches
            docs_and_scores_web = db_web.similarity_search_with_score(prompt, k=3)
            for doc, score in docs_and_scores_web:
                if score <= 0.80:
                    return True
    except Exception as e:
        print(f"Error checking website db relatedness: {e}")
        
    return False


@app.on_event("startup")
def startup_event():
    """Trigger PDF vector index sync when the application starts."""
    try:
        msg = sync_pdf_index()
        print(f"Startup Sync: {msg}")
    except Exception as e:
        print(f"Startup Sync failed: {e}")


@app.get("/")
def home():
    return {
        "message": "NNRG Backend is running successfully with LangChain & ChromaDB.",
        "endpoints": {
            "chat": "/chat?prompt={prompt}&mode={general|pdf|website}",
            "scrape": "/scrape",
            "upload_dashboard": "/upload-gui",
            "upload_file": "/upload (POST)",
            "list_files": "/uploaded-files",
            "delete_file": "/delete-file/{filename} (DELETE)",
            "reindex": "/reindex (POST)"
        }
    }


@app.get("/chat")
def chat(prompt: str, mode: str = "general"):
    contextual_prompt = get_contextual_prompt(prompt)

    # Pre-Gemini validation check for query relevance using contextual prompt
    if not is_query_related(contextual_prompt):
        return {"response": "Sorry, I can only answer questions related to NNRG Group of Institutions or the currently uploaded PDF document."}
        
    # Check if query matches the PDF database with high confidence to trigger automatic routing (evaluate on contextual prompt)
    pdf_has_match = False
    try:
        from services.pdf_service import get_vector_store, UPLOADS_DIR
        active_pdf = get_active_pdf()
        if active_pdf:
            db = get_vector_store()
            res = db.get(limit=1)
            if res and res.get("ids"):
                docs_and_scores = db.similarity_search_with_score(contextual_prompt, k=1, filter={"source": active_pdf})
                if docs_and_scores and docs_and_scores[0][1] <= 0.85:
                    pdf_has_match = True
    except Exception as e:
        print(f"Error checking PDF relevance: {e}")

    # Automatically select the correct knowledge source based on the user's query (detect on contextual prompt)
    detected_intent = detect_intent(contextual_prompt)
    
    global PREVIOUS_RAG_MODE
    if detected_intent in ["pdf", "website"]:
        chosen_mode = detected_intent
    elif pdf_has_match:
        chosen_mode = "pdf"
    elif mode in ["pdf", "website"]:
        chosen_mode = mode
    elif PREVIOUS_RAG_MODE in ["pdf", "website"]:
        # Inherit previous mode for conversational follow-ups
        chosen_mode = PREVIOUS_RAG_MODE
    else:
        chosen_mode = "general"

    PREVIOUS_RAG_MODE = chosen_mode

    if chosen_mode == "pdf":
        pdf_content = search_pdf(contextual_prompt)
        if "No PDF documents have been uploaded" in pdf_content:
            answer = "📄 PDF mode is active, but no documents have been uploaded yet. Please upload PDF files first at http://127.0.0.1:8000/upload-gui"
        else:
            pdf_content = filter_and_rank_chunks(pdf_content, contextual_prompt, "pdf")
            if "Sorry, I couldn't find that information" in pdf_content:
                answer = pdf_content
            else:
                answer = get_response(
                    f"""
Use ONLY the information below from the uploaded PDF documents to answer.
If the documents do not contain the answer, say "Sorry, I don't have that information in the available knowledge base."

PDF Information:
{pdf_content}

Question:
{prompt}
""",
                    history=CHAT_HISTORY
                )
    elif chosen_mode == "website":
        website_content = search_website(contextual_prompt)
        if "Website data not found" in website_content:
            answer = "🌐 Website RAG mode is active, but no website data was found. Please scrape the website first at http://127.0.0.1:8000/scrape"
        else:
            website_content = filter_and_rank_chunks(website_content, contextual_prompt, "website")
            if "Sorry, I couldn't find that information" in website_content:
                answer = website_content
            else:
                answer = get_response(
                    f"""
Use ONLY the NNRG website information below to answer.
If the information does not contain the answer, say "Sorry, I don't have that information in the available knowledge base."

Website Information:
{website_content}

Question:
{prompt}
""",
                    history=CHAT_HISTORY
                )
    else:
        answer = get_response(prompt, history=CHAT_HISTORY)

    # Record the conversation turn
    CHAT_HISTORY.append({"role": "user", "content": prompt})
    CHAT_HISTORY.append({"role": "model", "content": answer})

    return {"response": answer}


@app.get("/scrape")
def scrape():
    return {
        "message": scrape_website()
    }


@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files (.pdf) are allowed.")
    
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Trigger indexing sync in ChromaDB
        sync_msg = sync_pdf_index()
        set_active_pdf(file.filename)
        CHAT_HISTORY.clear()
        global PREVIOUS_RAG_MODE
        PREVIOUS_RAG_MODE = "general"
        return {
            "message": f"Successfully uploaded and indexed '{file.filename}'.",
            "sync_status": sync_msg
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload and index file: {str(e)}")


@app.get("/uploaded-files")
def get_uploaded_files():
    if not os.path.exists(UPLOADS_DIR):
        return {"files": []}
    files = []
    for name in os.listdir(UPLOADS_DIR):
        if name.lower().endswith(".pdf"):
            filepath = os.path.join(UPLOADS_DIR, name)
            size = os.path.getsize(filepath)
            mtime = os.path.getmtime(filepath)
            files.append({
                "filename": name,
                "size_kb": round(size / 1024, 2),
                "uploaded_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
            })
    return {"files": files}


@app.delete("/delete-file/{filename}")
def delete_file(filename: str):
    file_path = os.path.join(UPLOADS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    try:
        os.remove(file_path)
        # Update the index to remove references to the deleted file from Chroma DB
        sync_msg = sync_pdf_index()
        CHAT_HISTORY.clear()
        global PREVIOUS_RAG_MODE
        PREVIOUS_RAG_MODE = "general"
        return {
            "message": f"Successfully deleted '{filename}' from server.",
            "sync_status": sync_msg
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@app.post("/reindex")
def reindex():
    try:
        msg = sync_pdf_index(force=True)
        return {"message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild index: {str(e)}")


@app.get("/upload-gui", response_class=HTMLResponse)
def upload_gui():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NNRG AI - RAG Document Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #0d6efd;
                --primary-glow: rgba(13, 110, 253, 0.15);
                --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
                --glass-bg: rgba(30, 41, 59, 0.7);
                --glass-border: rgba(255, 255, 255, 0.08);
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --success: #10b981;
                --danger: #ef4444;
            }

            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: 'Outfit', sans-serif;
            }

            body {
                background: var(--bg-gradient);
                color: var(--text-main);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 2rem 1rem;
            }

            .container {
                width: 100%;
                max-width: 900px;
                display: flex;
                flex-direction: column;
                gap: 2rem;
            }

            header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1.5rem 2rem;
                background: var(--glass-bg);
                backdrop-filter: blur(12px);
                border: 1px solid var(--glass-border);
                border-radius: 16px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            }

            .logo-section {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }

            .logo-icon {
                font-size: 2rem;
            }

            h1 {
                font-size: 1.5rem;
                font-weight: 700;
                letter-spacing: -0.5px;
                background: linear-gradient(to right, #60a5fa, #a78bfa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .status-badge {
                font-size: 0.85rem;
                font-weight: 500;
                padding: 0.4rem 0.8rem;
                border-radius: 20px;
                background: rgba(16, 185, 129, 0.15);
                color: #34d399;
                border: 1px solid rgba(16, 185, 129, 0.2);
                display: flex;
                align-items: center;
                gap: 0.4rem;
            }

            .pulse {
                width: 8px;
                height: 8px;
                background: #10b981;
                border-radius: 50%;
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
                animation: pulsing 1.6s infinite;
            }

            @keyframes pulsing {
                0% {
                    transform: scale(0.95);
                    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
                }
                70% {
                    transform: scale(1);
                    box-shadow: 0 0 0 6px rgba(16, 185, 129, 0);
                }
                100% {
                    transform: scale(0.95);
                    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
                }
            }

            .card {
                background: var(--glass-bg);
                backdrop-filter: blur(12px);
                border: 1px solid var(--glass-border);
                border-radius: 20px;
                padding: 2rem;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            }

            .dropzone {
                border: 2px dashed rgba(255, 255, 255, 0.15);
                border-radius: 14px;
                padding: 3rem 2rem;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                background: rgba(30, 41, 59, 0.3);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
            }

            .dropzone:hover, .dropzone.dragover {
                border-color: var(--primary);
                background: rgba(13, 110, 253, 0.05);
                box-shadow: 0 0 20px var(--primary-glow);
            }

            .upload-icon {
                font-size: 3rem;
                color: #60a5fa;
                transition: transform 0.3s ease;
            }

            .dropzone:hover .upload-icon {
                transform: translateY(-5px);
            }

            .dropzone p {
                font-size: 1.1rem;
                color: var(--text-main);
                font-weight: 500;
            }

            .dropzone span {
                font-size: 0.875rem;
                color: var(--text-muted);
            }

            #fileInput {
                display: none;
            }

            .btn {
                padding: 0.6rem 1.2rem;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                border: none;
                transition: all 0.2s ease;
                font-size: 0.95rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .btn-primary {
                background: var(--primary);
                color: white;
            }

            .btn-primary:hover {
                background: #2563eb;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
            }

            .btn-secondary {
                background: rgba(255, 255, 255, 0.08);
                color: var(--text-main);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .btn-secondary:hover {
                background: rgba(255, 255, 255, 0.15);
            }

            .btn-danger {
                background: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.2);
                padding: 0.4rem 0.8rem;
                font-size: 0.85rem;
            }

            .btn-danger:hover {
                background: var(--danger);
                color: white;
            }

            .section-title {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
            }

            .section-title h2 {
                font-size: 1.25rem;
                font-weight: 600;
                color: var(--text-main);
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .file-table-container {
                overflow-x: auto;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }

            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }

            th, td {
                padding: 1rem 1.25rem;
            }

            th {
                background: rgba(15, 23, 42, 0.6);
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: var(--text-muted);
                font-weight: 600;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }

            td {
                background: rgba(30, 41, 59, 0.2);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                font-size: 0.95rem;
            }

            tr:last-child td {
                border-bottom: none;
            }

            .file-name {
                font-weight: 500;
                color: #60a5fa;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .no-files {
                text-align: center;
                padding: 3rem;
                color: var(--text-muted);
                font-size: 1rem;
                background: rgba(30, 41, 59, 0.2);
            }

            .notification {
                position: fixed;
                bottom: 24px;
                right: 24px;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                background: var(--glass-bg);
                backdrop-filter: blur(8px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.3);
                border: 1px solid var(--glass-border);
                transform: translateY(150%);
                transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                z-index: 10000;
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }

            .notification.show {
                transform: translateY(0);
            }

            .notification.success {
                border-left: 4px solid var(--success);
            }

            .notification.error {
                border-left: 4px solid var(--danger);
            }

            .loader-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(15, 23, 42, 0.8);
                backdrop-filter: blur(4px);
                z-index: 9999;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                gap: 1.5rem;
            }

            .spinner {
                width: 50px;
                height: 50px;
                border: 3px solid rgba(96, 165, 250, 0.1);
                border-top: 3px solid #60a5fa;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .loader-text {
                font-weight: 500;
                color: var(--text-main);
                font-size: 1.1rem;
            }

            .dashboard-actions {
                display: flex;
                gap: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="logo-section">
                    <span class="logo-icon">🤖</span>
                    <div>
                        <h1>NNRG AI Document Dashboard</h1>
                        <span style="font-size: 0.8rem; color: var(--text-muted)">Manage PDF Knowledge Files for Chat RAG (LangChain + ChromaDB)</span>
                    </div>
                </div>
                <div class="status-badge">
                    <div class="pulse"></div>
                    <span>Service Online</span>
                </div>
            </header>

            <div class="card">
                <div class="dropzone" id="dropzone">
                    <div class="upload-icon">📁</div>
                    <p>Drag & drop your PDF document here</p>
                    <span>or click to browse local files</span>
                    <button class="btn btn-primary" style="margin-top: 0.5rem;">Select PDF</button>
                    <input type="file" id="fileInput" accept=".pdf">
                </div>
            </div>

            <div class="card">
                <div class="section-title">
                    <h2>📋 Uploaded Documents</h2>
                    <div class="dashboard-actions">
                        <button class="btn btn-secondary" id="btnRefresh" title="Refresh List">🔄 Refresh</button>
                        <button class="btn btn-secondary" id="btnReindex" title="Rebuild Vector Index">⚙️ Rebuild Index</button>
                    </div>
                </div>

                <div class="file-table-container">
                    <table id="fileTable">
                        <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Size</th>
                                <th>Uploaded At</th>
                                <th style="text-align: right;">Action</th>
                            </tr>
                        </thead>
                        <tbody id="fileListBody">
                            <!-- Populated dynamically via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="loader-overlay" id="loader">
            <div class="spinner"></div>
            <div class="loader-text" id="loaderText">Uploading & indexing document...</div>
        </div>

        <div class="notification" id="notification">
            <span id="notificationIcon"></span>
            <span id="notificationMessage"></span>
        </div>

        <script>
            const dropzone = document.getElementById('dropzone');
            const fileInput = document.getElementById('fileInput');
            const fileListBody = document.getElementById('fileListBody');
            const loader = document.getElementById('loader');
            const loaderText = document.getElementById('loaderText');
            const notification = document.getElementById('notification');
            const notificationMessage = document.getElementById('notificationMessage');
            const notificationIcon = document.getElementById('notificationIcon');
            const btnRefresh = document.getElementById('btnRefresh');
            const btnReindex = document.getElementById('btnReindex');

            // Show notifications
            function showToast(message, isSuccess = true) {
                notificationMessage.textContent = message;
                notificationIcon.textContent = isSuccess ? '✅' : '❌';
                notification.className = `notification show ${isSuccess ? 'success' : 'error'}`;
                setTimeout(() => {
                    notification.classList.remove('show');
                }, 4000);
            }

            function showLoader(text) {
                loaderText.textContent = text;
                loader.style.display = 'flex';
            }

            function hideLoader() {
                loader.style.display = 'none';
            }

            // Drag and drop event handlers
            ['dragenter', 'dragover'].forEach(eventName => {
                dropzone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    dropzone.classList.add('dragover');
                }, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropzone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    dropzone.classList.remove('dragover');
                }, false);
            });

            dropzone.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                if (files.length > 0) {
                    uploadFile(files[0]);
                }
            });

            dropzone.addEventListener('click', () => {
                fileInput.click();
            });

            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) {
                    uploadFile(fileInput.files[0]);
                }
            });

            // Upload function
            async function uploadFile(file) {
                if (!file.name.toLowerCase().endsWith('.pdf')) {
                    showToast('Only PDF files are supported.', false);
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                showLoader('Uploading and indexing PDF file in ChromaDB...');
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();
                    if (response.ok) {
                        showToast(`Successfully uploaded and indexed ${file.name}`);
                        loadFiles();
                    } else {
                        showToast(data.detail || 'Upload failed.', false);
                    }
                } catch (error) {
                    console.error('Error uploading:', error);
                    showToast('Network error during upload.', false);
                } finally {
                    hideLoader();
                    fileInput.value = ''; // clear input
                }
            }

            // Fetch and list uploaded files
            async function loadFiles() {
                try {
                    const response = await fetch('/uploaded-files');
                    const data = await response.json();
                    
                    fileListBody.innerHTML = '';
                    
                    if (!data.files || data.files.length === 0) {
                        fileListBody.innerHTML = `
                            <tr>
                                <td colspan="4" class="no-files">
                                    📂 No PDF documents uploaded yet. Drag one above to start!
                                </td>
                            </tr>
                        `;
                        return;
                    }

                    data.files.forEach(file => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>
                                <div class="file-name">
                                    <span>📄</span>
                                    <span>${escapeHTML(file.filename)}</span>
                                </div>
                            </td>
                            <td>${file.size_kb} KB</td>
                            <td>${file.uploaded_at}</td>
                            <td style="text-align: right;">
                                <button class="btn btn-danger" onclick="deleteFile('${escapeJS(file.filename)}')">
                                    🗑️ Delete
                                </button>
                            </td>
                        `;
                        fileListBody.appendChild(tr);
                    });
                } catch (error) {
                    console.error('Error loading files:', error);
                    showToast('Error loading uploaded files.', false);
                }
            }

            // Delete file function
            async function deleteFile(filename) {
                if (!confirm(`Are you sure you want to delete ${filename}?`)) {
                    return;
                }

                showLoader(`Deleting ${filename} and updating ChromaDB index...`);
                try {
                    const response = await fetch(`/delete-file/${encodeURIComponent(filename)}`, {
                        method: 'DELETE'
                    });

                    const data = await response.json();
                    if (response.ok) {
                        showToast(`Deleted ${filename} successfully.`);
                        loadFiles();
                    } else {
                        showToast(data.detail || 'Deletion failed.', false);
                    }
                } catch (error) {
                    console.error('Error deleting:', error);
                    showToast('Network error during deletion.', false);
                } finally {
                    hideLoader();
                }
            }

            // Force rebuild index
            btnReindex.addEventListener('click', async () => {
                showLoader('Rebuilding Chroma vector database from scratch...');
                try {
                    const response = await fetch('/reindex', {
                        method: 'POST'
                    });
                    const data = await response.json();
                    if (response.ok) {
                        showToast('Chroma vector database rebuilt successfully!');
                    } else {
                        showToast(data.detail || 'Index rebuild failed.', false);
                    }
                } catch (error) {
                    console.error('Error re-indexing:', error);
                    showToast('Network error during re-indexing.', false);
                } finally {
                    hideLoader();
                }
            });

            btnRefresh.addEventListener('click', () => {
                loadFiles();
                showToast('Documents list refreshed.');
            });

            // Utilities
            function escapeHTML(str) {
                return str.replace(/[&<>'"]/g, 
                    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
                );
            }

            function escapeJS(str) {
                return str.replace(/'/g, "\\'");
            }

            // Initial load
            loadFiles();
        </script>
    </body>
    </html>
    """
    return html_content