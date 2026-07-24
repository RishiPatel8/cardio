import React, { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

interface DataPoint {
  time: string;
  value: number;
}

interface MetricConfig {
  label: string;
  unit: string;
  color: string;
  domain: [number, number];
  gradientId: string;
}

const METRIC_CONFIGS: Record<string, MetricConfig> = {
  heartRate: { label: "Heart Rate", unit: "BPM", color: "#FF2D55", domain: [50, 120], gradientId: "colorBpm" },
  hrv: { label: "Heart Rate Variability", unit: "ms", color: "#AF52DE", domain: [20, 100], gradientId: "colorHrv" },
  spo2: { label: "Oxygen Saturation", unit: "%", color: "#007AFF", domain: [90, 100], gradientId: "colorSpo2" },
  sleep: { label: "Sleep Duration", unit: "min", color: "#5856D6", domain: [200, 600], gradientId: "colorSleep" },
  steps: { label: "Active Steps", unit: "steps", color: "#34C759", domain: [0, 12000], gradientId: "colorSteps" },
  calories: { label: "Active Calories", unit: "kcal", color: "#FF9500", domain: [0, 800], gradientId: "colorCalories" },
  stress: { label: "Stress Level", unit: "lvl", color: "#FFCC00", domain: [0, 10], gradientId: "colorStress" },
};

interface HeartRateChartProps {
  activeMetric: string;
  data: Record<string, DataPoint[]>;
}

export const HeartRateChart: React.FC<HeartRateChartProps> = React.memo(({ activeMetric = "heartRate", data }) => {
  const [period, setPeriod] = useState<"1d" | "7d" | "30d" | "90d" | "1y">("1d");

  const config = METRIC_CONFIGS[activeMetric] || METRIC_CONFIGS.heartRate;
  const activePoints = data[activeMetric] || [];

  return (
    <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h3 style={{ fontSize: "1.15rem", fontWeight: "800", color: "#FFFFFF" }}>
            {config.label} Trend
          </h3>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Interactive Apple Health Telemetry</span>
        </div>

        <div style={{ display: "flex", gap: "4px", backgroundColor: "rgba(255, 255, 255, 0.04)", padding: "4px", borderRadius: "10px" }}>
          {(["1d", "7d", "30d", "90d", "1y"] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              style={{
                padding: "6px 12px",
                fontSize: "0.7rem",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
                backgroundColor: period === p ? "var(--color-primary)" : "transparent",
                color: period === p ? "#FFFFFF" : "var(--text-secondary)",
                fontWeight: "600",
                transition: "all 0.15s ease"
              }}
            >
              {p.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          <AreaChart data={activePoints} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id={config.gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={config.color} stopOpacity={0.4}/>
                <stop offset="95%" stopColor={config.color} stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              stroke="var(--text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              domain={config.domain}
              stroke="var(--text-muted)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1B1D24",
                border: "1px solid var(--border-glass)",
                borderRadius: "12px",
                color: "#FFFFFF",
                fontSize: "0.8rem",
              }}
              formatter={(value: any) => [`${value} ${config.unit}`, config.label]}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={config.color}
              strokeWidth={3}
              fillOpacity={1}
              fill={`url(#${config.gradientId})`}
              animationDuration={500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});
