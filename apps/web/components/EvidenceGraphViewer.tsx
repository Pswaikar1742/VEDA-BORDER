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
      <div style={{ padding: "20px", textAlign: "center", color: "#64748b", background: "#f8fafc", borderRadius: "6px" }}>
        Evidence graph is unavailable.
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
        return "#12b76a";
      case "CONTRADICTS":
        return "#f04438";
      case "UNAVAILABLE":
        return "#94a3b8";
      case "LOW_QUALITY":
        return "#f79009";
      default:
        return "#64748b";
    }
  };

  const getNodeColor = (node: EvidenceGraphNode) => {
    if (node.type === "CLAIM") return "#0f2735";
    if (node.status === "FAIL" || node.status === "SUSPICIOUS") return "#b42318";
    if (node.status === "PASS") return "#067647";
    return "#475467";
  };

  return (
    <div style={{ backgroundColor: "#ffffff", border: "1px solid #cbd5e1", borderRadius: "8px", padding: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "15px", color: "#0f2735", fontWeight: 700 }}>
            Adaptive Forensic Evidence Graph & Truth Hierarchy
          </h3>
          <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#64748b" }}>
            Independent evidence sources retain distinct truth values; higher authority tiers override lower tiers.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px", fontSize: "11px" }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#12b76a" }} /> SUPPORTS
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#f04438" }} /> CONTRADICTS
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#94a3b8" }} /> UNAVAILABLE
          </span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr 1fr", gap: "16px", marginTop: "16px" }}>
        {/* LEFT: Machine-Readable & Authoritative Evidence */}
        <div>
          <div style={columnHeaderStyle}>
            <span>TIER 1 & 2: DETERMINISTIC / MRZ</span>
            <span style={badgePillStyle}>HIGH AUTHORITY</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {tier1.concat(tier2).map((node) => (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node.id)}
                style={{
                  ...nodeCardStyle,
                  borderColor: selectedNode === node.id ? "#0284c7" : "#e2e8f0",
                  borderLeft: `4px solid ${getNodeColor(node)}`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong style={{ fontSize: "12px", color: "#1e293b" }}>{node.source}</strong>
                  <span style={{ fontSize: "10px", color: "#64748b" }}>Tier {node.authority_tier}</span>
                </div>
                {node.field && (
                  <div style={{ fontSize: "11px", color: "#475467", marginTop: "2px" }}>
                    {node.field}: <code>{node.normalized_value || "—"}</code>
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

        {/* MIDDLE: Identity Claims */}
        <div>
          <div style={columnHeaderStyle}>
            <span>CENTRAL IDENTITY CLAIMS</span>
            <span style={{ ...badgePillStyle, background: "#0f2735", color: "#fff" }}>CLAIMS</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {claimNodes.map((node) => {
              // Find edges pointing to this claim
              const incomingEdges = graph.edges.filter((e) => e.to === node.id);
              const hasContradiction = incomingEdges.some((e) => e.relation === "CONTRADICTS");
              const hasSupport = incomingEdges.some((e) => e.relation === "SUPPORTS");

              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node.id)}
                  style={{
                    ...nodeCardStyle,
                    backgroundColor: hasContradiction ? "#fff1f2" : "#f8fafc",
                    borderColor: selectedNode === node.id ? "#0284c7" : (hasContradiction ? "#fca5a5" : "#e2e8f0"),
                    borderLeft: `4px solid ${hasContradiction ? "#e11d48" : (hasSupport ? "#10b981" : "#64748b")}`,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <strong style={{ fontSize: "12px", color: "#0f2735", textTransform: "uppercase" }}>
                      {node.claim?.replace(/_/g, " ")}
                    </strong>
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 700,
                        padding: "1px 6px",
                        borderRadius: "4px",
                        backgroundColor: hasContradiction ? "#ffe4e6" : (hasSupport ? "#d1fae5" : "#f1f5f9"),
                        color: hasContradiction ? "#be123c" : (hasSupport ? "#047857" : "#475467"),
                      }}
                    >
                      {hasContradiction ? "CONTRADICTION" : (hasSupport ? "VERIFIED" : "UNRESOLVED")}
                    </span>
                  </div>

                  {/* Connected relations summary */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", marginTop: "6px" }}>
                    {incomingEdges.map((edge, idx) => (
                      <span
                        key={idx}
                        style={{
                          fontSize: "10px",
                          padding: "1px 4px",
                          borderRadius: "3px",
                          backgroundColor: "#fff",
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

        {/* RIGHT: Observed Document & Probabilistic Evidence */}
        <div>
          <div style={columnHeaderStyle}>
            <span>TIER 3 & 4: OBSERVED / BIOMETRIC</span>
            <span style={badgePillStyle}>LOCAL EVIDENCE</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {tier3.concat(tier4).map((node) => (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node.id)}
                style={{
                  ...nodeCardStyle,
                  borderColor: selectedNode === node.id ? "#0284c7" : "#e2e8f0",
                  borderLeft: `4px solid ${getNodeColor(node)}`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong style={{ fontSize: "12px", color: "#1e293b" }}>{node.source}</strong>
                  <span style={{ fontSize: "10px", color: "#64748b" }}>Tier {node.authority_tier}</span>
                </div>
                {node.field && (
                  <div style={{ fontSize: "11px", color: "#475467", marginTop: "2px" }}>
                    {node.field}: <code>{node.normalized_value || "—"}</code>
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

      <div style={{ marginTop: "14px", padding: "8px 12px", backgroundColor: "#f8fafc", borderRadius: "4px", fontSize: "11px", color: "#475467", border: "1px solid #e2e8f0" }}>
        <strong>Evidence Authority Principle:</strong> Lower numeric tier has strictly higher authority (Tier 1 &gt; Tier 2 &gt; Tier 3 &gt; Tier 4). Deterministic MRZ contradictions cannot be averaged away by multiple probabilistic PASS signals.
      </div>
    </div>
  );
}

const columnHeaderStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  fontSize: "11px",
  fontWeight: 700,
  color: "#475467",
  marginBottom: "8px",
  paddingBottom: "4px",
  borderBottom: "1px solid #cbd5e1",
};

const badgePillStyle: React.CSSProperties = {
  fontSize: "10px",
  padding: "2px 6px",
  borderRadius: "4px",
  backgroundColor: "#e2e8f0",
  color: "#334155",
  fontWeight: 600,
};

const nodeCardStyle: React.CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #e2e8f0",
  borderRadius: "6px",
  padding: "8px 10px",
  cursor: "pointer",
  transition: "all 0.15s ease",
};
