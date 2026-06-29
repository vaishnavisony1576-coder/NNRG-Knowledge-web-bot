import { useState } from "react";
import { FaRobot, FaTimes, FaPaperPlane, FaPlus } from "react-icons/fa";

const BACKEND_URL = `https://nnrg-knowledge-web-bot.onrender.com`;

function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("general");

  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "👋 Welcome to the NNRG AI Assistant!\n\nI can help you with:\n• Admissions\n• Courses\n• Placements\n• Campus Facilities\n• Uploaded PDF Documents\n\nAsk me anything about NNRG or upload a PDF to get started.",
    },
  ]);

  const handleSend = async () => {
    if (!message.trim()) return;

    const userMessage = message;

    setMessages((prev) => [
      ...prev,
      {
        sender: "user",
        text: userMessage,
      },
    ]);

    setMessage("");
    setLoading(true);

    try {
     const response = await fetch(
  `${BACKEND_URL}/chat?prompt=${encodeURIComponent(userMessage)}&mode=${mode}`
);

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: data.response,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "❌ Unable to connect to the backend.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "❌ Only PDF files are supported.",
        },
      ]);
      return;
    }

    setLoading(true);
    setMessages((prev) => [
      ...prev,
      {
        sender: "bot",
        text: `📄 Uploading:\n${file.name}\n\n🔍 Processing document...\n\n🧠 Creating embeddings...`,
      },
    ]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (response.ok) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "bot",
            text: `✅ PDF indexed successfully.\n\nCurrent Active Document:\n📄 ${file.name}\n\nAsk me anything about this document.`,
          },
        ]);
        setMode("pdf");
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: "bot",
            text: `❌ Upload failed: ${data.detail || "Server error"}`,
          },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "❌ Network error. Make sure the backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
      e.target.value = ""; // Reset file input
    }
  };

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="btn btn-primary rounded-circle position-fixed shadow"
          style={{
            bottom: "20px",
            right: "20px",
            width: "65px",
            height: "65px",
            fontSize: "28px",
            zIndex: 9999,
          }}
        >
          🤖
        </button>
      )}

      {open && (
        <div
          className="card shadow position-fixed"
          style={{
            bottom: "20px",
            right: "20px",
            width: "380px",
            height: "550px",
            borderRadius: "20px",
            zIndex: 9999,
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div
            className="d-flex justify-content-between align-items-center p-3"
            style={{
              background: "#0d6efd",
              color: "white",
            }}
          >
            <div className="d-flex align-items-center">
              <FaRobot size={22} />
              <span className="ms-2 fw-bold">
                NNRG AI Assistant
              </span>
            </div>

            <FaTimes
              style={{ cursor: "pointer" }}
              onClick={() => setOpen(false)}
            />
          </div>
                    {/* Chat Area */}
          <div
            className="p-3"
            style={{
              height: "420px",
              overflowY: "auto",
              background: "#f8f9fa",
            }}
          >
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`mb-3 ${
                  msg.sender === "user"
                    ? "text-end"
                    : "text-start"
                }`}
              >
                <div
                  className={`d-inline-block p-3 rounded ${
                    msg.sender === "user"
                      ? "bg-primary text-white"
                      : "bg-white shadow-sm"
                  }`}
                  style={{
                    maxWidth: "80%",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {loading && (
              <div className="text-start mb-3">
                <div className="d-inline-block bg-white shadow-sm rounded p-3">
                  🤖 Typing...
                </div>
              </div>
            )}
          </div>

          {/* Bottom */}
          <div className="border-top p-2 d-flex align-items-center position-relative">

            {/* Plus Button */}
            <div className="position-relative me-2">
              <button
                className="btn btn-light"
                onClick={() => setShowMenu(!showMenu)}
              >
                <FaPlus />
              </button>

              {showMenu && (
                <div
                  className="card shadow position-absolute"
                  style={{
                    bottom: "55px",
                    left: "0",
                    width: "180px",
                    borderRadius: "12px",
                    zIndex: 10000,
                  }}
                >
                  <button
                    className="dropdown-item py-2"
                    onClick={() => {
                      setShowMenu(false);
                      document.getElementById("pdf-file-input").click();
                    }}
                  >
                    📄 Upload PDF
                  </button>

                  <button
                    className="dropdown-item py-2"
                    onClick={() => {
                      setShowMenu(false);
                      setMode("website");
                      setShowMenu(false);

                      setMessages((prev) => [
                        ...prev,
                        {
                          sender: "bot",
                          text: "🌐 Website RAG enabled.\nAsk me anything about NNRG.",
                        },
                      ]);
                    }}
                  >
                    🌐 Website RAG
                  </button>
                </div>
              )}
            </div>

            {/* Hidden PDF file input */}
            <input
              type="file"
              id="pdf-file-input"
              accept=".pdf"
              style={{ display: "none" }}
              onChange={handleFileChange}
            />

            {/* Input */}
            <input
              type="text"
              className="form-control"
              placeholder="Ask something..."
              value={message}
              disabled={loading}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleSend();
                }
              }}
            />

            {/* Send */}
            <button
              className="btn btn-primary ms-2"
              onClick={handleSend}
              disabled={loading}
            >
              <FaPaperPlane />
            </button>

          </div>

        </div>
      )}
    </>
  );
}

export default ChatWidget;