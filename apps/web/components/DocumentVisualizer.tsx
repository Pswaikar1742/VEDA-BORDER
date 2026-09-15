"use client";

import React, { useState } from "react";
import { BoundingBox, VisualForensicFinding } from "../lib/types";

interface DocumentVisualizerProps {
  imageSrc?: string | null;
  findings?: VisualForensicFinding[];
  portraitRegion?: BoundingBox;
  title?: string;
}

export function DocumentVisualizer({
  imageSrc,
  findings = [],
  portraitRegion,
  title = "Document Visualizer & Tamper Overlay",
}: DocumentVisualizerProps) {
  const [showOverlays, setShowOverlays] = useState(true);
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  if (!imageSrc) {
    return (
      <div
        style={{
          border: "2px dashed #1e3a4d",
          borderRadius: "8px",
          padding: "48px 24px",
          textAlign: "center",
          color: "#64748b",
          backgroundColor: "#0a1622",
        }}
      >
        <div style={{ fontSize: "24px", marginBottom: "8px" }}>📄</div>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "#94a3b8" }}>No document specimen loaded</div>
        <div style={{ fontSize: "11px", color: "#475569", marginTop: "4px" }}>Upload a document or select a preset scenario above.</div>
      </div>
    );
  }

  const handleZoom = (delta: number) => {
    setZoomLevel((prev) => Math.max(1, Math.min(2.5, +(prev + delta).toFixed(1))));
  };

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "13px", fontWeight: 700, color: "#f8fafc" }}>{title}</span>
            {findings.length > 0 ? (
              <span style={anomalyBadgeStyle}>{findings.length} TAMPER REGION(S)</span>
            ) : (
              <span style={cleanBadgeStyle}>NO SURFACE ANOMALIES</span>
            )}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {/* Zoom controls */}
          <div style={zoomGroupStyle}>
            <button
              type="button"
              onClick={() => handleZoom(-0.2)}
              disabled={zoomLevel <= 1}
              style={zoomButtonStyle}
              title="Zoom out"
            >
              -
            </button>
            <span style={zoomLabelStyle}>{Math.round(zoomLevel * 100)}%</span>
            <button
              type="button"
              onClick={() => handleZoom(0.2)}
              disabled={zoomLevel >= 2.5}
              style={zoomButtonStyle}
              title="Zoom in"
            >
              +
            </button>
            {zoomLevel > 1 && (
              <button
                type="button"
                onClick={() => setZoomLevel(1)}
                style={{ ...zoomButtonStyle, fontSize: "10px", padding: "2px 6px" }}
                title="Reset zoom"
              >
                Reset
              </button>
            )}
          </div>

          <button
            type="button"
            onClick={() => setShowOverlays(!showOverlays)}
            style={{
              ...toggleButtonStyle,
              backgroundColor: showOverlays ? "#0369a1" : "#1e293b",
              color: showOverlays ? "#ffffff" : "#94a3b8",
              borderColor: showOverlays ? "#38bdf8" : "#334155",
            }}
          >
            {showOverlays ? "👁️ Hide Overlays" : "👁️ Show Overlays"}
          </button>
        </div>
      </div>

      <div style={viewportContainerStyle}>
        <div
          style={{
            transform: `scale(${zoomLevel})`,
            transformOrigin: "center center",
            transition: "transform 0.2s ease",
            display: "inline-block",
            position: "relative",
            maxWidth: "100%",
          }}
        >
          <img
            src={imageSrc}
            alt="Document specimen preview"
            style={{
              maxWidth: "100%",
              maxHeight: "360px",
              objectFit: "contain",
              display: "block",
              margin: "0 auto",
              borderRadius: "4px",
            }}
          />

          {showOverlays && (
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: "none",
              }}
            >
              {/* Render suspicious regions if relative bounding box is provided */}
              {findings.map((f, idx) => {
                const bbox = f.bounding_box;
                if (!bbox) return null;
                return (
                  <div
                    key={idx}
                    style={{
                      position: "absolute",
                      left: `${(bbox.x / 800) * 100}%`,
                      top: `${(bbox.y / 500) * 100}%`,
                      width: `${(bbox.width / 800) * 100}%`,
                      height: `${(bbox.height / 500) * 100}%`,
                      border: "2px solid #ef4444",
                      backgroundColor: "rgba(239, 68, 68, 0.25)",
                      boxShadow: "0 0 8px rgba(239, 68, 68, 0.6)",
                      borderRadius: "3px",
                    }}
                    title={f.explanation}
                  />
                );
              })}
            </div>
          )}
        </div>
      </div>

      {findings.length > 0 && (
        <div style={{ marginTop: "10px", display: "flex", flexDirection: "column", gap: "6px" }}>
          {findings.map((f, idx) => (
            <div key={idx} style={findingItemStyle}>
              <strong style={{ color: "#f87171", textTransform: "uppercase" }}>{f.finding_type}</strong>:{" "}
              <span>{f.explanation}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const containerStyle: React.CSSProperties = {
  backgroundColor: "#091520",
  border: "1px solid #162c3f",
  borderRadius: "8px",
  padding: "14px",
  boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
};
const headerStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "10px",
  paddingBottom: "8px",
  borderBottom: "1px solid #132433",
};

const anomalyBadgeStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 700,
  padding: "2px 6px",
  borderRadius: "4px",
  backgroundColor: "rgba(239, 68, 68, 0.15)",
  color: "#f87171",
  border: "1px solid rgba(239, 68, 68, 0.3)",
  letterSpacing: "0.5px",
};

const cleanBadgeStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 700,
  padding: "2px 6px",
  borderRadius: "4px",
  backgroundColor: "rgba(16, 185, 129, 0.15)",
  color: "#6ee7b7",
  border: "1px solid rgba(16, 185, 129, 0.3)",
  letterSpacing: "0.5px",
};

const zoomGroupStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "2px",
  backgroundColor: "#0d1b26",
  border: "1px solid #1e3a4d",
  borderRadius: "4px",
  padding: "2px",
};

const zoomButtonStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "#94a3b8",
  cursor: "pointer",
  fontSize: "13px",
  fontWeight: 700,
  padding: "2px 6px",
  borderRadius: "3px",
};

const zoomLabelStyle: React.CSSProperties = {
  fontSize: "10px",
  color: "#cbd5e1",
  fontWeight: 600,
  padding: "0 4px",
  minWidth: "32px",
  textAlign: "center",
};

const toggleButtonStyle: React.CSSProperties = {
  fontSize: "11px",
  padding: "4px 8px",
  border: "1px solid",
  borderRadius: "4px",
  cursor: "pointer",
  fontWeight: 600,
  transition: "all 0.15s ease",
};

const viewportContainerStyle: React.CSSProperties = {
  position: "relative",
  width: "100%",
  maxHeight: "360px",
  overflow: "hidden",
  borderRadius: "6px",
  border: "1px solid #162a3b",
  backgroundColor: "#050b11",
  textAlign: "center",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
};

const findingItemStyle: React.CSSProperties = {
  padding: "6px 10px",
  backgroundColor: "rgba(239, 68, 68, 0.08)",
  border: "1px solid rgba(239, 68, 68, 0.25)",
  borderRadius: "4px",
  fontSize: "11px",
  color: "#fca5a5",
};
