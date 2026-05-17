import apiClient from './client';

export interface JobFormData {
  title: string;
  description?: string;
  skills: string[];
  min_experience: number;
  difficulty: 'easy' | 'medium' | 'hard';
  questions_count: number;
}

export interface Job {
  id: string;
  title: string;
  status: string;
  candidate_count: number;
  avg_score: number | null;
  description?: string;
  skills?: string[];
  min_experience?: number;
  difficulty?: string;
  questions_count?: number;
}

export const getJobs = () => {
  return apiClient.get<Job[]>('/jobs/');
};

export const getJob = (jobId: string) => {
  return apiClient.get<Job>(`/jobs/${jobId}`);
};

export const createJob = (data: JobFormData) => {
  return apiClient.post<Job>('/jobs/', data);
};

export const archiveJob = (jobId: string) => {
  return apiClient.delete(`/jobs/${jobId}/archive`);
};

export const getCandidates = (jobId: string) => {
  return apiClient.get(`/jobs/${jobId}/candidates`);
};

export const inviteCandidates = (jobId: string, emails: string[]) => {
  return apiClient.post(`/jobs/${jobId}/invite`, { emails });
};
