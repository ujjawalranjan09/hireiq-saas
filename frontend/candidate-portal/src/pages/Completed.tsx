import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from './api/client';

export const Completed = () => {
  const { token } = useParams<{ token: string }>();
  const [reportReady, setReportReady] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkReport = async () => {
      try {
        await apiClient.get(`/candidates/${token}/report`, { responseType: 'blob' });
        setReportReady(true);
      } catch (err) {
        setReportReady(false);
      } finally {
        setLoading(false);
      }
    };

    checkReport();
  }, [token]);

  const downloadReport = async () => {
    try {
      const response = await apiClient.get(`/candidates/${token}/report`, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `interview-report-${token}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download report. Please try again later.');
    }
  };

  if (loading) return <div style={styles.loading}>Loading...</div>;

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Thank You!</h1>
        <p style={styles.message}>
          Your interview has been completed successfully. Our HR team will review your responses and be in touch soon.
        </p>
        
        {reportReady && (
          <button onClick={downloadReport} style={styles.button}>
            Download Your Report
          </button>
        )}
        
        {!reportReady && (
          <p style={styles.note}>
            Your detailed report will be available for download shortly. Please check back later.
          </p>
        )}
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
    maxWidth: '500px',
    width: '100%',
    textAlign: 'center',
  },
  title: {
    color: '#4caf50',
    marginBottom: '20px',
  },
  message: {
    fontSize: '16px',
    lineHeight: '1.6',
    marginBottom: '30px',
  },
  button: {
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    padding: '14px 28px',
    fontSize: '16px',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  note: {
    color: '#666',
    fontStyle: 'italic',
  },
  loading: { textAlign: 'center', padding: '40px', fontSize: '18px' },
};
