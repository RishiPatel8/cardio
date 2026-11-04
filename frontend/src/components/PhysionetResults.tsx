import React, { useEffect, useRef } from "react";
import { Activity, AlertTriangle, CheckCircle, BarChart3 } from "lucide-react";
import * as echarts from "echarts";

interface PhysionetResultsProps {
  data: {
    record_id: string;
    sampling_rate: number;
    segments_analyzed: number;
    prediction: {
      class: string;
      label: string;
      confidence: number;
    };
    probabilities: {
      max_risk_prob: number;
      avg_risk_prob: number;
    };
    distribution: Record<string, number>;
    dominant_class: string;
    shap: {
      available: boolean;
      values: any[];
    };
    reference_annotations: {
      available: boolean;
    };
    highest_risk_segment: number[];
  };
  onClose: () => void;
}

export const PhysionetResults: React.FC<PhysionetResultsProps> = ({ data, onClose }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const shapRef = useRef<HTMLDivElement>(null);

  const isAnomalous = data.prediction.class !== "0";

  // ECharts render
  useEffect(() => {
    if (!chartRef.current || !data.highest_risk_segment) return;
    
    const chart = echarts.init(chartRef.current);
    const times = Array.from({ length: data.highest_risk_segment.length }, (_, i) => i * (1000 / data.sampling_rate));
    
    chart.setOption({
      grid: { top: 20, right: 20, bottom: 30, left: 50 },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: times.map(t => t.toFixed(1) + 'ms'),
        axisLabel: { color: 'rgba(255,255,255,0.5)' }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: 'rgba(255,255,255,0.5)' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      series: [
        {
          data: data.highest_risk_segment,
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: {
            color: isAnomalous ? '#ef4444' : '#10b981',
            width: 2
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: isAnomalous ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)' },
              { offset: 1, color: 'rgba(0, 0, 0, 0)' }
            ])
          }
        }
      ]
    });

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [data]);

  // SHAP Chart
  useEffect(() => {
    if (!shapRef.current || !data.shap.available || !data.shap.values.length) return;
    
    const chart = echarts.init(shapRef.current);
    const topFeatures = data.shap.values.slice(0, 5).reverse();
    
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 20, left: 100 },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: {
        type: 'value',
        axisLabel: { color: 'rgba(255,255,255,0.5)' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      yAxis: {
        type: 'category',
        data: topFeatures.map((f: any) => f.feature),
        axisLabel: { color: 'rgba(255,255,255,0.8)' }
      },
      series: [
        {
          type: 'bar',
          data: topFeatures.map((f: any) => ({
            value: f.contribution,
            itemStyle: { color: f.contribution > 0 ? '#ef4444' : '#3b82f6' }
          }))
        }
      ]
    });

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [data]);

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      backdropFilter: 'blur(10px)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '1000px',
        maxHeight: '90vh',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        padding: '30px'
      }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '700' }}>PhysioNet MIT-BIH Analysis Result</h2>
              <span style={{
                padding: '4px 10px',
                borderRadius: '20px',
                fontSize: '0.75rem',
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                color: '#c4b5fd',
                border: '1px solid rgba(139, 92, 246, 0.3)'
              }}>
                Record: {data.record_id}
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
              Processed {data.segments_analyzed} segments at {data.sampling_rate} Hz.
              {data.reference_annotations.available && " Annotations (.atr) used for exact R-peak extraction."}
            </p>
          </div>
          <button onClick={onClose} className="btn-secondary" style={{ padding: '8px 16px' }}>
            Close Report
          </button>
        </div>

        <div style={{ height: '1px', backgroundColor: 'rgba(255,255,255,0.1)' }} />

        {/* Top Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
          <div style={{
            backgroundColor: isAnomalous ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
            border: `1px solid ${isAnomalous ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {isAnomalous ? <AlertTriangle size={20} color="#ef4444" /> : <CheckCircle size={20} color="#10b981" />}
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Primary Model Prediction</span>
            </div>
            <span style={{ fontSize: '1.2rem', fontWeight: '700', color: isAnomalous ? '#ef4444' : '#10b981' }}>
              Consistent with {data.prediction.label}
            </span>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Confidence: {data.prediction.confidence.toFixed(1)}%
            </span>
          </div>

          <div style={{
            backgroundColor: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.05)',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart3 size={20} color="var(--text-secondary)" />
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Record Distribution</span>
            </div>
            <span style={{ fontSize: '1.4rem', fontWeight: '700' }}>
              {data.dominant_class}
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {Object.entries(data.distribution).map(([cls, count]) => (
                <span key={cls} style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {cls}: {count}
                </span>
              ))}
            </div>
          </div>
          
          <div style={{
            backgroundColor: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.05)',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={20} color="var(--text-secondary)" />
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Global Probabilities</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Max Risk Prob:</span>
                <span>{(data.probabilities.max_risk_prob * 100).toFixed(1)}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Avg Risk Prob:</span>
                <span>{(data.probabilities.avg_risk_prob * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Visualizations */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginTop: '10px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '600' }}>Analyzed ECG Segment (1000 samples, 10s)</h3>
            <div 
              ref={chartRef} 
              style={{ width: '100%', height: '250px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }} 
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '600' }}>SHAP Explanation</h3>
            {data.shap.available ? (
              <div 
                ref={shapRef} 
                style={{ width: '100%', height: '250px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }} 
              />
            ) : (
              <div style={{ width: '100%', height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                SHAP explanation unavailable
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
