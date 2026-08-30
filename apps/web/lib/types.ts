export type EvidenceState = 'PASS' | 'FAIL' | 'SUSPICIOUS' | 'UNAVAILABLE' | 'NOT_APPLICABLE';
export type ScreeningOutcome = 'CLEAR' | 'LOW_RISK' | 'REFER' | 'HIGH_RISK' | 'INDETERMINATE';
export type DocumentFamily = 'TRAVEL_DOCUMENT' | 'VISA_OR_PERMIT' | 'NATIONAL_ID' | 'DRIVING_LICENCE';

export interface EvidenceItem {
  evidence_id: string;
  title: string;
  summary: string;
  state: EvidenceState;
  severity?: string;
  source?: Record<string, unknown>;
}

export interface EvidenceLane {
  lane_id: string;
  name: string;
  status: EvidenceState;
  summary: string;
  required: boolean;
  provider?: string | null;
  evidence_items?: EvidenceItem[];
}

export interface EvidenceCoverageLane {
  lane: string;
  state: string;
  mandatory: boolean;
}

export interface EvidenceCoverage {
  mandatory_total: number;
  mandatory_completed: number;
  coverage_ratio: number;
  missing_mandatory: string[];
  state: string;
  lanes?: EvidenceCoverageLane[];
}

export interface CaptureQualityFinding {
  check: string;
  state: string;
  measure: number | number[] | null;
  threshold: string;
  explanation: string;
}

export interface CaptureQuality {
  status: string;
  acceptable: boolean;
  findings: CaptureQualityFinding[];
  recommendation?: string | null;
  detector?: { name: string; version: string; probability: number | null };
}

export interface VisibleDocumentExtraction {
  visible_fields?: Record<string, string>;
  raw_visible_fields?: Record<string, string>;
  field_confidence?: Record<string, number>;
  missing_fields?: string[];
  uncertain_fields?: string[];
  raw_ocr_text?: string;
  ocr_metadata?: {
    backend?: string;
    engine?: string;
    psm?: number;
    dpi?: number;
    error?: string | null;
  };
}

export interface MrzAnalysis {
  mrz_detected?: boolean;
  fields?: Record<string, string>;
  checks?: Record<string, string>;
  raw_lines?: string[];
  error?: string | null;
  applicability?: string;
}

export interface DocumentRuleFinding {
  rule_id: string;
  status: string;
  observed_value: unknown;
  expected_condition: string;
  reason: string;
}

export interface CrossSourceComparison {
  field: string;
  source_a: 'VIZ';
  value_a: string | null;
  source_b: 'MRZ';
  value_b: string | null;
  status: string;
  severity: string;
  reason: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface VisualForensicFinding {
  finding_type: string;
  status: string;
  bounding_box?: BoundingBox;
  raw_measure?: Record<string, unknown>;
  explanation: string;
}

export interface VisualForensics {
  status: string;
  findings?: VisualForensicFinding[];
  suspicious_regions?: BoundingBox[];
  detector?: { name: string; version: string; kind: string; probability: number | null };
  measures?: Record<string, unknown>;
  limitations?: string[];
  reason?: string;
}

export interface BiometricVerification {
  model?: string;
  model_version?: string;
  similarity_measure?: string;
  configured_prototype_threshold?: number;
  source?: string;
  status?: string;
  decision?: string;
  reason?: string;
  similarity?: number | null;
  document_face?: BoundingBox & { detector_score?: number };
  comparison_face?: BoundingBox & { detector_score?: number };
  limitations?: string[];
}

export interface ThreatIntelligenceLookup {
  lookup_type?: string;
  query_type?: string;
  queried_synthetic_identifier?: string | null;
  source?: string;
  display_source?: string;
  result?: string;
  reason?: string;
  lookup_timestamp?: string;
}

export interface ThreatIntelligence {
  source?: string;
  display_source?: string;
  local_prototype?: boolean;
  demo_data?: boolean;
  status?: string;
  result?: string;
  reason?: string;
  lookups?: ThreatIntelligenceLookup[];
}

export interface IdentityLinkageMatch {
  case_id: string;
  identity_reference: string;
  claimed_name: string | null;
  document_number: string | null;
  similarity: number;
  finding: string;
}

export interface IdentityLinkage {
  status?: string;
  source?: string;
  reason?: string;
  matches?: IdentityLinkageMatch[];
  identity_reference?: string;
  configured_prototype_threshold?: number;
  enrolled?: boolean;
  legal_conclusion?: string | null;
}

export interface EvidenceGraphNode {
  id: string;
  type: 'CLAIM' | 'EVIDENCE';
  claim?: string;
  source?: string;
  authority_tier?: number;
  field?: string;
  normalized_value?: string | null;
  status?: string | null;
  provenance?: string;
}

export interface EvidenceGraphEdge {
  from: string;
  to: string;
  relation: 'SUPPORTS' | 'CONTRADICTS' | 'UNAVAILABLE' | 'LOW_QUALITY' | 'NOT_APPLICABLE';
}

export interface EvidenceGraph {
  nodes: EvidenceGraphNode[];
  edges: EvidenceGraphEdge[];
  authority_policy?: string;
}

export interface ForensicHypothesis {
  hypothesis: string;
  severity: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  missing_evidence: string[];
  explanation: string;
  limitations: string;
}

export interface NextBestAction {
  action: string;
  priority: number;
  reason: string;
  policy_driven: boolean;
}

export interface HardGate {
  gate: string;
  triggered: boolean;
  severity: string;
  evidence: string;
  reason: string;
}

export interface IdentityForensicAutopsy {
  scan_id: string;
  case_id?: string | null;
  created_at?: string | null;
  specimen_filename: string;
  specimen_sha256: string;
  document_type: string;
  document_family?: string | null;
  extracted_identity: Record<string, unknown>;
  evidence_lanes: EvidenceLane[];
  evidence_coverage: EvidenceCoverage;
  outcome: ScreeningOutcome;
  critical_findings: string[];
  outcome_reasons?: string[];
  visible_document_data: VisibleDocumentExtraction;
  visible_document?: VisibleDocumentExtraction;
  mrz_analysis: MrzAnalysis;
  document_rules: DocumentRuleFinding[];
  cross_source_consistency: CrossSourceComparison[];
  threat_intelligence: ThreatIntelligence;
  capture_quality?: CaptureQuality;
  visual_forensics?: VisualForensics;
  biometric_verification?: BiometricVerification;
  identity_linkage?: IdentityLinkage;
  evidence_graph?: EvidenceGraph;
  forensic_hypotheses?: ForensicHypothesis[];
  next_best_actions?: NextBestAction[];
  hard_gates?: HardGate[];
  triage_risk_index?: number | null;
  triage_risk_label?: string | null;
  audit_trail?: Array<{ timestamp: string; event: string; actor: string; outcome?: string }>;
  limitations?: string[];
  disclaimer: string;
}

export interface CaseSummaryItem {
  case_id: string;
  created_at: string;
  document_family: string;
  claimed_identity: string | null;
  document_number: string | null;
  outcome: ScreeningOutcome;
  major_findings: string[];
  coverage: EvidenceCoverage;
}

export interface CaseSummaryResponse {
  cases: CaseSummaryItem[];
  summary: {
    cases_screened: number;
    refer: number;
    high_risk: number;
    indeterminate: number;
    low_risk: number;
  };
}

export interface IdentityCluster {
  identity_reference: string;
  source: string;
  credentials: Array<{
    identity_reference: string;
    case_id: string;
    claimed_name: string | null;
    document_number: string | null;
    created_at: string;
  }>;
}

export interface SystemModuleStatus {
  module: string;
  state: 'READY' | 'DEGRADED' | 'UNAVAILABLE';
  detail: string;
}

export interface SystemStatusResponse {
  status: 'READY' | 'DEGRADED' | 'UNAVAILABLE';
  research_prototype: boolean;
  modules: SystemModuleStatus[];
}
