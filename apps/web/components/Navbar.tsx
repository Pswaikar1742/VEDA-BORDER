"use client";

import React from "react";

export type NavTab = "dashboard" | "screening" | "cases" | "linkage" | "status" | "settings";

interface NavbarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  systemReady?: boolean;
}

export function Navbar({ activeTab, onSelectTab, systemReady = true }: NavbarProps) {
  const tabs: Array<{ id: NavTab; label: string; icon: string }> = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "screening", label: "New Screening", icon: "🔍" },
    { id: "cases", label: "Case Ledger", icon: "📁" },
    { id: "linkage", label: "Identity Linkage", icon: "🔗" },
    { id: "status", label: "System Status", icon: "⚡" },
    { id: "settings", label: "Policy & Settings", icon: "⚙️" },
  ];

  return (
    <header style={headerStyle}>
      <div style={topBarStyle}>
        <div style={brandContainerStyle}>
          <div style={logoBadgeStyle}>VEDA</div>
          <div>
            <div style={titleStyle}>VEDA-BORDER</div>
            <div style={subtitleStyle}>Verification & Evidence-Driven Autopsy • Border Identity Forensics</div>
          </div>
        </div>

        <div style={badgeContainerStyle}>
          <span style={prototypeBadgeStyle}>RESEARCH PROTOTYPE</span>
          <span style={sihBadgeStyle}>SSB / MHA • PS 26188</span>
          <div style={statusPillStyle}>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                backgroundColor: systemReady ? "#12b76a" : "#f79009",
                display: "inline-block",
                marginRight: 6,
              }}
            />
            <span>{systemReady ? "SYSTEM READY" : "DEGRADED"}</span>
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
                borderBottom: isActive ? "3px solid #0ba5ec" : "3px solid transparent",
                color: isActive ? "#ffffff" : "#94a3b8",
                backgroundColor: isActive ? "rgba(255, 255, 255, 0.06)" : "transparent",
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
  backgroundColor: "#0b1924",
  borderBottom: "1px solid #1e3a4d",
  color: "#f8fafc",
  position: "sticky",
  top: 0,
  zIndex: 100,
};

const topBarStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "12px 24px",
  borderBottom: "1px solid #162b3a",
};

const brandContainerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "12px",
};

const logoBadgeStyle: React.CSSProperties = {
  backgroundColor: "#0284c7",
  color: "#ffffff",
  fontWeight: 900,
  fontSize: "14px",
  letterSpacing: "1.5px",
  padding: "6px 10px",
  borderRadius: "6px",
  border: "1px solid #38bdf8",
};

const titleStyle: React.CSSProperties = {
  fontSize: "18px",
  fontWeight: 800,
  letterSpacing: "0.5px",
  color: "#f1f5f9",
};

const subtitleStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "#94a3b8",
  letterSpacing: "0.2px",
};

const badgeContainerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "10px",
};

const prototypeBadgeStyle: React.CSSProperties = {
  backgroundColor: "#1e293b",
  color: "#38bdf8",
  border: "1px solid #0284c7",
  fontSize: "11px",
  fontWeight: 700,
  padding: "3px 8px",
  borderRadius: "4px",
  letterSpacing: "0.5px",
};

const sihBadgeStyle: React.CSSProperties = {
  backgroundColor: "#312e81",
  color: "#c7d2fe",
  border: "1px solid #4338ca",
  fontSize: "11px",
  fontWeight: 600,
  padding: "3px 8px",
  borderRadius: "4px",
};

const statusPillStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  backgroundColor: "#0f172a",
  color: "#e2e8f0",
  fontSize: "11px",
  fontWeight: 600,
  padding: "4px 10px",
  borderRadius: "12px",
  border: "1px solid #334155",
};

const navBarStyle: React.CSSProperties = {
  display: "flex",
  gap: "4px",
  padding: "0 20px",
  overflowX: "auto",
};

const navButtonStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  padding: "10px 16px",
  fontSize: "13px",
  fontWeight: 600,
  cursor: "pointer",
  transition: "all 0.15s ease",
  display: "flex",
  alignItems: "center",
  whiteSpace: "nowrap",
};
