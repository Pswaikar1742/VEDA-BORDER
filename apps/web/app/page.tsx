"use client";

import React, { useEffect, useRef, useState } from "react";
import { OfficerWorkspace, DeveloperDiagnostics } from "../components/OfficerWorkspace";
import { DocumentVisualizer } from "../components/DocumentVisualizer";
import { EvidenceGraphViewer } from "../components/EvidenceGraphViewer";
import { Navbar, NavTab } from "../components/Navbar";
import {
  createScreening,
  fetchCase,
  fetchCases,
  fetchIdentityLinkage,
  fetchSystemStatus,
  getReportHtmlUrl,
  getReportJsonUrl,
} from "../lib/api";
import {
  CaseSummaryItem,
  CaseSummaryResponse,
  CrossSourceComparison,
  DocumentFamily,
  IdentityCluster,
  IdentityForensicAutopsy,
  ScreeningOutcome,
  SystemStatusResponse,
} from "../lib/types";

const FIELD_LABELS: Record<string, string> = {
  holder_name: "Holder Name",
  document_number: "Document Number",
  nationality: "Nationality",
  date_of_birth: "Date of Birth",
  sex: "Sex",
  expiry_date: "Expiry Date",
};

const PRESET_SCENARIOS = [
  {
    id: "clean",
    name: "1. Clean / Consistent Travel Document",
    docFile: "travel_clean.png",
    selfieFile: "ari_selfie.png",
    expected: "LOW RISK (All lanes complete and consistent)",
    family: "TRAVEL_DOCUMENT",
    desc: "Clean ICAO TD3 passport with matching live face selfie.",
  },
  {
    id: "dob_altered",
    name: "2. Visible DOB Alteration",
    docFile: "travel_dob_altered.png",
    selfieFile: null,
    expected: "HIGH RISK / REFER (VIZ ≠ MRZ contradiction)",
    family: "TRAVEL_DOCUMENT",
    desc: "Printed DOB altered on document surface; fails cross-check with MRZ.",
  },
  {
    id: "face_mismatch",
    name: "3. Portrait / Face Mismatch",
    docFile: "travel_clean.png",
    selfieFile: "lio_selfie.png",
    expected: "HIGH RISK (Biometric face mismatch)",
    family: "TRAVEL_DOCUMENT",
    desc: "Clean passport presented by an alternate subject (impersonation).",
  },
  {
    id: "expired",
    name: "4. Expired Credential",
    docFile: "travel_expired.png",
    selfieFile: null,
    expected: "REFER (Expired credential gate)",
    family: "TRAVEL_DOCUMENT",
    desc: "Expiry date is in the past relative to current UTC clock.",
  },
  {
    id: "blacklisted",
    name: "5. Prototype Watchlist Match",
    docFile: "travel_blacklisted.png",
    selfieFile: null,
    expected: "HIGH RISK (Local watchlist alert)",
    family: "TRAVEL_DOCUMENT",
    desc: "Document number triggers mock border threat intelligence hit.",
  },
  {
    id: "poor_capture",
    name: "6. Poor Capture Quality",
    docFile: "travel_poor_capture.png",
    selfieFile: null,
    expected: "INDETERMINATE (Quality gate stop)",
    family: "TRAVEL_DOCUMENT",
    desc: "Degraded image resolution and blur trigger quality gate stop.",
  },
  {
    id: "linkage",
    name: "7. Multi-Identity Linkage",
    docFile: "travel_clean.png",
    selfieFile: "ari_selfie_variant.png",
    expected: "REFER (Biometric alias cluster)",
    family: "TRAVEL_DOCUMENT",
    desc: "Same physical face enrolled under multiple distinct names.",
  },
  {
    id: "visa",
    name: "8. Visa / Permit Example",
    docFile: "visa_or_permit.png",
    selfieFile: null,
    expected: "MRZ = NOT_APPLICABLE",
    family: "VISA_OR_PERMIT",
    desc: "Non-MRZ entry permit evaluated with family-aware document rules.",
  },
  {
    id: "national_id",
    name: "9. National ID Example",
    docFile: "national_id.png",
    selfieFile: null,
    expected: "MRZ = NOT_APPLICABLE",
    family: "NATIONAL_ID",
    desc: "Domestic identification card evaluated with layout rules.",
  },
  {
    id: "midv_grc_passport",
    name: "10. MIDV-2020 sample: template",
    docFile: "midv-demo/templates/alb_id/00.jpg",
    selfieFile: null,
    expected: "Sample processing only",
    family: "TRAVEL_DOCUMENT",
    desc: "Curated external dataset sample. Processing is a research demonstration, not an authenticity decision.",
  },
  {
    id: "midv_lva_passport",
    name: "11. MIDV-2020 sample: upright scan",
    docFile: "midv-demo/scan_upright/alb_id/00.jpg",
    selfieFile: null,
    expected: "Sample processing only",
    family: "TRAVEL_DOCUMENT",
    desc: "Curated external dataset sample for robustness inspection.",
  },
  {
    id: "midv_esp_id",
    name: "12. MIDV-2020 sample: rotated scan",
    docFile: "midv-demo/scan_rotated/alb_id/00.jpg",
    selfieFile: null,
    expected: "Sample processing only",
    family: "NATIONAL_ID",
    desc: "Curated external dataset sample; no global performance claim is implied.",
  },
  {
    id: "sidtd_fake",
    name: "13. SIDTD sample: manipulated specimen",
    docFile: "sidtd/templates/Images/fakes/alb_id_00_fake_6_25.jpg",
    selfieFile: null,
    expected: "Sample processing only",
    family: "NATIONAL_ID",
    desc: "Curated external research sample. The prototype reports evidence signals only.",
  },
  {
    id: "fantasyid_usa",
    name: "14. FantasyID sample: USA specimen",
    docFile: "fantasyid/FantasyID/examples/usa-NF-1004.jpg",
    selfieFile: null,
    expected: "Sample processing only",
    family: "TRAVEL_DOCUMENT",
    desc: "Curated external research sample for demonstration.",
  },
  {
    id: "midv_photo_wild",
    name: "15. MIDV-2020 sample: smartphone photo",
    docFile: "midv-demo/photo/alb_id/00.jpg",
    selfieFile: null,
    expected: "Sample processing only",
    family: "NATIONAL_ID",
    desc: "Curated phone-photo sample for capture robustness inspection.",
  },
];

export default function Home() {
  const [developerMode, setDeveloperMode] = useState(false);
  const [reportPreview, setReportPreview] = useState<string | null>(null);
  const [reportSelfiePreview, setReportSelfiePreview] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<NavTab>("dashboard");
  const [autopsy, setAutopsy] = useState<IdentityForensicAutopsy | null>(null);
  const [casesData, setCasesData] = useState<CaseSummaryResponse | null>(null);
  const [linkageData, setLinkageData] = useState<IdentityCluster[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);

  // Screening form state
  const [docFile, setDocFile] = useState<File | null>(null);
  const [docPreview, setDocPreview] = useState<string | null>(null);
  const [selfieFile, setSelfieFile] = useState<File | null>(null);
  const [selfiePreview, setSelfiePreview] = useState<string | null>(null);
  const [selectedFamily, setSelectedFamily] = useState<string>("");
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Expandable card states
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  // Filter state for Cases
  const [caseFilter, setCaseFilter] = useState<string>("ALL");
  const [caseSearch, setCaseSearch] = useState<string>("");

  // Camera modal state
  const [cameraMode, setCameraMode] = useState<"document" | "selfie" | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [autopsy, developerMode]);

  // Load initial data
  useEffect(() => {
    refreshData();
  }, []);

  async function refreshData() {
    try {
      const [cases, linkage, status] = await Promise.all([
        fetchCases(50).catch(() => null),
        fetchIdentityLinkage().catch(() => ({ clusters: [] })),
        fetchSystemStatus().catch(() => null),
      ]);
      if (cases) setCasesData(cases);
      if (linkage?.clusters) setLinkageData(linkage.clusters);
      if (status) setSystemStatus(status);
    } catch {
      // ignore background refresh errors
    }
  }

  const toggleCard = (cardKey: string) => {
    setExpandedCards((prev) => ({ ...prev, [cardKey]: !prev[cardKey] }));
  };

  // Handle file picker
  const handleDocChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAutopsy(null);
      setDocFile(file);
      setDocPreview(file.type === "application/pdf" ? null : URL.createObjectURL(file));
    }
  };

  const handleSelfieChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAutopsy(null);
      setSelfieFile(file);
      setSelfiePreview(URL.createObjectURL(file));
    }
  };

  // Preset fixture loader
  async function loadPreset(preset: (typeof PRESET_SCENARIOS)[0]) {
    setAutopsy(null);
    setDocFile(null);
    setDocPreview(null);
    setSelfieFile(null);
    setSelfiePreview(null);
    setErrorMessage(null);
    setSelectedFamily(preset.family);
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const docRes = await fetch(`${apiBase}/api/v1/fixtures/${preset.docFile}`);
      if (!docRes.ok) throw new Error(`Could not load fixture ${preset.docFile}`);
      const docBlob = await docRes.blob();
      const docF = new File([docBlob], preset.docFile, { type: "image/png" });
      setDocFile(docF);
      setDocPreview(URL.createObjectURL(docBlob));

      if (preset.selfieFile) {
        const selfieRes = await fetch(`${apiBase}/api/v1/fixtures/${preset.selfieFile}`);
        if (selfieRes.ok) {
          const selfieBlob = await selfieRes.blob();
          const selfieF = new File([selfieBlob], preset.selfieFile, { type: "image/png" });
          setSelfieFile(selfieF);
          setSelfiePreview(URL.createObjectURL(selfieBlob));
        } else {
          setSelfieFile(null);
          setSelfiePreview(null);
        }
      } else {
        setSelfieFile(null);
        setSelfiePreview(null);
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load preset fixture.");
    }
  }

  // Camera handling
  async function startCamera(mode: "document" | "selfie") {
    setCameraMode(mode);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      alert("Unable to access camera: " + (err instanceof Error ? err.message : String(err)));
      setCameraMode(null);
    }
  }

  function stopCamera() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraMode(null);
  }

  function captureFrame() {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 1280;
    canvas.height = videoRef.current.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (!blob) return;
        const filename = cameraMode === "document" ? "camera_document.png" : "camera_selfie.png";
        const file = new File([blob], filename, { type: "image/png" });
        setAutopsy(null);
        if (cameraMode === "document") {
          setDocFile(file);
          setDocPreview(URL.createObjectURL(blob));
        } else {
          setSelfieFile(file);
          setSelfiePreview(URL.createObjectURL(blob));
        }
        stopCamera();
      }, "image/png");
    }
  }

  // Execute Screening
  async function handleRunScreening() {
    if (!docFile) {
      setErrorMessage("Please upload or select a document specimen before screening.");
      return;
    }
    setErrorMessage(null);
    setIsAnalyzing(true);
    setAutopsy(null);
    const submittedPreview = docPreview;
    const submittedSelfiePreview = selfiePreview;
    try {
      const result = await createScreening(
        docFile,
        docFile.name,
        selfieFile,
        selfieFile?.name,
        selectedFamily || undefined
      );
      setReportPreview(submittedPreview);
      setReportSelfiePreview(submittedSelfiePreview);
      setAutopsy(result);
      setActiveTab("screening");
      refreshData();
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Screening analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  // Reopen existing case
  async function handleReopenCase(caseId: string) {
    try {
      const caseResult = await fetchCase(caseId);
      setReportPreview(null);
      setReportSelfiePreview(null);
      setDocFile(null);
      setDocPreview(null);
      setSelfieFile(null);
      setSelfiePreview(null);
      setAutopsy(caseResult);
      setActiveTab("screening");
    } catch (err) {
      alert("Failed to load case: " + (err instanceof Error ? err.message : String(err)));
    }
  }

  const outcomeColors: Record<ScreeningOutcome | string, string> = {
    LOW_RISK: "#10b981", // Green
    REFER: "#f59e0b", // Amber
    HIGH_RISK: "#ef4444", // Red
    INDETERMINATE: "#94a3b8", // Slate
    CLEAR: "#10b981",
  };

  const outcomeBg: Record<ScreeningOutcome | string, string> = {
    LOW_RISK: "rgba(16, 185, 129, 0.12)",
    REFER: "rgba(245, 158, 11, 0.12)",
    HIGH_RISK: "rgba(239, 68, 68, 0.15)",
    INDETERMINATE: "rgba(100, 116, 139, 0.12)",
    CLEAR: "rgba(16, 185, 129, 0.12)",
  };

  const outcomeBorder: Record<ScreeningOutcome | string, string> = {
    LOW_RISK: "rgba(16, 185, 129, 0.4)",
    REFER: "rgba(245, 158, 11, 0.4)",
    HIGH_RISK: "rgba(239, 68, 68, 0.5)",
    INDETERMINATE: "rgba(100, 116, 139, 0.35)",
    CLEAR: "rgba(16, 185, 129, 0.4)",
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PASS":
      case "MATCH":
      case "CLEARED":
      case "VERIFIED":
      case "COMPLETE":
        return { color: "#6ee7b7", bg: "rgba(16, 185, 129, 0.2)", border: "rgba(16, 185, 129, 0.4)" };
      case "FAIL":
      case "HIGH_RISK":
      case "MISMATCH":
      case "CONTRADICTION":
        return { color: "#fca5a5", bg: "rgba(239, 68, 68, 0.2)", border: "rgba(239, 68, 68, 0.45)" };
      case "REFER":
      case "SUSPICIOUS":
      case "DEGRADED":
        return { color: "#fcd34d", bg: "rgba(245, 158, 11, 0.2)", border: "rgba(245, 158, 11, 0.4)" };
      default:
        return { color: "#94a3b8", bg: "rgba(100, 116, 139, 0.18)", border: "rgba(100, 116, 139, 0.35)" };
    }
  };

  return (
    <div style={pageWrapperStyle}>
      {!developerMode ? <OfficerWorkspace
        report={autopsy} cases={casesData} status={systemStatus}
        document={docFile} selfie={selfieFile} preview={autopsy ? reportPreview : docPreview}
        selfiePreview={autopsy ? reportSelfiePreview : selfiePreview}
        family={selectedFamily} busy={isAnalyzing} error={errorMessage} presets={PRESET_SCENARIOS}
        onDocument={handleDocChange} onSelfie={handleSelfieChange} onFamily={setSelectedFamily}
        onRun={handleRunScreening} onCamera={startCamera} onPreset={loadPreset} onReopen={handleReopenCase}
        onDeveloper={() => setDeveloperMode(true)}
        onNew={() => { setAutopsy(null); setDocFile(null); setDocPreview(null); setSelfieFile(null); setSelfiePreview(null); setErrorMessage(null); setSelectedFamily(""); }}
      /> : <>
      <div style={{padding:"12px 24px",background:"#102131",color:"#e2e8f0",display:"flex",justifyContent:"space-between",alignItems:"center"}}><strong>Developer Mode · Pipeline inspection</strong><button onClick={() => setDeveloperMode(false)} style={outlineButtonStyle}>Return to Officer Mode</button></div>
      <Navbar
        activeTab={activeTab}
        onSelectTab={(tab) => {
          setActiveTab(tab);
          if (tab === "cases" || tab === "dashboard" || tab === "linkage") refreshData();
        }}
        systemReady={systemStatus?.status === "READY"}
        activeCaseId={autopsy?.case_id || autopsy?.scan_id}
        aiStatus={autopsy?.ai_explanation?.status || "UNAVAILABLE"}
      />

      <main style={mainContentStyle}>
        <DeveloperDiagnostics report={autopsy} status={systemStatus} />
        {/* ===================================================================== */}
        {/* 1. DASHBOARD VIEW */}
        {/* ===================================================================== */}
        {activeTab === "dashboard" && (
          <div>
            <div style={dashboardHeaderStyle}>
              <div>
                <h1 style={{ margin: 0, fontSize: "22px", color: "#f8fafc", fontWeight: 800 }}>
                  Forensic Screening Workstation
                </h1>
                <p style={{ margin: "4px 0 0 0", color: "#94a3b8", fontSize: "13px" }}>
                  Border identity inspection, cross-source consistency reconciliation, and multi-identity face linkage.
                </p>
              </div>
              <button onClick={() => setActiveTab("screening")} style={primaryButtonStyle}>
                + Start New Screening
              </button>
            </div>

            {/* Metric counters */}
            <div style={statsGridStyle}>
              <div style={statCardStyle}>
                <div style={statLabelStyle}>TOTAL SCREENINGS</div>
                <div style={statValueStyle}>{casesData?.summary.cases_screened ?? 0}</div>
                <div style={statSubtextStyle}>Forensic Ledger Records</div>
              </div>
              <div style={{ ...statCardStyle, borderLeft: "4px solid #10b981" }}>
                <div style={statLabelStyle}>LOW RISK (CLEARED)</div>
                <div style={{ ...statValueStyle, color: "#10b981" }}>{casesData?.summary.low_risk ?? 0}</div>
                <div style={statSubtextStyle}>Consistent Complete Evidence</div>
              </div>
              <div style={{ ...statCardStyle, borderLeft: "4px solid #f59e0b" }}>
                <div style={statLabelStyle}>REFER (OFFICER REVIEW)</div>
                <div style={{ ...statValueStyle, color: "#f59e0b" }}>{casesData?.summary.refer ?? 0}</div>
                <div style={statSubtextStyle}>Forensic Anomaly / Expired</div>
              </div>
              <div style={{ ...statCardStyle, borderLeft: "4px solid #ef4444" }}>
                <div style={statLabelStyle}>HIGH RISK (HARD GATES)</div>
                <div style={{ ...statValueStyle, color: "#ef4444" }}>{casesData?.summary.high_risk ?? 0}</div>
                <div style={statSubtextStyle}>Contradiction / Blacklist Hit</div>
              </div>
              <div style={{ ...statCardStyle, borderLeft: "4px solid #64748b" }}>
                <div style={statLabelStyle}>INDETERMINATE</div>
                <div style={{ ...statValueStyle, color: "#94a3b8" }}>{casesData?.summary.indeterminate ?? 0}</div>
                <div style={statSubtextStyle}>Incomplete Mandatory Lanes</div>
              </div>
            </div>

            {/* Quick Test Fixtures Grid */}
            <div style={{ ...cardSectionStyle, marginTop: "20px" }}>
              <div style={sectionHeaderFlexStyle}>
                <div>
                  <h3 style={{ margin: 0, fontSize: "15px", color: "#f8fafc", fontWeight: 700 }}>
                    Presentation Scenarios (1-Click Launch)
                  </h3>
                  <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                    Select pre-configured synthetic specimens to inspect the Identity Forensic Autopsy Engine behavior.
                  </p>
                </div>
                <span style={prototypeBadgeStyle}>SYNTHETIC DEMO CREDENTIALS</span>
              </div>

              <div style={presetGridStyle}>
                {PRESET_SCENARIOS.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => {
                      loadPreset(p);
                      setActiveTab("screening");
                    }}
                    style={presetCardStyle}
                  >
                    <div style={{ fontWeight: 700, fontSize: "13px", color: "#f8fafc" }}>{p.name}</div>
                    <div style={{ fontSize: "11px", color: "#38bdf8", marginTop: "3px", fontWeight: 600 }}>
                      Expected: {p.expected}
                    </div>
                    <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px", lineHeight: "1.3" }}>
                      {p.desc}
                    </div>
                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "6px", fontFamily: "monospace" }}>
                      {p.docFile} {p.selfieFile ? `+ ${p.selfieFile}` : ""}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Module Readiness Matrix */}
            <div style={{ ...cardSectionStyle, marginTop: "20px" }}>
              <h3 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#f8fafc", fontWeight: 700 }}>
                Subsystem Diagnostics & Readiness
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "10px" }}>
                {(systemStatus?.modules || []).map((m) => {
                  const isReady = m.state === "READY";
                  const badge = getStatusBadge(m.state);
                  return (
                    <div
                      key={m.module}
                      style={{
                        border: `1px solid ${isReady ? "rgba(16, 185, 129, 0.3)" : "rgba(245, 158, 11, 0.3)"}`,
                        backgroundColor: "#0d1c28",
                        padding: "10px 12px",
                        borderRadius: "6px",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <strong style={{ fontSize: "12px", color: "#f1f5f9" }}>{m.module}</strong>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 700,
                            color: badge.color,
                            backgroundColor: badge.bg,
                            border: `1px solid ${badge.border}`,
                            padding: "1px 5px",
                            borderRadius: "3px",
                          }}
                        >
                          {m.state}
                        </span>
                      </div>
                      <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>{m.detail}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Recent Cases */}
            <div style={{ ...cardSectionStyle, marginTop: "20px" }}>
              <div style={sectionHeaderFlexStyle}>
                <h3 style={{ margin: 0, fontSize: "15px", color: "#f8fafc", fontWeight: 700 }}>Recent Screenings Ledger</h3>
                <button
                  onClick={() => setActiveTab("cases")}
                  style={{ fontSize: "12px", color: "#38bdf8", background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}
                >
                  View Full Case Ledger &rarr;
                </button>
              </div>

              {casesData?.cases && casesData.cases.length > 0 ? (
                <div style={{ overflowX: "auto", marginTop: "8px" }}>
                  <table style={tableStyle}>
                    <thead>
                      <tr>
                        <th style={thStyle}>Case ID</th>
                        <th style={thStyle}>Timestamp</th>
                        <th style={thStyle}>Claimed Identity</th>
                        <th style={thStyle}>Doc Number</th>
                        <th style={thStyle}>Family</th>
                        <th style={thStyle}>Outcome</th>
                        <th style={thStyle}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {casesData.cases.slice(0, 5).map((c) => {
                        const badge = getStatusBadge(c.outcome);
                        return (
                          <tr key={c.case_id} style={trStyle}>
                            <td style={{ ...tdStyle, fontFamily: "monospace", color: "#38bdf8", fontWeight: 600 }}>
                              {c.case_id.slice(0, 8)}...
                            </td>
                            <td style={{ ...tdStyle, color: "#94a3b8" }}>
                              {new Date(c.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                            </td>
                            <td style={{ ...tdStyle, fontWeight: 600, color: "#f1f5f9" }}>{c.claimed_identity || "—"}</td>
                            <td style={{ ...tdStyle, fontFamily: "monospace", color: "#cbd5e1" }}>{c.document_number || "—"}</td>
                            <td style={tdStyle}>{c.document_family}</td>
                            <td style={tdStyle}>
                              <span
                                style={{
                                  fontSize: "11px",
                                  fontWeight: 700,
                                  color: badge.color,
                                  backgroundColor: badge.bg,
                                  border: `1px solid ${badge.border}`,
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                }}
                              >
                                {c.outcome}
                              </span>
                            </td>
                            <td style={tdStyle}>
                              <button onClick={() => handleReopenCase(c.case_id)} style={actionButtonStyle}>
                                Inspect Autopsy
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div style={{ textAlign: "center", color: "#64748b", padding: "20px", fontSize: "12px" }}>
                  No screenings recorded yet. Execute a screening above to populate the ledger.
                </div>
              )}
            </div>
          </div>
        )}

        {/* ===================================================================== */}
        {/* 2. SCREENING WORKSTATION VIEW */}
        {/* ===================================================================== */}
        {activeTab === "screening" && (
          <div>
            {/* INGESTION BAR */}
            <div style={cardSectionStyle}>
              <div style={sectionHeaderFlexStyle}>
                <div>
                  <h2 style={{ margin: 0, fontSize: "18px", color: "#f8fafc", fontWeight: 800 }}>
                    Forensic Credential Screening Workstation
                  </h2>
                  <p style={{ margin: "2px 0 0 0", color: "#94a3b8", fontSize: "12px" }}>
                    Multi-modal evidence ingestion: image pixels, deterministic MRZ, 1:1 biometrics, and watchlist intelligence.
                  </p>
                </div>

                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <select
                    value=""
                    onChange={(e) => {
                      const found = PRESET_SCENARIOS.find((p) => p.id === e.target.value);
                      if (found) loadPreset(found);
                    }}
                    style={selectStyle}
                  >
                    <option value="" disabled>
                      ⚡ Quick-Load Scenario...
                    </option>
                    {PRESET_SCENARIOS.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Ingestion Inputs Grid */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 280px", gap: "14px", marginTop: "14px" }}>
                {/* 1. Document Upload Box */}
                <div style={uploadBoxStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <label style={{ fontSize: "12px", fontWeight: 700, color: "#f1f5f9" }}>
                      1. Document Specimen (PNG, JPG, PDF)
                    </label>
                    <button type="button" onClick={() => startCamera("document")} style={cameraButtonStyle}>
                      📷 Camera
                    </button>
                  </div>

                  <input
                    type="file"
                    accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf"
                    onChange={handleDocChange}
                    style={{ fontSize: "11px", color: "#94a3b8", width: "100%" }}
                  />

                  {docPreview && (
                    <div style={{ marginTop: "8px", textAlign: "center" }}>
                      <img
                        src={docPreview}
                        alt="Doc preview"
                        style={{ maxHeight: "120px", maxWidth: "100%", borderRadius: "4px", border: "1px solid #1e3a4d" }}
                      />
                      <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
                        {docFile?.name} ({(docFile?.size || 0) / 1024 > 1024 ? `${((docFile?.size || 0) / (1024 * 1024)).toFixed(1)} MB` : `${Math.round((docFile?.size || 0) / 1024)} KB`})
                      </div>
                    </div>
                  )}
                </div>

                {/* 2. Live Face Comparison Box */}
                <div style={uploadBoxStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <label style={{ fontSize: "12px", fontWeight: 700, color: "#f1f5f9" }}>
                      2. Live Comparison Face (Optional)
                    </label>
                    <button type="button" onClick={() => startCamera("selfie")} style={cameraButtonStyle}>
                      📷 Selfie
                    </button>
                  </div>

                  <input
                    type="file"
                    accept=".png,.jpg,.jpeg,image/png,image/jpeg"
                    onChange={handleSelfieChange}
                    style={{ fontSize: "11px", color: "#94a3b8", width: "100%" }}
                  />

                  {selfiePreview && (
                    <div style={{ marginTop: "8px", textAlign: "center" }}>
                      <img
                        src={selfiePreview}
                        alt="Selfie preview"
                        style={{ maxHeight: "120px", maxWidth: "100%", borderRadius: "4px", border: "1px solid #1e3a4d" }}
                      />
                      <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>{selfieFile?.name}</div>
                    </div>
                  )}
                </div>

                {/* 3. Controls & Execution */}
                <div style={controlBoxStyle}>
                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8" }}>Document Family Override</label>
                    <select
                      value={selectedFamily}
                      onChange={(e) => setSelectedFamily(e.target.value)}
                      style={{ ...selectStyle, width: "100%", marginTop: "4px" }}
                    >
                      <option value="">Auto-Detect from OCR</option>
                      <option value="TRAVEL_DOCUMENT">Travel Document (Passport/TD3)</option>
                      <option value="VISA_OR_PERMIT">Visa or Permit</option>
                      <option value="NATIONAL_ID">National ID Card</option>
                      <option value="DRIVING_LICENCE">Driving Licence</option>
                    </select>
                  </div>

                  <button
                    type="button"
                    onClick={handleRunScreening}
                    disabled={isAnalyzing || !docFile}
                    style={{
                      ...primaryButtonStyle,
                      width: "100%",
                      padding: "11px",
                      opacity: isAnalyzing || !docFile ? 0.6 : 1,
                      marginTop: "10px",
                    }}
                  >
                    {isAnalyzing ? "🔬 Executing Autopsy…" : "⚡ Run Forensic Screening"}
                  </button>
                </div>
              </div>

              {errorMessage && (
                <div style={errorBannerStyle}>
                  <strong>Error:</strong> {errorMessage}
                </div>
              )}
            </div>

            {/* ================================================================= */}
            {/* FULL AUTOPSY REPORT */}
            {/* ================================================================= */}
            {autopsy && (
              <div style={{ marginTop: "20px", display: "flex", flexDirection: "column", gap: "20px" }}>
                {/* SECTION 1 — CASE SUMMARY (READABLE IN 3 SECONDS) */}
                <div
                  style={{
                    backgroundColor: outcomeBg[autopsy.outcome] || "#0c1a27",
                    border: `2px solid ${outcomeBorder[autopsy.outcome] || "#1e3a4d"}`,
                    borderRadius: "8px",
                    padding: "18px 20px",
                    boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
                    <div>
                      <div style={{ fontSize: "11px", fontWeight: 700, color: outcomeColors[autopsy.outcome], textTransform: "uppercase", letterSpacing: "1.2px" }}>
                        SCREENING CASE OUTCOME
                      </div>
                      <div style={{ fontSize: "28px", fontWeight: 900, color: outcomeColors[autopsy.outcome], marginTop: "2px" }}>
                        {autopsy.outcome}
                      </div>
                      {autopsy.triage_risk_index !== null && autopsy.triage_risk_index !== undefined && (
                        <div style={{ fontSize: "13px", fontWeight: 700, color: "#f1f5f9", marginTop: "4px" }}>
                          Triage Risk Index: <span style={{ color: outcomeColors[autopsy.outcome] }}>{autopsy.triage_risk_index.toFixed(1)} / 100</span>
                          <span style={{ fontSize: "11px", fontWeight: 500, color: "#94a3b8", marginLeft: "8px" }}>
                            ({autopsy.triage_risk_label})
                          </span>
                        </div>
                      )}
                      {autopsy.outcome_reasons && autopsy.outcome_reasons.length > 0 && (
                        <div style={{ marginTop: "6px", fontSize: "13px", color: "#f8fafc", fontWeight: 500 }}>
                          {autopsy.outcome_reasons.map((r, i) => (
                            <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "2px" }}>
                              <span style={{ color: outcomeColors[autopsy.outcome] }}>•</span>
                              <span>{r}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Summary Metadata Pills */}
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "8px" }}>
                      <div style={metaSummaryGridStyle}>
                        <div style={metaSummaryItemStyle}>
                          <span style={metaLabelStyle}>CLAIMED IDENTITY:</span>
                          <strong style={{ color: "#f8fafc" }}>
                            {(autopsy.extracted_identity as any)?.holder_name || (autopsy.visible_document_data?.visible_fields as any)?.holder_name || "UNIDENTIFIED"}
                          </strong>
                        </div>
                        <div style={metaSummaryItemStyle}>
                          <span style={metaLabelStyle}>DOCUMENT TYPE:</span>
                          <strong style={{ color: "#f8fafc" }}>{autopsy.document_family || autopsy.document_type}</strong>
                        </div>
                        <div style={metaSummaryItemStyle}>
                          <span style={metaLabelStyle}>DOCUMENT NUMBER:</span>
                          <strong style={{ color: "#38bdf8", fontFamily: "monospace" }}>
                            {(autopsy.extracted_identity as any)?.document_number || (autopsy.visible_document_data?.visible_fields as any)?.document_number || "—"}
                          </strong>
                        </div>
                        <div style={metaSummaryItemStyle}>
                          <span style={metaLabelStyle}>EVIDENCE COVERAGE:</span>
                          <strong style={{ color: autopsy.evidence_coverage.state === "COMPLETE" ? "#10b981" : "#f59e0b" }}>
                            {Math.round(autopsy.evidence_coverage.coverage_ratio * 100)}% ({autopsy.evidence_coverage.state})
                          </strong>
                        </div>
                      </div>

                      {/* Export Action Buttons */}
                      <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
                        <a
                          href={getReportHtmlUrl(autopsy.case_id || autopsy.scan_id)}
                          target="_blank"
                          rel="noreferrer"
                          style={outlineButtonStyle}
                        >
                          📄 Export Printable HTML
                        </a>
                        <a
                          href={getReportJsonUrl(autopsy.case_id || autopsy.scan_id)}
                          download
                          style={outlineButtonStyle}
                        >
                          💾 Export JSON Autopsy
                        </a>
                      </div>
                    </div>
                  </div>
                </div>

                {/* SECTION 2 — DOCUMENT + SUBJECT (2-COLUMN LAYOUT) */}
                <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "16px" }}>
                  {/* LEFT: Document Image Visualizer */}
                  <div>
                    <DocumentVisualizer
                      imageSrc={reportPreview}
                      findings={autopsy.visual_forensics?.findings || []}
                      title="Document Specimen Visualizer"
                    />
                  </div>

                  {/* RIGHT: Live Subject Biometrics */}
                  <div style={cardSectionStyle}>
                    <div style={sectionHeaderFlexStyle}>
                      <div>
                        <h3 style={{ margin: 0, fontSize: "14px", color: "#f8fafc", fontWeight: 700 }}>
                          1:1 Subject Biometric Verification
                        </h3>
                        <span style={{ fontSize: "11px", color: "#94a3b8" }}>
                          YuNet deep face detector + SFace 128-d cosine matcher
                        </span>
                      </div>
                      {autopsy.biometric_verification?.status === "PASS" ? (
                        <span
                          style={{
                            ...badgeStyle,
                            backgroundColor: autopsy.biometric_verification.decision === "MATCH" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                            color: autopsy.biometric_verification.decision === "MATCH" ? "#6ee7b7" : "#fca5a5",
                            borderColor: autopsy.biometric_verification.decision === "MATCH" ? "rgba(16, 185, 129, 0.4)" : "rgba(239, 68, 68, 0.4)",
                          }}
                        >
                          {autopsy.biometric_verification.decision || "MATCH"}
                        </span>
                      ) : (
                        <span style={{ ...badgeStyle, backgroundColor: "rgba(100, 116, 139, 0.2)", color: "#94a3b8" }}>
                          {autopsy.biometric_verification?.status || "NOT_SUPPLIED"}
                        </span>
                      )}
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginTop: "12px" }}>
                      <div style={bioPreviewBoxStyle}>
                        <div style={bioLabelStyle}>DOCUMENT PORTRAIT</div>
                        <div style={bioImageBoxStyle}>
                          {reportPreview ? (
                            <img src={reportPreview} alt="Doc portrait" style={bioImgStyle} />
                          ) : (
                            <span style={{ color: "#64748b", fontSize: "11px" }}>No document image</span>
                          )}
                        </div>
                      </div>

                      <div style={bioPreviewBoxStyle}>
                        <div style={bioLabelStyle}>LIVE CAPTURE</div>
                        <div style={bioImageBoxStyle}>
                          {reportSelfiePreview ? (
                            <img src={reportSelfiePreview} alt="Live face" style={bioImgStyle} />
                          ) : (
                            <span style={{ color: "#64748b", fontSize: "11px" }}>No live selfie provided</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div style={bioMetricsGridStyle}>
                      <div style={bioMetricItemStyle}>
                        <span style={metaLabelStyle}>SIMILARITY SCORE:</span>
                        <strong style={{ fontSize: "14px", color: (autopsy.biometric_verification?.similarity ?? 0) >= (autopsy.biometric_verification?.configured_prototype_threshold ?? 0.55) ? "#10b981" : "#ef4444" }}>
                          {autopsy.biometric_verification?.similarity !== null && autopsy.biometric_verification?.similarity !== undefined
                            ? autopsy.biometric_verification.similarity.toFixed(4)
                            : "—"}
                        </strong>
                      </div>
                      <div style={bioMetricItemStyle}>
                        <span style={metaLabelStyle}>PASS THRESHOLD:</span>
                        <strong style={{ color: "#cbd5e1" }}>
                          &ge; {autopsy.biometric_verification?.configured_prototype_threshold?.toFixed(2) || "0.55"}
                        </strong>
                      </div>
                      <div style={bioMetricItemStyle}>
                        <span style={metaLabelStyle}>MODEL ASSET:</span>
                        <strong style={{ color: "#94a3b8", fontSize: "11px" }}>
                          {autopsy.biometric_verification?.model || "OpenCV YuNet + SFace"}
                        </strong>
                      </div>
                    </div>
                  </div>
                </div>

                {/* SECTION 3 — EVIDENCE MODULES (8 CLEAN EXPANDABLE CARDS) */}
                <div>
                  <h3 style={{ margin: "0 0 10px 0", fontSize: "14px", color: "#94a3b8", fontWeight: 700, letterSpacing: "0.5px" }}>
                    INDEPENDENT EVIDENCE LANES
                  </h3>

                  <div style={moduleCardsGridStyle}>
                    {/* Card 1: Capture Quality */}
                    <div style={moduleCardStyle}>
                      <div style={moduleHeaderStyle}>
                        <span style={moduleTitleStyle}>1. Capture Quality Gate</span>
                        <span style={getModuleBadgeStyle(autopsy.capture_quality?.status || "PASS")}>
                          {autopsy.capture_quality?.status || "PASS"}
                        </span>
                      </div>
                      <p style={moduleSummaryStyle}>
                        {autopsy.capture_quality?.acceptable
                          ? "Image resolution, sharpness, and exposure passed all prerequisite gate checks."
                          : "Image quality requires recapture before dependable extraction."}
                      </p>
                      <button onClick={() => toggleCard("quality")} style={expandToggleStyle}>
                        {expandedCards["quality"] ? "▲ Hide Details" : "▼ Technical Details"}
                      </button>
                      {expandedCards["quality"] && (
                        <div style={expandedContentStyle}>
                          <div style={detailRowStyle}>
                            <span>Resolution:</span>
                            <span>{autopsy.capture_quality?.findings?.find((f) => f.check === "resolution")?.threshold || "Passed minimum 700x440"}</span>
                          </div>
                          <div style={detailRowStyle}>
                            <span>Sharpness / Blur:</span>
                            <span>{autopsy.capture_quality?.findings?.find((f) => f.check === "sharpness")?.state || "ACCEPTABLE"}</span>
                          </div>
                          <div style={detailRowStyle}>
                            <span>Exposure:</span>
                            <span>{autopsy.capture_quality?.findings?.find((f) => f.check === "exposure")?.state || "ACCEPTABLE"}</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Card 2: OCR / VIZ Extraction */}
                    <div style={moduleCardStyle}>
                      <div style={moduleHeaderStyle}>
                        <span style={moduleTitleStyle}>2. OCR / VIZ Extraction</span>
                        <span style={getModuleBadgeStyle(autopsy.visible_document_data?.visible_fields ? "PASS" : "UNAVAILABLE")}>
                          {autopsy.visible_document_data?.visible_fields ? "PASS" : "UNAVAILABLE"}
                        </span>
                      </div>
                      <p style={moduleSummaryStyle}>
                        {Object.keys(autopsy.visible_document_data?.visible_fields || {}).length} alphanumeric fields extracted from document surface.
                      </p>
                      <button onClick={() => toggleCard("ocr")} style={expandToggleStyle}>
                        {expandedCards["ocr"] ? "▲ Hide Details" : "▼ Technical Details"}
                      </button>
                      {expandedCards["ocr"] && (
                        <div style={expandedContentStyle}>
                          {Object.entries(autopsy.visible_document_data?.visible_fields || {}).map(([k, v]) => (
                            <div key={k} style={detailRowStyle}>
                              <span>{FIELD_LABELS[k] || k}:</span>
                              <strong style={{ color: "#38bdf8" }}>{String(v)}</strong>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Card 3: MRZ Validation */}
                    <div style={moduleCardStyle}>
                      <div style={moduleHeaderStyle}>
                        <span style={moduleTitleStyle}>3. MRZ Validation (ICAO 9303)</span>
                        <span style={getModuleBadgeStyle(autopsy.mrz_analysis?.checks && Object.values(autopsy.mrz_analysis.checks).includes("FAIL") ? "FAIL" : (autopsy.mrz_analysis?.applicability === "NOT_APPLICABLE" ? "NOT_APPLICABLE" : "PASS"))}>
                          {autopsy.mrz_analysis?.checks && Object.values(autopsy.mrz_analysis.checks).includes("FAIL") ? "FAIL" : (autopsy.mrz_analysis?.applicability === "NOT_APPLICABLE" ? "NOT_APPLICABLE" : "PASS")}
                        </span>
                      </div>
                      <p style={moduleSummaryStyle}>
                        {autopsy.mrz_analysis?.applicability === "NOT_APPLICABLE"
                          ? "Machine-Readable Zone is not applicable to this domestic credential."
                          : `${Object.values(autopsy.mrz_analysis?.checks || {}).filter((v) => v === "PASS").length}/${Object.keys(autopsy.mrz_analysis?.checks || {}).length} check digits valid (7-3-1 weight).`}
                      </p>
                      <button onClick={() => toggleCard("mrz")} style={expandToggleStyle}>
                        {expandedCards["mrz"] ? "▲ Hide Details" : "▼ Technical Details"}
                      </button>
                      {expandedCards["mrz"] && (
                        <div style={expandedContentStyle}>
                          {Object.entries(autopsy.mrz_analysis?.checks || {}).map(([k, v]) => (
                            <div key={k} style={detailRowStyle}>
                              <span>{k.replace(/_/g, " ")}:</span>
                              <span style={{ color: v === "PASS" ? "#10b981" : "#ef4444", fontWeight: 700 }}>{v}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Card 4: Cross-Source Consistency */}
                    <div style={moduleCardStyle}>
                      <div style={moduleHeaderStyle}>
                        <span style={moduleTitleStyle}>4. Cross-Source Consistency</span>
                        <span style={getModuleBadgeStyle(autopsy.cross_source_consistency?.some((c) => c.status === "FAIL") ? "FAIL" : "PASS")}>
                          {autopsy.cross_source_consistency?.some((c) => c.status === "FAIL") ? "FAIL" : "PASS"}
                        </span>
                      </div>
                      <p style={moduleSummaryStyle}>
                        {autopsy.cross_source_consistency?.some((c) => c.status === "FAIL")
                          ? "Contradiction detected between visible text and machine-readable zone."
                          : "Visual Zone and Machine-Readable Zone are semantically consistent."}
                      </p>
                      <button onClick={() => toggleCard("consistency")} style={expandToggleStyle}>
                        {expandedCards["consistency"] ? "▲ Hide Details" : "▼ Technical Details"}
                      </button>
                      {expandedCards["consistency"] && (
                        <div style={expandedContentStyle}>
                          {autopsy.cross_source_consistency?.map((c, i) => (
                            <div key={i} style={detailRowStyle}>
                              <span>{FIELD_LABELS[c.field] || c.field}:</span>
                              <span style={{ color: c.status === "MATCH" || c.status === "PASS" ? "#10b981" : "#ef4444", fontWeight: 700 }}>
                                {c.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Card 5: Visual Forensics */}
                    <div style={moduleCardStyle}>
                      <div style={moduleHeaderStyle}>
                        <span style={moduleTitleStyle}>5. Visual Forensics</span>
                        <span style={getModuleBadgeStyle(autopsy.visual_forensics?.status || "PASS")}>
                          {autopsy.visual_forensics?.status || "PASS"}
                        </span>
                      </div>
                      <p style={moduleSummaryStyle}>
                        {autopsy.visual_forensics?.status === "SUSPICIOUS"
                          ? `${autopsy.visual_forensics.findings?.length || 1} high-frequency edge/noise anomaly localized.`
                          : "No edge gradient or noise variance anomalies detected."}
                      </p>
                      <button onClick={() => toggleCard("forensics")} style={expandToggleStyle}>
                        {expandedCards["forensics"] ? "▲ Hide Details" : "▼ Technical Details"}
                      </button>
                      {expandedCards["forensics"] && (
                        <div style={expandedContentStyle}>
                          <div style={detailRowStyle}>
                            <span>Detector:</span>
                            <span>{autopsy.visual_forensics?.detector?.name || "Local Deterministic Heuristics"}</span>
                          </div>
                          {autopsy.visual_forensics?.findings?.map((f, i) => (
                            <div key={i} style={{ fontSize: "11px", color: "#fca5a5", marginTop: "4px" }}>
                              • {f.finding_type}: {f.explanation}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Card 6: Face Verification */}
                    <div style={moduleCardStyle}>
                      <div style={moduleHeaderStyle}>
                        <span style={moduleTitleStyle}>6. Face Verification</span>
                        <span style={getModuleBadgeStyle(autopsy.biometric_verification?.status || "UNAVAILABLE")}>
                          {autopsy.biometric_verification?.status || "UNAVAILABLE"}
                        </span>
                      </div>
                      <p style={moduleSummaryStyle}>
                        {autopsy.biometric_verification?.similarity !== null && autopsy.biometric_verification?.similarity !== undefined
                          ? `Cosine similarity ${autopsy.biometric_verification.similarity.toFixed(4)} (${autopsy.biometric_verification.decision})`
                          : "No live selfie capture supplied for biometric comparison."}
                      </p>
                      <button onClick={() => toggleCard("bio")} style={expandToggleStyle}>
                        {expandedCards["bio"] ? "▲ Hide Details" : "▼ Technical Details"}
                      </button>
                      {expandedCards["bio"] && (
                        <div style={expandedContentStyle}>
                          <div style={detailRowStyle}>
                            <span>Decision:</span>
                            <span style={{ color: autopsy.biometric_verification?.decision === "MATCH" ? "#10b981" : "#ef4444", fontWeight: 700 }}>
                              {autopsy.biometric_verification?.decision || "—"}
                            </span>
                          </div>
                          <div style={detailRowStyle}>
                            <span>Similarity:</span>
                            <span>{autopsy.biometric_verification?.similarity?.toFixed(4) || "—"}</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Card 7: Threat Intelligence */}
                    <div style={moduleCardStyle}>
                      <div style={moduleHeaderStyle}>
                        <span style={moduleTitleStyle}>7. Threat Intelligence</span>
                        <span style={getModuleBadgeStyle(autopsy.threat_intelligence?.result === "ALERT" ? "FAIL" : "PASS")}>
                          {autopsy.threat_intelligence?.result === "ALERT" ? "FAIL" : "PASS"}
                        </span>
                      </div>
                      <p style={moduleSummaryStyle}>
                        {autopsy.threat_intelligence?.result === "ALERT"
                          ? "Alert: Document identifier present on local prototype watchlist."
                          : "Local prototype watchlist query returned clear (no hits)."}
                      </p>
                      <button onClick={() => toggleCard("intel")} style={expandToggleStyle}>
                        {expandedCards["intel"] ? "▲ Hide Details" : "▼ Technical Details"}
                      </button>
                      {expandedCards["intel"] && (
                        <div style={expandedContentStyle}>
                          <div style={detailRowStyle}>
                            <span>Watchlist Source:</span>
                            <span>{autopsy.threat_intelligence?.display_source || "LOCAL PROTOTYPE WATCHLIST"}</span>
                          </div>
                          <div style={detailRowStyle}>
                            <span>Status:</span>
                            <span>{autopsy.threat_intelligence?.result || "CLEAR"}</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Card 8: Identity Linkage */}
                    <div style={moduleCardStyle}>
                      <div style={moduleHeaderStyle}>
                        <span style={moduleTitleStyle}>8. Identity Linkage</span>
                        <span style={getModuleBadgeStyle(autopsy.identity_linkage?.matches && autopsy.identity_linkage.matches.length > 0 ? "REFER" : "PASS")}>
                          {autopsy.identity_linkage?.matches && autopsy.identity_linkage.matches.length > 0 ? "REFER" : "PASS"}
                        </span>
                      </div>
                      <p style={moduleSummaryStyle}>
                        {autopsy.identity_linkage?.matches && autopsy.identity_linkage.matches.length > 0
                          ? `Identical biometric face enrolled under ${autopsy.identity_linkage.matches.length} alternate identity alias(es).`
                          : "No duplicate facial biometrics detected across case ledger."}
                      </p>
                      <button onClick={() => toggleCard("linkage")} style={expandToggleStyle}>
                        {expandedCards["linkage"] ? "▲ Hide Details" : "▼ Technical Details"}
                      </button>
                      {expandedCards["linkage"] && (
                        <div style={expandedContentStyle}>
                          <div style={detailRowStyle}>
                            <span>Cluster Ref:</span>
                            <span>{autopsy.identity_linkage?.identity_reference || "Cluster 001"}</span>
                          </div>
                          {autopsy.identity_linkage?.matches?.map((m, i) => (
                            <div key={i} style={{ fontSize: "11px", color: "#fcd34d", marginTop: "4px" }}>
                              • Linked Case {m.case_id.slice(0, 8)}: {m.claimed_name} ({m.document_number})
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* SECTION 4 — DEDICATED CROSS-SOURCE CONSISTENCY TABLE */}
                {autopsy.cross_source_consistency && autopsy.cross_source_consistency.length > 0 && (
                  <div style={cardSectionStyle}>
                    <div style={sectionHeaderFlexStyle}>
                      <div>
                        <h3 style={{ margin: 0, fontSize: "15px", color: "#f8fafc", fontWeight: 700 }}>
                          Cross-Source Semantic Consistency Reconciliation
                        </h3>
                        <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                          Field-by-field verification between Visual Inspection Zone (VIZ) and Machine-Readable Zone (MRZ).
                        </p>
                      </div>
                      <span style={prototypeBadgeStyle}>TIER 2 HARD INTEGRITY</span>
                    </div>

                    <div style={{ overflowX: "auto", marginTop: "12px" }}>
                      <table style={tableStyle}>
                        <thead>
                          <tr>
                            <th style={thStyle}>FIELD NAME</th>
                            <th style={thStyle}>VIZ (PRINTED / OBSERVED)</th>
                            <th style={thStyle}>MRZ (MACHINE-READABLE)</th>
                            <th style={thStyle}>CONSISTENCY STATUS</th>
                          </tr>
                        </thead>
                        <tbody>
                          {autopsy.cross_source_consistency.map((c, idx) => {
                            const isContradiction = c.status === "FAIL" || c.status === "SUSPICIOUS" || c.status === "CRITICAL_CONTRADICTION";
                            const isMatch = c.status === "MATCH" || c.status === "PASS";
                            return (
                              <tr
                                key={idx}
                                style={{
                                  ...trStyle,
                                  backgroundColor: isContradiction ? "rgba(239, 68, 68, 0.1)" : "#0c1a27",
                                }}
                              >
                                <td style={{ ...tdStyle, fontWeight: 700, color: "#f8fafc" }}>
                                  {FIELD_LABELS[c.field] || c.field}
                                </td>
                                <td style={{ ...tdStyle, fontFamily: "monospace", color: isContradiction ? "#f87171" : "#cbd5e1", fontWeight: isContradiction ? 700 : 500 }}>
                                  {c.value_a || "—"}
                                </td>
                                <td style={{ ...tdStyle, fontFamily: "monospace", color: isContradiction ? "#38bdf8" : "#cbd5e1", fontWeight: isContradiction ? 700 : 500 }}>
                                  {c.value_b || "—"}
                                </td>
                                <td style={tdStyle}>
                                  {isContradiction ? (
                                    <span style={contradictionBadgeStyle}>
                                      ⚠️ CONTRADICTION ({c.severity || "CRITICAL"})
                                    </span>
                                  ) : isMatch ? (
                                    <span style={matchBadgeStyle}>✓ MATCH</span>
                                  ) : (
                                    <span style={naBadgeStyle}>{c.status}</span>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* SECTION 5 — EVIDENCE GRAPH */}
                <EvidenceGraphViewer graph={autopsy.evidence_graph} />

                {/* SECTION 6 — FORENSIC HYPOTHESES */}
                {autopsy.forensic_hypotheses && autopsy.forensic_hypotheses.length > 0 && (
                  <div style={cardSectionStyle}>
                    <h3 style={{ margin: "0 0 10px 0", fontSize: "15px", color: "#f8fafc", fontWeight: 700 }}>
                      Deterministic Forensic Hypotheses
                    </h3>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "12px" }}>
                      {autopsy.forensic_hypotheses.map((h, i) => {
                        const isSevere = h.severity === "CRITICAL" || h.severity === "HIGH";
                        return (
                          <div
                            key={i}
                            style={{
                              backgroundColor: isSevere ? "rgba(239, 68, 68, 0.08)" : "#0d1c28",
                              border: `1px solid ${isSevere ? "rgba(239, 68, 68, 0.3)" : "#1e3a4d"}`,
                              borderRadius: "6px",
                              padding: "12px",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <strong style={{ fontSize: "12px", color: isSevere ? "#fca5a5" : "#f1f5f9" }}>
                                {h.hypothesis.replace(/_/g, " ")}
                              </strong>
                              <span
                                style={{
                                  fontSize: "10px",
                                  fontWeight: 700,
                                  color: isSevere ? "#f87171" : "#38bdf8",
                                  backgroundColor: isSevere ? "rgba(239, 68, 68, 0.2)" : "rgba(56, 189, 248, 0.15)",
                                  padding: "1px 6px",
                                  borderRadius: "3px",
                                }}
                              >
                                {h.severity}
                              </span>
                            </div>
                            <p style={{ fontSize: "12px", color: "#cbd5e1", margin: "6px 0 0 0", lineHeight: "1.4" }}>
                              {h.explanation}
                            </p>
                            {h.supporting_evidence && h.supporting_evidence.length > 0 && (
                              <div style={{ marginTop: "6px", fontSize: "11px", color: "#94a3b8" }}>
                                <strong>Evidence:</strong> {h.supporting_evidence.join(", ")}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* SECTION 7 — NEXT-BEST-EVIDENCE ACTIONS */}
                {autopsy.next_best_actions && autopsy.next_best_actions.length > 0 && (
                  <div style={cardSectionStyle}>
                    <div style={sectionHeaderFlexStyle}>
                      <div>
                        <h3 style={{ margin: 0, fontSize: "15px", color: "#f8fafc", fontWeight: 700 }}>
                          Recommended Next-Best Actions (Prioritized Investigation)
                        </h3>
                        <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                          Autonomous decision support recommendations for front-line and secondary inspection officers.
                        </p>
                      </div>
                      <span style={prototypeBadgeStyle}>ACTION PLANNER</span>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "12px" }}>
                      {autopsy.next_best_actions.map((act, idx) => (
                        <div key={idx} style={actionCardStyle}>
                          <div style={actionNumberStyle}>{idx + 1}</div>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <strong style={{ fontSize: "13px", color: "#f8fafc" }}>
                                {act.action.replace(/_/g, " ")}
                              </strong>
                              <span style={priorityPillStyle}>Priority #{act.priority}</span>
                            </div>
                            <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "2px" }}>{act.reason}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* SECTION 8 — AI FORENSIC ASSISTANT (FASTROUTER BOUNDED LAYER) */}
                <div style={aiPanelContainerStyle}>
                  <div style={sectionHeaderFlexStyle}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div style={aiLogoStyle}>AI</div>
                      <div>
                        <h3 style={{ margin: 0, fontSize: "15px", color: "#f8fafc", fontWeight: 800 }}>
                          AI FORENSIC ASSISTANT (FastRouter Reasoning Layer)
                        </h3>
                        <p style={{ margin: "2px 0 0 0", fontSize: "11px", color: "#38bdf8" }}>
                          AI explanation is bounded by verified forensic evidence and policy rules.
                        </p>
                      </div>
                    </div>

                    <span
                      style={{
                        ...badgeStyle,
                        backgroundColor: autopsy.ai_explanation?.status === "ACTIVE" ? "rgba(56, 189, 248, 0.2)" : "rgba(100, 116, 139, 0.2)",
                        color: autopsy.ai_explanation?.status === "ACTIVE" ? "#7dd3fc" : "#94a3b8",
                        borderColor: autopsy.ai_explanation?.status === "ACTIVE" ? "#38bdf8" : "#334155",
                      }}
                    >
                      AI STATUS: {autopsy.ai_explanation?.status || "ACTIVE"}
                    </span>
                  </div>

                  <div style={aiContentGridStyle}>
                    {/* 1. Case Summary */}
                    <div style={aiBlockStyle}>
                      <div style={aiBlockTitleStyle}>📌 EXECUTIVE CASE SUMMARY</div>
                      <p style={aiBlockTextStyle}>
                        {autopsy.ai_explanation?.summary ||
                          `Screening evaluated ${autopsy.document_family || "credential"} with an outcome of ${autopsy.outcome}. All findings are traceable in the autopsy evidence graph.`}
                      </p>
                    </div>

                    {/* 2. Why Outcome Occurred */}
                    <div style={aiBlockStyle}>
                      <div style={aiBlockTitleStyle}>⚖️ WHY THIS OUTCOME OCCURRED</div>
                      <p style={aiBlockTextStyle}>
                        {autopsy.ai_explanation?.why_outcome ||
                          (autopsy.outcome_reasons?.join("; ") || "Outcome determined by policy evaluation across verified lanes.")}
                      </p>
                    </div>

                    {/* 3. Contradictions & Key Evidence */}
                    <div style={aiBlockStyle}>
                      <div style={aiBlockTitleStyle}>🔍 CONTRADICTIONS & VERIFIED FINDINGS</div>
                      {autopsy.ai_explanation?.contradictions && autopsy.ai_explanation.contradictions.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                          {autopsy.ai_explanation.contradictions.map((c, i) => (
                            <div key={i} style={{ fontSize: "12px", color: "#fca5a5" }}>
                              • {c}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ fontSize: "12px", color: "#6ee7b7" }}>
                          ✓ No unresolved deterministic or biometric contradictions detected.
                        </div>
                      )}
                    </div>

                    {/* 4. Recommended Action */}
                    <div style={aiBlockStyle}>
                      <div style={aiBlockTitleStyle}>🎯 RECOMMENDED NEXT ACTION</div>
                      {autopsy.ai_explanation?.recommended_actions && autopsy.ai_explanation.recommended_actions.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                          {autopsy.ai_explanation.recommended_actions.map((a, i) => (
                            <div key={i} style={{ fontSize: "12px", color: "#cbd5e1" }}>
                              {i + 1}. {a}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ fontSize: "12px", color: "#cbd5e1" }}>
                          {autopsy.next_best_actions?.[0]?.action?.replace(/_/g, " ") || "Refer to secondary inspection if required."}
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={aiFooterDisclaimerStyle}>
                    <strong>Governance Note:</strong> FastRouter AI explanations are strictly explanatory and bounded by deterministic policy. The AI does not decide authenticity or override evidence.
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ===================================================================== */}
        {/* 3. CASE LEDGER VIEW */}
        {/* ===================================================================== */}
        {activeTab === "cases" && (
          <div style={cardSectionStyle}>
            <div style={sectionHeaderFlexStyle}>
              <div>
                <h2 style={{ margin: 0, fontSize: "18px", color: "#f8fafc", fontWeight: 800 }}>
                  Case Audit Ledger & Persistence
                </h2>
                <p style={{ margin: "2px 0 0 0", color: "#94a3b8", fontSize: "12px" }}>
                  Persistent SQLite forensic audit database with cryptographically signed JSON & HTML autopsy records.
                </p>
              </div>

              <div style={{ display: "flex", gap: "8px" }}>
                <select
                  value={caseFilter}
                  onChange={(e) => setCaseFilter(e.target.value)}
                  style={selectStyle}
                >
                  <option value="ALL">All Outcomes</option>
                  <option value="LOW_RISK">Low Risk</option>
                  <option value="REFER">Refer</option>
                  <option value="HIGH_RISK">High Risk</option>
                  <option value="INDETERMINATE">Indeterminate</option>
                </select>
              </div>
            </div>

            <div style={{ marginTop: "14px" }}>
              <input
                type="text"
                placeholder="🔍 Search by Case ID, Claimed Name, or Document Number..."
                value={caseSearch}
                onChange={(e) => setCaseSearch(e.target.value)}
                style={searchInputStyle}
              />
            </div>

            {casesData?.cases && casesData.cases.length > 0 ? (
              <div style={{ overflowX: "auto", marginTop: "12px" }}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Case ID</th>
                      <th style={thStyle}>Timestamp</th>
                      <th style={thStyle}>Claimed Identity</th>
                      <th style={thStyle}>Doc Number</th>
                      <th style={thStyle}>Family</th>
                      <th style={thStyle}>Outcome</th>
                      <th style={thStyle}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {casesData.cases
                      .filter((c) => (caseFilter === "ALL" ? true : c.outcome === caseFilter))
                      .filter((c) => {
                        if (!caseSearch) return true;
                        const s = caseSearch.toLowerCase();
                        return (
                          c.case_id.toLowerCase().includes(s) ||
                          (c.claimed_identity || "").toLowerCase().includes(s) ||
                          (c.document_number || "").toLowerCase().includes(s)
                        );
                      })
                      .map((c) => {
                        const badge = getStatusBadge(c.outcome);
                        return (
                          <tr key={c.case_id} style={trStyle}>
                            <td style={{ ...tdStyle, fontFamily: "monospace", color: "#38bdf8", fontWeight: 600 }}>
                              {c.case_id.slice(0, 8)}...
                            </td>
                            <td style={{ ...tdStyle, color: "#94a3b8" }}>
                              {new Date(c.created_at).toLocaleString()}
                            </td>
                            <td style={{ ...tdStyle, fontWeight: 600, color: "#f8fafc" }}>{c.claimed_identity || "—"}</td>
                            <td style={{ ...tdStyle, fontFamily: "monospace", color: "#cbd5e1" }}>{c.document_number || "—"}</td>
                            <td style={tdStyle}>{c.document_family}</td>
                            <td style={tdStyle}>
                              <span
                                style={{
                                  fontSize: "11px",
                                  fontWeight: 700,
                                  color: badge.color,
                                  backgroundColor: badge.bg,
                                  border: `1px solid ${badge.border}`,
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                }}
                              >
                                {c.outcome}
                              </span>
                            </td>
                            <td style={tdStyle}>
                              <button onClick={() => handleReopenCase(c.case_id)} style={actionButtonStyle}>
                                Inspect Autopsy
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ textAlign: "center", color: "#64748b", padding: "32px", fontSize: "13px" }}>
                No cases found in ledger.
              </div>
            )}
          </div>
        )}

        {/* ===================================================================== */}
        {/* 4. IDENTITY LINKAGE VIEW */}
        {/* ===================================================================== */}
        {activeTab === "linkage" && (
          <div style={cardSectionStyle}>
            <div style={sectionHeaderFlexStyle}>
              <div>
                <h2 style={{ margin: 0, fontSize: "18px", color: "#f8fafc", fontWeight: 800 }}>
                  Multi-Identity Biometric Linkage Ledger
                </h2>
                <p style={{ margin: "2px 0 0 0", color: "#94a3b8", fontSize: "12px" }}>
                  128-dimensional facial vector store detecting duplicate face presentation across distinct biographic claims.
                </p>
              </div>
              <span style={prototypeBadgeStyle}>VECTOR CLUSTERING</span>
            </div>

            {linkageData && linkageData.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "14px" }}>
                {linkageData.map((cluster, idx) => (
                  <div key={idx} style={clusterCardStyle}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong style={{ fontSize: "13px", color: "#38bdf8" }}>
                        🔗 {cluster.identity_reference} ({cluster.credentials.length} Associated Cases)
                      </strong>
                      <span style={{ fontSize: "11px", color: "#94a3b8" }}>{cluster.source}</span>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "8px", marginTop: "10px" }}>
                      {cluster.credentials.map((cred, cIdx) => (
                        <div key={cIdx} style={clusterCredCardStyle}>
                          <div style={{ fontSize: "12px", fontWeight: 700, color: "#f8fafc" }}>
                            {cred.claimed_name || "Unknown Name"}
                          </div>
                          <div style={{ fontSize: "11px", color: "#38bdf8", fontFamily: "monospace" }}>
                            Doc: {cred.document_number || "—"}
                          </div>
                          <div style={{ fontSize: "10px", color: "#64748b", marginTop: "4px" }}>
                            Case: {cred.case_id.slice(0, 8)}... • {new Date(cred.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: "center", color: "#64748b", padding: "32px", fontSize: "13px" }}>
                No multi-identity clusters formed yet. Execute screenings with facial images to build vector clusters.
              </div>
            )}
          </div>
        )}

        {/* ===================================================================== */}
        {/* 5. SYSTEM STATUS VIEW */}
        {/* ===================================================================== */}
        {activeTab === "status" && (
          <div style={cardSectionStyle}>
            <div style={sectionHeaderFlexStyle}>
              <div>
                <h2 style={{ margin: 0, fontSize: "18px", color: "#f8fafc", fontWeight: 800 }}>
                  System Diagnostics & Subsystem Status
                </h2>
                <p style={{ margin: "2px 0 0 0", color: "#94a3b8", fontSize: "12px" }}>
                  Real-time health status across all 11 forensic screening subsystems and AI reasoning layer.
                </p>
              </div>
              <span
                style={{
                  ...badgeStyle,
                  backgroundColor: systemStatus?.status === "READY" ? "rgba(16, 185, 129, 0.2)" : "rgba(245, 158, 11, 0.2)",
                  color: systemStatus?.status === "READY" ? "#6ee7b7" : "#fcd34d",
                }}
              >
                OVERALL: {systemStatus?.status || "UNKNOWN"}
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px", marginTop: "14px" }}>
              {(systemStatus?.modules || []).map((m) => {
                const isReady = m.state === "READY";
                const badge = getStatusBadge(m.state);
                return (
                  <div
                    key={m.module}
                    style={{
                      backgroundColor: "#0d1c28",
                      border: `1px solid ${isReady ? "rgba(16, 185, 129, 0.3)" : "rgba(245, 158, 11, 0.3)"}`,
                      borderRadius: "6px",
                      padding: "14px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong style={{ fontSize: "13px", color: "#f8fafc" }}>{m.module}</strong>
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: 700,
                          color: badge.color,
                          backgroundColor: badge.bg,
                          border: `1px solid ${badge.border}`,
                          padding: "2px 6px",
                          borderRadius: "3px",
                        }}
                      >
                        {m.state}
                      </span>
                    </div>
                    <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "6px", lineHeight: "1.4" }}>
                      {m.detail}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ===================================================================== */}
        {/* 6. POLICY & SETTINGS VIEW */}
        {/* ===================================================================== */}
        {activeTab === "settings" && (
          <div style={cardSectionStyle}>
            <h2 style={{ margin: "0 0 12px 0", fontSize: "18px", color: "#f8fafc", fontWeight: 800 }}>
              4-Tier Truth Hierarchy & Policy Rules
            </h2>
            <p style={{ color: "#94a3b8", fontSize: "13px", lineHeight: "1.5" }}>
              VEDA-BORDER enforces strict authority tiers. Higher-tier deterministic evidence unconditionally overrides lower-tier probabilistic scores.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "14px" }}>
              <div style={tierCardStyle}>
                <div style={{ color: "#ef4444", fontWeight: 800, fontSize: "13px" }}>
                  TIER 1 (HIGHEST AUTHORITY): HARD GATES & CRYPTOGRAPHIC INVARIANTS
                </div>
                <div style={{ color: "#cbd5e1", fontSize: "12px", marginTop: "4px" }}>
                  • ICAO 9303 MRZ Checksums • 1:1 Live Face Match (&lt; 0.55) • Threat Intelligence Watchlist • Capture Quality Gate
                </div>
              </div>

              <div style={tierCardStyle}>
                <div style={{ color: "#f59e0b", fontWeight: 800, fontSize: "13px" }}>
                  TIER 2: DETERMINISTIC CROSS-SOURCE INTEGRITY
                </div>
                <div style={{ color: "#cbd5e1", fontSize: "12px", marginTop: "4px" }}>
                  • VIZ-to-MRZ Semantic Field Comparisons (DOB, Expiry, Number) • Document Expiry Date vs UTC Clock • Multi-Identity Alias Linkage
                </div>
              </div>

              <div style={tierCardStyle}>
                <div style={{ color: "#38bdf8", fontWeight: 800, fontSize: "13px" }}>
                  TIER 3: OBSERVED HEURISTICS & SIGNAL ANOMALIES
                </div>
                <div style={{ color: "#cbd5e1", fontSize: "12px", marginTop: "4px" }}>
                  • Laplacian Edge Profile • High-Frequency Noise Residual Discontinuities
                </div>
              </div>

              <div style={tierCardStyle}>
                <div style={{ color: "#94a3b8", fontWeight: 800, fontSize: "13px" }}>
                  TIER 4: BOUNDED AI EXPLANATION LAYER (FastRouter)
                </div>
                <div style={{ color: "#cbd5e1", fontSize: "12px", marginTop: "4px" }}>
                  • Plain-English summaries and decision explanations bounded by verified forensic lanes. Never overrides evidence.
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
      </>}

      {/* CAMERA CAPTURE MODAL */}
      {cameraMode && (
        <div style={cameraModalOverlayStyle}>
          <div style={cameraModalContentStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <strong style={{ fontSize: "14px", color: "#f8fafc" }}>
                📷 Capture {cameraMode === "document" ? "Document Specimen" : "Live Subject Selfie"}
              </strong>
              <button onClick={stopCamera} style={{ background: "none", border: "none", color: "#94a3b8", fontSize: "16px", cursor: "pointer" }}>
                ✕
              </button>
            </div>
            <video ref={videoRef} autoPlay playsInline style={{ width: "100%", maxHeight: "360px", backgroundColor: "#000", borderRadius: "6px" }} />
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
              <button onClick={stopCamera} style={outlineButtonStyle}>
                Cancel
              </button>
              <button onClick={captureFrame} style={primaryButtonStyle}>
                📸 Snap Photo
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// -----------------------------------------------------------------------------
// STYLES (DARK GOVERNMENT-TECH WORKSTATION THEME)
// -----------------------------------------------------------------------------

const pageWrapperStyle: React.CSSProperties = {
  minHeight: "100vh",
  backgroundColor: "#060e15",
  fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  color: "#f1f5f9",
};

const mainContentStyle: React.CSSProperties = {
  maxWidth: 1400,
  margin: "0 auto",
  padding: "20px 24px",
};

const dashboardHeaderStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "18px",
  flexWrap: "wrap",
  gap: "12px",
};

const primaryButtonStyle: React.CSSProperties = {
  backgroundColor: "#0284c7",
  color: "#ffffff",
  border: "1px solid #38bdf8",
  borderRadius: "6px",
  padding: "8px 16px",
  fontSize: "13px",
  fontWeight: 700,
  cursor: "pointer",
  boxShadow: "0 0 10px rgba(56, 189, 248, 0.25)",
  transition: "all 0.15s ease",
};

const outlineButtonStyle: React.CSSProperties = {
  backgroundColor: "#0c1924",
  color: "#38bdf8",
  border: "1px solid #1e3a4d",
  borderRadius: "5px",
  padding: "6px 12px",
  fontSize: "12px",
  fontWeight: 600,
  cursor: "pointer",
  textDecoration: "none",
  display: "inline-flex",
  alignItems: "center",
  gap: "4px",
};

const actionButtonStyle: React.CSSProperties = {
  backgroundColor: "#0369a1",
  color: "#ffffff",
  border: "1px solid #38bdf8",
  borderRadius: "4px",
  padding: "4px 8px",
  fontSize: "11px",
  fontWeight: 600,
  cursor: "pointer",
};

const statsGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
  gap: "12px",
};

const statCardStyle: React.CSSProperties = {
  backgroundColor: "#091520",
  border: "1px solid #162c3f",
  borderRadius: "8px",
  padding: "14px 16px",
  boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
};

const statLabelStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 700,
  color: "#64748b",
  letterSpacing: "0.8px",
};

const statValueStyle: React.CSSProperties = {
  fontSize: "24px",
  fontWeight: 900,
  color: "#f8fafc",
  margin: "4px 0",
};

const statSubtextStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "#94a3b8",
};

const cardSectionStyle: React.CSSProperties = {
  backgroundColor: "#091520",
  border: "1px solid #162c3f",
  borderRadius: "8px",
  padding: "16px 20px",
  boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
};

const sectionHeaderFlexStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "12px",
  flexWrap: "wrap",
  gap: "10px",
};

const prototypeBadgeStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 700,
  padding: "2px 6px",
  borderRadius: "4px",
  backgroundColor: "rgba(56, 189, 248, 0.12)",
  color: "#38bdf8",
  border: "1px solid rgba(56, 189, 248, 0.3)",
  letterSpacing: "0.5px",
};

const presetGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
  gap: "10px",
};

const presetCardStyle: React.CSSProperties = {
  backgroundColor: "#0c1a27",
  border: "1px solid #1e3a4d",
  borderRadius: "6px",
  padding: "12px",
  cursor: "pointer",
  transition: "all 0.15s ease",
  textAlign: "left",
};

const selectStyle: React.CSSProperties = {
  backgroundColor: "#0c1a27",
  color: "#f8fafc",
  border: "1px solid #1e3a4d",
  borderRadius: "5px",
  padding: "7px 10px",
  fontSize: "12px",
  fontWeight: 600,
  cursor: "pointer",
};

const uploadBoxStyle: React.CSSProperties = {
  backgroundColor: "#0c1a27",
  border: "1px solid #1e3a4d",
  borderRadius: "6px",
  padding: "12px",
};

const controlBoxStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  justifyContent: "space-between",
  backgroundColor: "#0c1a27",
  border: "1px solid #1e3a4d",
  borderRadius: "6px",
  padding: "12px",
};

const cameraButtonStyle: React.CSSProperties = {
  backgroundColor: "#08131e",
  color: "#38bdf8",
  border: "1px solid #1e3a4d",
  borderRadius: "4px",
  padding: "2px 6px",
  fontSize: "11px",
  fontWeight: 600,
  cursor: "pointer",
};

const errorBannerStyle: React.CSSProperties = {
  marginTop: "12px",
  padding: "10px 14px",
  backgroundColor: "rgba(239, 68, 68, 0.15)",
  border: "1px solid rgba(239, 68, 68, 0.4)",
  borderRadius: "6px",
  color: "#fca5a5",
  fontSize: "12px",
};

const metaSummaryGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "8px 16px",
  backgroundColor: "rgba(6, 14, 21, 0.6)",
  border: "1px solid #162c3f",
  borderRadius: "6px",
  padding: "10px 14px",
  fontSize: "12px",
};

const metaSummaryItemStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "2px",
};

const metaLabelStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 700,
  color: "#64748b",
  letterSpacing: "0.5px",
};

const bioPreviewBoxStyle: React.CSSProperties = {
  backgroundColor: "#07111a",
  border: "1px solid #162c3f",
  borderRadius: "6px",
  padding: "10px",
  textAlign: "center",
};

const bioLabelStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 700,
  color: "#64748b",
  letterSpacing: "0.5px",
  marginBottom: "6px",
};

const bioImageBoxStyle: React.CSSProperties = {
  height: "120px",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  overflow: "hidden",
  borderRadius: "4px",
  backgroundColor: "#050b11",
};

const bioImgStyle: React.CSSProperties = {
  maxHeight: "120px",
  maxWidth: "100%",
  objectFit: "contain",
};

const bioMetricsGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr 1fr",
  gap: "8px",
  marginTop: "12px",
  backgroundColor: "#07111a",
  border: "1px solid #162c3f",
  borderRadius: "6px",
  padding: "10px 12px",
};

const bioMetricItemStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "2px",
};

const moduleCardsGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
  gap: "12px",
};

const moduleCardStyle: React.CSSProperties = {
  backgroundColor: "#091520",
  border: "1px solid #162c3f",
  borderRadius: "7px",
  padding: "12px 14px",
  display: "flex",
  flexDirection: "column",
  justifyContent: "space-between",
};

const moduleHeaderStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "4px",
};

const moduleTitleStyle: React.CSSProperties = {
  fontSize: "12px",
  fontWeight: 700,
  color: "#f8fafc",
};

const moduleSummaryStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "#94a3b8",
  lineHeight: "1.4",
  margin: "4px 0 8px 0",
};

const expandToggleStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "#38bdf8",
  fontSize: "11px",
  fontWeight: 600,
  cursor: "pointer",
  textAlign: "left",
  padding: 0,
};

const expandedContentStyle: React.CSSProperties = {
  marginTop: "8px",
  paddingTop: "8px",
  borderTop: "1px solid #162c3f",
  display: "flex",
  flexDirection: "column",
  gap: "4px",
  fontSize: "11px",
};

const detailRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  color: "#cbd5e1",
};

const getModuleBadgeStyle = (status: string): React.CSSProperties => {
  const isPass = status === "PASS" || status === "MATCH";
  const isFail = status === "FAIL" || status === "MISMATCH";
  const isSusp = status === "SUSPICIOUS" || status === "REFER";
  return {
    fontSize: "9px",
    fontWeight: 800,
    padding: "2px 5px",
    borderRadius: "3px",
    backgroundColor: isPass ? "rgba(16, 185, 129, 0.2)" : isFail ? "rgba(239, 68, 68, 0.2)" : isSusp ? "rgba(245, 158, 11, 0.2)" : "rgba(100, 116, 139, 0.2)",
    color: isPass ? "#6ee7b7" : isFail ? "#fca5a5" : isSusp ? "#fcd34d" : "#94a3b8",
    border: `1px solid ${isPass ? "rgba(16, 185, 129, 0.4)" : isFail ? "rgba(239, 68, 68, 0.4)" : isSusp ? "rgba(245, 158, 11, 0.4)" : "rgba(100, 116, 139, 0.3)"}`,
    letterSpacing: "0.5px",
  };
};

const matchBadgeStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 800,
  padding: "2px 6px",
  borderRadius: "3px",
  backgroundColor: "rgba(16, 185, 129, 0.2)",
  color: "#6ee7b7",
  border: "1px solid rgba(16, 185, 129, 0.4)",
};

const contradictionBadgeStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 800,
  padding: "2px 6px",
  borderRadius: "3px",
  backgroundColor: "rgba(239, 68, 68, 0.25)",
  color: "#fca5a5",
  border: "1px solid rgba(239, 68, 68, 0.5)",
  boxShadow: "0 0 6px rgba(239, 68, 68, 0.4)",
};

const naBadgeStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 600,
  padding: "2px 6px",
  borderRadius: "3px",
  backgroundColor: "rgba(100, 116, 139, 0.15)",
  color: "#94a3b8",
  border: "1px solid rgba(100, 116, 139, 0.3)",
};

const actionCardStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "12px",
  backgroundColor: "#0c1a27",
  border: "1px solid #1e3a4d",
  borderRadius: "6px",
  padding: "10px 14px",
};

const actionNumberStyle: React.CSSProperties = {
  width: "24px",
  height: "24px",
  borderRadius: "50%",
  backgroundColor: "#0284c7",
  color: "#ffffff",
  fontSize: "12px",
  fontWeight: 800,
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  boxShadow: "0 0 6px rgba(56, 189, 248, 0.4)",
};

const priorityPillStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 700,
  color: "#38bdf8",
  backgroundColor: "rgba(56, 189, 248, 0.1)",
  padding: "1px 6px",
  borderRadius: "3px",
};

const aiPanelContainerStyle: React.CSSProperties = {
  backgroundColor: "#08131e",
  border: "1px solid #0284c7",
  borderRadius: "8px",
  padding: "18px 20px",
  boxShadow: "0 0 16px rgba(2, 132, 199, 0.2)",
};

const aiLogoStyle: React.CSSProperties = {
  width: "28px",
  height: "28px",
  borderRadius: "6px",
  backgroundColor: "#0284c7",
  color: "#ffffff",
  fontSize: "12px",
  fontWeight: 900,
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  boxShadow: "0 0 8px rgba(56, 189, 248, 0.5)",
};

const aiContentGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "12px",
  marginTop: "14px",
};

const aiBlockStyle: React.CSSProperties = {
  backgroundColor: "#0b1a28",
  border: "1px solid #162e43",
  borderRadius: "6px",
  padding: "12px 14px",
};

const aiBlockTitleStyle: React.CSSProperties = {
  fontSize: "11px",
  fontWeight: 800,
  color: "#38bdf8",
  letterSpacing: "0.5px",
  marginBottom: "6px",
};

const aiBlockTextStyle: React.CSSProperties = {
  fontSize: "12px",
  color: "#cbd5e1",
  lineHeight: "1.5",
  margin: 0,
};

const aiFooterDisclaimerStyle: React.CSSProperties = {
  marginTop: "14px",
  padding: "8px 12px",
  backgroundColor: "rgba(2, 132, 199, 0.08)",
  borderRadius: "4px",
  fontSize: "11px",
  color: "#94a3b8",
  border: "1px solid rgba(2, 132, 199, 0.2)",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: "12px",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "8px 10px",
  borderBottom: "1px solid #162c3f",
  color: "#64748b",
  fontSize: "10px",
  fontWeight: 700,
  letterSpacing: "0.5px",
};

const tdStyle: React.CSSProperties = {
  padding: "10px",
  borderBottom: "1px solid #102231",
  color: "#cbd5e1",
};

const trStyle: React.CSSProperties = {
  transition: "background-color 0.15s ease",
};

const searchInputStyle: React.CSSProperties = {
  width: "100%",
  backgroundColor: "#0c1a27",
  color: "#f8fafc",
  border: "1px solid #1e3a4d",
  borderRadius: "6px",
  padding: "8px 12px",
  fontSize: "12px",
  boxSizing: "border-box",
};

const clusterCardStyle: React.CSSProperties = {
  backgroundColor: "#0c1a27",
  border: "1px solid #1e3a4d",
  borderRadius: "6px",
  padding: "12px 14px",
};

const clusterCredCardStyle: React.CSSProperties = {
  backgroundColor: "#07111a",
  border: "1px solid #162c3f",
  borderRadius: "4px",
  padding: "8px 10px",
};

const tierCardStyle: React.CSSProperties = {
  backgroundColor: "#0c1a27",
  border: "1px solid #1e3a4d",
  borderRadius: "6px",
  padding: "12px 14px",
};

const badgeStyle: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 700,
  padding: "2px 8px",
  borderRadius: "4px",
  border: "1px solid",
  letterSpacing: "0.5px",
};

const cameraModalOverlayStyle: React.CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: "rgba(0,0,0,0.85)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  zIndex: 1000,
};

const cameraModalContentStyle: React.CSSProperties = {
  backgroundColor: "#091520",
  border: "1px solid #1e3a4d",
  borderRadius: "8px",
  padding: "16px",
  maxWidth: "600px",
  width: "90%",
};
