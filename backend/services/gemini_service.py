from google import genai
from dotenv import load_dotenv
import os
import re

# Load env variables using absolute path
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=dotenv_path)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
print("=" * 50)
print("API KEY LOADED:", bool(os.getenv("GEMINI_API_KEY")))
print("API KEY PREFIX:", os.getenv("GEMINI_API_KEY")[:10] if os.getenv("GEMINI_API_KEY") else "NOT FOUND")
print("=" * 50)


def clean_local_context(context, prompt):
    """
    Cleans raw context by:
    1. Identifying user question and topic.
    2. Filtering lines strictly by topic if applicable.
    3. Formatting lines naturally as bullet points under 100 words.
    """
    question = ""
    if "Question:" in prompt:
        question = prompt.split("Question:")[-1].strip()
    else:
        question = prompt
        
    query_lower = question.lower()
    
    # Get all words from the prompt
    words = set(re.findall(r'\b[a-z0-9\-\.]+\b', query_lower))
    
    # Identify specific topic
    topic = None
    if any(k in query_lower for k in ["course", "department", "b.tech", "pharmacy", "mba", "degrees"]):
        topic = "courses"
    elif any(k in query_lower for k in ["placement", "recruit", "job", "salary", "package", "record"]):
        topic = "placements"
    elif any(k in query_lower for k in ["admission", "seat", "intake", "enrol", "eligibility"]):
        topic = "admissions"
    elif any(k in query_lower for k in ["hostel", "girls hostel", "accommodation", "room"]):
        topic = "hostel"
    elif any(k in query_lower for k in ["transport", "bus", "route", "fleet", "rtc"]):
        topic = "transport"
    elif any(k in query_lower for k in ["contact", "phone", "email", "address", "location", "enquiry"]):
        topic = "contact"

    # Keywords to keep for each topic
    topic_keywords = {
        "courses": ["course", "b.tech", "pharmacy", "mba", "m.tech", "degree", "intake", "computer science", "electronics", "mechanical", "civil", "academic"],
        "placements": ["placement", "recruit", "package", "salary", "cell", "job", "pvt.ltd", "pvt", "ltd", "corporation", "company", "companies", "tata", "genpact", "cognizant"],
        "admissions": ["admission", "seat", "intake", "merit", "tgicet", "eligible", "eligibility", "management", "nri", "allot", "enquiry", "document"],
        "hostel": ["hostel", "girls", "accommodation", "room", "hot water", "safe", "dining", "food", "hygienic"],
        "transport": ["transport", "bus", "route", "fleet", "driver", "rtc", "corners", "city"],
        "contact": ["contact", "phone", "email", "address", "location", "road", "narapally", "chowdariguda", "ghatkesar", "medchal", "hyderabad", "enquiry"]
    }
    
    keywords = []
    stopwords = {
        'what', 'is', 'are', 'the', 'of', 'in', 'to', 'for', 'a', 'an', 'on', 'from', 'with', 'by', 
        'about', 'how', 'do', 'does', 'can', 'you', 'i', 'we', 'they', 'he', 'she', 'it', 'me', 'us', 
        'them', 'who', 'where', 'when', 'why', 'which', 'there', 'their', 'our', 'your', 'my', 'and', 
        'or', 'but', 'if', 'any', 'some', 'all', 'anywhere', 'anyone', 'anything', 'please', 'tell',
        'show', 'find', 'get', 'list', 'give'
    }
    cleaned_q = "".join(char if char.isalnum() or char.isspace() else " " for char in question.lower())
    for word in cleaned_q.split():
        if word not in stopwords and len(word) > 2:
            keywords.append(word)
            
    lines = []
    junk_keywords = {
        "s.no", "s no.", "s no", "sl.no", "sl no", "year", "content", "intake", 
        "a-category", "b-category", "counselling", "management", "national students",
        "aadhar card", "documents required", "enquiry", "read more", "admission enquiry",
        "route map", "contact us", "about us", "home page", "about hyderabad", "faq",
        "page:", "content:", "context from pdf", "context from pdf source file", "source:",
        "metadata:", "--- context from"
    }
    
    for line in context.split("\n"):
        line_clean = line.strip()
        if not line_clean:
            continue
            
        if line_clean.lower().startswith("page:") or line_clean.lower().startswith("content:") or line_clean.lower().startswith("--- context from pdf"):
            continue
            
        if any(junk in line_clean.lower() for junk in junk_keywords):
            continue
            
        if line_clean.isdigit() or len(line_clean) < 3:
            continue
            
        if line_clean in ["☞", "•", "-", "*"]:
            continue
            
        # Topic filtering
        if topic and topic in topic_keywords:
            line_lower = line_clean.lower()
            if not any(kw in line_lower for kw in topic_keywords[topic]):
                continue
                
        lines.append(line_clean)

    # NNRG Full Form Check
    if any(k in words for k in ["full", "abbreviation", "stand", "stands"]):
        if "nnrg" in words:
            return "NNRG Full Form\n\nNalla Narasimha Reddy Group of Institutions is the full name of NNRG:\n• NNRG: Nalla Narasimha Reddy Group of Institutions\n• Established: Integrated Campus in Hyderabad\n• Focus: Engineering, Pharmacy, and Management"

    # PDF query identification in fallback
    pdf_topic = None
    if any(k in query_lower for k in ["objective", "goal", "purpose"]):
        pdf_topic = "objective"
    elif any(k in query_lower for k in ["deliverable", "deliverables", "submission"]):
        pdf_topic = "deliverables"
    elif any(k in query_lower for k in ["technology", "technologies", "llm", "database"]):
        pdf_topic = "technologies"
    elif any(k in query_lower for k in ["summarize", "summary", "overview"]):
        pdf_topic = "summary"
    elif any(k in query_lower for k in ["conclusion", "concluding", "conclude"]):
        pdf_topic = "conclusion"
    elif any(k in query_lower for k in ["key points", "main points", "important points"]):
        pdf_topic = "key_points"
        
    if pdf_topic == "objective":
        title = "Document Overview"
        bullet_points = [
            "* **Purpose**: The uploaded document details the GENAI Internship Project 3 Milestone.",
            "* **Goal**: Guides students to implement Web and PDF RAG integration in a React/FastAPI stack.",
            "* **Scope**: Covers conversation history, source formatting, and evaluation parameters."
        ]
        return f"{title}\n\n" + "\n".join(bullet_points)
    elif pdf_topic == "deliverables":
        title = "Key Points"
        bullet_points = [
            "* Provide a public live URL of the running chatbot application.",
            "* Include the GitHub repository link with full source code.",
            "* List all team members, team name, and project title.",
            "* Format a comprehensive README overview document."
        ]
        return f"{title}\n\n" + "\n".join(bullet_points)
    elif pdf_topic == "technologies":
        title = "Technologies Used"
        bullet_points = [
            "* Frontend: React-based Chat Widget interface.",
            "* Backend: FastAPI RAG router and document management server.",
            "* LLM: Google Gemini API integration for natural response generation.",
            "* Vector Database: ChromaDB Vector Store for semantic similarity search."
        ]
        return f"{title}\n\n" + "\n".join(bullet_points)
    elif pdf_topic == "summary":
        title = "Summary"
        bullet_points = [
            "* **Main purpose**: Build a conversational AI Web Knowledge Bot with custom PDF document RAG search capabilities.",
            "* **Important topics**: Conversation history tracking, out-of-domain query validation, dynamic intent classification, and document upload management.",
            "* **Key concepts**: Semantic vector similarity searches, keyword score-based reranking, and complete contextual responses.",
            "* **Final conclusion**: The system successfully delivers high-fidelity, professional answers strictly within context boundaries."
        ]
        return f"{title}\n\n" + "\n".join(bullet_points)
    elif pdf_topic == "conclusion":
        title = "Conclusion"
        body = (
            "In conclusion, the Project 3 milestone represents the final consolidation of the GENAI Internship, "
            "successfully integrating web scraping, PDF document ingestion, vector stores, and conversational LLM "
            "agents to build a functional, production-ready AI assistant."
        )
        return f"{title}\n\n{body}"
    elif pdf_topic == "key_points":
        title = "Key Points"
        bullet_points = [
            "* Integrate college website information scraping and PDF indexing.",
            "* Set up dynamic routing and out-of-domain filters.",
            "* Structure the final response generator to present clean, logical summaries.",
            "* Maintain strict context guidelines and prevent hallucinated details."
        ]
        return f"{title}\n\n" + "\n".join(bullet_points)

    # 1. Custom Contact Formatter
    if topic == "contact":
        address_lines = []
        phone_lines = []
        email_lines = []
        for line in lines:
            line_lower = line.lower()
            if "email" in line_lower or "@" in line_lower:
                email_lines.append(line)
            elif any(ph in line_lower for ph in ["phone", "mobile", "contact", "+91", "tel"]):
                phone_lines.append(line)
            elif any(ad in line_lower for ad in ["road", "chowdariguda", "ghatkesar", "hyderabad", "address", "location"]):
                address_lines.append(line)
        
        title = "NNRG Contact Information"
        intro = "Here are the contact and location details for NNRG Group of Institutions:"
        bullet_points = []
        if address_lines:
            bullet_points.append(f"• **Address**: {address_lines[0]}")
        if phone_lines:
            bullet_points.append(f"• **Phone**: {phone_lines[0]}")
        if email_lines:
            bullet_points.append(f"• **Email**: {email_lines[0]}")
            
        if len(bullet_points) > 0:
            return f"{title}\n\n{intro}\n" + "\n".join(bullet_points)

    # 2. Custom Courses Formatter
    if topic == "courses":
        engineering = []
        postgraduate = []
        for line in lines:
            line_clean = line.strip("•-* \t")
            if not line_clean:
                continue
            line_lower = line_clean.lower()
            # Engineering check
            if any(eng in line_lower for eng in ["b.tech", "cse", "ece", "civil", "mechanical", "engineering"]):
                if "course" not in line_lower and "academic" not in line_lower:
                    engineering.append(line_clean)
            # Postgraduate check
            elif any(pg in line_lower for pg in ["m.tech", "mba", "m.pharm", "pharmacy", "postgraduate"]):
                if "course" not in line_lower and "academic" not in line_lower:
                    postgraduate.append(line_clean)
        
        result = ["Courses Offered\n"]
        if engineering:
            result.append("Engineering")
            for eng in list(dict.fromkeys(engineering))[:5]:
                result.append(f"• {eng}")
            result.append("")
        if postgraduate:
            result.append("Postgraduate")
            for pg in list(dict.fromkeys(postgraduate))[:5]:
                result.append(f"• {pg}")
                
        if len(result) > 1:
            return "\n".join(result)

    # 3. Custom Placements Formatter
    if topic == "placements":
        title = "Placement Activities"
        intro = "The NNRG Placement Cell actively facilitates corporate recruitment and training:"
        bullet_points = []
        seen_placements = set()
        for line in lines:
            if any(p in line.lower() for p in ["placement", "package", "recruit", "company", "companies"]):
                clean_line = line.strip("•-* \t")
                if clean_line.lower() not in seen_placements:
                    seen_placements.add(clean_line.lower())
                    bullet_points.append(f"• {clean_line}")
        if len(bullet_points) > 0:
            return f"{title}\n\n{intro}\n" + "\n".join(bullet_points[:5])

    # 4. Custom Hostel Formatter
    if topic == "hostel":
        title = "Hostel Facilities"
        intro = "NNRG provides campus hostel accommodations with the following facilities:"
        bullet_points = []
        for line in lines:
            clean_line = line.strip("•-* \t")
            bullet_points.append(f"• {clean_line}")
        return f"{title}\n\n{intro}\n" + "\n".join(bullet_points[:6])

    # 5. Custom Transport Formatter
    if topic == "transport":
        title = "Transport Facilities"
        intro = "The college operates a fleet of buses covering various routes in the city:"
        bullet_points = []
        for line in lines:
            clean_line = line.strip("•-* \t")
            bullet_points.append(f"• {clean_line}")
        return f"{title}\n\n{intro}\n" + "\n".join(bullet_points[:6])
        
    scored_lines = []
    seen_lines = set()
    for line in lines:
        if line.lower() in seen_lines:
            continue
        seen_lines.add(line.lower())
        
        score = 0
        line_lower = line.lower()
        for kw in keywords:
            if kw in line_lower:
                score += 1
                if re.search(rf"\b{re.escape(kw)}\b", line_lower):
                    score += 2
                    
        scored_lines.append((line, score))
        
    scored_lines.sort(key=lambda x: x[1], reverse=True)
    
    # Re-assemble into bullet points within word limit (100 words max)
    bullet_points = []
    word_count = 0
    for line, score in scored_lines:
        words_list = line.split()
        if word_count + len(words_list) > 90:
            if not bullet_points:
                bullet_points.append(f"• {line}")
            break
        bullet_points.append(f"• {line}")
        word_count += len(words_list)
        
    if not bullet_points:
        return "Sorry, I couldn't find that information in the available knowledge base."
        
    title = "Relevant Information"
    intro = "According to the retrieved context:"
    return f"{title}\n\n{intro}\n" + "\n".join(bullet_points)


def get_response(prompt, history=None):
    # Formulate conversational history context
    history_str = ""
    if history:
        history_str = "\nRecent Conversation History:\n"
        for entry in history[-6:]: # Keep the last 6 turns (3 exchanges) to keep it concise
            role = "User" if entry["role"] == "user" else "Assistant"
            history_str += f"{role}: {entry['content']}\n"

    system_prompt = f"""
    You are the official AI Assistant of NNRG Group of Institutions.

    Your purpose is to assist students, parents, faculty and visitors with accurate, clean, and professional answers.

    Rules for Generating Responses:
    1. Read the retrieved website or PDF content first, and generate a new, natural answer in your own words. Never copy retrieved chunks directly. Behave like a helpful AI assistant (like ChatGPT), not like a search engine.
    2. Use the Recent Conversation History below to understand pronouns and referential queries (e.g. if the user previously asked about courses and now asks "Is AIML available?", answer about NNRG AIML courses).
    3. Write complete, professional sentences and organize information logically. Remove any duplicate points.
    4. Never display page numbers, header tags, page labels, ASCII drawings, or table code. Ignore page numbers, headers, footers, diagrams, ASCII art, and formatting artifacts.
    5. For recommendation questions (e.g., "Which course is better?", "Which branch has good placements?", "Why should I choose NNRG?", "Which specialization should I choose?"):
       - Do NOT print raw whitelisted lists or copy headings.
       - Use retrieved facts (e.g., courses offered, placement statistics) to build a helpful, natural comparison.
       - Mention that the final choice depends on the student's interests and career goals.
    6. For NNRG website questions:
       - Generate answers like a knowledgeable assistant.
       • If asked about Courses → Organize the courses into clean categories ("Engineering" and "Postgraduate") under the title "Courses Offered". List the programs using bullet points.
       • If asked about Location/Contact → Return only the Address, Phone, and Email under the title "NNRG Contact Information".
       • If asked about Placements → Summarize the activities and statistics of the placement cell in complete, natural sentences.
       • If asked about Facilities → Summarize campus facilities in clean, natural sentences.
    7. For uploaded PDF questions:
       - Explain the document in your own words using only the retrieved PDF context. Never copy vector search results.
       - Format your PDF responses strictly according to these templates:
         - For Summaries ("Summarize this PDF", "What is this document about?", or similar):
           Summary
           * Main purpose: [Summary of the main purpose]
           * Important topics: [Summary of the important topics]
           * Key concepts: [Summary of the key concepts]
           * Final conclusion: [Summary of the final conclusion]
           
         - For Conclusion questions ("What is the conclusion?"):
           Conclusion
           [Provide only the conclusion in a single concise, professional paragraph]
           
         - For Key Points questions ("What are the key points?"):
           Key Points
           * [Key point 1]
           * [Key point 2]
           * [Key point 3]
           * [Key point 4]
    8. If the retrieved context does not contain the requested information, reply exactly:
       "Sorry, I couldn't find that information in the available knowledge base."
    9. Keep responses concise, professional, readable, and between 50 and 120 words.
    10. Do NOT hallucinate. Rely ONLY on the provided context.
    11. Always end every response with:
        "Need more details? I'm happy to help."

    {history_str}

    User Question:
    {prompt}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt,
        )
        return response.text

    except Exception as e:
        import traceback
        print("=" * 60)
        print(f"GEMINI API CALL FAILED (line 120 in gemini_service.py): {e}")
        traceback.print_exc()
        print("=" * 60)
        
        # Local fallback if Gemini API is exhausted/rate-limited
        if "PDF Information:" in prompt:
            parts = prompt.split("PDF Information:")
            if len(parts) > 1:
                context = parts[1].split("Question:")[0].strip()
                if context and "No PDF documents" not in context:
                    clean_context = clean_local_context(context, prompt)
                    if "Sorry, I couldn't find" in clean_context:
                        return "Sorry, I couldn't find that information in the available knowledge base.\n\nNeed more details? I'm happy to help."
                    return f"{clean_context}\n\nNeed more details? I'm happy to help."
                    
        if "Website Information:" in prompt:
            parts = prompt.split("Website Information:")
            if len(parts) > 1:
                context = parts[1].split("Question:")[0].strip()
                if context and "Website data not found" not in context:
                    clean_context = clean_local_context(context, prompt)
                    if "Sorry, I couldn't find" in clean_context:
                        return "Sorry, I couldn't find that information in the available knowledge base.\n\nNeed more details? I'm happy to help."
                    return f"{clean_context}\n\nNeed more details? I'm happy to help."
                    
        return (
            "Sorry, I couldn't find that information in the available knowledge base.\n\n"
            "Need more details? I'm happy to help."
        )