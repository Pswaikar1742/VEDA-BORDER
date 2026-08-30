"use client";

import { useState } from "react";

type Lane = { lane_id: string; name: string; status: string; summary: string; required: boolean };
type Rule = { rule_id: string; status: string; observed_value: unknown; reason: string };
type Comparison = { field: string; source_a: "VIZ"; value_a: string | null; source_b: "MRZ"; value_b: string | null; status: string; severity: string; reason: string };
type Intelligence = { source: string; demo_data: boolean; status: string; result: string; reason: string };
type Extraction = { visible_fields?: Record<string, string>; raw_visible_fields?: Record<string, string>; field_confidence?: Record<string, number>; missing_fields?: string[]; raw_ocr_text?: string; ocr_metadata?: { backend?: string; error?: string | null } };
type Autopsy = {
  specimen_filename: string; specimen_sha256: string; outcome: string; critical_findings: string[]; disclaimer: string;
  evidence_coverage: { coverage_ratio: number; missing_mandatory: string[] }; evidence_lanes: Lane[];
  visible_document_data: Extraction; mrz_analysis: { mrz_detected?: boolean; fields?: Record<string, string>; checks?: Record<string, string>; raw_lines?: string[]; error?: string | null };
  document_rules: Rule[]; cross_source_consistency: Comparison[]; threat_intelligence: Intelligence;
};

const LABELS: Record<string, string> = { holder_name: "Name", document_number: "Document No.", nationality: "Nationality", date_of_birth: "DOB", sex: "Sex", expiry_date: "Expiry" };
const statusColor = (status: string) => status === "FAIL" ? "#b42318" : status === "PASS" ? "#067647" : "#b54708";

export default function Home() {
  const [result, setResult] = useState<Autopsy | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function upload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; if (!file) return;
    setError(""); setBusy(true); const form = new FormData(); form.append("file", file);
    try {
      const response = await fetch("http://localhost:8000/api/v1/scan", { method: "POST", body: form });
      if (!response.ok) throw new Error(await response.text());
      setResult(await response.json());
    } catch (e) { setError(e instanceof Error ? e.message : "Scan failed"); }
    finally { setBusy(false); }
  }

  const visible = result?.visible_document_data.visible_fields || {};
  const rawVisible = result?.visible_document_data.raw_visible_fields || {};
  const confidence = result?.visible_document_data.field_confidence || {};
  const mrz = result?.mrz_analysis.fields || {};
  const checks = result?.mrz_analysis.checks || {};

  return <main style={{fontFamily:"system-ui",maxWidth:1050,margin:"32px auto",padding:24,color:"#172b36"}}>
    <p style={{letterSpacing:2,marginBottom:4}}>VEDA-BORDER</p><h1 style={{marginTop:0}}>Identity Forensic Autopsy</h1>
    <div style={{background:"#fff3cd",border:"2px solid #b54708",padding:12,fontWeight:800,letterSpacing:1}}>DEMO DATA — FICTIONAL CREDENTIALS AND MOCK INTELLIGENCE ONLY</div>
    <p>Task 04 local image extraction and deterministic consistency evidence. No authenticity or fraud probability is asserted.</p>
    <input aria-label="Upload fictional credential image" type="file" accept=".png,.jpg,.jpeg,image/png,image/jpeg" onChange={upload}/>{busy && <span style={{marginLeft:12}}>Analyzing local pixels…</span>}
    {error && <p role="alert" style={{color:"#b42318"}}>{error}</p>}
    {result && <section>
      <h2 style={{color:statusColor(result.outcome)}}>{result.outcome}</h2>
      <p><b>File:</b> {result.specimen_filename}</p><p><b>SHA-256:</b> <code>{result.specimen_sha256}</code></p>
      <p><b>Evidence coverage:</b> {Math.round(result.evidence_coverage.coverage_ratio * 100)}% — {result.evidence_coverage.missing_mandatory.length} mandatory lane(s) unavailable</p>

      <h3>Visible document data</h3>
      <table style={{width:"100%",borderCollapse:"collapse"}}><thead><tr><th style={cell}>Field</th><th style={cell}>Raw pixel extraction</th><th style={cell}>Normalized</th><th style={cell}>OCR confidence</th></tr></thead><tbody>
        {Object.entries(LABELS).map(([field,label]) => <tr key={field}><td style={cell}>{label}</td><td style={cell}>{rawVisible[field] || "UNAVAILABLE"}</td><td style={cell}>{visible[field] || "UNAVAILABLE"}</td><td style={cell}>{confidence[field] === undefined ? "—" : `${confidence[field].toFixed(1)}%`}</td></tr>)}
      </tbody></table>

      <h3>MRZ data</h3><p>Detected from pixels: <b>{String(result.mrz_analysis.mrz_detected)}</b></p>
      {result.mrz_analysis.error && <p style={{color:"#b54708"}}>{result.mrz_analysis.error}</p>}
      <pre style={pre}>{JSON.stringify(mrz, null, 2)}</pre>
      <h4>Individual check digits</h4><div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(220px,1fr))",gap:8}}>{Object.entries(checks).map(([name,status]) => <div key={name} style={{border:`2px solid ${statusColor(status)}`,padding:10}}><b>{name}</b>: <span style={{color:statusColor(status),fontWeight:800}}>{status}</span></div>)}</div>

      <h3>Cross-source consistency</h3>
      <table style={{width:"100%",borderCollapse:"collapse"}}><thead><tr><th style={cell}>Field</th><th style={cell}>VIZ</th><th style={cell}>MRZ</th><th style={cell}>Result</th><th style={cell}>Severity</th></tr></thead><tbody>
        {result.cross_source_consistency.map(item => <tr key={item.field} style={{background:item.status === "FAIL" ? "#fee4e2" : "transparent"}}><td style={cell}>{LABELS[item.field] || item.field}</td><td style={cell}>{item.value_a ?? "UNAVAILABLE"}</td><td style={cell}>{item.value_b ?? "UNAVAILABLE"}</td><td style={{...cell,color:statusColor(item.status),fontWeight:900}}>{item.status}</td><td style={cell}>{item.severity}</td></tr>)}
      </tbody></table>

      <h3>Threat intelligence</h3><div style={{border:`2px solid ${statusColor(result.threat_intelligence.status)}`,padding:14}}>
        <p><b>Source:</b> {result.threat_intelligence.source} — DEMO / MOCK</p><p><b>Status:</b> <span style={{color:statusColor(result.threat_intelligence.status)}}>{result.threat_intelligence.result}</span></p><p>{result.threat_intelligence.reason}</p>
      </div>

      <h3>Deterministic document rules</h3>{result.document_rules.map(rule => <article key={rule.rule_id} style={{border:`1px solid ${statusColor(rule.status)}`,padding:10,margin:"8px 0"}}><b>{rule.rule_id}</b><span style={{marginLeft:16,color:statusColor(rule.status)}}>{rule.status}</span><p>{rule.reason}</p></article>)}
      <h3>Evidence lanes</h3>{result.evidence_lanes.map(lane => <article key={lane.lane_id} style={{border:"1px solid #b8c8cf",padding:10,margin:"8px 0"}}><b>{lane.name}</b><span style={{marginLeft:16,color:statusColor(lane.status)}}>{lane.status}</span><p>{lane.summary}</p></article>)}
      {result.critical_findings.length > 0 && <><h3>Findings</h3><ul>{result.critical_findings.map(finding => <li key={finding}>{finding}</li>)}</ul></>}
      <small>{result.disclaimer}</small>
    </section>}
  </main>;
}

const cell: React.CSSProperties = {border:"1px solid #b8c8cf",padding:9,textAlign:"left",verticalAlign:"top"};
const pre: React.CSSProperties = {background:"#eef3f5",padding:14,overflowX:"auto"};
