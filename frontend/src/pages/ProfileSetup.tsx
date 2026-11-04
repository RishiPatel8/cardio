import React, { useState, useEffect } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { 
  ShieldAlert, CheckCircle, ChevronRight, ChevronLeft, Save
} from "lucide-react";

// Types matching the backend schema payload
interface PersonalInfo {
  fullName: string;
  gender: string;
  dob: string;
  height: number;
  weight: number;
  bloodGroup: string;
  phone: string;
  email: string;
}

interface LifestyleInfo {
  activityLevel: string;
  smokingStatus: string;
  alcoholConsumption: string;
  avgSleep: number;
  avgWater: number;
  avgSteps: number;
}

interface ClinicalHistory {
  medicalConditions: string[];
  currentSymptoms: string[];
  currentMedications: string;
  knownAllergies: string;
  previousSurgeries: string;
  exerciseRestrictions: string;
}

interface FamilyHistory {
  familyHeartDisease: string;
  familyHypertension: string;
  familyDiabetes: string;
  familyStroke: string;
  familyCholesterol: string;
  familySuddenCardiacDeath: string;
}

interface VitalSigns {
  systolicBp: number;
  diastolicBp: number;
  restingHr: number;
  spo2: number;
}

interface LabValues {
  totalCholesterol: number;
  ldl: number;
  hdl: number;
  triglycerides: number;
  fastingBloodSugar: number;
  hba1c: number;
}

interface WearableData {
  avgHeartRate: number;
  restingHeartRate: number;
  hrv: number;
  dailySteps: number;
  caloriesBurned: number;
  sleepDuration: number;
  sleepQuality: string;
  activityMinutes: number;
}

interface HealthRecord {
  id: string;
  uploadDate: string;
  fileName: string;
  reportType: string;
  fileSize: string;
}

const ProfileSetup: React.FC = () => {
  const { getUserToken, getAppCheckToken, fetchUserProfile, setProfileStatus, isFitConnected, dailyStats } = useOutletContext<any>();
  const navigate = useNavigate();

  const autoPopulateFromWearable = () => {
    if (isFitConnected && dailyStats) {
      setVitals(prev => ({
        ...prev,
        restingHr: dailyStats.avgBpm || prev.restingHr
      }));
      setLifestyle(prev => ({
        ...prev,
        avgSteps: dailyStats.steps || prev.avgSteps
      }));
    }
  };

  const [activeStep, setActiveStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [success, setSuccess] = useState<boolean>(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 12. Structured profile state separate JSON
  const [personal, setPersonal] = useState<PersonalInfo>({
    fullName: "",
    gender: "Male",
    dob: "1995-01-01",
    height: 175,
    weight: 70,
    bloodGroup: "O+",
    phone: "",
    email: ""
  });

  const [lifestyle, setLifestyle] = useState<LifestyleInfo>({
    activityLevel: "Moderately Active",
    smokingStatus: "Never",
    alcoholConsumption: "Occasionally",
    avgSleep: 7.5,
    avgWater: 2.2,
    avgSteps: 8000
  });

  const [clinical, setClinical] = useState<ClinicalHistory>({
    medicalConditions: [],
    currentSymptoms: [],
    currentMedications: "",
    knownAllergies: "",
    previousSurgeries: "",
    exerciseRestrictions: ""
  });

  const [family, setFamily] = useState<FamilyHistory>({
    familyHeartDisease: "No",
    familyHypertension: "No",
    familyDiabetes: "No",
    familyStroke: "No",
    familyCholesterol: "No",
    familySuddenCardiacDeath: "No"
  });

  const [vitals, setVitals] = useState<VitalSigns>({
    systolicBp: 120,
    diastolicBp: 80,
    restingHr: 72,
    spo2: 98
  });

  const [labs, setLabs] = useState<LabValues>({
    totalCholesterol: 0,
    ldl: 0,
    hdl: 0,
    triglycerides: 0,
    fastingBloodSugar: 0,
    hba1c: 0
  });

  const [wearable] = useState<WearableData>({
    avgHeartRate: 74,
    restingHeartRate: 68,
    hrv: 45,
    dailySteps: 7200,
    caloriesBurned: 310,
    sleepDuration: 7.2,
    sleepQuality: "Good",
    activityMinutes: 45
  });

  const [records] = useState<HealthRecord[]>([]);

  // Calculate age from DOB
  const getAge = (dobString: string) => {
    const birth = new Date(dobString);
    const today = new Date();
    let computedAge = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
      computedAge--;
    }
    return computedAge >= 0 ? computedAge : 30;
  };

  // 8. Dynamic auto calculations
  const getCalculations = () => {
    const ageVal = getAge(personal.dob);
    const hM = personal.height / 100;
    const bmiVal = hM > 0 ? parseFloat((personal.weight / (hM * hM)).toFixed(2)) : 0;

    let bmiCategory = "Normal Weight";
    if (bmiVal < 18.5) bmiCategory = "Underweight";
    else if (bmiVal >= 25 && bmiVal < 29.9) bmiCategory = "Overweight";
    else if (bmiVal >= 30) bmiCategory = "Obese";

    let bmr = 0;
    if (personal.gender === "Male") {
      bmr = 10 * personal.weight + 6.25 * personal.height - 5 * ageVal + 5;
    } else {
      bmr = 10 * personal.weight + 6.25 * personal.height - 5 * ageVal - 161;
    }

    let multiplier = 1.2;
    if (lifestyle.activityLevel === "Lightly Active") multiplier = 1.375;
    else if (lifestyle.activityLevel === "Moderately Active") multiplier = 1.55;
    else if (lifestyle.activityLevel === "Very Active") multiplier = 1.725;
    else if (lifestyle.activityLevel === "Athlete") multiplier = 1.9;

    const tdee = Math.round(bmr * multiplier);
    const minWeight = parseFloat((18.5 * hM * hM).toFixed(1));
    const maxWeight = parseFloat((24.9 * hM * hM).toFixed(1));
    const healthyWeightRange = `${minWeight} kg - ${maxWeight} kg`;
    const recWater = parseFloat(((personal.weight * 35) / 1000).toFixed(2));

    let proteinMultiplier = 1.2;
    if (lifestyle.activityLevel === "Moderately Active" || lifestyle.activityLevel === "Very Active") {
      proteinMultiplier = 1.6;
    } else if (lifestyle.activityLevel === "Athlete") {
      proteinMultiplier = 2.0;
    }
    const recProtein = Math.round(personal.weight * proteinMultiplier);

    return {
      age: ageVal,
      bmi: bmiVal,
      bmiCategory,
      bmr: Math.round(bmr),
      tdee,
      healthyWeightRange,
      recWater,
      recProtein
    };
  };

  const calcs = getCalculations();

  // Completion calculation percentage
  const getCompletionPercentage = () => {
    let sectionsPassed = 0;
    const totalSections = 6;

    if (personal.fullName.trim() && personal.dob && personal.height > 0 && personal.weight > 0) sectionsPassed++;
    if (lifestyle.activityLevel && lifestyle.avgWater > 0) sectionsPassed++;
    if (clinical.currentSymptoms.length > 0 || clinical.medicalConditions.length > 0) sectionsPassed++;
    if (vitals.systolicBp > 0 && vitals.restingHr > 0) sectionsPassed++;
    if (labs.fastingBloodSugar > 0 || labs.totalCholesterol > 0) sectionsPassed++;
    if (records.length >= 0) sectionsPassed++; // Base record count pass

    return Math.round((sectionsPassed / totalSections) * 100);
  };

  const completionPct = getCompletionPercentage();

  // Ingest draft cache or existing settings
  const loadDraft = async () => {
    try {
      const cachedStep = localStorage.getItem("cardioguard_onboarding_step");
      if (cachedStep) setActiveStep(Number(cachedStep));

      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const res = await fetch(`${apiUrl}/profile`, { method: "GET", headers });
      if (res.ok) {
        const data = await res.json();
        if (data.personal_information) setPersonal(data.personal_information);
        if (data.lifestyle) setLifestyle(data.lifestyle);
        if (data.clinical_history) setClinical(data.clinical_history);
        if (data.family_history) setFamily(data.family_history);
        if (data.vital_signs) setVitals(data.vital_signs);
        if (data.lab_values) setLabs(data.lab_values);
      }
    } catch (e) {
      console.warn("No previous draft found. Starting clean onboarding session.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDraft();
  }, [getUserToken, getAppCheckToken]);

  // Form step-by-step validator
  const validateStep = (step: number): boolean => {
    const errs: Record<string, string> = {};

    if (step === 1) {
      if (!personal.fullName.trim()) errs.fullName = "Full Name is required.";
      if (personal.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(personal.email)) {
        errs.email = "Invalid email format.";
      }
      if (personal.phone.trim() && !/^\+?[0-9\s\-]{8,15}$/.test(personal.phone)) {
        errs.phone = "Invalid phone number digits.";
      }
      if (personal.height < 50 || personal.height > 250) {
        errs.height = "Height must fall between 50 and 250 cm.";
      }
      if (personal.weight < 20 || personal.weight > 300) {
        errs.weight = "Weight must fall between 20 and 300 kg.";
      }
    }

    if (step === 5) {
      if (vitals.systolicBp < 70 || vitals.systolicBp > 240) {
        errs.systolicBp = "Systolic BP must fall between 70 and 240 mmHg.";
      }
      if (vitals.diastolicBp < 40 || vitals.diastolicBp > 140) {
        errs.diastolicBp = "Diastolic BP must fall between 40 and 140 mmHg.";
      }
      if (vitals.restingHr < 30 || vitals.restingHr > 220) {
        errs.restingHr = "Resting HR must fall between 30 and 220 BPM.";
      }
      if (vitals.spo2 < 70 || vitals.spo2 > 100) {
        errs.spo2 = "SpO₂ must fall between 70 and 100%.";
      }
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // Autosave progress API sync
  const saveProgress = async (stepNumber: number) => {
    setSaving(true);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const payload = {
        personalInformation: personal,
        lifestyle,
        clinicalHistory: clinical,
        familyHistory: family,
        vitalSigns: vitals,
        labValues: labs,
        wearableData: wearable,
        calculatedMetrics: calcs,
        uploadedHealthRecords: records
      };

      // Call profile endpoint (PUT updates or registers the profile setup progress)
      await fetch(`${apiUrl}/profile`, {
        method: "PUT",
        headers,
        body: JSON.stringify(payload)
      });

      // Save step to local storage
      localStorage.setItem("cardioguard_onboarding_step", String(stepNumber));
    } catch (e) {
      console.error("Autosave step synchronization failure", e);
    } finally {
      setSaving(false);
    }
  };

  const handleNext = async () => {
    if (!validateStep(activeStep)) return;
    const nextStep = activeStep + 1;
    setActiveStep(nextStep);
    await saveProgress(nextStep);
  };

  const handleBack = () => {
    if (activeStep > 1) {
      const prevStep = activeStep - 1;
      setActiveStep(prevStep);
      localStorage.setItem("cardioguard_onboarding_step", String(prevStep));
    }
  };

  const handleFinish = async () => {
    if (!validateStep(activeStep)) return;
    setSaving(true);
    try {
      const token = await getUserToken();
      const appCheckToken = await getAppCheckToken();
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      if (appCheckToken) headers["X-Firebase-App-Check"] = appCheckToken;

      const payload = {
        personalInformation: personal,
        lifestyle,
        clinicalHistory: clinical,
        familyHistory: family,
        vitalSigns: vitals,
        labValues: labs,
        wearableData: wearable,
        calculatedMetrics: calcs,
        uploadedHealthRecords: records
      };

      const res = await fetch(`${apiUrl}/profile`, {
        method: "PUT",
        headers,
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSuccess(true);
        localStorage.removeItem("cardioguard_onboarding_step");
        
        // Update App layout profile context status directly
        if (setProfileStatus) {
          setProfileStatus({
            profileExists: true,
            profileCompleted: true
          });
        }
        
        if (fetchUserProfile) {
          await fetchUserProfile();
        }

        setTimeout(() => {
          navigate("/dashboard", { replace: true });
        }, 1500);
      }
    } catch (err) {
      console.error("Failed to complete patient profile setup", err);
    } finally {
      setSaving(false);
    }
  };

  const toggleCondition = (cond: string) => {
    const list = clinical.medicalConditions.includes(cond)
      ? clinical.medicalConditions.filter(c => c !== cond)
      : [...clinical.medicalConditions, cond];
    setClinical({ ...clinical, medicalConditions: list });
  };

  const toggleSymptom = (sym: string) => {
    const list = clinical.currentSymptoms.includes(sym)
      ? clinical.currentSymptoms.filter(s => s !== sym)
      : [...clinical.currentSymptoms, sym];
    setClinical({ ...clinical, currentSymptoms: list });
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "50vh" }}>
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Configuring Patient Profile Setup Wizard...</span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "680px", margin: "0 auto", paddingBottom: "50px" }}>
      
      {/* ⚠️ Access Warning Disclaimer */}
      <div style={{ padding: "14px 20px", borderRadius: "12px", background: "rgba(255, 59, 48, 0.08)", border: "1px solid rgba(255, 59, 48, 0.2)", display: "flex", alignItems: "flex-start", gap: "12px" }}>
        <ShieldAlert size={18} color="var(--color-risk)" style={{ marginTop: "2px", flexShrink: 0 }} />
        <div style={{ fontSize: "0.75rem", color: "#FFFFFF", lineHeight: "1.4" }}>
          <span style={{ fontWeight: "700" }}>Dashboard Blocked:</span> CardioGuard AI requires a completed Patient Profile before executing cardiovascular risk inferences. Complete the steps below to initialize.
        </div>
      </div>

      {/* Wizard Header Progress Bar */}
      <div className="glass-panel" style={{ padding: "20px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <h2 style={{ fontSize: "1.35rem", fontWeight: "800", color: "#FFFFFF", margin: 0 }}>Onboarding Profile Wizard</h2>
            <span style={{ fontSize: "0.72rem", color: "var(--text-secondary)" }}>Step {activeStep} of 7: {
              activeStep === 1 ? "Personal Information" :
              activeStep === 2 ? "Lifestyle configuration" :
              activeStep === 3 ? "Clinical History details" :
              activeStep === 4 ? "Genetic Family History" :
              activeStep === 5 ? "Vital signs parameters" :
              activeStep === 6 ? "Lab reports cholesterol" : "Review and complete settings"
            }</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "var(--color-primary)" }}>{completionPct}% Done</span>
            {saving && <span style={{ fontSize: "0.58rem", color: "var(--text-muted)", marginTop: "2px" }}>Saving progress...</span>}
          </div>
        </div>

        {/* Multi-step indicator bar */}
        <div style={{ width: "100%", height: "6px", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "3px", overflow: "hidden", display: "flex", gap: "2px" }}>
          {[1, 2, 3, 4, 5, 6, 7].map(step => (
            <div 
              key={step} 
              style={{ 
                flex: 1, 
                height: "100%", 
                backgroundColor: step <= activeStep ? "var(--color-primary)" : "rgba(255,255,255,0.05)",
                transition: "background-color 0.3s ease" 
              }} 
            />
          ))}
        </div>
      </div>

      {success ? (
        <div className="glass-panel" style={{ padding: "40px", textAlign: "center", display: "flex", flexDirection: "column", gap: "16px", alignItems: "center" }}>
          <CheckCircle size={48} color="var(--color-normal)" style={{ animation: "scaleUp 0.5s ease-out" }} />
          <h3 style={{ fontSize: "1.2rem", fontWeight: "800", color: "#FFFFFF" }}>Profile Initialized Successfully</h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Encrypted patient records generated. Navigating to your clinical dashboard...</p>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: "24px" }}>
          
          {/* Step 1: Personal Info */}
          {activeStep === 1 && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }} className="profile-grid">
              <div style={{ display: "flex", flexDirection: "column", gap: "4px", gridColumn: "span 2" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Full Name *</label>
                <input 
                  type="text"
                  value={personal.fullName}
                  onChange={(e) => setPersonal({ ...personal, fullName: e.target.value })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  required
                />
                {errors.fullName && <span style={{ fontSize: "0.62rem", color: "var(--color-risk)" }}>{errors.fullName}</span>}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Gender</label>
                <select 
                  value={personal.gender}
                  onChange={(e) => setPersonal({ ...personal, gender: e.target.value })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Date of Birth *</label>
                <input 
                  type="date"
                  value={personal.dob}
                  onChange={(e) => setPersonal({ ...personal, dob: e.target.value })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  required
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Height (cm) *</label>
                <input 
                  type="number"
                  value={personal.height}
                  onChange={(e) => setPersonal({ ...personal, height: Number(e.target.value) })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  required
                />
                {errors.height && <span style={{ fontSize: "0.62rem", color: "var(--color-risk)" }}>{errors.height}</span>}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Weight (kg) *</label>
                <input 
                  type="number"
                  value={personal.weight}
                  onChange={(e) => setPersonal({ ...personal, weight: Number(e.target.value) })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  required
                />
                {errors.weight && <span style={{ fontSize: "0.62rem", color: "var(--color-risk)" }}>{errors.weight}</span>}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Blood Group</label>
                <select 
                  value={personal.bloodGroup}
                  onChange={(e) => setPersonal({ ...personal, bloodGroup: e.target.value })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
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

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Contact Number</label>
                <input 
                  type="text"
                  value={personal.phone}
                  onChange={(e) => setPersonal({ ...personal, phone: e.target.value })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                />
                {errors.phone && <span style={{ fontSize: "0.62rem", color: "var(--color-risk)" }}>{errors.phone}</span>}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px", gridColumn: "span 2" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Email Address</label>
                <input 
                  type="email"
                  value={personal.email}
                  onChange={(e) => setPersonal({ ...personal, email: e.target.value })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                />
                {errors.email && <span style={{ fontSize: "0.62rem", color: "var(--color-risk)" }}>{errors.email}</span>}
              </div>
            </div>
          )}

          {/* Step 2: Lifestyle */}
          {activeStep === 2 && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }} className="profile-grid">
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Activity Level</label>
                <select 
                  value={lifestyle.activityLevel}
                  onChange={(e) => setLifestyle({ ...lifestyle, activityLevel: e.target.value })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                >
                  <option value="Sedentary">Sedentary</option>
                  <option value="Lightly Active">Lightly Active</option>
                  <option value="Moderately Active">Moderately Active</option>
                  <option value="Very Active">Very Active</option>
                  <option value="Athlete">Athlete</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Smoking Status</label>
                <select 
                  value={lifestyle.smokingStatus}
                  onChange={(e) => setLifestyle({ ...lifestyle, smokingStatus: e.target.value })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                >
                  <option value="Never">Never</option>
                  <option value="Former">Former</option>
                  <option value="Current">Current</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Alcohol Consumption</label>
                <select 
                  value={lifestyle.alcoholConsumption}
                  onChange={(e) => setLifestyle({ ...lifestyle, alcoholConsumption: e.target.value })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                >
                  <option value="Never">Never</option>
                  <option value="Occasionally">Occasionally</option>
                  <option value="Weekly">Weekly</option>
                  <option value="Frequently">Frequently</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Average Sleep (hours/day)</label>
                <input 
                  type="number"
                  step="0.1"
                  value={lifestyle.avgSleep}
                  onChange={(e) => setLifestyle({ ...lifestyle, avgSleep: Number(e.target.value) })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Daily Water (Litres/day)</label>
                <input 
                  type="number"
                  step="0.1"
                  value={lifestyle.avgWater}
                  onChange={(e) => setLifestyle({ ...lifestyle, avgWater: Number(e.target.value) })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Daily Steps Goal</label>
                <input 
                  type="number"
                  value={lifestyle.avgSteps}
                  onChange={(e) => setLifestyle({ ...lifestyle, avgSteps: Number(e.target.value) })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                />
              </div>
            </div>
          )}

          {/* Step 3: Clinical History */}
          {activeStep === 3 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-secondary)", fontWeight: "700" }}>Medical Conditions</span>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "8px" }}>
                  {[
                    "Hypertension", "Diabetes", "High Cholesterol", "Coronary Artery Disease", 
                    "Previous Heart Attack", "Heart Failure", "Stroke", "Arrhythmia", 
                    "Kidney Disease", "Thyroid Disorder", "Asthma", "None"
                  ].map(c => (
                    <label key={c} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.7rem", cursor: "pointer" }}>
                      <input 
                        type="checkbox"
                        checked={clinical.medicalConditions.includes(c)}
                        onChange={() => toggleCondition(c)}
                      />
                      <span>{c}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px", borderTop: "1px solid var(--border-glass)", paddingTop: "12px" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-secondary)", fontWeight: "700" }}>Current Symptoms</span>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "8px" }}>
                  {[
                    "Chest Pain", "Chest Tightness", "Shortness of Breath", "Palpitations",
                    "Dizziness", "Fainting", "Fatigue", "Swollen Legs",
                    "Excessive Sweating", "Pain in Left Arm", "Jaw Pain", "Nausea", "No Symptoms"
                  ].map(s => (
                    <label key={s} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.7rem", cursor: "pointer" }}>
                      <input 
                        type="checkbox"
                        checked={clinical.currentSymptoms.includes(s)}
                        onChange={() => toggleSymptom(s)}
                      />
                      <span>{s}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", borderTop: "1px solid var(--border-glass)", paddingTop: "12px" }} className="profile-grid">
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Current Medications</label>
                  <textarea 
                    rows={2}
                    value={clinical.currentMedications}
                    onChange={(e) => setClinical({ ...clinical, currentMedications: e.target.value })}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem", resize: "none" }}
                  />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Known Allergies</label>
                  <textarea 
                    rows={2}
                    value={clinical.knownAllergies}
                    onChange={(e) => setClinical({ ...clinical, knownAllergies: e.target.value })}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem", resize: "none" }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Family History */}
          {activeStep === 4 && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }} className="profile-grid">
              {[
                { field: "familyHeartDisease", label: "Heart Disease" },
                { field: "familyHypertension", label: "Hypertension" },
                { field: "familyDiabetes", label: "Diabetes" },
                { field: "familyStroke", label: "Stroke" },
                { field: "familyCholesterol", label: "High Cholesterol" },
                { field: "familySuddenCardiacDeath", label: "Sudden Cardiac Death" }
              ].map(f => (
                <div key={f.field} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{f.label}</label>
                  <select 
                    value={family[f.field as keyof FamilyHistory]}
                    onChange={(e) => setFamily({ ...family, [f.field]: e.target.value })}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  >
                    <option value="Yes">Yes</option>
                    <option value="No">No</option>
                    <option value="Don't Know">Don't Know</option>
                  </select>
                </div>
              ))}
            </div>
          )}

          {/* Step 5: Vital Signs */}
          {activeStep === 5 && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", width: "100%" }} className="profile-grid">
              {isFitConnected && (
                <div style={{
                  gridColumn: "span 2",
                  padding: "12px 16px",
                  borderRadius: "8px",
                  background: "rgba(52, 199, 89, 0.08)",
                  border: "1px solid rgba(52, 199, 89, 0.2)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "8px",
                  width: "100%"
                }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#FFFFFF" }}>Wearable Connected (Google Fit / Health Connect)</span>
                    <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>Pulse rate of {dailyStats?.avgBpm || 68} BPM and {dailyStats?.steps || 7200} steps detected.</span>
                  </div>
                  <button 
                    type="button" 
                    onClick={autoPopulateFromWearable}
                    className="btn-primary"
                    style={{ padding: "6px 12px", fontSize: "0.68rem", background: "var(--color-primary)" }}
                  >
                    Auto-Fill Telemetry
                  </button>
                </div>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Systolic Blood Pressure (mmHg)</label>
                <input 
                  type="number"
                  value={vitals.systolicBp}
                  onChange={(e) => setVitals({ ...vitals, systolicBp: Number(e.target.value) })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                />
                {errors.systolicBp && <span style={{ fontSize: "0.62rem", color: "var(--color-risk)" }}>{errors.systolicBp}</span>}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Diastolic Blood Pressure (mmHg)</label>
                <input 
                  type="number"
                  value={vitals.diastolicBp}
                  onChange={(e) => setVitals({ ...vitals, diastolicBp: Number(e.target.value) })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                />
                {errors.diastolicBp && <span style={{ fontSize: "0.62rem", color: "var(--color-risk)" }}>{errors.diastolicBp}</span>}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Resting Heart Rate (BPM)</label>
                <input 
                  type="number"
                  value={vitals.restingHr}
                  onChange={(e) => setVitals({ ...vitals, restingHr: Number(e.target.value) })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                />
                {errors.restingHr && <span style={{ fontSize: "0.62rem", color: "var(--color-risk)" }}>{errors.restingHr}</span>}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Oxygen Saturation SpO₂ (%)</label>
                <input 
                  type="number"
                  value={vitals.spo2}
                  onChange={(e) => setVitals({ ...vitals, spo2: Number(e.target.value) })}
                  style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                />
                {errors.spo2 && <span style={{ fontSize: "0.62rem", color: "var(--color-risk)" }}>{errors.spo2}</span>}
              </div>
            </div>
          )}

          {/* Step 6: Lab Values */}
          {activeStep === 6 && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }} className="profile-grid">
              {[
                { field: "totalCholesterol", label: "Total Cholesterol (mg/dL)" },
                { field: "ldl", label: "LDL Cholesterol (mg/dL)" },
                { field: "hdl", label: "HDL Cholesterol (mg/dL)" },
                { field: "triglycerides", label: "Triglycerides (mg/dL)" },
                { field: "fastingBloodSugar", label: "Fasting Blood Sugar (mg/dL)" },
                { field: "hba1c", label: "HbA1c (%)" }
              ].map(lb => (
                <div key={lb.field} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{lb.label}</label>
                  <input 
                    type="number"
                    step="0.01"
                    value={labs[lb.field as keyof LabValues] || ""}
                    onChange={(e) => setLabs({ ...labs, [lb.field]: Number(e.target.value) })}
                    style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.75rem" }}
                  />
                </div>
              ))}
            </div>
          )}

          {/* Step 7: Review & Auto Calculations Summary */}
          {activeStep === 7 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <div style={{ display: "flex", gap: "8px", backgroundColor: "rgba(52, 199, 89, 0.05)", border: "1px solid rgba(52, 199, 89, 0.15)", borderRadius: "8px", padding: "12px", fontSize: "0.72rem", color: "var(--text-secondary)" }}>
                <CheckCircle size={15} color="var(--color-normal)" style={{ flexShrink: 0, marginTop: "1px" }} />
                <span>All core steps registered successfully. Verify BMR / TDEE calculations and hit **Save & Finish** to sync with clinical DB modules.</span>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "10px" }}>
                {[
                  { label: "BMI Ratio", val: calcs.bmi, sub: calcs.bmiCategory },
                  { label: "BMR Index", val: `${calcs.bmr} kcal`, sub: "Basal Metabolic Rate" },
                  { label: "TDEE Index", val: `${calcs.tdee} kcal`, sub: "Daily Energy Expenditure" },
                  { label: "Healthy Weight", val: calcs.healthyWeightRange, sub: "Optimal target limits" },
                  { label: "Fluid Goals", val: `${calcs.recWater} L`, sub: "Water daily target" },
                  { label: "Protein Goals", val: `${calcs.recProtein} g`, sub: "Protein daily target" }
                ].map((c, idx) => (
                  <div key={idx} style={{ padding: "10px", borderRadius: "8px", backgroundColor: "rgba(255,255,255,0.01)", border: "1px solid var(--border-glass)", display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "0.6rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>{c.label}</span>
                    <span style={{ fontSize: "0.95rem", fontWeight: "900", color: "#FFFFFF" }}>{c.val}</span>
                    <span style={{ fontSize: "0.55rem", color: "var(--text-muted)", marginTop: "1px" }}>{c.sub}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Previous / Next Actions Buttons */}
          <div style={{ display: "flex", justifyContent: "space-between", borderTop: "1px solid var(--border-glass)", paddingTop: "16px", marginTop: "24px" }}>
            <button 
              type="button" 
              onClick={handleBack}
              disabled={activeStep === 1 || saving}
              className="btn-secondary"
              style={{ padding: "10px 20px", fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "6px" }}
            >
              <ChevronLeft size={14} /> Previous Step
            </button>

            {activeStep < 7 ? (
              <button 
                type="button" 
                onClick={handleNext}
                disabled={saving}
                className="btn-primary"
                style={{ padding: "10px 20px", fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "6px" }}
              >
                Next Step <ChevronRight size={14} />
              </button>
            ) : (
              <button 
                type="button" 
                onClick={handleFinish}
                disabled={saving}
                className="btn-primary"
                style={{ padding: "10px 24px", fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "8px", background: "linear-gradient(135deg, var(--color-primary), var(--color-secondary))" }}
              >
                <Save size={14} /> {saving ? "Finishing..." : "Save & Finish Onboarding"}
              </button>
            )}
          </div>

        </div>
      )}

    </div>
  );
};

export default ProfileSetup;
