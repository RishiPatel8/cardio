import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  ShieldAlert, User, ShieldCheck, Send, AlertTriangle 
} from "lucide-react";

interface DoctorNote {
  id: string;
  doctor_name: string;
  notes: string;
  status: string;
  created_at: string;
}

const Doctor: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [notes, setNotes] = useState<DoctorNote[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Clinician Form local states
  const [noteText, setNoteText] = useState("");
  const [docName, setDocName] = useState("Dr. Elizabeth Carter");
  const [docStatus, setDocStatus] = useState("Reviewed");
  const [submitting, setSubmitting] = useState(false);
  
  // Emergency alert state
  const [emergencyMessage, setEmergencyMessage] = useState("Critical tachycardia warning flagged by user.");
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTriggerResult] = useState<any>(null);

  const fetchDoctorNotes = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/clinical/notes`, { method: "GET", headers });
      if (res.ok) {
        const data = await res.json();
        setNotes(data);
      }
    } catch (err) {
      console.error("Failed to load doctor notes", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctorNotes();
  }, [getUserToken, getAppCheckToken]);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteText.trim() || submitting) return;
    setSubmitting(true);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/clinical/notes`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          doctor_name: docName,
          notes: noteText.trim(),
          status: docStatus
        }),
      });

      if (res.ok) {
        setNoteText("");
        fetchDoctorNotes();
      }
    } catch (err) {
      console.error("Failed to log clinician note", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEmergencyTrigger = async () => {
    setTriggering(true);
    setTriggerResult(null);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/emergency/trigger`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message: emergencyMessage }),
      });

      if (res.ok) {
        const data = await res.json();
        setTriggerResult(data);
      }
    } catch (err) {
      console.error("Emergency trigger failure", err);
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "24px", width: "100%", paddingBottom: "40px" }} className="profile-grid">
      
      {/* Left panel - Doctor notes */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        {/* Clinician Review List */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
            <ShieldCheck size={18} color="var(--color-normal)" />
            <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Clinician Reviews & Observations</h3>
          </div>
          
          {loading ? (
            <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Loading doctor observations...</span>
          ) : notes.length === 0 ? (
            <div style={{ padding: "16px", borderRadius: "8px", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-glass)", fontSize: "0.75rem", color: "var(--text-secondary)", textAlign: "center" }}>
              No doctor review notes have been logged for this profile.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {notes.map((note) => (
                <div 
                  key={note.id}
                  style={{ 
                    padding: "16px", 
                    borderRadius: "10px", 
                    backgroundColor: "rgba(255,255,255,0.01)", 
                    border: `1px solid ${note.status === "Critical Warning" ? "rgba(255,59,48,0.2)" : "var(--border-glass)"}`
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <span style={{ fontSize: "0.8rem", fontWeight: "700" }}>{note.doctor_name}</span>
                    <span style={{ 
                      fontSize: "0.6rem", 
                      padding: "3px 8px", 
                      borderRadius: "12px", 
                      fontWeight: "700",
                      backgroundColor: note.status === "Critical Warning" ? "rgba(255,59,48,0.12)" : "rgba(52,199,89,0.12)",
                      color: note.status === "Critical Warning" ? "var(--color-risk)" : "var(--color-normal)"
                    }}>
                      {note.status}
                    </span>
                  </div>
                  <p style={{ fontSize: "0.75rem", color: "#FFFFFF", lineHeight: "1.4" }}>{note.notes}</p>
                  <div style={{ fontSize: "0.6rem", color: "var(--text-muted)", marginTop: "10px", textAlign: "right" }}>
                    {new Date(note.created_at).toLocaleDateString()} {new Date(note.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Doctor portal simulation entry form */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
            <User size={18} color="var(--color-primary)" />
            <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Add Doctor Note (Clinician Portal Mock)</h3>
          </div>

          <form onSubmit={handleAddNote} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Doctor Name</label>
                <input 
                  type="text" 
                  value={docName} 
                  onChange={(e) => setDocName(e.target.value)}
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Clinical Status</label>
                <select 
                  value={docStatus} 
                  onChange={(e) => setDocStatus(e.target.value)}
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                >
                  <option value="Reviewed">Reviewed (Normal)</option>
                  <option value="Action Required">Action Required</option>
                  <option value="Critical Warning">Critical Warning</option>
                </select>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Observation Notes</label>
              <textarea 
                rows={3}
                placeholder="Type clinical review remarks..."
                value={noteText} 
                onChange={(e) => setNoteText(e.target.value)}
                style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem", resize: "none" }}
              />
            </div>

            <button 
              type="submit" 
              disabled={submitting || !noteText.trim()}
              className="btn-primary" 
              style={{ width: "100%", justifyContent: "center", padding: "12px", fontSize: "0.85rem" }}
            >
              <Send size={14} />
              {submitting ? "Saving Note..." : "Publish Doctor Note"}
            </button>
          </form>
        </div>

      </div>

      {/* Right panel - Emergency alert simulation */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
            <ShieldAlert size={18} color="var(--color-risk)" />
            <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Emergency Action Center</h3>
          </div>
          
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
            Triggering the emergency center manually alerts designated emergency contacts via simulated SMS logs and aggregates critical timeline incidents.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "4px" }}>
            <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Custom Incident Alert Message</label>
            <input 
              type="text" 
              value={emergencyMessage} 
              onChange={(e) => setEmergencyMessage(e.target.value)}
              style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
            />
          </div>

          <button 
            onClick={handleEmergencyTrigger} 
            disabled={triggering}
            className="btn-primary"
            style={{ width: "100%", justifyContent: "center", backgroundColor: "var(--color-risk)", boxShadow: "0 0 15px rgba(255, 59, 48, 0.3)", padding: "14px", fontSize: "0.9rem" }}
          >
            <AlertTriangle size={18} />
            {triggering ? "Dispatching Alarms..." : "TRIGGER CLINICAL EMERGENCY WORKFLOW"}
          </button>
        </div>

        {/* Emergency trigger results */}
        {triggerResult && (
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px", border: "1px solid rgba(255,59,48,0.3)", background: "rgba(255,59,48,0.02)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <AlertTriangle size={16} color="var(--color-risk)" />
              <span style={{ fontSize: "0.85rem", fontWeight: "800", color: "var(--color-risk)" }}>EMERGENCY CHANNELS TRIGGERED</span>
            </div>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Notified Emergency Contacts:</span>
              {triggerResult.contacts_notified.map((c: any, idx: number) => (
                <div key={idx} style={{ padding: "8px 12px", borderRadius: "8px", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-glass)", display: "flex", justifyContent: "space-between", fontSize: "0.7rem" }}>
                  <span>{c.name} ({c.relation})</span>
                  <span style={{ color: "var(--color-risk)", fontWeight: "700" }}>{c.status}</span>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px", borderTop: "1px solid var(--border-glass)", paddingTop: "12px" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#FFFFFF" }}>Immediate Patient Safety Instructions:</span>
              <ul style={{ paddingLeft: "16px", margin: 0, display: "flex", flexDirection: "column", gap: "4px" }}>
                {triggerResult.safety_instructions.map((ins: string, idx: number) => (
                  <li key={idx} style={{ fontSize: "0.68rem", color: "var(--text-secondary)", lineHeight: "1.3" }}>{ins}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

      </div>

    </div>
  );
};

export default Doctor;
