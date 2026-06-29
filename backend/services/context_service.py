import re

def filter_and_rank_chunks(context_str: str, prompt: str, mode: str) -> str:
    """
    Ranks, scores, and filters retrieved chunks based on keyword matching and query intent.
    If no relevant chunks remain, returns the default fallback.
    """
    if not context_str or "Sorry, I couldn't find" in context_str or "Website data not found" in context_str:
        return "Sorry, I couldn't find that information in the available knowledge base."

    # 1. Parse individual chunks from the combined text
    chunks = []
    if mode == "pdf":
        # PDF search results are formatted with headers: --- Context from PDF Source File: ...
        parts = context_str.split("\n\n--- Context from PDF")
        for i, part in enumerate(parts):
            chunk_content = part.strip()
            if not chunk_content:
                continue
            if i > 0:
                chunk_content = "--- Context from PDF" + chunk_content
            chunks.append(chunk_content)
    else:
        # Website search results are split by \n\n
        parts = context_str.split("\n\n")
        for part in parts:
            chunk_content = part.strip()
            if chunk_content:
                chunks.append(chunk_content)

    if not chunks:
        return "Sorry, I couldn't find that information in the available knowledge base."

    # 2. Extract words from prompt
    prompt_lower = prompt.lower().strip()
    words = set(re.findall(r'\b[a-z0-9\-\.]+\b', prompt_lower))

    # Identify search intents for acronyms and technology questions
    is_abbreviation_query = any(k in words for k in ["abbreviation", "stand", "stands", "full", "form", "acronym"])
    is_tech_query = any(k in words for k in ["tech", "technology", "technologies", "framework", "library", "libraries", "tool", "tools", "stack"])
    is_generic_query = mode == "pdf" and any(k in prompt_lower for k in [
        "summarize", "summary", "overview", "conclusion", "concluding", 
        "conclude", "key points", "main points", "important points", 
        "document about", "pdf about", "explain this document", 
        "explain the document", "what is this document", "what are the key"
    ])

    scored_chunks = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = 0

        # Heuristic 1: Prioritize exact acronym or full institution name for abbreviations
        if is_abbreviation_query:
            if "nnrg" in chunk_lower or "nalla narasimha reddy" in chunk_lower:
                score += 50

        # Heuristic 2: Prioritize technology names and deprioritize design diagrams
        if is_tech_query:
            tech_names = ["fastapi", "react", "gemini", "chromadb", "python", "langchain", "bootstrap", "css", "html"]
            if any(t in chunk_lower for t in tech_names):
                score += 30
            # Penalize design diagrams or ASCII layouts
            if any(d in chunk_lower for d in ["diagram", "diagrams", "architecture diagram", "ascii", "drawings", "flowchart"]):
                score -= 20

        # Heuristic 3: Word boundary query overlap scoring
        overlap = 0
        for w in words:
            if len(w) > 2 and w not in {"what", "is", "are", "the", "of", "in", "to", "for", "and", "our", "you"}:
                if w in chunk_lower:
                    overlap += 1
                    if re.search(rf"\b{re.escape(w)}\b", chunk_lower):
                        overlap += 2
        score += overlap

        # Remove irrelevant chunks (score <= 0 means zero keyword matching or penalized out of relevance)
        if score > 0 or is_generic_query:
            scored_chunks.append((chunk, max(score, 1)))

    # 3. Sort by score descending
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    if not scored_chunks:
        return "Sorry, I couldn't find that information in the available knowledge base."

    # Return top ranked chunks joined back together
    results = [chunk for chunk, _ in scored_chunks]
    return "\n\n".join(results)
