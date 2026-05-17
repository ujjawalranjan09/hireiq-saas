import apiClient from './client';

export interface Candidate {
  id: string;
  name: string;
  email: string;
  status: 'invited' | 'started' | 'completed' | 'expired';
  score: number | null;
  rank: number | null;
  token: string;
}

export const getCandidateStatus = (token: string) => {
  return apiClient.get<{ status: string; score: number | null }>(`/candidates/${token}/status`);
};

export const getCandidateReport = async (token: string) => {
  const response = await apiClient.get(`/candidates/${token}/report`, {
    responseType: 'blob',
  });
  return response.data;
};

export const downloadCandidateReport = (token: string, filename: string = 'report.pdf') => {
  getCandidateReport(token).then((blob) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }).catch((err) => {
    console.error('Failed to download report:', err);
    alert('Failed to download report');
  });
};
