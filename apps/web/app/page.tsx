"use client";
import { useState } from "react";

type Lane = { lane_id: string; name: string; status: string; summary: string; required: boolean };
type Rule = { rule_id: string; status: string; observed_value: unknown; reason: string };
type Autopsy = { specimen_filename: string; specimen_sha256: string; outcome: string; evidence_coverage: { coverage_ratio: number; missing_mandatory: string[] }; evidence_lanes: Lane[]; disclaimer: string; visible_document: { visible_fields?: Record<string, string>; raw_ocr_text?: string }; mrz_analysis: { mrz_detected?: boolean; fields?: Record<string, string>; checks?: Record<string, string> }; document_rules: Rule[] };

export default function Home() {
  const [result, setResult] = useState<Autopsy | null>(null);
  const [error, setError] = useState("");
  async function upload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; if (!file) return;
    setError(""); const form = new FormData(); form.append("file", file);
    try { const response = await fetch("http://localhost:8000/api/v1/scan", { method: "POST", body: form }); if (!response.ok) throw new Error(await response.text()); setResult(await response.json()); }
    catch (e) { setError(e instanceof Error ? e.message : "Scan failed"); }
  }
  const visible = result?.visible_document.visible_fields || {}; const mrz = result?.mrz_analysis.fields || {}; const checks = result?.mrz_analysis.checks || {};
  return <main style={{fontFamily:"system-ui",maxWidth:900,margin:"40px auto",padding:24}}><p style={{letterSpacing:2}}>VEDA-BORDER</p><h1>Identity Forensic Autopsy</h1><p>Task 03 technical shell: local extraction and deterministic document validation.</p><input type="file" accept=".json,.png,.jpg,.jpeg,.pdf" onChange={upload}/>{error && <p role="alert">{error}</p>}{result && <section><h2>{result.outcome}</h2><p><b>File:</b> {result.specimen_filename}</p><p><b>SHA-256:</b> <code>{result.specimen_sha256}</code></p><p><b>Coverage:</b> {Math.round(result.evidence_coverage.coverage_ratio * 100)}% — {result.evidence_coverage.missing_mandatory.length} required lane(s) unavailable</p><h3>Visible document data</h3><pre>{JSON.stringify(visible, null, 2)}</pre><h3>MRZ analysis</h3><p>Detected: {String(result.mrz_analysis.mrz_detected)}</p><pre>{JSON.stringify({fields: mrz, checks}, null, 2)}</pre><h3>Document rules</h3>{result.document_rules.map(rule => <article key={rule.rule_id} style={{border:"1px solid #ccc",padding:12,margin:"12px 0"}}><b>{rule.rule_id}</b><span style={{marginLeft:16}}>{rule.status}</span><p>{rule.reason}</p></article>)}<h3>Other evidence lanes</h3><div>{result.evidence_lanes.map(lane => <article key={lane.lane_id} style={{border:"1px solid #ccc",padding:12,margin:"12px 0"}}><b>{lane.name}</b><span style={{marginLeft:16,color:lane.status === "UNAVAILABLE" ? "#a15c00" : "green"}}>{lane.status}</span><p>{lane.summary}</p></article>)}</div><small>{result.disclaimer}</small></section>}</main>;
}
