"use client";

import React, { useState } from 'react';
import { IdentityForensicAutopsy, CaseSummaryResponse, SystemStatusResponse } from '../lib/types';
import { officerSummary, fieldName, stateLabel, readable } from '../lib/officer-summary';
import { getReportHtmlUrl, getReportJsonUrl } from '../lib/api';
import styles from './OfficerWorkspace.module.css';

type Preset = { id: string; name: string; docFile: string; selfieFile: string | null; family: string; desc: string; expected: string };
type Props = {
  report: IdentityForensicAutopsy | null; cases: CaseSummaryResponse | null; status: SystemStatusResponse | null;
  document: File | null; selfie: File | null; preview: string | null; selfiePreview: string | null;
  family: string; busy: boolean; error: string | null; presets: Preset[];
  onDocument: (e: React.ChangeEvent<HTMLInputElement>) => void; onSelfie: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onFamily: (value: string) => void; onRun: () => void; onCamera: (mode: 'document' | 'selfie') => void;
  onPreset: (preset: Preset) => void; onReopen: (id: string) => void; onDeveloper: () => void; onNew: () => void;
};

export function OfficerWorkspace(p: Props) {
  const [tab, setTab] = useState<'check' | 'cases'>('check');
  const [size, setSize] = useState({width: 0, height: 0});
  const report = p.report;
  const summary = report ? officerSummary(report) : null;
  const id = report?.case_id || report?.scan_id;
  const statuses = report?.module_statuses || [];
  const tone = !report || summary?.incomplete || summary?.conflictingLow || report.outcome === 'INDETERMINATE' ? 'neutral' : report.outcome === 'HIGH_RISK' ? 'danger' : report.outcome === 'REFER' ? 'warning' : 'good';
  return <div className={styles.workspace}>
    <header className={styles.header}>
      <div><strong className={styles.brand}>VEDA<span> / BORDER</span></strong><div className={styles.small}>Document & identity screening · Research prototype</div></div>
      <button className={styles.secondary} onClick={p.onDeveloper}>Developer Mode</button>
    </header>
    <nav className={styles.nav} aria-label="Officer workspace">
      <button aria-current={tab === 'check' ? 'page' : undefined} onClick={() => setTab('check')}>Check a document</button>
      <button aria-current={tab === 'cases' ? 'page' : undefined} onClick={() => setTab('cases')}>Recent cases</button>
      <span className={styles.small}>Officer Mode</span>
    </nav>
    <main className={styles.main}>
      {tab === 'cases' ? <section className={styles.card}><h1>Recent cases</h1><p>Open a saved result to review the checks. Original images are not stored.</p>
        {!p.cases ? <p>Case history is unavailable. Check that the local service is running.</p> : !p.cases.cases.length ? <p>No saved cases yet.</p> : <div className={styles.caseList}>{p.cases.cases.map(c => <button key={c.case_id} className={styles.case} onClick={() => {p.onReopen(c.case_id); setTab('check');}}><strong>{c.claimed_identity || 'Identity not read'}</strong><span>{readable(c.outcome)} · {new Date(c.created_at).toLocaleString()}</span><span>Open result →</span></button>)}</div>}
        <p className={styles.small}>Showing up to 50 recent cases.</p>
      </section> : <>
        <div className={styles.heading}><div><div className={styles.eyebrow}>{report ? 'SCREENING RESULT' : 'START A CHECK'}</div><h1>{report ? 'What needs your attention?' : 'Understand what needs checking.'}</h1><p>{report ? 'Review the findings, inspect the image and decide the next step.' : 'Add a document image. We’ll explain what was checked, what looks inconsistent and what to do next.'}</p></div>{report && <button className={styles.secondary} disabled={p.busy} onClick={p.onNew}>Start a new check</button>}</div>
        {p.error && <div className={styles.error} role="alert">{p.error}</div>}
        {p.busy && <div className={styles.card} role="status">Checking your document… Image, text, face and available records are being examined. Please wait.</div>}
        {report && summary && <>
          <section className={`${styles.result} ${styles[tone]}`} aria-label="Screening result">
            <div><div className={styles.eyebrow}>OVERALL RESULT</div><h2>{summary.title}</h2><p>{summary.conflictingLow ? 'The returned outcome and individual checks disagree. Do not rely on the low-risk score; review the findings below.' : report.outcome === 'INDETERMINATE' || summary.incomplete ? 'Some evidence is missing or could not be checked. A dependable overall assessment is not available.' : summary.issues.length ? `${summary.issues.length} finding${summary.issues.length === 1 ? '' : 's'} need your attention. These are screening observations, not proof of fraud.` : 'No configured major issue was found in the available checks. This does not establish that the document is genuine.'}</p>
              <div className={styles.action}><span>NEXT STEP</span><strong>{summary.action}</strong></div>
            </div>
            <div className={styles.score}><span>Screening risk index</span><strong>{summary.score == null ? '—' : Math.round(summary.score)}{summary.score != null && <small> / 100</small>}</strong><p>{summary.score == null ? 'Not available for a dependable assessment' : 'Higher means more concern. This is a policy category indicator, not a probability of fraud.'}</p><div className={styles.coverage}><b>{Math.round(report.evidence_coverage.coverage_ratio * 100)}% required checks completed</b><p>Completion does not mean the checks passed.</p></div></div>
          </section>
          <div className={styles.columns}>
            <section className={styles.card}><h2>What is the issue?</h2>{summary.issues.length ? summary.issues.map((issue,i) => <article className={styles.finding} key={i}><span className={styles.number}>{i+1}</span><div><h3>{issue.title}</h3><p>{issue.detail}</p></div></article>) : <p>{summary.incomplete ? 'We could not collect enough evidence to describe this document reliably.' : 'No specific issue was reported by the completed checks.'}</p>}
              <h3>Checks that could not be completed</h3>{statuses.filter(l => l.status === 'UNAVAILABLE').length ? statuses.filter(l => l.status === 'UNAVAILABLE').map(l => <p key={l.module}><strong>{l.module.replaceAll('_',' ')}</strong> — {l.summary}</p>) : <p>No unavailable lanes reported.</p>}
            </section>
            <section className={styles.card}><h2>Inspect the submitted image</h2><p className={styles.small}>{report.specimen_filename}</p>{p.preview ? <><div className={styles.imageFrame}><img src={p.preview} alt="Document submitted for this result" onLoad={e => setSize({width:e.currentTarget.naturalWidth,height:e.currentTarget.naturalHeight})}/>{size.width > 0 && report.visual_forensics?.findings?.map((f,i) => f.bounding_box && <span key={i} className={styles.region} style={{left:`${100*f.bounding_box.x/size.width}%`,top:`${100*f.bounding_box.y/size.height}%`,width:`${100*f.bounding_box.width/size.width}%`,height:`${100*f.bounding_box.height/size.height}%`}} title={f.explanation}><b>{i+1}</b></span>)}</div><p className={styles.small}>Red boxes mark image-pattern anomalies only. Text disagreements may have no highlighted region.</p></> : <p className={styles.empty}>Image preview unavailable for this saved case or PDF. The extracted findings remain available below.</p>}{p.selfiePreview && <details><summary>View comparison face</summary><img className={styles.face} src={p.selfiePreview} alt="Submitted comparison face; liveness not verified"/></details>}
              <details><summary>{report.visible_document_data.raw_ocr_text ? (Object.keys(report.visible_document_data.visible_fields || {}).length ? 'Structured fields (partial extraction)' : 'Raw OCR available; structured fields unavailable') : 'Identity details read from the image'}</summary><dl>{Object.entries(report.visible_document_data.visible_fields || {}).map(([key,value]) => <div className={styles.field} key={key}><dt>{fieldName(key)}</dt><dd>{value}</dd></div>)}</dl>{report.visible_document_data.raw_ocr_text && <p className={styles.small}>Raw OCR evidence is available in Developer Mode. Fields are shown only when the parser found a stable value.</p>}</details>
            </section>
          </div>
          <section className={styles.card}><h2>What was checked</h2><div className={styles.checks}>{statuses.map(l => <div key={l.module} className={styles.check}><strong>{l.module.replaceAll('_',' ')}</strong><span data-state={l.status}>{stateLabel(l.status)}</span><small>{l.summary}</small></div>)}</div></section>
          <section className={styles.card}><h2>Visible vs machine-readable fields</h2><p className={styles.small}>A contradiction means the two readings disagree; it does not by itself prove how the document was altered.</p><div className={styles.table}>{(report.cross_source_consistency || []).map((item:any) => <div className={styles.row} key={item.field}><strong>{fieldName(item.field)}</strong><span>{item.value_a ?? '—'}</span><span>{item.value_b ?? '—'}</span><b data-state={item.status}>{item.status === 'PASS' ? 'MATCH' : item.status === 'FAIL' ? 'CONTRADICTION' : item.status}</b></div>)}</div></section>
          <div className={styles.export}><span className={styles.small}>Case {id?.slice(0,8)} · Human review remains required.</span>{id && <a href={getReportHtmlUrl(id)} target="_blank" rel="noreferrer">Open printable report</a>}<button className={styles.secondary} onClick={p.onDeveloper}>Inspect pipeline details</button></div>
        </>}
        <section className={styles.card}><h2>{report ? 'Check another image or recapture' : 'Add your images'}</h2><div className={styles.uploads}>
          <div><label htmlFor="officer-document">1. Document image <span>Required</span></label><p>PNG, JPG or PDF · Up to 15 MB</p><input id="officer-document" disabled={p.busy} type="file" accept="image/png,image/jpeg,application/pdf,.pdf" onChange={p.onDocument}/><button disabled={p.busy} className={styles.secondary} onClick={() => p.onCamera('document')}>Use camera</button>{!report && p.preview && <img className={styles.uploadPreview} src={p.preview} alt="Selected document, not yet checked"/>}</div>
          <div><label htmlFor="officer-selfie">2. Comparison face <span>Optional</span></label><p>Add a clear face image to compare with the portrait.</p><input id="officer-selfie" disabled={p.busy} type="file" accept="image/png,image/jpeg" onChange={p.onSelfie}/><button disabled={p.busy} className={styles.secondary} onClick={() => p.onCamera('selfie')}>Use camera</button>{p.selfie && <p className={styles.small}>{p.selfie.name}</p>}</div>
        </div><details><summary>Document type</summary><label htmlFor="officer-family">Choose a type if automatic recognition is incorrect</label><select id="officer-family" disabled={p.busy} value={p.family} onChange={e => p.onFamily(e.target.value)}><option value="">Recognize automatically</option><option value="TRAVEL_DOCUMENT">Passport / travel document</option><option value="VISA_OR_PERMIT">Visa / permit</option><option value="NATIONAL_ID">National identity card</option><option value="DRIVING_LICENCE">Driving licence</option></select></details>
          <div className={styles.run}><button disabled={!p.document || p.busy} className={styles.primary} onClick={p.onRun}>{p.busy ? 'Checking…' : 'Check document →'}</button><span className={styles.small}>{p.document ? p.document.name : 'Choose an image to begin.'}</span></div>
        </section>
        <details className={styles.card}><summary>Try a research example</summary><p>Controlled fixtures demonstrate known conditions. External dataset entries are sample processing only; neither mode proves authenticity or benchmark accuracy.</p>{['Controlled Research Fixtures','External Dataset Samples'].map((label,index) => <div key={label}><h3>{label}</h3><div className={styles.examples}>{p.presets.filter(x => index === 0 ? !x.docFile.includes('/') : x.docFile.includes('/')).map(x => <button disabled={p.busy} key={x.id} className={styles.secondary} onClick={() => p.onPreset(x)}>{x.name.replace(/^\d+\. /,'')}</button>)}</div></div>)}</details>
      </>}
      <footer className={styles.footer}>Research decision support. A low screening risk does not mean genuine. Face comparison does not establish liveness. Watchlist checks use local synthetic records.</footer>
    </main>
  </div>;
}

export function DeveloperDiagnostics({report,status}: {report: IdentityForensicAutopsy | null; status: SystemStatusResponse | null}) {
 return <section style={{padding:20,color:'#e2e8f0',background:'#102131',border:'1px solid #456'}}><h2>Pipeline diagnostics</h2><p>Inspect execution failures, unavailable evidence and the exact returned payload. Outcome and lane status are shown separately.</p>{report ? <><p>Case: {report.case_id} · Backend outcome: {report.outcome} · Coverage: {report.evidence_coverage.state}</p>{report.evidence_lanes.map(l => <details key={l.lane_id}><summary>{l.name}: {l.status} {l.required ? '(required)' : '(optional)'}</summary><p>{l.summary}</p><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(l,null,2)}</pre></details>)}<details><summary>Full case payload, errors, thresholds and evidence graph</summary><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(report,null,2)}</pre></details><a href={getReportJsonUrl(report.case_id || report.scan_id)} style={{color:'#7dd3fc'}}>Download diagnostic JSON</a></> : <p>Run a screening to inspect its pipeline results.</p>}<details><summary>Service readiness payload</summary><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(status,null,2)}</pre></details></section>;
}
