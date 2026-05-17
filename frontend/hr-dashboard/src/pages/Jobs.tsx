import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';

interface Job {
  id: string;
  title: string;
  status: string;
  candidate_count: number;
  avg_score: number | null;
}

export const JobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await apiClient.get('/jobs/');
      setJobs(response.data);
    } catch (err: any) {
      console.error('Failed to fetch jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleArchive = async (jobId: string) => {
    if (confirm('Are you sure you want to archive this job?')) {
      try {
        await apiClient.delete(`/jobs/${jobId}/archive`);
        fetchJobs();
      } catch (err: any) {
        alert('Failed to archive job');
      }
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1>Jobs</h1>
        <button style={styles.createButton} onClick={() => setShowModal(true)}>
          Create New Job
        </button>
      </div>
      <table style={styles.table}>
        <thead>
          <tr>
            <th>Title</th>
            <th>Status</th>
            <th>Candidates</th>
            <th>Avg Score</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>{job.title}</td>
              <td>
                <span style={{
                  ...styles.badge,
                  backgroundColor: job.status === 'active' ? '#28a745' : '#6c757d'
                }}>
                  {job.status}
                </span>
              </td>
              <td>{job.candidate_count}</td>
              <td>{job.avg_score?.toFixed(1) || 'N/A'}</td>
              <td>
                <button 
                  style={styles.actionButton}
                  onClick={() => navigate(`/jobs/${job.id}`)}
                >
                  View
                </button>
                {job.status === 'active' && (
                  <button 
                    style={{...styles.actionButton, backgroundColor: '#dc3545'}}
                    onClick={() => handleArchive(job.id)}
                  >
                    Archive
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {showModal && <CreateJobModal onClose={() => setShowModal(false)} onCreated={fetchJobs} />}
    </div>
  );
};

const CreateJobModal: React.FC<{ onClose: () => void; onCreated: () => void }> = ({ onClose, onCreated }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    skills: [] as string[],
    min_experience: 0,
    difficulty: 'medium',
    questions_count: 10,
  });
  const [skillInput, setSkillInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAddSkill = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && skillInput.trim()) {
      e.preventDefault();
      setFormData(prev => ({
        ...prev,
        skills: [...prev.skills, skillInput.trim()]
      }));
      setSkillInput('');
    }
  };

  const removeSkill = (skill: string) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.filter(s => s !== skill)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiClient.post('/jobs/', formData);
      onCreated();
      onClose();
    } catch (err: any) {
      alert('Failed to create job: ' + (err.response?.data?.detail || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.modalOverlay}>
      <div style={styles.modal}>
        <h2>Create New Job</h2>
        <form onSubmit={handleSubmit}>
          <div style={styles.formGroup}>
            <label>Job Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              required
              style={styles.input}
            />
          </div>
          <div style={styles.formGroup}>
            <label>Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              style={{ ...styles.input, minHeight: '100px' }}
            />
          </div>
          <div style={styles.formGroup}>
            <label>Required Skills (press Enter to add)</label>
            <input
              type="text"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={handleAddSkill}
              style={styles.input}
              placeholder="Type a skill and press Enter"
            />
            <div style={styles.skillsContainer}>
              {formData.skills.map(skill => (
                <span key={skill} style={styles.skillChip}>
                  {skill}
                  <button type="button" onClick={() => removeSkill(skill)}>×</button>
                </span>
              ))}
            </div>
          </div>
          <div style={styles.formRow}>
            <div style={styles.formGroup}>
              <label>Min Experience (years)</label>
              <input
                type="number"
                value={formData.min_experience}
                onChange={(e) => setFormData(prev => ({ ...prev, min_experience: parseInt(e.target.value) || 0 }))}
                style={styles.input}
              />
            </div>
            <div style={styles.formGroup}>
              <label>Difficulty</label>
              <select
                value={formData.difficulty}
                onChange={(e) => setFormData(prev => ({ ...prev, difficulty: e.target.value }))}
                style={styles.input}
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            <div style={styles.formGroup}>
              <label>Questions Count</label>
              <input
                type="number"
                value={formData.questions_count}
                onChange={(e) => setFormData(prev => ({ ...prev, questions_count: parseInt(e.target.value) || 10 }))}
                style={styles.input}
              />
            </div>
          </div>
          <div style={styles.modalActions}>
            <button type="button" onClick={onClose} style={styles.cancelButton}>Cancel</button>
            <button type="submit" disabled={loading} style={styles.submitButton}>
              {loading ? 'Creating...' : 'Create Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: { padding: '2rem' },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  createButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: 'white',
  },
  badge: {
    padding: '0.25rem 0.75rem',
    borderRadius: '12px',
    color: 'white',
    fontSize: '0.875rem',
  },
  actionButton: {
    padding: '0.5rem 1rem',
    marginRight: '0.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    width: '100%',
    maxWidth: '600px',
    maxHeight: '90vh',
    overflow: 'auto',
  },
  formGroup: { marginBottom: '1rem' },
  formRow: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' },
  input: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    marginTop: '0.25rem',
  },
  skillsContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    marginTop: '0.5rem',
  },
  skillChip: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#e0e0e0',
    borderRadius: '16px',
    fontSize: '0.875rem',
  },
  modalActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '1rem',
    marginTop: '1.5rem',
  },
  cancelButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  submitButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
};
