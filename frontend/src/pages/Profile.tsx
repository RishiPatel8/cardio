import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { 
  User, ShieldAlert, Save, Plus, Trash2, Heart, Activity, Compass 
} from "lucide-react";

interface MedicationItem {
  name: string;
  dosage: string;
  frequency: string;
}

interface ProfileData {
  age: number;
  sex: string;
  blood_group: string;
  height: number;
  weight: number;
  bmi: number;
  waist_circumference: number;
  
  diabetes: boolean;
  hypertension: boolean;
  cholesterol: boolean;
  previous_heart_disease: boolean;
  stroke_history: boolean;
  family_history: boolean;
  current_medications: MedicationItem[];
  allergies: string[];
  
  smoking: boolean;
  alcohol: boolean;
  physical_activity_level: string;
  occupation: string;
  sleep_schedule: string;
  
  daily_steps_goal: number;
  weekly_exercise_goal: number;
  weight_goal: number;
  hydration_goal: number;
}

const Profile: React.FC = () => {
  const { getUserToken, getAppCheckToken } = useOutletContext<any>();
  
  const [profile, setProfile] = useState<ProfileData>({
    age: 30,
    sex: "Unspecified",
    blood_group: "O+",
    height: 175.0,
    weight: 70.0,
    bmi: 22.86,
    waist_circumference: 80.0,
    diabetes: false,
    hypertension: false,
    cholesterol: false,
    previous_heart_disease: false,
    stroke_history: false,
    family_history: false,
    current_medications: [],
    allergies: [],
    smoking: false,
    alcohol: false,
    physical_activity_level: "Sedentary",
    occupation: "Office Worker",
    sleep_schedule: "10:00 PM - 06:00 AM",
    daily_steps_goal: 10000,
    weekly_exercise_goal: 150,
    weight_goal: 70.0,
    hydration_goal: 2500,
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [newMed, setNewMed] = useState<MedicationItem>({ name: "", dosage: "", frequency: "" });
  const [newAllergy, setNewAllergy] = useState<string>("");
  const [message, setMessage] = useState<{ text: string; isError: boolean } | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = await getUserToken();
        const appCheckToken = await getAppCheckToken();
        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

        const headers: Record<string, string> = {};
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        if (appCheckToken) {
          headers["X-Firebase-App-Check"] = appCheckToken;
        }

        const res = await fetch(`${apiUrl}/users/me/profile`, {
          method: "GET",
          headers,
        });

        if (res.ok) {
          const data = await res.json();
          setProfile(data);
        }
      } catch (err) {
        console.error("Failed to load user profile", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [getUserToken, getAppCheckToken]);

  const calculateBmi = (w: number, h: number) => {
    if (h <= 0) return 0;
    const heightInMeters = h / 100.0;
    return parseFloat((w / (heightInMeters * heightInMeters)).toFixed(2));
  };

  const handleInputChange = (field: keyof ProfileData, val: any) => {
    setProfile((prev) => {
      const updated = { ...prev, [field]: val };
      if (field === "weight" || field === "height") {
        updated.bmi = calculateBmi(
          field === "weight" ? Number(val) : prev.weight,
          field === "height" ? Number(val) : prev.height
        );
      }
      return updated;
    });
  };

  const handleAddMedication = () => {
    if (!newMed.name || !newMed.dosage) return;
    setProfile((prev) => ({
      ...prev,
      current_medications: [...prev.current_medications, newMed],
    }));
    setNewMed({ name: "", dosage: "", frequency: "" });
  };

  const handleRemoveMedication = (idx: number) => {
    setProfile((prev) => ({
      ...prev,
      current_medications: prev.current_medications.filter((_, i) => i !== idx),
    }));
  };

  const handleAddAllergy = () => {
    if (!newAllergy) return;
    setProfile((prev) => ({
      ...prev,
      allergies: [...prev.allergies, newAllergy],
    }));
    setNewAllergy("");
  };

  const handleRemoveAllergy = (idx: number) => {
    setProfile((prev) => ({
      ...prev,
      allergies: prev.allergies.filter((_, i) => i !== idx),
    }));
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      if (appCheckToken) {
        headers["X-Firebase-App-Check"] = appCheckToken;
      }

      const res = await fetch(`${apiUrl}/users/me/profile`, {
        method: "PUT",
        headers,
        body: JSON.stringify(profile),
      });

      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        setMessage({ text: "Profile updated successfully!", isError: false });
      } else {
        setMessage({ text: "Failed to update profile statistics.", isError: true });
      }
    } catch (err) {
      setMessage({ text: "Communication error saving profile details.", isError: true });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "200px" }}>
        <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>Loading health profile data...</span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%", paddingBottom: "40px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "#FFFFFF" }}>Personal Health Profile</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
            Configure clinical history, wellness goals, and physical characteristics.
          </p>
        </div>
        <button 
          onClick={handleSaveProfile} 
          disabled={saving} 
          className="btn-primary" 
          style={{ padding: "10px 18px", fontSize: "0.85rem" }}
        >
          <Save size={16} />
          {saving ? "Saving..." : "Save Profile"}
        </button>
      </div>

      {message && (
        <div style={{ 
          padding: "12px 16px", 
          borderRadius: "10px", 
          backgroundColor: message.isError ? "rgba(255, 59, 48, 0.08)" : "rgba(52, 199, 89, 0.08)", 
          border: `1px solid ${message.isError ? "rgba(255, 59, 48, 0.2)" : "rgba(52, 199, 89, 0.2)"}`,
          color: message.isError ? "var(--color-risk)" : "var(--color-normal)",
          fontSize: "0.85rem",
          fontWeight: "600"
        }}>
          {message.text}
        </div>
      )}

      <form onSubmit={handleSaveProfile} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }} className="profile-grid">
        {/* Left Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* Card 1: Personal Characteristics */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <User size={18} color="var(--color-primary)" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Biometrics & Characteristics</h3>
            </div>
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Age (Years)</label>
                <input 
                  type="number" 
                  value={profile.age} 
                  onChange={(e) => handleInputChange("age", Number(e.target.value))} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Sex</label>
                <select 
                  value={profile.sex} 
                  onChange={(e) => handleInputChange("sex", e.target.value)} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                  <option value="Unspecified">Unspecified</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Height (cm)</label>
                <input 
                  type="number" 
                  value={profile.height} 
                  onChange={(e) => handleInputChange("height", Number(e.target.value))} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Weight (kg)</label>
                <input 
                  type="number" 
                  value={profile.weight} 
                  onChange={(e) => handleInputChange("weight", Number(e.target.value))} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Waist Circumference (cm)</label>
                <input 
                  type="number" 
                  value={profile.waist_circumference} 
                  onChange={(e) => handleInputChange("waist_circumference", Number(e.target.value))} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Blood Group</label>
                <select 
                  value={profile.blood_group} 
                  onChange={(e) => handleInputChange("blood_group", e.target.value)} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                >
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                </select>
              </div>
            </div>

            <div style={{ padding: "12px", borderRadius: "8px", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-glass)", display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "4px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Calculated BMI</span>
              <span style={{ fontSize: "0.95rem", fontWeight: "800", color: profile.bmi > 25 ? "var(--color-risk)" : "var(--color-normal)" }}>
                {profile.bmi} ({profile.bmi < 18.5 ? "Underweight" : profile.bmi < 25 ? "Healthy" : "Overweight"})
              </span>
            </div>
          </div>

          {/* Card 2: Medical Conditions History */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <ShieldAlert size={18} color="var(--color-risk)" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Medical History & Conditions</h3>
            </div>
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              {[
                { key: "diabetes", label: "Diabetes Mellitus" },
                { key: "hypertension", label: "Hypertension (High BP)" },
                { key: "cholesterol", label: "Hypercholesterolemia" },
                { key: "previous_heart_disease", label: "Prior Cardiac Disease" },
                { key: "stroke_history", label: "Prior Stroke / TIA" },
                { key: "family_history", label: "Family Cardiac History" }
              ].map((item) => (
                <label 
                  key={item.key} 
                  style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "0.75rem", padding: "10px", borderRadius: "8px", backgroundColor: profile[item.key as keyof ProfileData] ? "rgba(255,45,85,0.08)" : "rgba(255,255,255,0.02)", border: `1px solid ${profile[item.key as keyof ProfileData] ? "rgba(255,45,85,0.2)" : "var(--border-glass)"}`, transition: "all 0.2s" }}
                >
                  <input 
                    type="checkbox" 
                    checked={profile[item.key as keyof ProfileData] as boolean} 
                    onChange={(e) => handleInputChange(item.key as keyof ProfileData, e.target.checked)} 
                    style={{ accentColor: "var(--color-primary)" }}
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Card 3: Lifestyle Factors */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <Compass size={18} color="#FF9500" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Lifestyle Parameters</h3>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Physical Activity Level</label>
                <select 
                  value={profile.physical_activity_level} 
                  onChange={(e) => handleInputChange("physical_activity_level", e.target.value)} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#181a1f", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                >
                  <option value="Sedentary">Sedentary (Little or no exercise)</option>
                  <option value="Moderate">Moderate (1-3 days exercise/week)</option>
                  <option value="Active">Active (4-6 days heavy exercise/week)</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Occupation</label>
                <input 
                  type="text" 
                  value={profile.occupation} 
                  onChange={(e) => handleInputChange("occupation", e.target.value)} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px", gridColumn: "span 2" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Sleep Schedule (Ideal Hours)</label>
                <input 
                  type="text" 
                  placeholder="e.g. 10:00 PM - 06:00 AM"
                  value={profile.sleep_schedule} 
                  onChange={(e) => handleInputChange("sleep_schedule", e.target.value)} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "16px" }}>
              <label style={{ flex: 1, display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "0.75rem", padding: "10px", borderRadius: "8px", backgroundColor: profile.smoking ? "rgba(255,45,85,0.08)" : "rgba(255,255,255,0.02)", border: `1px solid ${profile.smoking ? "rgba(255,45,85,0.2)" : "var(--border-glass)"}` }}>
                <input 
                  type="checkbox" 
                  checked={profile.smoking} 
                  onChange={(e) => handleInputChange("smoking", e.target.checked)} 
                  style={{ accentColor: "var(--color-primary)" }}
                />
                <span>Active Smoking</span>
              </label>

              <label style={{ flex: 1, display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "0.75rem", padding: "10px", borderRadius: "8px", backgroundColor: profile.alcohol ? "rgba(255,45,85,0.08)" : "rgba(255,255,255,0.02)", border: `1px solid ${profile.alcohol ? "rgba(255,45,85,0.2)" : "var(--border-glass)"}` }}>
                <input 
                  type="checkbox" 
                  checked={profile.alcohol} 
                  onChange={(e) => handleInputChange("alcohol", e.target.checked)} 
                  style={{ accentColor: "var(--color-primary)" }}
                />
                <span>Regular Alcohol Consumption</span>
              </label>
            </div>
          </div>

        </div>

        {/* Right Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* Card 4: Daily Vitals Goals */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <Activity size={18} color="#34C759" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Daily Fitness & Hydration Goals</h3>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Steps Count Goal</label>
                <input 
                  type="number" 
                  value={profile.daily_steps_goal} 
                  onChange={(e) => handleInputChange("daily_steps_goal", Number(e.target.value))} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Exercise Goal (Min/Week)</label>
                <input 
                  type="number" 
                  value={profile.weekly_exercise_goal} 
                  onChange={(e) => handleInputChange("weekly_exercise_goal", Number(e.target.value))} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Hydration Goal (ml/Day)</label>
                <input 
                  type="number" 
                  value={profile.hydration_goal} 
                  onChange={(e) => handleInputChange("hydration_goal", Number(e.target.value))} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Target Weight Goal (kg)</label>
                <input 
                  type="number" 
                  value={profile.weight_goal} 
                  onChange={(e) => handleInputChange("weight_goal", Number(e.target.value))} 
                  className="input-field" 
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.8rem" }}
                />
              </div>
            </div>
          </div>

          {/* Card 5: Current Medications */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <Heart size={18} color="var(--color-primary)" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Current Medications</h3>
            </div>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {profile.current_medications.map((med, idx) => (
                <div key={idx} style={{ padding: "8px 12px", borderRadius: "8px", backgroundColor: "rgba(255,255,255,0.02)", border: "1px solid var(--border-glass)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <span style={{ fontSize: "0.8rem", fontWeight: "600" }}>{med.name}</span>
                    <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>{med.dosage} • {med.frequency}</span>
                  </div>
                  <button type="button" onClick={() => handleRemoveMedication(idx)} style={{ background: "none", border: "none", color: "var(--color-risk)", cursor: "pointer" }}>
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr auto", gap: "8px", alignItems: "end" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Name</label>
                <input 
                  type="text" 
                  value={newMed.name} 
                  onChange={(e) => setNewMed(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Aspirin"
                  className="input-field" 
                  style={{ width: "100%", padding: "6px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Dosage</label>
                <input 
                  type="text" 
                  value={newMed.dosage} 
                  onChange={(e) => setNewMed(prev => ({ ...prev, dosage: e.target.value }))}
                  placeholder="81mg"
                  className="input-field" 
                  style={{ width: "100%", padding: "6px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Frequency</label>
                <input 
                  type="text" 
                  value={newMed.frequency} 
                  onChange={(e) => setNewMed(prev => ({ ...prev, frequency: e.target.value }))}
                  placeholder="Once daily"
                  className="input-field" 
                  style={{ width: "100%", padding: "6px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                />
              </div>
              <button 
                type="button" 
                onClick={handleAddMedication}
                style={{ padding: "6px 8px", borderRadius: "6px", backgroundColor: "rgba(255,255,255,0.05)", border: "1px solid var(--border-glass)", color: "#FFFFFF", cursor: "pointer" }}
              >
                <Plus size={14} />
              </button>
            </div>
          </div>

          {/* Card 6: Allergies */}
          <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px" }}>
              <ShieldAlert size={18} color="var(--color-warning)" />
              <h3 style={{ fontSize: "0.95rem", fontWeight: "700" }}>Allergies & Sensitivities</h3>
            </div>
            
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {profile.allergies.map((alg, idx) => (
                <div key={idx} style={{ padding: "6px 12px", borderRadius: "20px", backgroundColor: "rgba(255,149,0,0.08)", border: "1px solid rgba(255,149,0,0.2)", display: "flex", alignItems: "center", gap: "6px", fontSize: "0.7rem", color: "#FF9500" }}>
                  <span>{alg}</span>
                  <button type="button" onClick={() => handleRemoveAllergy(idx)} style={{ background: "none", border: "none", color: "#FF9500", cursor: "pointer", padding: 0 }}>
                    ×
                  </button>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", gap: "8px", alignItems: "end" }}>
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "4px" }}>
                <input 
                  type="text" 
                  value={newAllergy} 
                  onChange={(e) => setNewAllergy(e.target.value)}
                  placeholder="e.g. Penicillin, Peanuts"
                  className="input-field" 
                  style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFF", fontSize: "0.75rem" }}
                />
              </div>
              <button 
                type="button" 
                onClick={handleAddAllergy}
                style={{ padding: "8px 12px", borderRadius: "6px", backgroundColor: "rgba(255,255,255,0.05)", border: "1px solid var(--border-glass)", color: "#FFFFFF", cursor: "pointer", fontSize: "0.75rem" }}
              >
                Add Allergy
              </button>
            </div>
          </div>

        </div>
      </form>
    </div>
  );
};

export default Profile;
