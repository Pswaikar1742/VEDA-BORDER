"use client";

import React from "react";

export type NavTab = "dashboard" | "screening" | "cases" | "linkage" | "status" | "settings";

interface NavbarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  systemReady?: boolean;
  activeCaseId?: string | null;
  aiStatus?: string | null;
}

export function Navbar({
  activeTab,
  onSelectTab,
  systemReady = true,
  activeCaseId = null,
  aiStatus = "ACTIVE",
}: NavbarProps) {
  const tabs: Array<{ id: NavTab; label: string; icon: string }> = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "screening", label: "New Screening", icon: "🔍" },
    { id: "cases", label: "Case Ledger", icon: "📁" },
    { id: "linkage", label: "Identity Linkage", icon: "🔗" },
    { id: "status", label: "System Status", icon: "⚡" },
    { id: "settings", label: "Policy & Settings", icon: "⚙️" },
  ];

  const isAiActive = aiStatus === "ACTIVE" || aiStatus === "READY";

  return (
    <header style={headerStyle}>
      <div style={topBarStyle}>
        <div style={brandContainerStyle}>
          <div style={logoBadgeStyle}>VEDA</div>
          <div>
            <div style={titleContainerStyle}>
              <span style={titleStyle}>VEDA-BORDER</span>
              <span style={engineTagStyle}>Identity Forensic Autopsy Engine</span>
            </div>
            <div style={subtitleStyle}>AI-Based Fake Identity & Document Screening • MHA / SSB PS 26188</div>
          </div>
        </div>

        <div style={badgeContainerStyle}>
          {activeCaseId && (
            <div style={caseBadgeStyle}>
              <span style={{ color: "#64748b", marginRight: 4 }}>CASE:</span>
              <span style={{ fontFamily: "monospace", color: "#38bdf8", fontWeight: 700 }}>
                {activeCaseId.length > 12 ? `${activeCaseId.slice(0, 8)}...` : activeCaseId}
              </span>
            </div>
          )}

          <div
            style={{
              ...statusPillStyle,
              borderColor: isAiActive ? "#0284c7" : "#334155",
              backgroundColor: isAiActive ? "rgba(2, 132, 199, 0.12)" : "#0f172a",
            }}
          >
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                backgroundColor: isAiActive ? "#38bdf8" : "#94a3b8",
                display: "inline-block",
                marginRight: 6,
              }}
            />
            <span style={{ color: isAiActive ? "#7dd3fc" : "#94a3b8" }}>
              {isAiActive ? "AI REASONING: ACTIVE" : "AI REASONING: OFF"}
            </span>
          </div>

          <div style={statusPillStyle}>
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                backgroundColor: systemReady ? "#10b981" : "#f59e0b",
                display: "inline-block",
                marginRight: 6,
              }}
            />
            <span style={{ color: systemReady ? "#6ee7b7" : "#fcd34d" }}>
              {systemReady ? "SYSTEM READY" : "DEGRADED"}
            </span>
          </div>
        </div>
      </div>

      <nav style={navBarStyle}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              style={{
                ...navButtonStyle,
                borderBottom: isActive ? "3px solid #38bdf8" : "3px solid transparent",
                color: isActive ? "#ffffff" : "#94a3b8",
                backgroundColor: isActive ? "rgba(56, 189, 248, 0.08)" : "transparent",
              }}
            >
              <span style={{ marginRight: 6 }}>{tab.icon}</span>
              {tab.label}
            </button>
          );
        })}
      </nav>
    </header>
  );
}

const headerStyle: React.CSSProperties = {
  backgroundColor: "#07111a",
  borderBottom: "1px solid #162a3b",
  color: "#f8fafc",
  position: "sticky",
  top: 0,
  zIndex: 100,
  boxShadow: "0 2px 8px rgba(0,0,0,0.4)",
};
const topBarStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "10px 24px",
  borderBottom: "1px solid #102231",
};

const brandContainerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "12px",
};

const logoBadgeStyle: React.CSSProperties = {
  backgroundColor: "#0369a1",
  color: "#ffffff",
  fontWeight: 900,
  fontSize: "13px",
  letterSpacing: "1.5px",
  padding: "5px 9px",
  borderRadius: "5px",
  border: "1px solid #38bdf8",
  boxShadow: "0 0 10px rgba(56, 189, 248, 0.25)",
};

const titleContainerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
};

const titleStyle: React.CSSProperties = {
  fontSize: "17px",
  fontWeight: 800,
  letterSpacing: "0.5px",
  color: "#f8fafc",
};

const engineTagStyle: React.CSSProperties = {
  fontSize: "12px",
  fontWeight: 600,
  color: "#38bdf8",
  backgroundColor: "rgba(56, 189, 248, 0.1)",
  border: "1px solid rgba(56, 189, 248, 0.25)",
  padding: "1px 6px",
  borderRadius: "4px",
};

const subtitleStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "#64748b",
  letterSpacing: "0.2px",
  marginTop: "2px",
};

const badgeContainerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "10px",
};

const caseBadgeStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  backgroundColor: "#0d1b26",
  border: "1px solid #1e3a4d",
  borderRadius: "6px",
  padding: "4px 8px",
  fontSize: "11px",
};

const statusPillStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  backgroundColor: "#0d1b26",
  color: "#e2e8f0",
  fontSize: "11px",
  fontWeight: 600,
  padding: "4px 10px",
  borderRadius: "12px",
  border: "1px solid #1e3a4d",
};

const navBarStyle: React.CSSProperties = {
  display: "flex",
  gap: "4px",
  padding: "0 20px",
  overflowX: "auto",
  backgroundColor: "#091520",
};

const navButtonStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  padding: "9px 16px",
  fontSize: "13px",
  fontWeight: 600,
  cursor: "pointer",
  transition: "all 0.15s ease",
  display: "flex",
  alignItems: "center",
  whiteSpace: "nowrap",
};
