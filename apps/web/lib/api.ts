import {
  CaseSummaryResponse,
  IdentityCluster,
  IdentityForensicAutopsy,
  SystemStatusResponse,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function createScreening(
  file: File | Blob,
  filename: string,
  selfie?: File | Blob | null,
  selfieFilename?: string,
  documentFamily?: string
): Promise<IdentityForensicAutopsy> {
  const formData = new FormData();
  formData.append('file', file, filename);
  if (selfie) {
    formData.append('selfie', selfie, selfieFilename || 'selfie.png');
  }
  if (documentFamily) {
    formData.append('document_family', documentFamily);
  }

  const response = await fetch(`${API_BASE}/api/v1/screenings`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = 'Screening request failed';
    try {
      const err = await response.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function fetchCases(limit: number = 50): Promise<CaseSummaryResponse> {
  const response = await fetch(`${API_BASE}/api/v1/cases?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch cases');
  }
  return response.json();
}

export async function fetchCase(caseId: string): Promise<IdentityForensicAutopsy> {
  const response = await fetch(`${API_BASE}/api/v1/cases/${encodeURIComponent(caseId)}`);
  if (!response.ok) {
    throw new Error('Failed to fetch case details');
  }
  return response.json();
}

export async function fetchIdentityLinkage(): Promise<{ source: string; clusters: IdentityCluster[] }> {
  const response = await fetch(`${API_BASE}/api/v1/identity-linkage`);
  if (!response.ok) {
    throw new Error('Failed to fetch identity linkage');
  }
  return response.json();
}

export async function fetchSystemStatus(): Promise<SystemStatusResponse> {
  const response = await fetch(`${API_BASE}/api/v1/system/status`);
  if (!response.ok) {
    throw new Error('Failed to fetch system status');
  }
  return response.json();
}

export function getReportHtmlUrl(caseId: string): string {
  return `${API_BASE}/api/v1/cases/${encodeURIComponent(caseId)}/report.html`;
}

export function getReportJsonUrl(caseId: string): string {
  return `${API_BASE}/api/v1/cases/${encodeURIComponent(caseId)}/report.json`;
}
