import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip as ChartTooltip, Legend 
} from "recharts";
import { 
  TrendingUp, Activity, PlusCircle, Calendar, Clock, Coffee 
} from "lucide-react";

interface TimelineEvent {
  id: string;
  event_type: string;
  title: string;
  description: string;
  created_at: string;
}

interface NutritionLog {
  id: string;
  meal_name: string;
  calories: number;
  created_at: string;
}

interface HydrationLog {
  id: string;
  amount_ml: number;
  created_at: string;
}

const Trends: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  // Historical data states
  const [vitalsHistory, setVitalsHistory] = useState<any[]>([]);
  const [nutritionLogs, setNutritionLogs] = useState<NutritionLog[]>([]);
  const [hydrationLogs, setHydrationLogs] = useState<HydrationLog[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  
  // Intake log forms local states
  const [mealName, setMealName] = useState("");
  const [mealCals, setMealCals] = useState(300);
  const [waterMl, setWaterMl] = useState(250);
  const [logging, setLogging] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchLongitudinalData = async () => {
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      // 1. Fetch wearables history
      const vitalsRes = await fetch(`${apiUrl}/wearables/history?limit=10`, { method: "GET", headers });
      if (vitalsRes.ok) {
        const vitalsData = await vitalsRes.json();
        // Reverse to display chronologically from left to right in charts
        setVitalsHistory(vitalsData.reverse());
      }

      // 2. Fetch nutrition
      const nutRes = await fetch(`${apiUrl}/nutrition?limit=10`, { method: "GET", headers });
      if (nutRes.ok) {
        const nutData = await nutRes.json();
        setNutritionLogs(nutData);
      }

      // 3. Fetch hydration
      const hydRes = await fetch(`${apiUrl}/hydration?limit=10`, { method: "GET", headers });
      if (hydRes.ok) {
        const hydData = await hydRes.json();
        setHydrationLogs(hydData);
      }

      // 4. Fetch timeline
      const timeRes = await fetch(`${apiUrl}/timeline?limit=15`, { method: "GET", headers });
      if (timeRes.ok) {
        const timeData = await timeRes.json();
        setTimelineEvents(timeData);
      }
    } catch (err) {
      console.error("Failed to load longitudinal logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLongitudinalData();
  }, [getUserToken, getAppCheckToken]);

  const handleLogMeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mealName.trim() || logging) return;
    setLogging(true);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/nutrition`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          meal_name: mealName.trim(),
          calories: mealCals,
          protein_g: 15.0,
          carbs_g: 40.0,
          fat_g: 10.0
        }),
      });

      if (res.ok) {
        setMealName("");
        fetchLongitudinalData();
      }
    } catch (err) {
      console.error("Failed to log meal nutrition", err);
    } finally {
      setLogging(false);
    }
  };

  const handleLogWater = async (e: React.FormEvent) => {
    e.preventDefault();
    if (logging) return;
    setLogging(true);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/hydration`, {
        method: "POST",
        headers,
        body: JSON.stringify({ amount_ml: waterMl }),
      });

      if (res.ok) {
        fetchLongitudinalData();
      }
    } catch (err) {
      console.error("Failed to log hydration", err);
    } finally {
      setLogging(false);
    }
  };

  // Compile datasets for charts
  const bpChartData = vitalsHistory.map((item) => ({
    name: new Date(item.created_at).toLocaleDateString([], { month: "short", day: "numeric" }),
    systolic: item.systolic_bp,
    diastolic: item.diastolic_bp,
    spo2: item.spo2
  }));

  const weightChartData = vitalsHistory.map((item) => ({
    name: new Date(item.created_at).toLocaleDateString([], { month: "short", day: "numeric" }),
    weight: item.sleep_minutes > 0 ? (item.sleep_minutes / 60) : 7.0, // fallback to mapping sleep duration trends
  }));


  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "200px" }}>
        <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>Loading trends logs data...</span>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "24px", width: "100%", paddingBottom: "40px" }} className="profile-grid">
      
      {/* Left panel - Charts and logger forms */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        {/* Chart 1: Blood Pressure Trends */}
        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <TrendingUp size={20} color="var(--color-primary)" />
            <h3 style={{ fontSize: "1rem", fontWeight: "700" }}>Arterial Blood Pressure Trends</h3>
          </div>
          
          <div style={{ width: "100%", height: "200px" }}>
            {bpChartData.length === 0 ? (
              <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                No blood pressure logs logged. Use Manual Entry sync on Dashboard.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={bpChartData}>
                  <defs>
                    <linearGradient id="sysColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="diaColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#007AFF" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#007AFF" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} />
                  <YAxis stroke="var(--text-muted)" domain={[50, 160]} fontSize={10} />
                  <ChartTooltip contentStyle={{ backgroundColor: "#1e1e24", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "11px", color: "#FFF" }} />
                  <Legend />
                  <Area type="monotone" dataKey="systolic" name="Systolic BP" stroke="var(--color-primary)" fillOpacity={1} fill="url(#sysColor)" strokeWidth={2} />
                  <Area type="monotone" dataKey="diastolic" name="Diastolic BP" stroke="#007AFF" fillOpacity={1} fill="url(#diaColor)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Chart 2: Sleep Duration Trends */}
        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <Activity size={20} color="var(--color-secondary)" />
            <h3 style={{ fontSize: "1rem", fontWeight: "700" }}>Longitudinal Sleep Tracking (Hours)</h3>
          </div>
          
          <div style={{ width: "100%", height: "180px" }}>
            {weightChartData.length === 0 ? (
              <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                No sleep cycles records synced.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={weightChartData}>
                  <defs>
                    <linearGradient id="sleepColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-secondary)" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="var(--color-secondary)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} />
                  <YAxis stroke="var(--text-muted)" domain={[3, 10]} fontSize={10} />
                  <ChartTooltip contentStyle={{ backgroundColor: "#1e1e24", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "11px", color: "#FFF" }} />
                  <Area type="monotone" dataKey="weight" name="Sleep Hours" stroke="var(--color-secondary)" fillOpacity={1} fill="url(#sleepColor)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Logger widgets forms */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }} className="insights-row">
          
          {/* Meal intake log */}
          <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <Coffee size={18} color="#FF9500" />
              <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Log Meal & Nutrition</h3>
            </div>
            
            <form onSubmit={handleLogMeal} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Meal Name</label>
                <input 
                  type="text" 
                  placeholder="e.g. Oatmeal with Bananas"
                  value={mealName} 
                  onChange={(e) => setMealName(e.target.value)}
                  style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                />
              </div>
              
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Calories (kcal)</label>
                <input 
                  type="number" 
                  value={mealCals} 
                  onChange={(e) => setMealCals(Number(e.target.value))}
                  style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                />
              </div>
              
              <button 
                type="submit" 
                disabled={logging || !mealName.trim()}
                className="btn-secondary" 
                style={{ justifyContent: "center", padding: "10px", fontSize: "0.75rem", fontWeight: "700" }}
              >
                Log Meal
              </button>
            </form>
            {nutritionLogs.length > 0 && (
              <div style={{ marginTop: "12px", borderTop: "1px solid var(--border-glass)", paddingTop: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
                <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", fontWeight: "700" }}>Recent Logged Meals:</span>
                {nutritionLogs.slice(0, 3).map((item) => (
                  <div key={item.id} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.65rem", color: "var(--text-muted)" }}>
                    <span>{item.meal_name}</span>
                    <span>{item.calories} kcal</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Hydration log */}
          <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <PlusCircle size={18} color="#007AFF" />
              <h3 style={{ fontSize: "0.9rem", fontWeight: "700" }}>Log Hydration Intake</h3>
            </div>
            
            <form onSubmit={handleLogWater} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Water Intake (ml)</label>
                <select 
                  value={waterMl} 
                  onChange={(e) => setWaterMl(Number(e.target.value))}
                  style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                >
                  <option value={150}>150 ml (Small Cup)</option>
                  <option value={250}>250 ml (Standard Glass)</option>
                  <option value={500}>500 ml (Water Bottle)</option>
                  <option value={750}>750 ml (Sport Flask)</option>
                </select>
              </div>
              
              <button 
                type="submit" 
                disabled={logging}
                className="btn-secondary" 
                style={{ justifyContent: "center", padding: "10px", marginTop: "24px", fontSize: "0.75rem", fontWeight: "700" }}
              >
                Log Water
              </button>
            </form>
            {hydrationLogs.length > 0 && (
              <div style={{ marginTop: "12px", borderTop: "1px solid var(--border-glass)", paddingTop: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
                <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", fontWeight: "700" }}>Recent Hydration Intake:</span>
                {hydrationLogs.slice(0, 3).map((item) => (
                  <div key={item.id} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.65rem", color: "var(--text-muted)" }}>
                    <span>Water Log</span>
                    <span>{item.amount_ml} ml</span>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>

      {/* Right panel - Chronological Health Timeline */}
      <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px", height: "100%" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
          <Calendar size={18} color="var(--color-primary)" />
          <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Health Incident Timeline</h3>
        </div>

        {timelineEvents.length === 0 ? (
          <div style={{ padding: "20px", fontSize: "0.75rem", color: "var(--text-secondary)", textAlign: "center" }}>
            No health milestone logs recorded. Complete syncs, predictions, or logs to populate.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", overflowY: "auto", maxHeight: "600px", paddingRight: "5px" }}>
            {timelineEvents.map((evt) => (
              <div 
                key={evt.id}
                style={{ 
                  padding: "12px 14px", 
                  borderRadius: "8px", 
                  backgroundColor: "rgba(255,255,255,0.01)", 
                  border: `1px solid ${evt.event_type === "emergency" ? "rgba(255,59,48,0.25)" : "var(--border-glass)"}`
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: "700", color: evt.event_type === "emergency" ? "var(--color-risk)" : "#FFFFFF" }}>
                    {evt.title}
                  </span>
                  <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.55rem", color: "var(--text-muted)" }}>
                    <Clock size={10} />
                    <span>{new Date(evt.created_at).toLocaleDateString([], { month: "short", day: "numeric" })}</span>
                  </div>
                </div>
                <p style={{ fontSize: "0.68rem", color: "var(--text-secondary)", lineHeight: "1.3" }}>
                  {evt.description}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
};

export default Trends;
