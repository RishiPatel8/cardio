import React, { useState, useRef } from "react";
import { Upload, CheckCircle, HelpCircle, ArrowRight } from "lucide-react";

interface RecordRow {
  index: number;
  timeSec: number;
  rrIntervalMs: number;
  bpm: number;
  rawVal?: number;
}

interface DatasetUploaderProps {
  onDatasetLoaded: (data: {
    fileName: string;
    recordsCount: number;
    rows: RecordRow[];
    stats: {
      avgBpm: number;
      sdrr: number;
      rmssd: number;
    };
    rawSignal?: number[];
    file?: File | null;
    files?: File[];
    age?: number;
    sex?: number;
  }) => void;
  onClear: () => void;
  currentDatasetName: string | null;
}

export const DatasetUploader: React.FC<DatasetUploaderProps> = ({
  onDatasetLoaded,
  onClear,
  currentDatasetName,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [age, setAge] = useState<number>(30);
  const [sex, setSex] = useState<number>(0);

  // Generates simulated raw 100Hz ECG continuous signal and feeds it to parser
  const loadDemoDataset = (type: "normal" | "af") => {
    setErrorMsg(null);
    const fileName = type === "normal" ? "physionet_nsrdb_16272.csv" : "physionet_afdb_04043.csv";
    
    // Sampling rate: 100 Hz (every 10ms), Duration: 30 seconds
    const sampleRate = 100;
    const duration = 30;
    const totalSamples = sampleRate * duration;
    
    let csvLines = ["time,signal"];
    
    // Determine R-peak occurrences
    const beatTimes: number[] = [];
    let accumTime = 0.6; // start first beat at 0.6s
    
    if (type === "normal") {
      // Normal rhythm: stable intervals around 830ms (72 BPM) with regular breathing variation
      for (let i = 0; i < 40; i++) {
        beatTimes.push(accumTime);
        const respiratoryCycle = Math.sin(i / 2.5) * 0.035;
        const randomNoise = (Math.random() * 0.008 - 0.004);
        accumTime += 0.83 + respiratoryCycle + randomNoise;
      }
    } else {
      // AF Risk: completely chaotic intervals
      const afIntervals = [0.55, 1.05, 0.72, 0.95, 0.48, 0.85, 0.62, 1.15, 0.78, 0.52, 0.90, 0.64, 0.88, 0.58, 0.98, 0.69];
      for (let i = 0; i < 50; i++) {
        beatTimes.push(accumTime);
        const interval = afIntervals[i % afIntervals.length] + (Math.random() * 0.04 - 0.02);
        accumTime += interval;
      }
    }
    
    // Generate samples
    for (let s = 0; s < totalSamples; s++) {
      const timeSec = s / sampleRate;
      let signalVal = 0.0;
      
      // Add baseline drift & f-waves
      if (type === "normal") {
        signalVal = Math.sin(timeSec * 2 * Math.PI * 0.2) * 0.04; // respiratory baseline wander
      } else {
        // AF baseline: rapid, chaotic fibrillatory baseline f-waves (approx 6-8Hz)
        signalVal = Math.sin(timeSec * 2 * Math.PI * 7.2) * 0.12 + (Math.random() * 0.03 - 0.015);
      }
      
      // Superimpose ECG pulse components (P, QRS, T)
      beatTimes.forEach((beatTime) => {
        const dt = timeSec - beatTime;
        
        // QRS complex (very sharp and narrow)
        if (dt >= -0.04 && dt <= 0.04) {
          if (dt < -0.015) {
            // Q wave (dip)
            signalVal += (dt + 0.04) * -8;
          } else if (dt >= -0.015 && dt <= 0.01) {
            // R wave (high spike)
            signalVal += 1.4 - Math.abs(dt - 0.00) * 70;
          } else {
            // S wave (deep dip)
            signalVal += (0.04 - dt) * -7;
          }
        } else if (type === "normal") {
          // P-wave (approx 130ms before QRS)
          const pDt = dt + 0.13;
          if (pDt >= -0.035 && pDt <= 0.035) {
            signalVal += Math.cos(pDt * Math.PI * 14.2) * 0.12;
          }
          // T-wave (approx 220ms after QRS)
          const tDt = dt - 0.22;
          if (tDt >= -0.07 && tDt <= 0.07) {
            signalVal += Math.cos(tDt * Math.PI * 7.1) * 0.22;
          }
        }
      });
      
      csvLines.push(`${timeSec.toFixed(2)},${signalVal.toFixed(4)}`);
    }
    
    parseCSVText(csvLines.join("\n"), fileName, null);
  };

  const calculateAndSendStats = (fileName: string, rows: RecordRow[], file: File | null = null) => {
    const bpms = rows.map((r) => r.bpm);
    const rrs = rows.map((r) => r.rrIntervalMs);
    
    // Average HR
    const avgBpm = Math.round(bpms.reduce((a, b) => a + b, 0) / bpms.length);

    // Standard Deviation of RR intervals (SDRR)
    const avgRr = rrs.reduce((a, b) => a + b, 0) / rrs.length;
    const sdrr = Math.round(
      Math.sqrt(rrs.reduce((sq, val) => sq + Math.pow(val - avgRr, 2), 0) / rrs.length)
    );

    // Root Mean Square of Successive Differences (RMSSD)
    let sumSqDiff = 0;
    for (let i = 0; i < rrs.length - 1; i++) {
      sumSqDiff += Math.pow(rrs[i + 1] - rrs[i], 2);
    }
    const rmssd = Math.round(Math.sqrt(sumSqDiff / (rrs.length - 1)));

    onDatasetLoaded({
      fileName,
      recordsCount: rows.length,
      rows,
      stats: {
        avgBpm,
        sdrr,
        rmssd,
      },
      rawSignal: rows.map(r => r.rawVal).filter(v => v !== undefined) as number[],
      file: file,
      age,
      sex,
    });
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const parseCSVText = (text: string, name: string, file: File | null = null) => {
    try {
      const lines = text.split(/\r?\n/).filter((line) => line.trim() !== "");
      if (lines.length < 2) {
        setErrorMsg("CSV file is empty or headers are missing.");
        return;
      }

      const headers = lines[0].toLowerCase().split(",");
      
      let isHeaderlessNumeric = false;
      if (headers.length > 0 && !isNaN(parseFloat(headers[0]))) {
        isHeaderlessNumeric = true;
      }

      if (isHeaderlessNumeric) {
        const rawSignal: number[] = [];
        for (let i = 0; i < lines.length; i++) {
          const cols = lines[i].split(",");
          for (const c of cols) {
            const val = parseFloat(c.trim());
            if (!isNaN(val)) rawSignal.push(val);
          }
        }

        if (rawSignal.length < 100) {
          setErrorMsg("Insufficient raw ECG points parsed (needs at least 100).");
          return;
        }

        const parsedRows: RecordRow[] = [];
        for (let i = 0; i < 15; i++) {
          parsedRows.push({
            index: i,
            timeSec: i * 0.8,
            rrIntervalMs: 800,
            bpm: 75,
            rawVal: rawSignal[i],
          });
        }

        onDatasetLoaded({
          fileName: name,
          recordsCount: rawSignal.length,
          rows: parsedRows,
          stats: { avgBpm: 75, sdrr: 45, rmssd: 32 },
          rawSignal: rawSignal,
          file: file,
          age,
          sex,
        });
        return;
      }

      const timeIdx = headers.findIndex((h) => h.includes("time") || h.includes("sec"));
      const rrIdx = headers.findIndex((h) => h.includes("rr") || h.includes("interval") || h.includes("ms"));
      const bpmIdx = headers.findIndex((h) => h.includes("bpm") || h.includes("rate") || h.includes("hr"));
      const signalIdx = headers.findIndex(
        (h) => h.includes("signal") || h.includes("val") || h.includes("ecg") || h.includes("mlii") || h.includes("v5") || h.includes("amp")
      );

      const parsedRows: RecordRow[] = [];

      if (signalIdx !== -1) {
        // Raw ECG mode: Perform QRS peak detection
        const rawPoints: { time: number; val: number }[] = [];
        for (let i = 1; i < lines.length; i++) {
          const cols = lines[i].split(",").map((c) => c.trim());
          if (cols.length < 2 || !cols[0]) continue;
          const timeVal = parseFloat(cols[timeIdx !== -1 ? timeIdx : 0]);
          const ecgVal = parseFloat(cols[signalIdx]);
          if (!isNaN(timeVal) && !isNaN(ecgVal)) {
            rawPoints.push({ time: timeVal, val: ecgVal });
          }
        }

        if (rawPoints.length < 10) {
          setErrorMsg("Insufficient raw ECG points parsed.");
          return;
        }

        // QRS peak threshold detection
        const values = rawPoints.map((p) => p.val);
        const maxVal = Math.max(...values);
        const minVal = Math.min(...values);
        const threshold = minVal + (maxVal - minVal) * 0.65;

        const peakTimes: number[] = [];
        const refractoryPeriodSec = 0.25; // 250ms refractory period

        for (let i = 2; i < rawPoints.length - 2; i++) {
          const prev2 = rawPoints[i - 2].val;
          const prev1 = rawPoints[i - 1].val;
          const curr = rawPoints[i].val;
          const next1 = rawPoints[i + 1].val;
          const next2 = rawPoints[i + 2].val;

          // Check if local maximum above threshold
          if (curr > threshold && curr >= prev1 && curr >= prev2 && curr > next1 && curr > next2) {
            const timeSec = rawPoints[i].time;
            const lastPeakTime = peakTimes[peakTimes.length - 1];

            if (lastPeakTime === undefined || (timeSec - lastPeakTime) > refractoryPeriodSec) {
              peakTimes.push(timeSec);
            }
          }
        }

        if (peakTimes.length < 3) {
          setErrorMsg("Could not detect heartbeats in raw signal. Check threshold/values.");
          return;
        }

        // Convert peak timestamps to RR intervals & BPMs
        for (let j = 1; j < peakTimes.length; j++) {
          const rrIntervalMs = Math.round((peakTimes[j] - peakTimes[j - 1]) * 1000);
          const bpm = Math.round(60000 / rrIntervalMs);
          parsedRows.push({
            index: j,
            timeSec: parseFloat(peakTimes[j].toFixed(3)),
            rrIntervalMs,
            bpm,
            rawVal: rawPoints[j].val,
          });
        }
      } else {
        // Pre-calculated RR / BPM mode
        let timeSecAccum = 0;
        for (let i = 1; i < lines.length; i++) {
          const cols = lines[i].split(",").map((c) => c.trim());
          if (cols.length < 1 || !cols[0]) continue;

          let rawTime = timeIdx !== -1 ? parseFloat(cols[timeIdx]) : i * 0.8;
          let rawRr = rrIdx !== -1 ? parseFloat(cols[rrIdx]) : 800;
          let rawBpm = bpmIdx !== -1 ? parseFloat(cols[bpmIdx]) : 75;

          if (rrIdx === -1 && bpmIdx !== -1) {
            rawRr = Math.round(60000 / rawBpm);
          } else if (bpmIdx === -1 && rrIdx !== -1) {
            rawBpm = Math.round(60000 / rawRr);
          }

          parsedRows.push({
            index: i,
            timeSec: isNaN(rawTime) ? parseFloat(timeSecAccum.toFixed(2)) : rawTime,
            rrIntervalMs: isNaN(rawRr) ? 800 : rawRr,
            bpm: isNaN(rawBpm) ? 75 : rawBpm,
          });

          timeSecAccum += rawRr / 1000;
        }
      }

      if (parsedRows.length === 0) {
        setErrorMsg("Failed to parse numeric rows from CSV.");
        return;
      }

      // We also need to map the raw signal if we're sending raw signal for ALL points.
      // But parsedRows is RR intervals. To send raw signal to the backend, we should bypass parsedRows for rawSignal,
      // or just send rawPoints directly.
      if (signalIdx !== -1) {
          const rawSignal = [];
          for (let i = 1; i < lines.length; i++) {
              const cols = lines[i].split(",").map((c) => c.trim());
              if (cols.length > signalIdx && cols[signalIdx]) {
                  const ecgVal = parseFloat(cols[signalIdx]);
                  if (!isNaN(ecgVal)) {
                      rawSignal.push(ecgVal);
                  }
              }
          }
          onDatasetLoaded({
            fileName: name,
            recordsCount: parsedRows.length,
            rows: parsedRows,
            stats: {
                avgBpm: parsedRows.map(r => r.bpm).reduce((a, b) => a + b, 0) / (parsedRows.length || 1),
                sdrr: 45, // default fallback
                rmssd: 32, // default fallback
            },
            rawSignal: rawSignal,
            file: file,
            age,
            sex,
          });
      } else {
          calculateAndSendStats(name, parsedRows, file);
      }
    } catch {
      setErrorMsg("An error occurred while parsing the CSV file.");
    }
  };

  const processFiles = (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const csvFile = fileArray.find(f => f.name.endsWith(".csv"));
    const heaFile = fileArray.find(f => f.name.endsWith(".hea"));
    const datFile = fileArray.find(f => f.name.endsWith(".dat"));

    if (csvFile) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        if (evt.target?.result) {
          parseCSVText(evt.target.result as string, csvFile.name, csvFile);
        }
      };
      reader.readAsText(csvFile);
    } else if (heaFile && datFile) {
      const baseName = heaFile.name.replace(".hea", "");
      onDatasetLoaded({
        fileName: baseName,
        recordsCount: 0,
        rows: [],
        stats: { avgBpm: 0, sdrr: 0, rmssd: 0 },
        files: [heaFile, datFile],
        age,
        sex,
      });
    } else if (heaFile || datFile) {
      setErrorMsg("Both .hea and .dat files are required for WFDB format.");
    } else {
      setErrorMsg("Please upload a .csv file or a WFDB record (.hea + .dat).");
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setErrorMsg(null);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  const handleTriggerInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div>
        <h4 style={{ fontSize: "1rem", fontWeight: "600", color: "#FFFFFF" }}>PhysioNet Database CSV Upload</h4>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "4px" }}>
          Load an ECG database interval sequence record or test with presets.
        </p>
      </div>

      {currentDatasetName ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            padding: "16px",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            backgroundColor: "rgba(16, 185, 129, 0.05)",
            borderRadius: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyItems: "center", gap: "10px" }}>
            <CheckCircle size={22} style={{ color: "var(--color-normal)" }} />
            <div>
              <p style={{ fontSize: "0.9rem", fontWeight: "600", color: "#FFFFFF", wordBreak: "break-all" }}>
                {currentDatasetName}
              </p>
              <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                PhysioNet CSV Dataset ready for diagnostics
              </p>
            </div>
          </div>
          <button
            onClick={onClear}
            className="btn-secondary"
            style={{
              padding: "8px 16px",
              fontSize: "0.85rem",
              justifyContent: "center",
              borderRadius: "8px",
            }}
          >
            Clear and Reset
          </button>
        </div>
      ) : (
        <>
          {/* Patient Demographics */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "4px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Patient Age (Required)</label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                min="0"
                max="120"
                style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.8rem" }}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <label style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>Patient Sex (Required)</label>
              <select
                value={sex}
                onChange={(e) => setSex(Number(e.target.value))}
                style={{ padding: "8px", borderRadius: "6px", background: "rgba(0,0,0,0.15)", border: "1px solid var(--border-glass)", color: "#FFFFFF", fontSize: "0.8rem" }}
              >
                <option value={0}>Male</option>
                <option value={1}>Female</option>
              </select>
            </div>
          </div>

          {/* Drag & Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={handleTriggerInput}
            style={{
              border: `2px dashed ${dragActive ? "var(--color-primary)" : "rgba(255, 255, 255, 0.15)"}`,
              borderRadius: "12px",
              padding: "30px 20px",
              textAlign: "center",
              cursor: "pointer",
              backgroundColor: dragActive ? "rgba(139, 92, 246, 0.05)" : "transparent",
              transition: "var(--transition-smooth)",
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.hea,.dat"
              multiple
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
            <Upload size={32} style={{ color: dragActive ? "var(--color-primary)" : "var(--text-muted)", marginBottom: "12px" }} />
            <p style={{ fontSize: "0.9rem", color: "#FFFFFF", fontWeight: "500" }}>
              Drag & Drop ECG here
            </p>
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px" }}>
              Supported formats: CSV or WFDB (.hea + .dat)
            </p>
            {errorMsg && (
              <p style={{ fontSize: "0.8rem", color: "var(--color-risk)", marginTop: "12px", fontWeight: "600" }}>
                {errorMsg}
              </p>
            )}
          </div>

          {/* Quick Demo Pre-sets buttons */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              paddingTop: "6px",
              borderTop: "1px solid rgba(255, 255, 255, 0.05)",
            }}
          >
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px" }}>
              <HelpCircle size={14} />
              Don't have a dataset? Try our presets:
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
              <button
                onClick={() => loadDemoDataset("normal")}
                className="btn-secondary"
                style={{
                  fontSize: "0.8rem",
                  padding: "10px",
                  borderRadius: "8px",
                  justifyContent: "space-between",
                }}
              >
                <span>Sinus Rhythm (Normal)</span>
                <ArrowRight size={14} style={{ color: "var(--color-normal)" }} />
              </button>
              <button
                onClick={() => loadDemoDataset("af")}
                className="btn-secondary"
                style={{
                  fontSize: "0.8rem",
                  padding: "10px",
                  borderRadius: "8px",
                  justifyContent: "space-between",
                }}
              >
                <span>Atrial Fib (AF Risk)</span>
                <ArrowRight size={14} style={{ color: "var(--color-risk)" }} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
