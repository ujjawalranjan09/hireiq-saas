import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from '../api/client';
import { useAuthStore } from '../store/auth';

interface Candidate {
  id: string;
  name: string;
  email: string;
  status: 'invited' | 'started' | 'completed' | 'expired';
  score: number | null;
  rank: number | null;
  token: string;
}

export default function InterviewDetail() {
  const { jobId, candidateId } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  React.useEffect(() => {
    const fetchCandidate = async () => {
      try {
        const response = await axios.get(`/jobs/${jobId}/candidates`);
        const found = response.data.find((c: Candidate) => c.id === candidateId);
        if (found) {
          setCandidate(found);
        } else {
          setError('Candidate not found');
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load candidate');
      } finally {
        setLoading(false);
      }
    };
    fetchCandidate();
  }, [jobId, candidateId]);

  const handleDownloadReport = async () => {
    if (!candidate?.token) return;
    try {
      const response = await axios.get(`/candidates/${candidate.token}/report`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `interview-report-${candidate.name}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      alert('Failed to download report: ' + (err.response?.data?.detail || 'Unknown error'));
    }
  };

  if (loading) return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  if (error) return <div className="text-red-600 p-4">{error}</div>;
  if (!candidate) return <div className="text-gray-600 p-4">Candidate not found</div>;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'started': return 'bg-blue-100 text-blue-800';
      case 'invited': return 'bg-yellow-100 text-yellow-800';
      case 'expired': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getMedalIcon = (rank: number | null) => {
    if (!rank) return '';
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <button onClick={() => navigate(-1)} className="mb-4 text-blue-600 hover:underline">← Back</button>
      
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h1 className="text-2xl font-bold mb-4">Candidate Details</h1>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-gray-600">Name</p>
            <p className="font-semibold">{candidate.name}</p>
          </div>
          <div>
            <p className="text-gray-600">Email</p>
            <p className="font-semibold">{candidate.email}</p>
          </div>
          <div>
            <p className="text-gray-600">Status</p>
            <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(candidate.status)}`}>
              {candidate.status}
            </span>
          </div>
          <div>
            <p className="text-gray-600">Rank</p>
            <p className="font-semibold text-xl">{getMedalIcon(candidate.rank)}</p>
          </div>
          <div className="col-span-2">
            <p className="text-gray-600">Score</p>
            <div className="w-full bg-gray-200 rounded-full h-4 mt-2">
              <div 
                className="bg-blue-600 h-4 rounded-full transition-all"
                style={{ width: `${candidate.score || 0}%` }}
              ></div>
            </div>
            <p className="text-right mt-1">{candidate.score || 'N/A'}%</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">Skill Assessment</h2>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">Radar chart showing skill scores across dimensions</p>
          {/* Plotly radar chart would be rendered here */}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">Emotion Timeline</h2>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">Line chart showing confidence score per question</p>
          {/* Plotly line chart would be rendered here */}
        </div>
      </div>

      <div className="flex justify-end">
        <button 
          onClick={handleDownloadReport}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          Download PDF Report
        </button>
      </div>
    </div>
  );
}
