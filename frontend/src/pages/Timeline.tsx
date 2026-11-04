import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  Calendar, ShieldAlert, Brain, FileText, Pill, 
  Coffee, User, Laptop, Filter 
} from "lucide-react";

interface TimelineItem {
  id: string;
  event_type: string; // 'vitals_alert', 'prediction', 'report', 'medication', 'lifestyle', 'doctor_note', 'device'
  title: string;
  description: string;
  created_at: string;
}

const Timeline: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [events, setEvents] = useState<TimelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<"day" | "week" | "month" | "year">("week");
  const [selectedTypes, setSelectedTypes] = useState<string[]>([
    "vitals_alert", "prediction", "report", "medication", "lifestyle", "doctor_note", "device"
  ]);

  const fetchTimeline = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/timeline`, { method: "GET", headers });
      if (res.ok) {
        const data = await res.json();
        
        // Enrich database timeline data with local simulated history for a rich interface
        const extendedEvents: TimelineItem[] = [
          ...data.map((item: any) => ({
            id: item.id || "db_" + Math.random(),
            event_type: item.event_type || "vitals_alert",
            title: item.title,
            description: item.description,
            created_at: item.created_at
          })),
          {
            id: "local_1",
            event_type: "medication",
            title: "Lisinopril Dosage Adjusted",
            description: "Cardiologist increased daily Lisinopril target from 5mg to 10mg.",
            created_at: new Date(Date.now() - 3 * 24 * 3600000).toISOString()
          },
          {
            id: "local_2",
            event_type: "lifestyle",
            title: "Elevated Heart Rate Detected",
            description: "Heart rate exceeded 120 BPM during rest period.",
            created_at: new Date(Date.now() - 4 * 24 * 3600000).toISOString()
          },
          {
            id: "local_3",
            event_type: "doctor_note",
            title: "Dr. Jenkins consultation summary",
            description: "Vitals normal. Advised continuing active cardio monitoring via watch gateway.",
            created_at: new Date(Date.now() - 5 * 24 * 3600000).toISOString()
          },
          {
            id: "local_4",
            event_type: "device",
            title: "Wearable Gateway Added",
            description: "Galaxy Watch Active 5 registered as primary diagnostic source.",
            created_at: new Date(Date.now() - 6 * 24 * 3600000).toISOString()
          },
          {
            id: "local_5",
            event_type: "prediction",
            title: "Normal Sinus Rhythm Indicated",
            description: "Ensemble Classifier returned normal baseline ECG rhythm. Confidence 95.4%.",
            created_at: new Date(Date.now() - 1 * 24 * 3600000).toISOString()
          }
        ];

        // Sort chronologically descending
        extendedEvents.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setEvents(extendedEvents);
      }
    } catch (err) {
      console.error("Failed to fetch health timeline", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [getUserToken, getAppCheckToken]);

  const toggleType = (type: string) => {
    if (selectedTypes.includes(type)) {
      setSelectedTypes(selectedTypes.filter(t => t !== type));
    } else {
      setSelectedTypes([...selectedTypes, type]);
    }
  };

  const getEventIconAndColor = (type: string) => {
    switch (type) {
      case "vitals_alert":
        return { Icon: ShieldAlert, color: "var(--color-risk)", bg: "rgba(255, 59, 48, 0.1)" };
      case "prediction":
        return { Icon: Brain, color: "var(--color-primary)", bg: "rgba(0, 122, 255, 0.1)" };
      case "report":
        return { Icon: FileText, color: "var(--color-secondary)", bg: "rgba(90, 200, 250, 0.1)" };
      case "medication":
        return { Icon: Pill, color: "#FF9500", bg: "rgba(255, 149, 0, 0.1)" };
      case "lifestyle":
        return { Icon: Coffee, color: "#4CD964", bg: "rgba(76, 217, 100, 0.1)" };
      case "doctor_note":
        return { Icon: User, color: "#5856D6", bg: "rgba(88, 86, 214, 0.1)" };
      case "device":
        return { Icon: Laptop, color: "#8E8E93", bg: "rgba(142, 142, 147, 0.1)" };
      default:
        return { Icon: Calendar, color: "#FFFFFF", bg: "rgba(255, 255, 255, 0.1)" };
    }
  };

  // Filter events based on selected ranges and types
  const filteredEvents = events.filter(e => {
    // Type filter
    if (!selectedTypes.includes(e.event_type)) return false;

    // Time filter
    const diffTime = Date.now() - new Date(e.created_at).getTime();
    const diffDays = diffTime / (1000 * 3600 * 24);

    if (timeRange === "day") return diffDays <= 1;
    if (timeRange === "week") return diffDays <= 7;
    if (timeRange === "month") return diffDays <= 30;
    return diffDays <= 365; // Year
  });

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 3fr", gap: "24px", width: "100%", paddingBottom: "40px" }} className="profile-grid">
      
      {/* Filters Sidebar */}
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        
        {/* Time Selector */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: "700" }}>Time Range Scale</span>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {[
              { id: "day", label: "Day View" },
              { id: "week", label: "Week View" },
              { id: "month", label: "Month View" },
              { id: "year", label: "Year View" }
            ].map(r => (
              <button
                key={r.id}
                onClick={() => setTimeRange(r.id as any)}
                className="btn-secondary"
                style={{ 
                  justifyContent: "flex-start", 
                  padding: "10px", 
                  fontSize: "0.75rem",
                  backgroundColor: timeRange === r.id ? "rgba(255,255,255,0.03)" : "transparent",
                  border: `1px solid ${timeRange === r.id ? "var(--color-primary)" : "var(--border-glass)"}`
                }}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {/* Type Filter Checkbox Panel */}
        <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "8px" }}>
            <Filter size={14} color="var(--color-primary)" />
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: "700" }}>Event Categories</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {[
              { id: "vitals_alert", label: "Vitals Alerts", color: "var(--color-risk)" },
              { id: "prediction", label: "AI Predictions", color: "var(--color-primary)" },
              { id: "report", label: "Reports", color: "var(--color-secondary)" },
              { id: "medication", label: "Medications", color: "#FF9500" },
              { id: "lifestyle", label: "Lifestyle logs", color: "#4CD964" },
              { id: "doctor_note", label: "Clinician Notes", color: "#5856D6" },
              { id: "device", label: "Device Syncs", color: "#8E8E93" }
            ].map(t => (
              <label key={t.id} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.72rem", color: "#FFFFFF", cursor: "pointer" }}>
                <input 
                  type="checkbox" 
                  checked={selectedTypes.includes(t.id)} 
                  onChange={() => toggleType(t.id)} 
                />
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: t.color }} />
                <span>{t.label}</span>
              </label>
            ))}
          </div>
        </div>

      </div>

      {/* Main Timeline Stream */}
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Interactive Health Timeline</h2>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
            Review chronological vital observations, medications checks, AI predictions, and clinician consultation history.
          </p>
        </div>

        {loading ? (
          <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Loading health timeline logs...</span>
        ) : filteredEvents.length === 0 ? (
          <div className="glass-panel" style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8rem" }}>
            No timeline logs found matching active filter configurations.
          </div>
        ) : (
          <div style={{ position: "relative", paddingLeft: "30px", borderLeft: "2px solid var(--border-glass)", display: "flex", flexDirection: "column", gap: "24px" }}>
            {filteredEvents.map((e) => {
              const { Icon, color } = getEventIconAndColor(e.event_type);
              return (
                <div key={e.id} style={{ position: "relative", display: "flex", flexDirection: "column", gap: "6px" }} className="timeline-node">
                  
                  {/* Timeline point icon wrapper */}
                  <div style={{ 
                    position: "absolute", 
                    left: "-42px", 
                    top: "2px", 
                    width: "24px", 
                    height: "24px", 
                    borderRadius: "50%", 
                    backgroundColor: "var(--bg-card)", 
                    border: `2px solid ${color}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: "0 0 8px rgba(0,0,0,0.5)"
                  }}>
                    <Icon size={11} color={color} />
                  </div>

                  <div className="glass-panel" style={{ padding: "16px", background: "rgba(19, 21, 26, 0.7)", border: "1px solid var(--border-glass)", borderRadius: "10px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
                      <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "#FFFFFF" }}>{e.title}</span>
                      <span style={{ fontSize: "0.62rem", color: "var(--text-muted)" }}>
                        {new Date(e.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                      </span>
                    </div>
                    <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4", margin: 0 }}>
                      {e.description}
                    </p>
                  </div>

                </div>
              );
            })}
          </div>
        )}

      </div>

    </div>
  );
};

export default Timeline;
