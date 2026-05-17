import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from './api/client';

interface JobInfo {
  job_title: string;
  company_name: string;
}

export const Welcome = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [jobInfo, setJobInfo] = useState<JobInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [permissionGranted, setPermissionGranted] = useState(false);

  useEffect(() => {
    const validateToken = async () => {
      try {
        const response = await apiClient.get(`/candidates/${token}/validate`);
        setJobInfo(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Invalid or expired invite token');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      validateToken();
    }
  }, [token]);

  const requestPermissions = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setPermissionGranted(true);
      alert('Camera and microphone permissions granted!');
    } catch (err) {
      alert('Please grant camera and microphone permissions to continue.');
    }
  };

  const beginInterview = async () => {
    try {
      const response = await apiClient.post(`/candidates/${token}/start`);
      navigate(`/interview/${token}/session`);
    } catch (err: any) {
      alert('Failed to start interview: ' + (err.response?.data?.detail || 'Unknown error'));
    }
  };

  if (loading) return <div style={styles.loading}>Loading...</div>;
  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.errorBox}>
          <h1>Interview Not Available</h1>
          <p>{error}</p>
          <p>Please contact the hiring team for assistance.</p>
        </div>
      </div>
    );
  }
  if (!jobInfo) return null;

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1>Welcome to Your Interview</h1>
        <h2>{jobInfo.job_title}</h2>
        <p style={styles.company}>{jobInfo.company_name}</p>
        
        <div style={styles.info}>
          <p>This interview will assess your skills and experience for the position.</p>
          <p>Please ensure you are in a quiet environment with good lighting.</p>
        </div>

        <div style={styles.permissions}>
          <button 
            onClick={requestPermissions}
            style={{...styles.button, backgroundColor: permissionGranted ? '#4caf50' : '#ff9800'}}
          >
            {permissionGranted ? '✓ Permissions Granted' : 'Request Camera & Microphone Permission'}
          </button>
        </div>

        <button 
          onClick={beginInterview}
          disabled={!permissionGranted}
          style={{
            ...styles.button,
            ...styles.primaryButton,
            opacity: permissionGranted ? 1 : 0.5,
            cursor: permissionGranted ? 'pointer' : 'not-allowed'
          }}
        >
          Begin Interview
        </button>
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
  company: {
    color: '#666',
    fontSize: '18px',
    marginBottom: '30px',
  },
  info: {
    backgroundColor: '#e3f2fd',
    padding: '20px',
    borderRadius: '8px',
    marginBottom: '20px',
    textAlign: 'left',
  },
  permissions: {
    marginBottom: '20px',
  },
  button: {
    padding: '14px 28px',
    fontSize: '16px',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    margin: '10px',
    transition: 'all 0.3s',
  },
  primaryButton: {
    backgroundColor: '#007bff',
    color: 'white',
  },
  loading: { textAlign: 'center', padding: '40px', fontSize: '18px' },
  errorBox: {
    backgroundColor: 'white',
    padding: '40px',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
    maxWidth: '500px',
    textAlign: 'center',
  },
};
