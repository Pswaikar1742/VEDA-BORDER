import { IdentityForensicAutopsy } from './types';

export const readable = (value: string) => value.replace(/_/g, ' ').toLowerCase();
export const fieldName = (value: string) => ({holder_name: 'Name', document_number: 'Document number', date_of_birth: 'Date of birth', expiry_date: 'Expiry date', nationality: 'Nationality', sex: 'Sex'}[value] || readable(value));
export const stateLabel = (value?: string) => ({PASS: 'Check complete', FAIL: 'Issue found', SUSPICIOUS: 'Needs inspection', UNAVAILABLE: 'Could not check', NOT_APPLICABLE: 'Not needed'}[value || ''] || 'Could not check');

export function officerSummary(report: IdentityForensicAutopsy) {
  const issues: { title: string; detail: string }[] = [];
  const quality = report.capture_quality;
  if (quality?.acceptable === false) issues.push({title: 'Please take a clearer document image', detail: 'The image could not be checked reliably. Keep the whole document in view, use even lighting and hold the camera steady.'});
  for (const item of report.cross_source_consistency || []) {
    if (item.status === 'FAIL') issues.push({title: `${fieldName(item.field)} does not agree`, detail: `Printed text: ${item.value_a || 'unreadable'}. Machine-readable text: ${item.value_b || 'unreadable'}. Re-read this field; an OCR error can also cause a disagreement.`});
  }
  for (const rule of report.document_rules || []) {
    if (rule.status === 'FAIL') issues.push({title: rule.rule_id === 'date.expiry.current' ? 'The document has expired' : 'A document check failed', detail: rule.reason});
  }
  if (report.biometric_verification?.status === 'FAIL') issues.push({title: 'The two face images do not match closely enough', detail: 'Repeat the comparison with good lighting and a clear, forward-facing image. This result alone does not prove impersonation.'});
  if (report.threat_intelligence?.status === 'FAIL') issues.push({title: 'Match on the local research watchlist', detail: 'A submitted identifier matches a synthetic test record. This is not a government watchlist result.'});
  if (report.visual_forensics?.status === 'SUSPICIOUS') issues.push({title: 'Some image regions need closer inspection', detail: 'The highlighted areas have unusual image patterns. Compression, repeated designs or capture conditions can also cause these findings.'});
  if (report.identity_linkage?.status === 'SUSPICIOUS') issues.push({title: 'A similar face appears with different identity details', detail: 'Compare the linked cases in Developer Mode before drawing an identity conclusion.'});
  const incomplete = report.evidence_coverage.evidence_sufficient === false || report.evidence_coverage.state !== 'COMPLETE' || report.evidence_lanes.some(l => l.required && l.status === 'UNAVAILABLE') || (report.module_statuses || []).some(l => l.status === 'UNAVAILABLE' && ['ocr_viz','mrz','consistency','document_rules','visual_forensics'].includes(l.module));
  const conflictingLow = ['LOW_RISK', 'CLEAR'].includes(report.outcome) && (issues.length > 0 || incomplete);
  const titles: Record<string, string> = {LOW_RISK: 'Low screening risk', CLEAR: 'Low screening risk', REFER: 'Further inspection needed', HIGH_RISK: 'Serious concerns found', INDETERMINATE: 'Not enough evidence to assess'};
  return {
    issues, incomplete, conflictingLow,
    title: conflictingLow ? 'Result needs manual review' : titles[report.outcome] || 'Result needs manual review',
    score: incomplete || conflictingLow || report.outcome === 'INDETERMINATE' ? null : report.triage_risk_index,
    action: quality?.acceptable === false ? 'Recapture the document' : incomplete ? 'Complete the missing checks before relying on this result' : conflictingLow || report.outcome === 'HIGH_RISK' || report.outcome === 'REFER' ? 'Refer for a closer human inspection' : 'Review the completed checks and follow your screening procedure',
  };
}
