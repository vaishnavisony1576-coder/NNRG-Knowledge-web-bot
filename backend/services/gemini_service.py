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
    elif any(k in query_lower for k in ["admission", "seat", "intake", "enrol", "eligibility", "process"]):
        topic = "admissions"
    elif any(k in query_lower for k in ["hostel", "girls hostel", "accommodation", "room"]):
        topic = "hostel"
    elif any(k in query_lower for k in ["transport", "bus", "route", "fleet", "rtc"]):
        topic = "transport"
    elif any(k in query_lower for k in ["contact", "phone", "email", "address", "location", "enquiry", "located", "where is"]):
        topic = "contact"

    # Keywords to keep for each topic
    topic_keywords = {
        "courses": ["course", "b.tech", "pharmacy", "mba", "m.tech", "degree", "intake", "computer science", "electronics", "mechanical", "civil", "academic"],
        "placements": ["placement", "recruit", "package", "salary", "cell", "job", "pvt.ltd", "pvt", "ltd", "corporation", "company", "companies", "tata", "genpact", "cognizant"],
        "admissions": ["admission", "seat", "intake", "merit", "tgicet", "eligible", "eligibility", "management", "nri", "allot", "enquiry", "document", "tgeapcet", "counseling", "counselling"],
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
        "a-category", "b-category", "national students",
        "aadhar card", "documents required", "read more",
        "route map", "about us", "about hyderabad", "faq",
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

    # 1. Check for specific topic overrides first
    # NNRG Location / Address Check
    if topic == "contact" or any(k in words for k in ["located", "address", "where is", "where"]):
        return (
            "NNRG Contact Information\n\n"
            "Nalla Narasimha Reddy Education Society's Group of Institutions\n\n"
            "Korremula X Road,\n"
            "Via Narapally,\n"
            "Chowdariguda,\n"
            "Ghatkesar,\n"
            "Medchal,\n"
            "Hyderabad – 500088\n\n"
            "• **Phone**: +91-9705353331, +91-9705353332\n"
            "• **Email**: admin@nnrg.edu.in, admissions@nnrg.edu.in"
        )

    # Placements Summarizer
    if topic == "placements":
        return (
            "Placement cell & Recruitment Activities\n\n"
            "The NNRG Placement Cell actively guides and prepares students for corporate success:\n"
            "• **Placement Cell**: Dedicated department managing student career guidance and recruitment drives.\n"
            "• **Training**: Structured programs for soft skills, quantitative aptitude, and technical preparation.\n"
            "• **Campus recruitment**: Regular placement drives hosting top IT, core engineering, and pharmacy enterprises.\n"
            "• **Industry interaction**: Guest lectures, industrial visits, and corporate seminars bridging academic gaps.\n"
            "• **Career guidance**: One-on-one counseling to assist students in identifying potential career paths."
        )

    # Admissions Process Explainer
    if topic == "admissions" or "admission" in query_lower:
        return (
            "Admission Process\n\n"
            "NNRG offers admissions to Engineering, Pharmacy, and Management programs:\n"
            "• **TGEAPCET**: State-level entrance exam required for undergraduate engineering and pharmacy admissions.\n"
            "• **Eligibility**: Candidates must meet academic criteria set by TSCHE and JNTU Hyderabad.\n"
            "• **Counseling**: Web-based counseling sessions administered by TSCHE for seat allocation.\n"
            "• **Admission steps**: Submit required certificates, pay the fee, and report to the campus for physical verification."
        )

    # Course Recommendations
    if any(k in query_lower for k in ["which course is better", "choose", "better course", "which branch", "cse or", "aiml or", "better placement"]):
        return (
            "Course Recommendation & Advice\n\n"
            "Choosing between B.Tech branches depends on your career goals and interests:\n"
            "• **Computer Science & Engineering (CSE)**: Offers broad foundational knowledge in software development, databases, and computer systems, making it highly versatile for various IT roles.\n"
            "• **AI & ML / Data Science**: Highly specialized programs focusing on machine learning algorithms, data engineering, and predictive modeling, ideal if you want a career specifically in artificial intelligence.\n"
            "• **Placements**: Both branches share excellent recruitment prospects, with CSE offering a wider variety of role profiles and AIML/DS attracting specialized high-paying roles.\n\n"
            "Recommendation: If you prefer a versatile IT foundation, go with CSE. If you are specifically passionate about machine learning and data science, specialize in AIML or DS."
        )

    # Founder / Foundation Details Check
    if any(k in query_lower for k in ["founder", "founded", "established", "who built", "who started"]):
        return (
            "NNRG Foundation Details\n\n"
            "Nalla Narasimha Reddy Education Society's Group of Institutions was established by the Nalla Narasimha Reddy Education Society:\n"
            "• **Founder**: Founded under the leadership of Shri Nalla Narasimha Reddy, who envisioned world-class technical education in Hyderabad.\n"
            "• **Establishment**: Started in 2009 with the primary objective of educating young men and women and preparing them for fast-changing global requirements.\n"
            "• **Affiliation**: Affiliated to JNTU Hyderabad and approved by AICTE, offering Contiguous Campus programs in Engineering, Pharmacy, and Management."
        )

    # Hostel facilities
    if topic == "hostel":
        return (
            "Hostel Facilities\n\n"
            "NNRG provides high-quality hostel accommodations within the campus:\n"
            "• **Girls Hostel**: Safe and secure housing in a 2-acre campus under continuous warden supervision.\n"
            "• **Amenities**: Spacious rooms, dedicated study halls, and 24/7 hot water facility.\n"
            "• **Dining**: Serves delicious, hygienic, and nutritious food in clean dining halls."
        )

    # Transport facilities
    if topic == "transport":
        return (
            "Transport Facilities\n\n"
            "The college operates a comprehensive fleet of buses covering key routes across Hyderabad:\n"
            "• **Fleet**: Fully-equipped buses driven by experienced and licensed drivers.\n"
            "• **RTC Connections**: Convenient pick-up and drop-off points connecting to local transit lines.\n"
            "• **Safety**: Designed to ensure a comfortable and safe commute for students and staff."
        )

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
    elif any(k in query_lower for k in ["summarize", "summary", "overview", "what is this document", "explain this document"]):
        pdf_topic = "summary"
    elif any(k in query_lower for k in ["conclusion", "concluding", "conclude"]):
        pdf_topic = "conclusion"
    elif any(k in query_lower for k in ["key points", "main points", "important points"]):
        pdf_topic = "key_points"
        
    # Dynamic fallback generator for PDF summaries if Gemini fails
    if pdf_topic == "summary" or pdf_topic == "objective":
        title = "Summary"
        ctx_lines = [l.strip("•-* \t") for l in context.split("\n") if l.strip() and not any(jk in l.lower() for jk in junk_keywords)]
        purpose = ctx_lines[0] if ctx_lines else "Details of the uploaded document."
        topics = list(dict.fromkeys(ctx_lines[1:4])) if len(ctx_lines) > 3 else ctx_lines
        concepts = list(dict.fromkeys(ctx_lines[4:7])) if len(ctx_lines) > 6 else []
        conclusion = ctx_lines[-1] if ctx_lines else "Consolidated report findings."
        
        bullet_points = [
            f"* **Main purpose**: {purpose}",
            f"* **Important topics**: {', '.join(topics) if topics else 'General concepts.'}",
            f"* **Key concepts**: {', '.join(concepts) if concepts else 'Technical details.'}",
            f"* **Final conclusion**: {conclusion}"
        ]
        return f"{title}\n\n" + "\n".join(bullet_points)
        
    elif pdf_topic == "conclusion":
        title = "Conclusion"
        ctx_lines = [l.strip() for l in context.split("\n") if l.strip()]
        body = ctx_lines[-1] if ctx_lines else "The document consolidates the key findings and results."
        return f"{title}\n\n{body}"
        
    elif pdf_topic == "key_points":
        title = "Key Points"
        ctx_lines = [l.strip("•-* \t") for l in context.split("\n") if l.strip() and not any(jk in l.lower() for jk in junk_keywords)]
        points = list(dict.fromkeys(ctx_lines))[:4]
        if not points:
            points = ["Integrate files and web indexing.", "Maintain strict validation rules.", "Deliver clean response summaries."]
        bullet_points = [f"* {p}" for p in points]
        return f"{title}\n\n" + "\n".join(bullet_points)

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