import React from "react";
import { motion } from "framer-motion";

interface ActivityRingsProps {
  calories: number;   
  steps: number;      
  activeMin: number;  
}

export const ActivityRings: React.FC<ActivityRingsProps> = ({
  calories = 320,
  steps = 6200,
  activeMin = 22,
}) => {
  const calorieTarget = 500;
  const stepTarget = 10000;
  const activeMinTarget = 30;

  const movePct = Math.min(calories / calorieTarget, 0.999);
  const exercisePct = Math.min(activeMin / activeMinTarget, 0.999);
  const standPct = Math.min(steps / stepTarget, 0.999);

  const size = 160;
  const center = size / 2;
  const strokeWidth = 12;
  const gap = 3;

  const ringRadius = (ringIndex: number) => {
    return center - strokeWidth / 2 - ringIndex * (strokeWidth + gap);
  };

  const ringCircumference = (radius: number) => {
    return 2 * Math.PI * radius;
  };

  const renderRing = (
    pct: number,
    radius: number,
    color: string,
    bgColor: string,
    index: number
  ) => {
    const circ = ringCircumference(radius);
    const strokeDashoffset = circ - pct * circ;

    return (
      <g key={index}>
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke={bgColor}
          strokeWidth={strokeWidth}
          fill="none"
        />
        <motion.circle
          cx={center}
          cy={center}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          strokeLinecap="round"
          fill="none"
          transform={`rotate(-90 ${center} ${center})`}
        />
      </g>
    );
  };

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "20px" }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {renderRing(movePct, ringRadius(0), "#FF1A53", "#330510", 0)}       
        {renderRing(exercisePct, ringRadius(1), "#34D399", "#064E3B", 1)}   
        {renderRing(standPct, ringRadius(2), "#38BDF8", "#0C4A6E", 2)}      
      </svg>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px", flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#FF1A53" }} />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Move</span>
            <span style={{ fontSize: "0.85rem", color: "#FFFFFF", fontWeight: "700" }}>{Math.round(calories)} / 500 kcal</span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#34D399" }} />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Exercise</span>
            <span style={{ fontSize: "0.85rem", color: "#FFFFFF", fontWeight: "700" }}>{Math.round(activeMin)} / 30 min</span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#38BDF8" }} />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Stand</span>
            <span style={{ fontSize: "0.85rem", color: "#FFFFFF", fontWeight: "700" }}>{Math.round((steps / 10000) * 12)} / 12 hr</span>
          </div>
        </div>
      </div>
    </div>
  );
};
