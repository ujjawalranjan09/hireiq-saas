import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from './api/client';

interface InterviewStatus {
  status: string;
  overall_score: number | null;
}

export const Interview = () => {
  const { token } = useParams<{ token: string }>();
  const [status, setStatus] = useState<InterviewStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const response = await apiClient.get(`/candidates/${token}/status`);
        setStatus(response.data);
        
        if (response.data.status === 'completed') {
          setTimeout(() => {
            window.location.href = `/interview/${token}/completed`;
          }, 2000);
        }
      } catch (err) {
        console.error('Failed to fetch status');
      } finally {
        setLoading(false);
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 10000);
    return () => clearInterval(interval);
  }, [token]);

  if (loading) return <div style={styles.loading}>Loading interview...</div>;
  if (!status) return null;

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1>Interview in Progress</h1>
        <p>Please wait while the AI interviewer conducts your session.</p>
        
        <div style={styles.statusBox}>
          <p><strong>Status:</strong> {status.status}</p>
          {status.overall_score !== null && (
            <p><strong>Score:</strong> {status.overall_score}</p>
          )}
        </div>

        <div style={styles.placeholder}>
          <p>The interview interface will appear here once the session is fully initialized.</p>
          <p>You will see a video panel and chat interface for answering questions.</p>
        </div>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '20px',
  },
  card: {
    backgroundColor: 'white',
    padding: '40px',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
    maxWidth: '600px',
    width: '100%',
    textAlign: 'center',
  },
  statusBox: {
    backgroundColor: '#e3f2fd',
    padding: '20px',
    borderRadius: '8px',
    margin: '20px 0',
  },
  placeholder: {
    backgroundColor: '#f9f9f9',
    padding: '30px',
    borderRadius: '8px',
    border: '2px dashed #ddd',
  },
  loading: { textAlign: 'center', padding: '40px', fontSize: '18px' },
};
