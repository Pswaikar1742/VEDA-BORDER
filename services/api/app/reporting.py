from __future__ import annotations

import html
import json
from typing import Any


def render_printable_html(case: dict[str, Any]) -> str:
    def h(val: Any) -> str:
        return html.escape(str(val) if val is not None else "—")

    outcome = case.get("outcome", "INDETERMINATE")
    outcome_colors = {
        "LOW_RISK": "#067647",
        "REFER": "#b54708",
        "HIGH_RISK": "#b42318",
        "INDETERMINATE": "#667085",
    }
    outcome_bg = {
        "LOW_RISK": "#ecfdf3",
        "REFER": "#fffaeb",
        "HIGH_RISK": "#fef3f2",
        "INDETERMINATE": "#f8f9fa",
    }
    badge_color = outcome_colors.get(outcome, "#172b36")
    badge_bg = outcome_bg.get(outcome, "#eef3f5")

    visible = case.get("visible_document_data", {}).get("visible_fields", {})
    raw_visible = case.get("visible_document_data", {}).get("raw_visible_fields", {})
    confidence = case.get("visible_document_data", {}).get("field_confidence", {})
    mrz = case.get("mrz_analysis", {})
    rules = case.get("document_rules", [])
    consistency = case.get("cross_source_consistency", [])
    forensics = case.get("visual_forensics", {})
    biometrics = case.get("biometric_verification", {})
    intelligence = case.get("threat_intelligence", {})
    linkage = case.get("identity_linkage", {})
    coverage = case.get("evidence_coverage", {})
    hypotheses = case.get("forensic_hypotheses", [])
    actions = case.get("next_best_actions", [])
    hard_gates = case.get("hard_gates", [])
    quality = case.get("capture_quality", {})

    # Build visible fields table rows
    field_labels = [
        ("holder_name", "Holder Name"),
        ("document_number", "Document Number"),
        ("nationality", "Nationality"),
        ("date_of_birth", "Date of Birth"),
        ("sex", "Sex"),
        ("expiry_date", "Expiry Date"),
    ]
    visible_rows = ""
    for field, label in field_labels:
        conf_val = f"{confidence[field]:.1f}%" if field in confidence else "—"
        visible_rows += f"""<tr>
            <td><strong>{h(label)}</strong></td>
            <td><code>{h(raw_visible.get(field))}</code></td>
            <td><code>{h(visible.get(field))}</code></td>
            <td>{conf_val}</td>
        </tr>"""

    # MRZ check digits
    mrz_checks_html = ""
    for check_name, check_stat in (mrz.get("checks") or {}).items():
        st_col = "#067647" if check_stat == "PASS" else ("#b42318" if check_stat == "FAIL" else "#b54708")
        mrz_checks_html += f"""<span class="tag" style="border: 1px solid {st_col}; color: {st_col};">
            {h(check_name)}: <strong>{h(check_stat)}</strong>
        </span> """

    # Consistency rows
    consistency_rows = ""
    for item in consistency:
        st = item.get("status", "UNAVAILABLE")
        st_col = "#067647" if st == "PASS" else ("#b42318" if st == "FAIL" else ("#667085" if st == "NOT_APPLICABLE" else "#b54708"))
        bg = "#fee4e2" if st == "FAIL" else "transparent"
        consistency_rows += f"""<tr style="background:{bg}">
            <td><strong>{h(item.get('field'))}</strong></td>
            <td><code>{h(item.get('value_a'))}</code></td>
            <td><code>{h(item.get('value_b'))}</code></td>
            <td style="color:{st_col}; font-weight:bold;">{h(st)}</td>
            <td>{h(item.get('severity'))}</td>
            <td>{h(item.get('reason'))}</td>
        </tr>"""

    # Rules rows
    rules_rows = ""
    for rule in rules:
        st = rule.get("status", "UNAVAILABLE")
        st_col = "#067647" if st == "PASS" else ("#b42318" if st == "FAIL" else "#b54708")
        rules_rows += f"""<tr>
            <td><code>{h(rule.get('rule_id'))}</code></td>
            <td style="color:{st_col}; font-weight:bold;">{h(st)}</td>
            <td>{h(rule.get('expected_condition'))}</td>
            <td>{h(rule.get('reason'))}</td>
        </tr>"""

    # Hypotheses cards
    hypotheses_html = ""
    for hyp in hypotheses:
        sev = hyp.get("severity", "INFO")
        sev_col = "#b42318" if sev == "CRITICAL" else ("#b54708" if sev == "HIGH" else "#175cd3")
        hypotheses_html += f"""<div class="card" style="border-left: 4px solid {sev_col};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; color:#172b36;">{h(hyp.get('hypothesis'))}</h4>
                <span class="tag" style="background:{sev_col}; color:#fff;">{h(sev)}</span>
            </div>
            <p style="margin:6px 0;">{h(hyp.get('explanation'))}</p>
            <div style="font-size:12px; color:#555;">
                <div><strong>Supporting Evidence:</strong> {h(', '.join(hyp.get('supporting_evidence', [])) or 'None')}</div>
                <div><strong>Contradicting Evidence:</strong> {h(', '.join(hyp.get('contradicting_evidence', [])) or 'None')}</div>
                <div><strong>Missing Evidence:</strong> {h(', '.join(hyp.get('missing_evidence', [])) or 'None')}</div>
                <div style="margin-top:4px; font-style:italic;"><strong>Limitations:</strong> {h(hyp.get('limitations'))}</div>
            </div>
        </div>"""

    # Next actions
    actions_html = ""
    for act in actions:
        prio = act.get("priority", 3)
        prio_label = "HIGH PRIORITY" if prio == 1 else ("MEDIUM PRIORITY" if prio == 2 else "RECOMMENDED")
        prio_col = "#b42318" if prio == 1 else ("#b54708" if prio == 2 else "#175cd3")
        actions_html += f"""<div style="margin:6px 0; padding:8px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px;">
            <span class="tag" style="background:{prio_col}; color:#fff; font-size:11px;">{prio_label}</span>
            <strong style="margin-left:8px;">{h(act.get('action'))}</strong>
            <div style="margin-top:4px; font-size:13px; color:#475467;">{h(act.get('reason'))}</div>
        </div>"""

    # Hard gates
    hard_gates_html = ""
    if hard_gates:
        for gate in hard_gates:
            hard_gates_html += f"""<div style="margin:6px 0; padding:8px 12px; background:#fef3f2; border:1px solid #fecdca; border-radius:4px; color:#b42318;">
                <strong>GATE ACTIVE: {h(gate.get('gate'))}</strong> [{h(gate.get('severity'))}]
                <div>{h(gate.get('reason'))}</div>
            </div>"""
    else:
        hard_gates_html = "<div style='color:#067647;'>No policy hard gates triggered.</div>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VEDA-BORDER Forensic Autopsy — {h(case.get('case_id'))}</title>
<style>
  @page {{ margin: 15mm; size: A4; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #172b36; margin: 24px; line-height: 1.45; font-size: 13px; }}
  header {{ border-bottom: 2px solid #0f2735; padding-bottom: 16px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; }}
  h1 {{ margin: 0; font-size: 22px; color: #0f2735; letter-spacing: -0.5px; }}
  h2 {{ font-size: 15px; margin: 20px 0 8px 0; color: #0f2735; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
  h3 {{ font-size: 13px; margin: 12px 0 6px 0; }}
  .tag {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
  .triage-banner {{ padding: 14px 18px; border-radius: 6px; margin-bottom: 20px; border: 2px solid {badge_color}; background: {badge_bg}; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0 16px 0; font-size: 12px; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #f1f5f9; font-weight: 600; color: #334155; }}
  code {{ font-family: "SFMono-Regular", Consolas, Menlo, monospace; font-size: 11px; background: #f1f5f9; padding: 1px 4px; border-radius: 3px; }}
  .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 10px; margin: 8px 0; }}
  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .grid3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }}
  .meta-item {{ margin-bottom: 4px; }}
  .meta-label {{ font-weight: 600; color: #64748b; font-size: 11px; text-transform: uppercase; }}
  .footer {{ margin-top: 30px; border-top: 1px solid #cbd5e1; padding-top: 12px; font-size: 11px; color: #64748b; }}
  @media print {{
    body {{ margin: 0; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>VEDA-BORDER</h1>
    <div style="font-size: 13px; color: #475467; font-weight: 500;">Verification & Evidence-Driven Autopsy for Border Identity and Document Screening</div>
    <div style="margin-top: 6px;">
      <span class="tag" style="background:#0f2735; color:#fff;">RESEARCH PROTOTYPE</span>
      <span class="tag" style="background:#e0e7ff; color:#3730a3; margin-left: 6px;">SSB / MHA PS 26188</span>
    </div>
  </div>
  <div style="text-align: right;">
    <div class="meta-label">Case ID</div>
    <code style="font-size: 12px; font-weight: bold;">{h(case.get('case_id'))}</code>
    <div class="meta-label" style="margin-top: 6px;">Analyzed At</div>
    <div style="font-size: 12px;">{h(case.get('created_at'))}</div>
  </div>
</header>

<div class="triage-banner">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div>
      <div class="meta-label" style="color:{badge_color};">Screening Triage Outcome</div>
      <div style="font-size: 24px; font-weight: 800; color: {badge_color};">{h(outcome)}</div>
    </div>
    <div style="text-align: right;">
      <div class="meta-label">Evidence Coverage</div>
      <div style="font-size: 18px; font-weight: 700;">{int(coverage.get('coverage_ratio', 1.0) * 100)}% ({h(coverage.get('state', 'COMPLETE'))})</div>
      <div style="font-size: 11px; color: #64748b;">Missing Mandatory: {h(', '.join(coverage.get('missing_mandatory', [])) or 'None')}</div>
    </div>
  </div>
  {f'<div style="margin-top:8px; font-size:13px; color:{badge_color}; font-weight:500;">' + '<br>'.join(h(r) for r in case.get('outcome_reasons', [])) + '</div>' if case.get('outcome_reasons') else ''}
</div>

<div class="grid2">
  <div>
    <h2>1. Document Overview</h2>
    <div class="card">
      <div class="meta-item"><span class="meta-label">Specimen Filename:</span> {h(case.get('specimen_filename'))}</div>
      <div class="meta-item"><span class="meta-label">Specimen SHA-256:</span> <code>{h(case.get('specimen_sha256'))}</code></div>
      <div class="meta-item"><span class="meta-label">Classified Family:</span> <strong>{h(case.get('document_family'))}</strong></div>
      <div class="meta-item"><span class="meta-label">Capture Quality Status:</span> <strong>{h(quality.get('status', 'UNAVAILABLE'))}</strong> (Sharpness Var: {h(next((f.get('measure') for f in quality.get('findings', []) if f.get('check') == 'blur'), '—'))})</div>
    </div>
  </div>
  <div>
    <h2>2. Hard Gates & Policy Alerts</h2>
    <div class="card">
      {hard_gates_html}
    </div>
  </div>
</div>

<h2>3. Visible Document Data vs MRZ Extraction</h2>
<table>
  <thead>
    <tr>
      <th style="width:25%;">Field</th>
      <th style="width:28%;">Raw OCR Pixels</th>
      <th style="width:28%;">Normalized Value</th>
      <th style="width:19%;">Confidence</th>
    </tr>
  </thead>
  <tbody>
    {visible_rows}
  </tbody>
</table>

<div class="grid2">
  <div>
    <h2>4. MRZ & Check Digits</h2>
    <div class="card">
      <div><strong>Detected:</strong> {h(mrz.get('mrz_detected'))} | <strong>Family Applicability:</strong> {h(mrz.get('applicability', 'APPLICABLE'))}</div>
      {f'<pre style="margin:6px 0; padding:6px; background:#e2e8f0; font-size:11px;">' + chr(10).join(h(l) for l in mrz.get('raw_lines', [])) + '</pre>' if mrz.get('raw_lines') else ''}
      <div style="margin-top:8px;">{mrz_checks_html}</div>
    </div>
  </div>
  <div>
    <h2>5. Biometrics & Identity Linkage</h2>
    <div class="card">
      <div><strong>Biometric Face Verification:</strong> <span class="tag" style="background:#0f2735; color:#fff;">{h(biometrics.get('decision', 'UNAVAILABLE'))}</span></div>
      <div style="margin:4px 0; font-size:12px;">Model: {h(biometrics.get('model'))} | Cosine Similarity: <strong>{h(biometrics.get('similarity'))}</strong> (Threshold: {h(biometrics.get('configured_prototype_threshold'))})</div>
      <hr style="border:none; border-top:1px solid #e2e8f0; margin:8px 0;">
      <div><strong>Identity Linkage:</strong> <span class="tag" style="background:#475467; color:#fff;">{h(linkage.get('status', 'UNAVAILABLE'))}</span></div>
      <div style="margin:4px 0; font-size:12px;">Assigned Cluster: <strong>{h(linkage.get('identity_reference'))}</strong></div>
      <div style="font-size:11px; color:#64748b;">{h(linkage.get('reason'))}</div>
    </div>
  </div>
</div>

<h2>6. Cross-Source Consistency Reconstruction</h2>
<table>
  <thead>
    <tr>
      <th>Field</th>
      <th>VIZ Value</th>
      <th>MRZ Value</th>
      <th>Status</th>
      <th>Severity</th>
      <th>Forensic Reason</th>
    </tr>
  </thead>
  <tbody>
    {consistency_rows}
  </tbody>
</table>

<div class="grid2">
  <div>
    <h2>7. Visual Forensics</h2>
    <div class="card">
      <div><strong>Status:</strong> <span class="tag" style="background:#0f2735; color:#fff;">{h(forensics.get('status', 'UNAVAILABLE'))}</span> | <strong>Detector:</strong> {h(forensics.get('detector', {}).get('name'))}</div>
      <div style="margin:6px 0; font-size:12px;">Suspicious Regions Detected: <strong>{len(forensics.get('suspicious_regions', []))}</strong></div>
      <div style="font-size:11px; color:#64748b;">{h('<br>'.join(forensics.get('limitations', [])))}</div>
    </div>
  </div>
  <div>
    <h2>8. Local Threat Intelligence</h2>
    <div class="card">
      <div><strong>Source:</strong> {h(intelligence.get('display_source', 'LOCAL PROTOTYPE WATCHLIST'))} <span class="tag" style="background:#fffaeb; color:#b54708; border:1px solid #b54708;">SYNTHETIC DATA</span></div>
      <div style="margin:6px 0; font-size:13px;"><strong>Result:</strong> {h(intelligence.get('result'))}</div>
      <div style="font-size:12px; color:#475467;">{h(intelligence.get('reason'))}</div>
    </div>
  </div>
</div>

<h2>9. Deterministic Document Rules</h2>
<table>
  <thead>
    <tr>
      <th style="width:25%;">Rule ID</th>
      <th style="width:15%;">Status</th>
      <th style="width:30%;">Expected Condition</th>
      <th style="width:30%;">Observed Reason</th>
    </tr>
  </thead>
  <tbody>
    {rules_rows}
  </tbody>
</table>

<h2>10. Forensic Hypotheses</h2>
{hypotheses_html}

<h2>11. Next-Best-Evidence Action Plan</h2>
{actions_html}

<div class="footer">
  <strong>LEGAL & RESEARCH DISCLAIMER:</strong> {h(case.get('disclaimer'))}<br>
  All identities, numbers, watchlist entries, and specimens are synthetic and fictional. No operational connection to Indian Passport Seva, MHA, SSB, ICAO PKD, or INTERPOL is present or claimed.
</div>

</body>
</html>"""
