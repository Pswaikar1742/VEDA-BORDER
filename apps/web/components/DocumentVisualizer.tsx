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
  title = "Document Visual Inspection & Tamper Overlay",
}: DocumentVisualizerProps) {
  const [showOverlays, setShowOverlays] = useState(true);

  if (!imageSrc) {
    return (
      <div
        style={{
          border: "2px dashed #cbd5e1",
          borderRadius: "8px",
          padding: "32px",
          textAlign: "center",
          color: "#64748b",
          backgroundColor: "#f8fafc",
        }}
      >
        No document image loaded for visual overlay.
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: "#ffffff", border: "1px solid #cbd5e1", borderRadius: "8px", padding: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "14px", color: "#0f2735", fontWeight: 700 }}>{title}</h3>
          <span style={{ fontSize: "11px", color: "#64748b" }}>
            {findings.length > 0
              ? `${findings.length} anomalous region(s) detected`
              : "No high-frequency or edge anomalies flagged"}
          </span>
        </div>
        <button
          type="button"
          onClick={() => setShowOverlays(!showOverlays)}
          style={{
            fontSize: "11px",
            padding: "4px 8px",
            backgroundColor: showOverlays ? "#0f2735" : "#f1f5f9",
            color: showOverlays ? "#ffffff" : "#475467",
            border: "1px solid #cbd5e1",
            borderRadius: "4px",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          {showOverlays ? "Hide Overlays" : "Show Overlays"}
        </button>
      </div>

      <div
        style={{
          position: "relative",
          display: "inline-block",
          width: "100%",
          maxHeight: "420px",
          overflow: "hidden",
          borderRadius: "6px",
          border: "1px solid #e2e8f0",
          backgroundColor: "#0f172a",
          textAlign: "center",
        }}
      >
        <img
          src={imageSrc}
          alt="Document specimen preview"
          style={{
            maxWidth: "100%",
            maxHeight: "420px",
            objectFit: "contain",
            display: "block",
            margin: "0 auto",
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
                    backgroundColor: "rgba(239, 68, 68, 0.2)",
                    borderRadius: "2px",
                  }}
                  title={f.explanation}
                />
              );
            })}
          </div>
        )}
      </div>

      {findings.length > 0 && (
        <div style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
          {findings.map((f, idx) => (
            <div
              key={idx}
              style={{
                padding: "6px 10px",
                backgroundColor: "#fff1f2",
                border: "1px solid #fecdd3",
                borderRadius: "4px",
                fontSize: "11px",
                color: "#be123c",
              }}
            >
              <strong>{f.finding_type}</strong>: {f.explanation}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
