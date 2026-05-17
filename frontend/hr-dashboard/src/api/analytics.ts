import apiClient from './client';

export interface DashboardStats {
  total_jobs: number;
  total_candidates: number;
  avg_score: number | null;
  completion_rate: number;
  jobs: Array<{
    id: string;
    title: string;
    candidate_count: number;
    avg_score: number | null;
  }>;
}

export interface JobAnalytics {
  min_score: number | null;
  max_score: number | null;
  median_score: number | null;
  percentile_25: number | null;
  percentile_75: number | null;
  percentile_90: number | null;
}

export const getDashboardStats = () => {
  return apiClient.get<DashboardStats>('/analytics/dashboard');
};

export const getJobAnalytics = (jobId: string) => {
  return apiClient.get<JobAnalytics>(`/analytics/jobs/${jobId}`);
};
