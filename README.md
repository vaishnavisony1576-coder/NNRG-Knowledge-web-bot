# 🎓 NNRG Web Knowledge Bot

An AI-powered chatbot developed for **NNRG Group of Institutions** that provides instant, context-aware answers using **Website Retrieval-Augmented Generation (Website RAG)** and **PDF Retrieval-Augmented Generation (PDF RAG)**. The chatbot helps students, parents, and visitors access college information while also allowing users to upload PDF documents and ask questions about their content.

---

## 🌐 Live Demo

**Frontend:** https://nnrg-knowledge-web-bot.vercel.app/

**Backend API:** https://nnrg-knowledge-web-bot.onrender.com

---

# 📖 Project Overview

The NNRG Web Knowledge Bot is an intelligent virtual assistant designed to simplify access to information related to NNRG Group of Institutions. It retrieves information directly from the college website using semantic search and also supports document-based question answering by allowing users to upload PDF files.

The chatbot uses Google's Gemini AI model along with Retrieval-Augmented Generation (RAG) to generate accurate, context-aware responses. It also detects and politely rejects questions that are unrelated to the college or uploaded documents.

---

# ✨ Features

## 🌐 Website Knowledge Assistant
- Answers questions about NNRG Group of Institutions
- Courses Offered
- Admissions
- Placements
- Campus Facilities
- Contact Information
- College Overview
- Departments

---

## 📄 PDF Question Answering (PDF RAG)

- Upload PDF documents
- Automatically process and index PDFs
- Ask questions related to uploaded documents
- AI-generated summaries
- Context-aware document answers

---

## 🤖 AI Capabilities

- Website RAG
- PDF RAG
- Semantic Search
- Intelligent Answer Generation
- Context-aware Responses
- Out-of-Domain Detection
- Source-based Response Routing

---

# 🛠️ Tech Stack

## Frontend
- React.js
- Vite
- Tailwind CSS
- JavaScript

## Backend
- Python
- FastAPI

## AI & Machine Learning
- Google Gemini API
- LangChain
- ChromaDB
- Sentence Transformers

## Other Tools
- BeautifulSoup
- Requests
- PyMuPDF
- dotenv

---

# 📂 Project Structure

```text
NNRG-Web-Knowledge-Bot
│
├── frontend
│   ├── public
│   ├── src
│   ├── components
│   ├── package.json
│   └── vite.config.js
│
├── backend
│   ├── services
│   ├── uploads
│   ├── app.py
│   ├── requirements.txt
│   └── .env
│
└── README.md
```

---


# 💬 Example Questions

## Website Questions

- What courses are offered at NNRG?
- Tell me about placements.
- What facilities are available?
- What is the admission process?
- Who founded NNRG?
- What is the college motto?
- Where is NNRG located?

---

## PDF Questions

- Summarize this PDF.
- What is this document about?
- What are the key points?
- Explain the technical architecture.
- What is the conclusion?
- What technologies are used?

---

# 🚀 How It Works

1. User enters a question or uploads a PDF.
2. The system identifies whether the query is related to the website or the uploaded document.
3. Relevant information is retrieved using semantic search.
4. Gemini AI generates a natural language response.
5. The chatbot displays the final answer to the user.

---

# 🎯 Future Enhancements

- Multiple PDF support
- Chat history
- Voice input
- OCR support for scanned PDFs
- Multi-language support
- Authentication & User Profiles

---


# 👩‍💻 Developer

**Vaishnavi Gungone**

B.Tech – Artificial Intelligence & Machine Learning

---
