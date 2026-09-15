"use client";

import React, { useState } from "react";
import { EvidenceGraph, EvidenceGraphEdge, EvidenceGraphNode } from "../lib/types";

interface EvidenceGraphViewerProps {
  graph?: EvidenceGraph;
}

export function EvidenceGraphViewer({ graph }: EvidenceGraphViewerProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div style={emptyGraphStyle}>
        <span style={{ fontSize: "18px", marginBottom: "4px", display: "block" }}>🕸️</span>
        Evidence Graph is currently compiling or unavailable.
      </div>
    );
  }

  const claimNodes = graph.nodes.filter((n) => n.type === "CLAIM");
  const evidenceNodes = graph.nodes.filter((n) => n.type === "EVIDENCE");

  // Group evidence by tier
  const tier1 = evidenceNodes.filter((n) => n.authority_tier === 1);
  const tier2 = evidenceNodes.filter((n) => n.authority_tier === 2);
  const tier3 = evidenceNodes.filter((n) => n.authority_tier === 3);
  const tier4 = evidenceNodes.filter((n) => n.authority_tier === 4);

  const getRelationColor = (relation: string) => {
    switch (relation) {
      case "SUPPORTS":
        return "#10b981"; // Green
      case "CONTRADICTS":
        return "#ef4444"; // Red
      case "UNAVAILABLE":
        return "#64748b"; // Gray
      case "LOW_QUALITY":
        return "#f59e0b"; // Amber
      default:
        return "#38bdf8"; // Blue/cyan
    }
  };

  const getNodeColor = (node: EvidenceGraphNode) => {
    if (node.type === "CLAIM") return "#38bdf8";
    if (node.status === "FAIL" || node.status === "SUSPICIOUS") return "#ef4444";
    if (node.status === "PASS") return "#10b981";
    return "#64748b";
  };

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <div>
          <h3 style={{ margin: 0, fontSize: "14px", color: "#f8fafc", fontWeight: 700 }}>
            EVIDENCE GRAPH
          </h3>
          <p style={{ margin: "2px 0 0 0", fontSize: "11px", color: "#94a3b8" }}>
            Multi-tier evidence provenance: higher authority tiers strictly override lower probabilistic tiers.
          </p>
        </div>

        {/* Color Legend */}
        <div style={legendContainerStyle}>
          <span style={legendItemStyle}>
            <span style={{ ...legendDotStyle, background: "#38bdf8" }} /> Blue = Source Evidence
          </span>
          <span style={legendItemStyle}>
            <span style={{ ...legendDotStyle, background: "#10b981" }} /> Green = Supports
          </span>
          <span style={legendItemStyle}>
            <span style={{ ...legendDotStyle, background: "#ef4444" }} /> Red = Contradiction
          </span>
          <span style={legendItemStyle}>
            <span style={{ ...legendDotStyle, background: "#f59e0b" }} /> Amber = Uncertain / Incomplete
          </span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.1fr 1fr", gap: "14px", marginTop: "12px" }}>
        {/* LEFT: Tier 1 & 2 Deterministic Evidence */}
        <div>
          <div style={columnHeaderStyle}>
            <span style={{ color: "#38bdf8" }}>TIER 1 & 2: DETERMINISTIC / MRZ</span>
            <span style={badgePillStyle}>AUTHORITATIVE</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {tier1.concat(tier2).map((node) => (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node.id)}
                style={{
                  ...nodeCardStyle,
                  borderColor: selectedNode === node.id ? "#38bdf8" : "#1e3a4d",
                  borderLeft: `4px solid ${getNodeColor(node)}`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong style={{ fontSize: "11px", color: "#f1f5f9" }}>{node.source || node.id}</strong>
                  <span style={{ fontSize: "9px", color: "#64748b", fontWeight: 600 }}>Tier {node.authority_tier}</span>
                </div>
                {node.field && (
                  <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>
                    {node.field}: <code style={{ color: "#cbd5e1", backgroundColor: "#0b1723", padding: "1px 4px", borderRadius: "3px" }}>{node.normalized_value || "—"}</code>
                  </div>
                )}
                {node.status && (
                  <div style={{ fontSize: "10px", fontWeight: 700, color: getNodeColor(node), marginTop: "2px" }}>
                    Status: {node.status}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* MIDDLE: Central Identity Claims */}
        <div>
          <div style={columnHeaderStyle}>
            <span style={{ color: "#f8fafc" }}>CENTRAL IDENTITY CLAIMS</span>
            <span style={{ ...badgePillStyle, background: "#0369a1", color: "#fff" }}>CLAIMS</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {claimNodes.map((node) => {
              const incomingEdges = graph.edges.filter((e) => e.to === node.id);
              const hasContradiction = incomingEdges.some((e) => e.relation === "CONTRADICTS");
              const hasSupport = incomingEdges.some((e) => e.relation === "SUPPORTS");

              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node.id)}
                  style={{
                    ...nodeCardStyle,
                    backgroundColor: hasContradiction ? "rgba(239, 68, 68, 0.12)" : "#0c1a27",
                    borderColor: selectedNode === node.id ? "#38bdf8" : (hasContradiction ? "#ef4444" : "#1e3a4d"),
                    borderLeft: `4px solid ${hasContradiction ? "#ef4444" : (hasSupport ? "#10b981" : "#64748b")}`,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <strong style={{ fontSize: "11px", color: "#f8fafc", textTransform: "uppercase" }}>
                      {node.claim?.replace(/_/g, " ") || node.id}
                    </strong>
                    <span
                      style={{
                        fontSize: "9px",
                        fontWeight: 700,
                        padding: "2px 5px",
                        borderRadius: "3px",
                        backgroundColor: hasContradiction ? "rgba(239, 68, 68, 0.25)" : (hasSupport ? "rgba(16, 185, 129, 0.2)" : "#1e293b"),
                        color: hasContradiction ? "#fca5a5" : (hasSupport ? "#6ee7b7" : "#94a3b8"),
                        border: `1px solid ${hasContradiction ? "rgba(239, 68, 68, 0.4)" : (hasSupport ? "rgba(16, 185, 129, 0.4)" : "#334155")}`,
                      }}
                    >
                      {hasContradiction ? "CONTRADICTION" : (hasSupport ? "VERIFIED" : "UNRESOLVED")}
                    </span>
                  </div>

                  {/* Connected relations summary */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "3px", marginTop: "5px" }}>
                    {incomingEdges.map((edge, idx) => (
                      <span
                        key={idx}
                        style={{
                          fontSize: "9px",
                          padding: "1px 4px",
                          borderRadius: "3px",
                          backgroundColor: "#08131e",
                          border: `1px solid ${getRelationColor(edge.relation)}`,
                          color: getRelationColor(edge.relation),
                          fontWeight: 600,
                        }}
                      >
                        {edge.from.replace("evidence:", "")}: {edge.relation}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT: Tier 3 & 4 Observed / Biometric Evidence */}
        <div>
          <div style={columnHeaderStyle}>
            <span style={{ color: "#38bdf8" }}>TIER 3 & 4: OBSERVED / BIOMETRIC</span>
            <span style={badgePillStyle}>LOCAL FORENSICS</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {tier3.concat(tier4).map((node) => (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node.id)}
                style={{
                  ...nodeCardStyle,
                  borderColor: selectedNode === node.id ? "#38bdf8" : "#1e3a4d",
                  borderLeft: `4px solid ${getNodeColor(node)}`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong style={{ fontSize: "11px", color: "#f1f5f9" }}>{node.source || node.id}</strong>
                  <span style={{ fontSize: "9px", color: "#64748b", fontWeight: 600 }}>Tier {node.authority_tier}</span>
                </div>
                {node.field && (
                  <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>
                    {node.field}: <code style={{ color: "#cbd5e1", backgroundColor: "#0b1723", padding: "1px 4px", borderRadius: "3px" }}>{node.normalized_value || "—"}</code>
                  </div>
                )}
                {node.status && (
                  <div style={{ fontSize: "10px", fontWeight: 700, color: getNodeColor(node), marginTop: "2px" }}>
                    Status: {node.status}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={principleFooterStyle}>
        <strong style={{ color: "#38bdf8" }}>Truth Hierarchy Invariant:</strong> Lower numeric tier has strictly higher authority (Tier 1 &gt; Tier 2 &gt; Tier 3 &gt; Tier 4). Deterministic MRZ contradictions mathematically override probabilistic pass signals.
      </div>
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
  marginBottom: "8px",
  paddingBottom: "8px",
  borderBottom: "1px solid #132433",
  flexWrap: "wrap",
  gap: "8px",
};

const legendContainerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "10px",
  fontSize: "10px",
  color: "#94a3b8",
  backgroundColor: "#0d1b26",
  padding: "4px 8px",
  borderRadius: "4px",
  border: "1px solid #1e3a4d",
  flexWrap: "wrap",
};

const legendItemStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "4px",
  fontWeight: 500,
};

const legendDotStyle: React.CSSProperties = {
  width: 8,
  height: 8,
  borderRadius: "50%",
  display: "inline-block",
};

const columnHeaderStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  fontSize: "10px",
  fontWeight: 700,
  color: "#94a3b8",
  marginBottom: "6px",
  paddingBottom: "4px",
  borderBottom: "1px solid #162c3f",
  letterSpacing: "0.5px",
};

const badgePillStyle: React.CSSProperties = {
  fontSize: "9px",
  padding: "1px 5px",
  borderRadius: "3px",
  backgroundColor: "#132536",
  color: "#94a3b8",
  fontWeight: 600,
};

const nodeCardStyle: React.CSSProperties = {
  backgroundColor: "#0c1a27",
  border: "1px solid #1e3a4d",
  borderRadius: "5px",
  padding: "7px 9px",
  cursor: "pointer",
  transition: "all 0.15s ease",
};

const emptyGraphStyle: React.CSSProperties = {
  padding: "24px",
  textAlign: "center",
  color: "#64748b",
  backgroundColor: "#0a1622",
  borderRadius: "6px",
  border: "1px dashed #1e3a4d",
  fontSize: "12px",
};

const principleFooterStyle: React.CSSProperties = {
  marginTop: "12px",
  padding: "6px 10px",
  backgroundColor: "#0a1622",
  borderRadius: "4px",
  fontSize: "10px",
  color: "#94a3b8",
  border: "1px solid #162a3b",
};
