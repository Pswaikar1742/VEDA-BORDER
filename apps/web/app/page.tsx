"use client";

import React, { useEffect, useRef, useState } from "react";
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
    name: "Scenario A: Clean Travel Credential + Matching Face",
    docFile: "travel_clean.png",
    selfieFile: "ari_selfie.png",
    expected: "LOW RISK (All lanes complete and consistent)",
    family: "TRAVEL_DOCUMENT",
  },
  {
    id: "dob_altered",
    name: "Scenario B: Date of Birth Altered (VIZ != MRZ)",
    docFile: "travel_dob_altered.png",
    selfieFile: null,
    expected: "HIGH RISK (Critical cross-source contradiction)",
    family: "TRAVEL_DOCUMENT",
  },
  {
    id: "portrait_replaced",
    name: "Scenario C: Portrait Region Replaced / Tampered",
    docFile: "travel_portrait_replaced.png",
    selfieFile: null,
    expected: "REFER (Visual forensics edge anomaly)",
    family: "TRAVEL_DOCUMENT",
  },
  {
    id: "expired",
    name: "Scenario D: Expired Travel Document",
    docFile: "travel_expired.png",
    selfieFile: null,
    expected: "REFER / HIGH RISK (Expired document gate)",
    family: "TRAVEL_DOCUMENT",
  },
  {
    id: "blacklisted",
    name: "Scenario E: Local Prototype Blacklist Hit",
    docFile: "travel_blacklisted.png",
    selfieFile: null,
    expected: "HIGH RISK (Local watchlist alert)",
    family: "TRAVEL_DOCUMENT",
  },
  {
    id: "face_mismatch",
    name: "Scenario F: Biometric Face Mismatch",
    docFile: "travel_clean.png",
    selfieFile: "lio_selfie.png",
    expected: "HIGH RISK (Required biometric mismatch)",
    family: "TRAVEL_DOCUMENT",
  },
  {
    id: "poor_capture",
    name: "Scenario I: Degraded / Low Resolution Capture",
    docFile: "travel_poor_capture.png",
    selfieFile: null,
    expected: "INDETERMINATE (Capture quality gate stop)",
    family: "TRAVEL_DOCUMENT",
  },
  {
    id: "visa",
    name: "Visa / Permit Credential",
    docFile: "visa_or_permit.png",
    selfieFile: null,
    expected: "MRZ = NOT_APPLICABLE",
    family: "VISA_OR_PERMIT",
  },
  {
    id: "national_id",
    name: "National ID Credential",
    docFile: "national_id.png",
    selfieFile: null,
    expected: "MRZ = NOT_APPLICABLE",
    family: "NATIONAL_ID",
  },
  {
    id: "dl",
    name: "Driving Licence Credential",
    docFile: "driving_licence.png",
    selfieFile: null,
    expected: "MRZ = NOT_APPLICABLE",
    family: "DRIVING_LICENCE",
  },
];

export default function Home() {
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

  // Filter state for Cases
  const [caseFilter, setCaseFilter] = useState<string>("ALL");
  const [caseSearch, setCaseSearch] = useState<string>("");

  // Camera modal state
  const [cameraMode, setCameraMode] = useState<"document" | "selfie" | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

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

  // Handle file picker
  const handleDocChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setDocFile(file);
      setDocPreview(URL.createObjectURL(file));
    }
  };

  const handleSelfieChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelfieFile(file);
      setSelfiePreview(URL.createObjectURL(file));
    }
  };

  // Preset fixture loader
  async function loadPreset(preset: typeof PRESET_SCENARIOS[0]) {
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
      setErrorMessage("Please upload or capture a document image before screening.");
      return;
    }
    setErrorMessage(null);
    setIsAnalyzing(true);
    try {
      const result = await createScreening(
        docFile,
        docFile.name,
        selfieFile,
        selfieFile?.name,
        selectedFamily || undefined
      );
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
      setAutopsy(caseResult);
      setActiveTab("screening");
    } catch (err) {
      alert("Failed to load case: " + (err instanceof Error ? err.message : String(err)));
    }
  }

  const outcomeColors: Record<ScreeningOutcome | string, string> = {
    LOW_RISK: "#067647",
    REFER: "#b54708",
    HIGH_RISK: "#b42318",
    INDETERMINATE: "#475467",
    CLEAR: "#067647",
  };

  const outcomeBg: Record<ScreeningOutcome | string, string> = {
    LOW_RISK: "#ecfdf3",
    REFER: "#fffaeb",
    HIGH_RISK: "#fef3f2",
    INDETERMINATE: "#f8fafc",
    CLEAR: "#ecfdf3",
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f1f5f9", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      <Navbar
        activeTab={activeTab}
        onSelectTab={(tab) => {
          setActiveTab(tab);
          if (tab === "cases" || tab === "dashboard" || tab === "linkage") refreshData();
        }}
        systemReady={systemStatus?.status === "READY"}
      />

      <main style={{ maxWidth: 1400, margin: "0 auto", padding: "24px 20px" }}>
        {/* ===================================================================== */}
        {/* 1. DASHBOARD VIEW */}
        {/* ===================================================================== */}
        {activeTab === "dashboard" && (
          <div>
            <div style={dashboardHeaderStyle}>
              <div>
                <h1 style={{ margin: 0, fontSize: "24px", color: "#0f2735", fontWeight: 800 }}>
                  Forensic Operations Dashboard
                </h1>
                <p style={{ margin: "4px 0 0 0", color: "#475467", fontSize: "14px" }}>
                  Real-time border screening diagnostics, triage statistics, and multi-identity cluster intelligence.
                </p>
              </div>
              <button
                onClick={() => setActiveTab("screening")}
                style={primaryActionButtonStyle}
              >
                + Start New Screening
              </button>
            </div>

            {/* Metric counters */}
            <div style={statsGridStyle}>
              <div style={statCardStyle}>
                <div style={statLabelStyle}>TOTAL SCREENINGS</div>
                <div style={statValueStyle}>{casesData?.summary.cases_screened ?? 0}</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Local Forensic Ledger</div>
              </div>
              <div style={{ ...statCardStyle, borderLeft: "4px solid #067647" }}>
                <div style={statLabelStyle}>LOW RISK (CLEARED)</div>
                <div style={{ ...statValueStyle, color: "#067647" }}>{casesData?.summary.low_risk ?? 0}</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Consistent Complete Evidence</div>
              </div>
              <div style={{ ...statCardStyle, borderLeft: "4px solid #b54708" }}>
                <div style={statLabelStyle}>REFER (OFFICER REVIEW)</div>
                <div style={{ ...statValueStyle, color: "#b54708" }}>{casesData?.summary.refer ?? 0}</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Forensic Anomaly / Expired</div>
              </div>
              <div style={{ ...statCardStyle, borderLeft: "4px solid #b42318" }}>
                <div style={statLabelStyle}>HIGH RISK (HARD GATES)</div>
                <div style={{ ...statValueStyle, color: "#b42318" }}>{casesData?.summary.high_risk ?? 0}</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Contradiction / Blacklist Hit</div>
              </div>
              <div style={{ ...statCardStyle, borderLeft: "4px solid #475467" }}>
                <div style={statLabelStyle}>INDETERMINATE</div>
                <div style={{ ...statValueStyle, color: "#475467" }}>{casesData?.summary.indeterminate ?? 0}</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Incomplete Mandatory Lanes</div>
              </div>
            </div>

            {/* Quick Test Fixtures Grid */}
            <div style={{ ...cardSectionStyle, marginTop: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: "16px", color: "#0f2735" }}>Controlled Synthetic Golden Scenarios (One-Click Launch)</h3>
                  <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#64748b" }}>
                    Select any pre-configured fictional test specimen to inspect the autopsy engine behavior instantly.
                  </p>
                </div>
                <span style={{ fontSize: "11px", background: "#fef3f2", color: "#b42318", border: "1px solid #fecdca", padding: "3px 8px", borderRadius: "4px", fontWeight: 600 }}>
                  SYNTHETIC DEMO CREDENTIALS ONLY
                </span>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px" }}>
                {PRESET_SCENARIOS.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      loadPreset(p);
                      setActiveTab("screening");
                    }}
                    style={presetButtonStyle}
                  >
                    <div style={{ fontWeight: 700, fontSize: "13px", color: "#0f2735" }}>{p.name}</div>
                    <div style={{ fontSize: "11px", color: "#0284c7", marginTop: "4px" }}>Expected: {p.expected}</div>
                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "4px" }}>File: {p.docFile} {p.selfieFile ? `+ ${p.selfieFile}` : ""}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Module Readiness Matrix */}
            <div style={{ ...cardSectionStyle, marginTop: "24px" }}>
              <h3 style={{ margin: "0 0 12px 0", fontSize: "16px", color: "#0f2735" }}>System Module Readiness & Diagnostics</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "10px" }}>
                {(systemStatus?.modules || []).map((m) => {
                  const isReady = m.state === "READY";
                  return (
                    <div key={m.module} style={{ border: `1px solid ${isReady ? "#bbf7d0" : "#fed7aa"}`, backgroundColor: isReady ? "#f0fdf4" : "#fffbeb", padding: "10px", borderRadius: "6px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <strong style={{ fontSize: "12px", color: "#1e293b" }}>{m.module}</strong>
                        <span style={{ fontSize: "10px", fontWeight: 700, color: isReady ? "#166534" : "#9a3412" }}>{m.state}</span>
                      </div>
                      <div style={{ fontSize: "11px", color: "#475467", marginTop: "4px" }}>{m.detail}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Recent Cases */}
            <div style={{ ...cardSectionStyle, marginTop: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <h3 style={{ margin: 0, fontSize: "16px", color: "#0f2735" }}>Recent Screenings Feed</h3>
                <button onClick={() => setActiveTab("cases")} style={{ fontSize: "12px", color: "#0284c7", background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}>
                  View All Screenings &rarr;
                </button>
              </div>

              {casesData?.cases && casesData.cases.length > 0 ? (
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
                    {casesData.cases.slice(0, 8).map((c) => (
                      <tr key={c.case_id}>
                        <td style={tdStyle}><code>{c.case_id.slice(0, 8)}...</code></td>
                        <td style={tdStyle}>{new Date(c.created_at).toLocaleTimeString()}</td>
                        <td style={tdStyle}><strong>{c.claimed_identity || "—"}</strong></td>
                        <td style={tdStyle}><code>{c.document_number || "—"}</code></td>
                        <td style={tdStyle}>{c.document_family}</td>
                        <td style={tdStyle}>
                          <span style={{ ...outcomeBadgeStyle, backgroundColor: outcomeBg[c.outcome], color: outcomeColors[c.outcome], border: `1px solid ${outcomeColors[c.outcome]}` }}>
                            {c.outcome}
                          </span>
                        </td>
                        <td style={tdStyle}>
                          <button onClick={() => handleReopenCase(c.case_id)} style={smallButtonStyle}>
                            Open Autopsy
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ textAlign: "center", padding: "24px", color: "#64748b" }}>No screening cases recorded yet.</div>
              )}
            </div>
          </div>
        )}

        {/* ===================================================================== */}
        {/* 2. NEW SCREENING VIEW (CORE FORENSIC WORKSTATION) */}
        {/* ===================================================================== */}
        {activeTab === "screening" && (
          <div>
            {/* Top Control Header */}
            <div style={cardSectionStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: "20px", color: "#0f2735", fontWeight: 800 }}>
                    Forensic Credential Screening & Autopsy
                  </h2>
                  <p style={{ margin: "2px 0 0 0", color: "#64748b", fontSize: "13px" }}>
                    Multi-modal evidence ingestion: pixels, deterministic MRZ, visual heuristics, 1:1 biometrics, and watchlist intelligence.
                  </p>
                </div>

                <div style={{ display: "flex", gap: "8px" }}>
                  <select
                    value=""
                    onChange={(e) => {
                      const found = PRESET_SCENARIOS.find((p) => p.id === e.target.value);
                      if (found) loadPreset(found);
                    }}
                    style={selectStyle}
                  >
                    <option value="" disabled>⚡ Quick-Load Test Preset...</option>
                    {PRESET_SCENARIOS.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Ingestion Inputs Grid */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 280px", gap: "16px" }}>
                {/* 1. Document Upload Box */}
                <div style={uploadBoxStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <label style={{ fontSize: "13px", fontWeight: 700, color: "#1e293b" }}>1. Document Specimen (PNG, JPG, PDF)</label>
                    <button type="button" onClick={() => startCamera("document")} style={cameraButtonStyle}>
                      📷 Camera
                    </button>
                  </div>

                  <input
                    type="file"
                    accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf"
                    onChange={handleDocChange}
                    style={{ fontSize: "12px", width: "100%" }}
                  />

                  {docPreview && (
                    <div style={{ marginTop: "10px", textAlign: "center" }}>
                      <img src={docPreview} alt="Doc preview" style={{ maxHeight: "140px", maxWidth: "100%", borderRadius: "4px", border: "1px solid #cbd5e1" }} />
                      <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>{docFile?.name} ({(docFile?.size || 0) / 1024 > 1024 ? `${((docFile?.size || 0) / (1024 * 1024)).toFixed(1)} MB` : `${Math.round((docFile?.size || 0) / 1024)} KB`})</div>
                    </div>
                  )}
                </div>

                {/* 2. Live Face Comparison Box */}
                <div style={uploadBoxStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <label style={{ fontSize: "13px", fontWeight: 700, color: "#1e293b" }}>2. Live Comparison Face (Optional)</label>
                    <button type="button" onClick={() => startCamera("selfie")} style={cameraButtonStyle}>
                      📷 Selfie
                    </button>
                  </div>

                  <input
                    type="file"
                    accept=".png,.jpg,.jpeg,image/png,image/jpeg"
                    onChange={handleSelfieChange}
                    style={{ fontSize: "12px", width: "100%" }}
                  />

                  {selfiePreview && (
                    <div style={{ marginTop: "10px", textAlign: "center" }}>
                      <img src={selfiePreview} alt="Selfie preview" style={{ maxHeight: "140px", maxWidth: "100%", borderRadius: "4px", border: "1px solid #cbd5e1" }} />
                      <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>{selfieFile?.name}</div>
                    </div>
                  )}
                </div>

                {/* 3. Controls & Document Family */}
                <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", backgroundColor: "#f8fafc", padding: "14px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                  <div>
                    <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>Document Family Override</label>
                    <select
                      value={selectedFamily}
                      onChange={(e) => setSelectedFamily(e.target.value)}
                      style={{ ...selectStyle, width: "100%", marginTop: "6px" }}
                    >
                      <option value="">Auto-Detect from OCR</option>
                      <option value="TRAVEL_DOCUMENT">Travel Document (Passport/TD3)</option>
                      <option value="VISA_OR_PERMIT">Visa or Permit</option>
                      <option value="NATIONAL_ID">National ID Card</option>
                      <option value="DRIVING_LICENCE">Driving Licence</option>
                    </select>
                    <div style={{ fontSize: "11px", color: "#64748b", marginTop: "6px" }}>
                      Auto-detector identifies markers like MRZ P&lt;, PERMIT, or IDENTITY.
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={handleRunScreening}
                    disabled={isAnalyzing || !docFile}
                    style={{
                      ...primaryActionButtonStyle,
                      width: "100%",
                      padding: "12px",
                      opacity: isAnalyzing || !docFile ? 0.6 : 1,
                    }}
                  >
                    {isAnalyzing ? "🔬 Analyzing Forensic Evidence…" : "⚡ Execute Full Autopsy"}
                  </button>
                </div>
              </div>

              {errorMessage && (
                <div style={{ marginTop: "14px", padding: "10px 14px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "6px", color: "#b91c1c", fontSize: "13px" }}>
                  <strong>Error:</strong> {errorMessage}
                </div>
              )}
            </div>

            {/* ================================================================= */}
            {/* FINAL AUTOPSY PRESENTATION */}
            {/* ================================================================= */}
            {autopsy && (
              <div style={{ marginTop: "24px" }}>
                {/* 1. Triage Outcome Summary Banner */}
                <div
                  style={{
                    backgroundColor: outcomeBg[autopsy.outcome],
                    border: `2px solid ${outcomeColors[autopsy.outcome]}`,
                    borderRadius: "8px",
                    padding: "20px",
                    marginBottom: "20px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
                    <div>
                      <div style={{ fontSize: "12px", fontWeight: 700, color: outcomeColors[autopsy.outcome], textTransform: "uppercase", letterSpacing: "1px" }}>
                        Screening Triage Outcome
                      </div>
                      <div style={{ fontSize: "28px", fontWeight: 900, color: outcomeColors[autopsy.outcome], marginTop: "2px" }}>
                        {autopsy.outcome}
                      </div>
                      {autopsy.triage_risk_index !== null && autopsy.triage_risk_index !== undefined && (
                        <div style={{ fontSize: "14px", fontWeight: 700, color: "#1e293b", marginTop: "4px" }}>
                          Triage Risk Index: <strong>{autopsy.triage_risk_index.toFixed(1)} / 100</strong>
                          <span style={{ fontSize: "12px", fontWeight: 500, color: "#64748b", marginLeft: "8px" }}>
                            ({autopsy.triage_risk_label})
                          </span>
                        </div>
                      )}
                      {autopsy.outcome_reasons && autopsy.outcome_reasons.length > 0 && (
                        <div style={{ marginTop: "8px", fontSize: "13px", color: "#1e293b" }}>
                          {autopsy.outcome_reasons.map((r, i) => (
                            <div key={i}>• {r}</div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "8px" }}>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b" }}>EVIDENCE COVERAGE</div>
                        <div style={{ fontSize: "18px", fontWeight: 800, color: autopsy.evidence_coverage.state === "COMPLETE" ? "#067647" : "#b54708" }}>
                          {Math.round(autopsy.evidence_coverage.coverage_ratio * 100)}% ({autopsy.evidence_coverage.state})
                        </div>
                        {autopsy.evidence_coverage.missing_mandatory.length > 0 && (
                          <div style={{ fontSize: "11px", color: "#b42318" }}>
                            Missing: {autopsy.evidence_coverage.missing_mandatory.join(", ")}
                          </div>
                        )}
                      </div>

                      <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
                        <a
                          href={getReportHtmlUrl(autopsy.case_id || autopsy.scan_id)}
                          target="_blank"
                          rel="noreferrer"
                          style={outlineReportButtonStyle}
                        >
                          📄 Print / HTML Report
                        </a>
                        <a
                          href={getReportJsonUrl(autopsy.case_id || autopsy.scan_id)}
                          target="_blank"
                          rel="noreferrer"
                          style={outlineReportButtonStyle}
                        >
                          💾 Export JSON
                        </a>
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: `1px solid ${outcomeColors[autopsy.outcome]}33`, fontSize: "11px", color: "#64748b", display: "flex", justifyContent: "space-between" }}>
                    <span>Case ID: <code>{autopsy.case_id || autopsy.scan_id}</code></span>
                    <span>SHA-256: <code>{autopsy.specimen_sha256}</code></span>
                    <span>Document Family: <strong>{autopsy.document_family || autopsy.document_type}</strong></span>
                  </div>
                </div>

                {/* Hard Gate Alerts */}
                {autopsy.hard_gates && autopsy.hard_gates.length > 0 && (
                  <div style={{ marginBottom: "20px" }}>
                    {autopsy.hard_gates.map((g, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: "#fef3f2",
                          border: "1px solid #fecdca",
                          borderLeft: "5px solid #b42318",
                          padding: "12px 16px",
                          borderRadius: "6px",
                          marginBottom: "8px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <strong style={{ color: "#b42318", fontSize: "13px" }}>HARD GATE TRIGGERED: {g.gate}</strong>
                          <span style={{ fontSize: "11px", backgroundColor: "#b42318", color: "#fff", padding: "2px 6px", borderRadius: "4px", fontWeight: 700 }}>
                            {g.severity}
                          </span>
                        </div>
                        <div style={{ fontSize: "12px", color: "#7a271a", marginTop: "4px" }}>{g.reason}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 2-Column Forensic Layout */}
                <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: "20px" }}>
                  {/* LEFT COLUMN: Data Extraction & Forensic Checks */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                    {/* Capture Quality Gate */}
                    {autopsy.capture_quality && (
                      <div style={cardSectionStyle}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                          <h3 style={sectionTitleStyle}>1. Capture Quality Gate</h3>
                          <span style={{ ...tagStyle, backgroundColor: autopsy.capture_quality.acceptable ? "#ecfdf3" : "#fef3f2", color: autopsy.capture_quality.acceptable ? "#067647" : "#b42318" }}>
                            {autopsy.capture_quality.status}
                          </span>
                        </div>
                        <table style={tableStyle}>
                          <thead>
                            <tr>
                              <th style={thStyle}>Check</th>
                              <th style={thStyle}>State</th>
                              <th style={thStyle}>Observed Measure</th>
                              <th style={thStyle}>Threshold</th>
                            </tr>
                          </thead>
                          <tbody>
                            {autopsy.capture_quality.findings.map((f, i) => (
                              <tr key={i}>
                                <td style={tdStyle}><strong>{f.check}</strong></td>
                                <td style={{ ...tdStyle, color: f.state === "PASS" ? "#067647" : "#b42318", fontWeight: 700 }}>{f.state}</td>
                                <td style={tdStyle}>{Array.isArray(f.measure) ? f.measure.join("x") : f.measure ?? "—"}</td>
                                <td style={tdStyle}>{f.threshold}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Visible Document Data */}
                    <div style={cardSectionStyle}>
                      <h3 style={sectionTitleStyle}>2. Visible Document Data (VIZ)</h3>
                      <table style={tableStyle}>
                        <thead>
                          <tr>
                            <th style={thStyle}>Field</th>
                            <th style={thStyle}>Raw OCR Pixels</th>
                            <th style={thStyle}>Normalized</th>
                            <th style={thStyle}>Confidence</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(FIELD_LABELS).map(([field, label]) => {
                            const raw = autopsy.visible_document_data.raw_visible_fields?.[field];
                            const norm = autopsy.visible_document_data.visible_fields?.[field];
                            const conf = autopsy.visible_document_data.field_confidence?.[field];
                            return (
                              <tr key={field}>
                                <td style={tdStyle}><strong>{label}</strong></td>
                                <td style={tdStyle}><code>{raw || "UNAVAILABLE"}</code></td>
                                <td style={tdStyle}><code>{norm || "UNAVAILABLE"}</code></td>
                                <td style={tdStyle}>{conf !== undefined ? `${conf.toFixed(1)}%` : "—"}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* MRZ Zone */}
                    <div style={cardSectionStyle}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                        <h3 style={sectionTitleStyle}>3. Machine-Readable Zone (MRZ)</h3>
                        <span style={{ ...tagStyle, backgroundColor: autopsy.mrz_analysis.mrz_detected ? "#ecfdf3" : "#f1f5f9", color: autopsy.mrz_analysis.mrz_detected ? "#067647" : "#475467" }}>
                          {autopsy.mrz_analysis.applicability === "NOT_APPLICABLE" ? "NOT APPLICABLE" : (autopsy.mrz_analysis.mrz_detected ? "DETECTED" : "UNAVAILABLE")}
                        </span>
                      </div>

                      {autopsy.mrz_analysis.raw_lines && autopsy.mrz_analysis.raw_lines.length > 0 && (
                        <div style={{ backgroundColor: "#0f172a", color: "#38bdf8", padding: "10px", borderRadius: "6px", fontFamily: "monospace", fontSize: "12px", marginBottom: "10px" }}>
                          {autopsy.mrz_analysis.raw_lines.map((l, i) => (
                            <div key={i}>{l}</div>
                          ))}
                        </div>
                      )}

                      {autopsy.mrz_analysis.checks && Object.keys(autopsy.mrz_analysis.checks).length > 0 && (
                        <div>
                          <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b", marginBottom: "6px" }}>ICAO 7-3-1 CHECK DIGITS</div>
                          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "8px" }}>
                            {Object.entries(autopsy.mrz_analysis.checks).map(([name, status]) => (
                              <div
                                key={name}
                                style={{
                                  border: `1px solid ${status === "PASS" ? "#bbf7d0" : "#fecaca"}`,
                                  backgroundColor: status === "PASS" ? "#f0fdf4" : "#fef2f2",
                                  padding: "8px",
                                  borderRadius: "4px",
                                  textAlign: "center",
                                }}
                              >
                                <div style={{ fontSize: "10px", color: "#475467", textTransform: "uppercase" }}>{name.replace(/_/g, " ")}</div>
                                <div style={{ fontSize: "13px", fontWeight: 800, color: status === "PASS" ? "#067647" : "#b42318", marginTop: "2px" }}>
                                  {status}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Cross-Source Consistency */}
                    <div style={cardSectionStyle}>
                      <h3 style={sectionTitleStyle}>4. Cross-Source Consistency Reconstruction</h3>
                      <table style={tableStyle}>
                        <thead>
                          <tr>
                            <th style={thStyle}>Field</th>
                            <th style={thStyle}>VIZ</th>
                            <th style={thStyle}>MRZ</th>
                            <th style={thStyle}>Status</th>
                            <th style={thStyle}>Severity</th>
                            <th style={thStyle}>Explanation</th>
                          </tr>
                        </thead>
                        <tbody>
                          {autopsy.cross_source_consistency.map((c: CrossSourceComparison) => {
                            const isFail = c.status === "FAIL";
                            return (
                              <tr key={c.field} style={{ backgroundColor: isFail ? "#fee4e2" : "transparent" }}>
                                <td style={tdStyle}><strong>{FIELD_LABELS[c.field] || c.field}</strong></td>
                                <td style={tdStyle}><code>{c.value_a || "—"}</code></td>
                                <td style={tdStyle}><code>{c.value_b || "—"}</code></td>
                                <td style={{ ...tdStyle, color: isFail ? "#b42318" : (c.status === "PASS" ? "#067647" : "#475467"), fontWeight: 700 }}>
                                  {c.status}
                                </td>
                                <td style={tdStyle}><span style={{ fontSize: "11px", fontWeight: 600, color: c.severity === "CRITICAL" ? "#b42318" : "#475467" }}>{c.severity}</span></td>
                                <td style={{ ...tdStyle, fontSize: "11px" }}>{c.reason}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* RIGHT COLUMN: Forensics, Biometrics, Hypotheses, Planner, Evidence Graph */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                    {/* Visual Forensics & Canvas */}
                    <DocumentVisualizer
                      imageSrc={docPreview}
                      findings={autopsy.visual_forensics?.findings || []}
                    />

                    {/* 1:1 Face Verification */}
                    {autopsy.biometric_verification && (
                      <div style={cardSectionStyle}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                          <h3 style={sectionTitleStyle}>5. Biometric Face Verification (1:1)</h3>
                          <span style={{ ...tagStyle, backgroundColor: autopsy.biometric_verification.decision === "MATCH" ? "#ecfdf3" : (autopsy.biometric_verification.decision === "MISMATCH" ? "#fef3f2" : "#f1f5f9"), color: autopsy.biometric_verification.decision === "MATCH" ? "#067647" : (autopsy.biometric_verification.decision === "MISMATCH" ? "#b42318" : "#475467") }}>
                            {autopsy.biometric_verification.decision || "UNAVAILABLE"}
                          </span>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginTop: "8px" }}>
                          <div style={{ backgroundColor: "#f8fafc", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                            <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b" }}>COSINE SIMILARITY</div>
                            <div style={{ fontSize: "20px", fontWeight: 800, color: "#0f2735", marginTop: "2px" }}>
                              {autopsy.biometric_verification.similarity !== null && autopsy.biometric_verification.similarity !== undefined
                                ? autopsy.biometric_verification.similarity.toFixed(4)
                                : "—"}
                            </div>
                            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
                              Threshold: <strong>{autopsy.biometric_verification.configured_prototype_threshold}</strong>
                            </div>
                          </div>

                          <div style={{ backgroundColor: "#f8fafc", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                            <div style={{ fontSize: "11px", fontWeight: 700, color: "#64748b" }}>MODEL & ENGINE</div>
                            <div style={{ fontSize: "12px", fontWeight: 700, color: "#0f2735", marginTop: "2px" }}>
                              {autopsy.biometric_verification.model || "OpenCV YuNet + SFace"}
                            </div>
                            <div style={{ fontSize: "11px", color: "#475467", marginTop: "2px" }}>
                              {autopsy.biometric_verification.reason}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Threat Intelligence & Identity Linkage */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                      <div style={cardSectionStyle}>
                        <h3 style={sectionTitleStyle}>6. Local Threat Watchlist</h3>
                        <div style={{ marginTop: "6px" }}>
                          <span style={{ ...tagStyle, backgroundColor: autopsy.threat_intelligence.result === "CLEAR" ? "#ecfdf3" : "#fef3f2", color: autopsy.threat_intelligence.result === "CLEAR" ? "#067647" : "#b42318" }}>
                            {autopsy.threat_intelligence.result || "UNAVAILABLE"}
                          </span>
                          <div style={{ fontSize: "11px", color: "#475467", marginTop: "6px" }}>
                            {autopsy.threat_intelligence.reason}
                          </div>
                          <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "4px" }}>
                            Source: {autopsy.threat_intelligence.display_source || "LOCAL PROTOTYPE WATCHLIST"}
                          </div>
                        </div>
                      </div>

                      <div style={cardSectionStyle}>
                        <h3 style={sectionTitleStyle}>7. Identity Linkage</h3>
                        <div style={{ marginTop: "6px" }}>
                          <span style={{ ...tagStyle, backgroundColor: autopsy.identity_linkage?.status === "PASS" ? "#ecfdf3" : (autopsy.identity_linkage?.status === "SUSPICIOUS" ? "#fef3f2" : "#f1f5f9"), color: autopsy.identity_linkage?.status === "PASS" ? "#067647" : (autopsy.identity_linkage?.status === "SUSPICIOUS" ? "#b42318" : "#475467") }}>
                            {autopsy.identity_linkage?.status || "UNAVAILABLE"}
                          </span>
                          <div style={{ fontSize: "11px", color: "#475467", marginTop: "6px" }}>
                            Cluster: <strong>{autopsy.identity_linkage?.identity_reference || "—"}</strong>
                          </div>
                          <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
                            {autopsy.identity_linkage?.reason}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Adaptive Evidence Graph */}
                    <EvidenceGraphViewer graph={autopsy.evidence_graph} />

                    {/* Forensic Hypotheses */}
                    {autopsy.forensic_hypotheses && autopsy.forensic_hypotheses.length > 0 && (
                      <div style={cardSectionStyle}>
                        <h3 style={sectionTitleStyle}>8. Forensic Hypotheses Engine</h3>
                        <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
                          {autopsy.forensic_hypotheses.map((h, idx) => {
                            const isCrit = h.severity === "CRITICAL";
                            const isHigh = h.severity === "HIGH";
                            const borderCol = isCrit ? "#ef4444" : (isHigh ? "#f97316" : "#3b82f6");
                            return (
                              <div
                                key={idx}
                                style={{
                                  padding: "10px",
                                  backgroundColor: "#f8fafc",
                                  border: "1px solid #e2e8f0",
                                  borderLeft: `4px solid ${borderCol}`,
                                  borderRadius: "4px",
                                }}
                              >
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                  <strong style={{ fontSize: "12px", color: "#0f2735" }}>{h.hypothesis}</strong>
                                  <span style={{ fontSize: "10px", fontWeight: 700, color: borderCol }}>{h.severity}</span>
                                </div>
                                <div style={{ fontSize: "12px", color: "#334155", marginTop: "4px" }}>{h.explanation}</div>
                                <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
                                  Supporting: <code>{h.supporting_evidence.join(", ") || "None"}</code>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Next-Best-Evidence Action Planner */}
                    {autopsy.next_best_actions && autopsy.next_best_actions.length > 0 && (
                      <div style={cardSectionStyle}>
                        <h3 style={sectionTitleStyle}>9. Next-Best-Evidence Action Plan</h3>
                        <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
                          {autopsy.next_best_actions.map((act, idx) => (
                            <div
                              key={idx}
                              style={{
                                padding: "10px",
                                backgroundColor: "#f8fafc",
                                border: "1px solid #e2e8f0",
                                borderRadius: "4px",
                              }}
                            >
                              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <span style={{ fontSize: "10px", fontWeight: 700, backgroundColor: act.priority === 1 ? "#ef4444" : (act.priority === 2 ? "#f97316" : "#3b82f6"), color: "#fff", padding: "2px 6px", borderRadius: "3px" }}>
                                  PRIORITY {act.priority}
                                </span>
                                <strong style={{ fontSize: "12px", color: "#0f2735" }}>{act.action}</strong>
                              </div>
                              <div style={{ fontSize: "12px", color: "#475467", marginTop: "4px" }}>{act.reason}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
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
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <h2 style={{ margin: 0, fontSize: "20px", color: "#0f2735", fontWeight: 800 }}>Case Audit Ledger</h2>
                <p style={{ margin: "2px 0 0 0", color: "#64748b", fontSize: "13px" }}>
                  Historical record of all screening sessions with cryptographic hashes and audit outcomes.
                </p>
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <input
                  type="text"
                  placeholder="Search name or document..."
                  value={caseSearch}
                  onChange={(e) => setCaseSearch(e.target.value)}
                  style={{ ...inputStyle, width: "220px" }}
                />
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

            {casesData?.cases && casesData.cases.length > 0 ? (
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>Case ID</th>
                    <th style={thStyle}>Date & Time</th>
                    <th style={thStyle}>Claimed Name</th>
                    <th style={thStyle}>Doc Number</th>
                    <th style={thStyle}>Family</th>
                    <th style={thStyle}>Outcome</th>
                    <th style={thStyle}>Coverage</th>
                    <th style={thStyle}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {casesData.cases
                    .filter((c) => {
                      if (caseFilter !== "ALL" && c.outcome !== caseFilter) return false;
                      if (caseSearch) {
                        const q = caseSearch.toUpperCase();
                        const matchName = (c.claimed_identity || "").toUpperCase().includes(q);
                        const matchDoc = (c.document_number || "").toUpperCase().includes(q);
                        const matchId = c.case_id.toUpperCase().includes(q);
                        if (!matchName && !matchDoc && !matchId) return false;
                      }
                      return true;
                    })
                    .map((c: CaseSummaryItem) => (
                      <tr key={c.case_id}>
                        <td style={tdStyle}><code>{c.case_id.slice(0, 8)}...</code></td>
                        <td style={tdStyle}>{new Date(c.created_at).toLocaleString()}</td>
                        <td style={tdStyle}><strong>{c.claimed_identity || "—"}</strong></td>
                        <td style={tdStyle}><code>{c.document_number || "—"}</code></td>
                        <td style={tdStyle}>{c.document_family}</td>
                        <td style={tdStyle}>
                          <span style={{ ...outcomeBadgeStyle, backgroundColor: outcomeBg[c.outcome], color: outcomeColors[c.outcome], border: `1px solid ${outcomeColors[c.outcome]}` }}>
                            {c.outcome}
                          </span>
                        </td>
                        <td style={tdStyle}>{Math.round(c.coverage.coverage_ratio * 100)}%</td>
                        <td style={tdStyle}>
                          <div style={{ display: "flex", gap: "6px" }}>
                            <button onClick={() => handleReopenCase(c.case_id)} style={smallButtonStyle}>
                              Autopsy
                            </button>
                            <a href={getReportHtmlUrl(c.case_id)} target="_blank" rel="noreferrer" style={{ ...smallButtonStyle, textDecoration: "none" }}>
                              HTML
                            </a>
                            <a href={getReportJsonUrl(c.case_id)} target="_blank" rel="noreferrer" style={{ ...smallButtonStyle, textDecoration: "none" }}>
                              JSON
                            </a>
                          </div>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            ) : (
              <div style={{ textAlign: "center", padding: "32px", color: "#64748b" }}>No cases found.</div>
            )}
          </div>
        )}

        {/* ===================================================================== */}
        {/* 4. IDENTITY LINKAGE VIEW */}
        {/* ===================================================================== */}
        {activeTab === "linkage" && (
          <div style={cardSectionStyle}>
            <div style={{ marginBottom: "16px" }}>
              <h2 style={{ margin: 0, fontSize: "20px", color: "#0f2735", fontWeight: 800 }}>Multi-Identity Biometric Linkage Graph</h2>
              <p style={{ margin: "2px 0 0 0", color: "#64748b", fontSize: "13px" }}>
                Detects multiple synthetic credentials sharing the same biometric face embedding but claiming conflicting names or document numbers.
              </p>
            </div>

            {linkageData.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {linkageData.map((cluster) => (
                  <div key={cluster.identity_reference} style={{ border: "1px solid #cbd5e1", borderRadius: "8px", padding: "16px", backgroundColor: "#ffffff" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", borderBottom: "1px solid #f1f5f9", paddingBottom: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "16px" }}>🔗</span>
                        <strong style={{ fontSize: "15px", color: "#0f2735" }}>{cluster.identity_reference}</strong>
                        <span style={tagStyle}>{cluster.credentials.length} linked credential(s)</span>
                      </div>
                      <span style={{ fontSize: "11px", color: "#64748b" }}>Source: {cluster.source}</span>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "10px" }}>
                      {cluster.credentials.map((cred, i) => (
                        <div key={i} style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "6px", padding: "10px" }}>
                          <div style={{ fontSize: "13px", fontWeight: 700, color: "#1e293b" }}>{cred.claimed_name || "Unknown Name"}</div>
                          <div style={{ fontSize: "11px", color: "#475467", marginTop: "2px" }}>Doc Number: <code>{cred.document_number || "—"}</code></div>
                          <div style={{ fontSize: "10px", color: "#64748b", marginTop: "4px" }}>Case ID: <code>{cred.case_id.slice(0, 8)}...</code></div>
                          <button onClick={() => handleReopenCase(cred.case_id)} style={{ ...smallButtonStyle, marginTop: "6px" }}>
                            Inspect Case
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "32px", color: "#64748b" }}>
                No multi-identity biometric clusters enrolled yet. Enrol multiple credentials with the same selfie to test.
              </div>
            )}
          </div>
        )}

        {/* ===================================================================== */}
        {/* 5. SYSTEM STATUS VIEW */}
        {/* ===================================================================== */}
        {activeTab === "status" && (
          <div style={cardSectionStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <h2 style={{ margin: 0, fontSize: "20px", color: "#0f2735", fontWeight: 800 }}>System Health & Diagnostics</h2>
                <p style={{ margin: "2px 0 0 0", color: "#64748b", fontSize: "13px" }}>
                  Live status of all 11 forensic verification sub-systems, local AI model assets, and database stores.
                </p>
              </div>
              <button onClick={refreshData} style={smallButtonStyle}>
                🔄 Refresh Status
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px" }}>
              {(systemStatus?.modules || []).map((m) => {
                const isReady = m.state === "READY";
                return (
                  <div
                    key={m.module}
                    style={{
                      border: `1px solid ${isReady ? "#bbf7d0" : "#fed7aa"}`,
                      backgroundColor: isReady ? "#f0fdf4" : "#fffbeb",
                      borderRadius: "8px",
                      padding: "14px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong style={{ fontSize: "14px", color: "#0f2735" }}>{m.module}</strong>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          backgroundColor: isReady ? "#166534" : "#9a3412",
                          color: "#fff",
                          padding: "2px 8px",
                          borderRadius: "4px",
                        }}
                      >
                        {m.state}
                      </span>
                    </div>
                    <div style={{ fontSize: "12px", color: "#475467", marginTop: "8px" }}>{m.detail}</div>
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
            <h2 style={{ margin: "0 0 8px 0", fontSize: "20px", color: "#0f2735", fontWeight: 800 }}>Policy & Architecture Configuration</h2>
            <p style={{ color: "#64748b", fontSize: "13px", marginBottom: "16px" }}>
              Active forensic thresholds, truth hierarchy rules, and scientific disclaimer boundaries.
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ backgroundColor: "#f8fafc", padding: "16px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                <h4 style={{ margin: "0 0 8px 0", color: "#0f2735" }}>Configured Policy Thresholds</h4>
                <ul style={{ fontSize: "13px", color: "#334155", lineHeight: "1.8", margin: 0, paddingLeft: "18px" }}>
                  <li>Biometric Face Match Threshold: <strong>0.55</strong> (Cosine Similarity)</li>
                  <li>Identity Linkage Threshold: <strong>0.50</strong> (Cosine Similarity)</li>
                  <li>Minimum Image Resolution: <strong>700 x 440 px</strong></li>
                  <li>Sharpness Variance of Laplacian Minimum: <strong>45.0</strong></li>
                  <li>Visual Forensics Portrait Region Z-Threshold: <strong>2.65</strong></li>
                </ul>
              </div>

              <div style={{ backgroundColor: "#f8fafc", padding: "16px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                <h4 style={{ margin: "0 0 8px 0", color: "#0f2735" }}>Disclaimers & Prototype Scope</h4>
                <ul style={{ fontSize: "12px", color: "#475467", lineHeight: "1.7", margin: 0, paddingLeft: "18px" }}>
                  <li>All identities, document numbers, and watchlist entries are synthetic and fictional.</li>
                  <li>No connection to Indian Passport Seva, MHA, SSB, ICAO PKD, or INTERPOL is active or claimed.</li>
                  <li>Triage outcomes are policy-driven screening categories, not calibrated mathematical probabilities of fraud.</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Camera Capture Modal */}
      {cameraMode && (
        <div style={modalOverlayStyle}>
          <div style={modalContentStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h3 style={{ margin: 0, fontSize: "16px", color: "#0f2735" }}>
                📷 Capture {cameraMode === "document" ? "Document" : "Live Face"}
              </h3>
              <button onClick={stopCamera} style={closeButtonStyle}>✕</button>
            </div>

            <video ref={videoRef} autoPlay playsInline style={{ width: "100%", maxHeight: "360px", backgroundColor: "#000", borderRadius: "6px" }} />

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "14px" }}>
              <button onClick={stopCamera} style={secondaryButtonStyle}>Cancel</button>
              <button onClick={captureFrame} style={primaryActionButtonStyle}>Capture Photo</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Styles
const dashboardHeaderStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "20px",
  flexWrap: "wrap",
  gap: "12px",
};

const statsGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
  gap: "14px",
};

const statCardStyle: React.CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #cbd5e1",
  borderRadius: "8px",
  padding: "16px",
};

const statLabelStyle: React.CSSProperties = {
  fontSize: "11px",
  fontWeight: 700,
  color: "#64748b",
  letterSpacing: "0.5px",
};

const statValueStyle: React.CSSProperties = {
  fontSize: "26px",
  fontWeight: 900,
  color: "#0f2735",
  margin: "4px 0",
};

const cardSectionStyle: React.CSSProperties = {
  backgroundColor: "#ffffff",
  border: "1px solid #cbd5e1",
  borderRadius: "8px",
  padding: "18px",
};

const sectionTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "14px",
  color: "#0f2735",
  fontWeight: 700,
};

const primaryActionButtonStyle: React.CSSProperties = {
  backgroundColor: "#0284c7",
  color: "#ffffff",
  border: "none",
  padding: "8px 16px",
  borderRadius: "6px",
  fontSize: "13px",
  fontWeight: 700,
  cursor: "pointer",
};

const secondaryButtonStyle: React.CSSProperties = {
  backgroundColor: "#f1f5f9",
  color: "#475467",
  border: "1px solid #cbd5e1",
  padding: "8px 16px",
  borderRadius: "6px",
  fontSize: "13px",
  fontWeight: 600,
  cursor: "pointer",
};

const smallButtonStyle: React.CSSProperties = {
  backgroundColor: "#f1f5f9",
  color: "#1e293b",
  border: "1px solid #cbd5e1",
  padding: "4px 8px",
  borderRadius: "4px",
  fontSize: "11px",
  fontWeight: 600,
  cursor: "pointer",
};

const outlineReportButtonStyle: React.CSSProperties = {
  backgroundColor: "#ffffff",
  color: "#0f2735",
  border: "1px solid #cbd5e1",
  padding: "6px 12px",
  borderRadius: "6px",
  fontSize: "12px",
  fontWeight: 700,
  cursor: "pointer",
  textDecoration: "none",
  display: "inline-flex",
  alignItems: "center",
};

const presetButtonStyle: React.CSSProperties = {
  backgroundColor: "#f8fafc",
  border: "1px solid #cbd5e1",
  borderRadius: "6px",
  padding: "12px",
  textAlign: "left",
  cursor: "pointer",
  transition: "all 0.15s ease",
};

const uploadBoxStyle: React.CSSProperties = {
  backgroundColor: "#f8fafc",
  border: "1px solid #e2e8f0",
  borderRadius: "6px",
  padding: "14px",
};

const cameraButtonStyle: React.CSSProperties = {
  backgroundColor: "#0f2735",
  color: "#ffffff",
  border: "none",
  borderRadius: "4px",
  padding: "3px 8px",
  fontSize: "11px",
  fontWeight: 600,
  cursor: "pointer",
};

const selectStyle: React.CSSProperties = {
  padding: "6px 10px",
  fontSize: "12px",
  borderRadius: "4px",
  border: "1px solid #cbd5e1",
  backgroundColor: "#ffffff",
  color: "#1e293b",
};

const inputStyle: React.CSSProperties = {
  padding: "6px 10px",
  fontSize: "12px",
  borderRadius: "4px",
  border: "1px solid #cbd5e1",
  backgroundColor: "#ffffff",
  color: "#1e293b",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: "12px",
  marginTop: "8px",
};

const thStyle: React.CSSProperties = {
  border: "1px solid #e2e8f0",
  backgroundColor: "#f8fafc",
  padding: "6px 10px",
  textAlign: "left",
  color: "#475467",
  fontWeight: 700,
  fontSize: "11px",
  textTransform: "uppercase",
};

const tdStyle: React.CSSProperties = {
  border: "1px solid #e2e8f0",
  padding: "6px 10px",
  textAlign: "left",
  verticalAlign: "top",
};

const tagStyle: React.CSSProperties = {
  display: "inline-block",
  fontSize: "11px",
  fontWeight: 700,
  padding: "2px 8px",
  borderRadius: "4px",
  backgroundColor: "#e2e8f0",
  color: "#334155",
};

const outcomeBadgeStyle: React.CSSProperties = {
  display: "inline-block",
  fontSize: "11px",
  fontWeight: 800,
  padding: "2px 8px",
  borderRadius: "4px",
};

const modalOverlayStyle: React.CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: "rgba(0, 0, 0, 0.6)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  zIndex: 1000,
};

const modalContentStyle: React.CSSProperties = {
  backgroundColor: "#ffffff",
  borderRadius: "8px",
  padding: "20px",
  width: "90%",
  maxWidth: "540px",
};

const closeButtonStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  fontSize: "16px",
  cursor: "pointer",
  color: "#64748b",
};
