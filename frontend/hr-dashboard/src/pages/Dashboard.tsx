import { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import Plot from 'react-plotly.js';

interface DashboardStats {
  total_jobs: number;
  total_candidates: number;
  average_score: number;
  completion_rate: number;
  jobs: Array<{
    job_id: string;
    title: string;
    average_score: number;
    candidate_count: number;
  }>;
}

export const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await apiClient.get('/analytics/dashboard');
        setStats(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) return <div style={styles.loading}>Loading...</div>;
  if (error) return <div style={styles.error}>{error}</div>;
  if (!stats) return null;

  const chartData = [{
    x: stats.jobs.map(j => j.title),
    y: stats.jobs.map(j => j.average_score || 0),
    type: 'bar' as const,
    marker: { color: '#007bff' },
  }];

  const chartLayout = {
    title: 'Average Candidate Score by Job',
    xaxis: { title: 'Job Title' },
    yaxis: { title: 'Average Score', range: [0, 100] },
    margin: { t: 50, b: 100, l: 60, r: 20 },
  };

  return (
    <div style={styles.container}>
      <h1>Dashboard</h1>
      
      <div style={styles.cards}>
        <div style={styles.card}>
          <h3>Total Jobs</h3>
          <p style={styles.number}>{stats.total_jobs}</p>
        </div>
        <div style={styles.card}>
          <h3>Total Candidates</h3>
          <p style={styles.number}>{stats.total_candidates}</p>
        </div>
        <div style={styles.card}>
          <h3>Average Score</h3>
          <p style={styles.number}>{stats.average_score?.toFixed(1) || 'N/A'}</p>
        </div>
        <div style={styles.card}>
          <h3>Completion Rate</h3>
          <p style={styles.number}>{stats.completion_rate?.toFixed(1) || 'N/A'}%</p>
        </div>
      </div>

      <div style={styles.chart}>
        <Plot data={chartData} layout={chartLayout} useResizeHandler style={{ width: '100%', height: '400px' }} />
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: { padding: '20px' },
  cards: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '30px',
  },
  card: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    textAlign: 'center',
  },
  number: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#007bff',
    margin: '10px 0 0 0',
  },
  chart: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  loading: { textAlign: 'center', padding: '40px' },
  error: { color: '#c62828', padding: '20px', textAlign: 'center' },
};
