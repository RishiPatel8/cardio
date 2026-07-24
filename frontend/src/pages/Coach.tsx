import React, { useState, useEffect, useRef } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  Send, User, Cpu, Sparkles, CheckCircle 
} from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "coach";
  text: string;
  timestamp: Date;
}

const Coach: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "coach",
      text: "Hello! I am your CardioGuard AI Wellness Coach. Ask me about your blood pressure trends, recovery status, sleep quality, or active goals today!",
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  
  const [wellnessScores, setWellnessScores] = useState({
    health_score: 91,
    readiness_score: 88,
    recovery_score: 86
  });
  const [recommendations, setRecommendations] = useState<string[]>([
    "Maintain hydration (target 2500ml daily).",
    "Monitor heart rate trends during moderate exercise.",
    "Take scheduled medications."
  ]);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || sending) return;

    const userMsgText = inputText.trim();
    setInputText("");
    
    const userMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: userMsgText,
      timestamp: new Date()
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setSending(true);

    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {
        "Content-Type": "application/json"
      };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/coach/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message: userMsgText }),
      });

      if (res.ok) {
        const data = await res.json();
        const coachMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: "coach",
          text: data.reply,
          timestamp: new Date()
        };
        setMessages((prev) => [...prev, coachMessage]);
        if (data.wellness_scores) setWellnessScores(data.wellness_scores);
        if (data.recommendations) setRecommendations(data.recommendations);
      } else {
        throw new Error("Coach response error");
      }
    } catch (err) {
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "coach",
        text: "I am having trouble communicating with the diagnostic engine. Please make sure the backend is active.",
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "24px", height: "calc(100vh - 120px)", width: "100%" }} className="profile-grid">
      
      {/* Left panel - Chat area */}
      <div className="glass-panel" style={{ display: "flex", flexDirection: "column", height: "100%", padding: 0 }}>
        
        {/* Chat header */}
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-glass)", display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: "linear-gradient(135deg, var(--color-primary), var(--color-secondary))", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Sparkles size={16} color="#FFFFFF" />
          </div>
          <div>
            <h3 style={{ fontSize: "0.95rem", fontWeight: "700", color: "#FFFFFF" }}>AI Wellness Coach</h3>
            <span style={{ fontSize: "0.65rem", color: "var(--color-normal)" }}>• Clinical Expert Assistant Active</span>
          </div>
        </div>

        {/* Messages container */}
        <div style={{ flex: 1, padding: "20px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
          {messages.map((m) => (
            <div 
              key={m.id}
              style={{
                display: "flex",
                gap: "10px",
                alignSelf: m.sender === "user" ? "flex-end" : "flex-start",
                flexDirection: m.sender === "user" ? "row-reverse" : "row",
                maxWidth: "80%"
              }}
            >
              <div style={{
                width: "28px",
                height: "28px",
                borderRadius: "50%",
                backgroundColor: m.sender === "user" ? "rgba(255,255,255,0.05)" : "rgba(255,45,85,0.1)",
                border: `1px solid ${m.sender === "user" ? "var(--border-glass)" : "rgba(255,45,85,0.2)"}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0
              }}>
                {m.sender === "user" ? <User size={12} color="#FFFFFF" /> : <Cpu size={12} color="var(--color-primary)" />}
              </div>

              <div style={{
                padding: "10px 14px",
                borderRadius: "12px",
                backgroundColor: m.sender === "user" ? "var(--color-primary)" : "rgba(255,255,255,0.02)",
                border: `1px solid ${m.sender === "user" ? "transparent" : "var(--border-glass)"}`,
                color: "#FFFFFF",
                fontSize: "0.8rem",
                lineHeight: "1.5"
              }}>
                {m.text}
                <div style={{ fontSize: "0.55rem", color: "var(--text-muted)", marginTop: "4px", textAlign: "right" }}>
                  {m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* Input area */}
        <form onSubmit={handleSendMessage} style={{ padding: "16px", borderTop: "1px solid var(--border-glass)", display: "flex", gap: "10px" }}>
          <input
            type="text"
            placeholder="Ask anything (e.g. 'Analyze my BP logs', 'How can I support my HRV?')..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={sending}
            style={{
              flex: 1,
              padding: "12px",
              borderRadius: "8px",
              background: "rgba(0,0,0,0.15)",
              border: "1px solid var(--border-glass)",
              color: "#FFFFFF",
              fontSize: "0.8rem"
            }}
          />
          <button 
            type="submit" 
            disabled={sending || !inputText.trim()}
            className="btn-primary" 
            style={{ padding: "12px", borderRadius: "8px" }}
          >
            <Send size={14} />
          </button>
        </form>

      </div>

      {/* Right panel - Scores & Checklists */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        {/* Scores panel */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Vitals Recovery Analysis</h3>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", textAlign: "center" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px", backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-glass)", padding: "10px", borderRadius: "8px" }}>
              <span style={{ fontSize: "0.55rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Health</span>
              <span style={{ fontSize: "1.1rem", fontWeight: "800", color: "var(--color-normal)" }}>{wellnessScores.health_score}</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px", backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-glass)", padding: "10px", borderRadius: "8px" }}>
              <span style={{ fontSize: "0.55rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Readiness</span>
              <span style={{ fontSize: "1.1rem", fontWeight: "800", color: "#FF9500" }}>{wellnessScores.readiness_score}</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px", backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-glass)", padding: "10px", borderRadius: "8px" }}>
              <span style={{ fontSize: "0.55rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Recovery</span>
              <span style={{ fontSize: "1.1rem", fontWeight: "800", color: "var(--color-secondary)" }}>{wellnessScores.recovery_score}</span>
            </div>
          </div>
        </div>

        {/* Coach Recommendations */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px", flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
            <Sparkles size={16} color="var(--color-primary)" />
            <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Personalized Wellness Steps</h3>
          </div>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {recommendations.map((rec, idx) => (
              <div 
                key={idx}
                style={{ padding: "12px", borderRadius: "10px", backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-glass)", display: "flex", gap: "10px", alignItems: "flex-start" }}
              >
                <CheckCircle size={14} color="var(--color-normal)" style={{ marginTop: "2px", flexShrink: 0 }} />
                <span style={{ fontSize: "0.75rem", lineHeight: "1.4", color: "#FFFFFF" }}>{rec}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
};

export default Coach;
