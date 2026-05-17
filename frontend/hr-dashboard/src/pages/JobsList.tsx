import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';

interface Job {
  id: string;
  title: string;
  description: string;
  status: 'active' | 'archived';
  candidate_count: number;
  average_score: number | null;
  created_at: string;
}

export const JobsList = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
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
      setError(err.response?.data?.detail || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleArchive = async (jobId: string) => {
    if (!confirm('Are you sure you want to archive this job?')) return;
    try {
      await apiClient.delete(`/jobs/${jobId}/archive`);
      fetchJobs();
    } catch (err: any) {
      alert('Failed to archive job');
    }
  };

  if (loading) return <div style={styles.loading}>Loading...</div>;
  if (error) return <div style={styles.error}>{error}</div>;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1>Jobs</h1>
        <button style={styles.createButton} onClick={() => setShowModal(true)}>
          + Create New Job
        </button>
      </div>

      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Title</th>
            <th style={styles.th}>Status</th>
            <th style={styles.th}>Candidates</th>
            <th style={styles.th}>Avg Score</th>
            <th style={styles.th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td style={styles.td}>{job.title}</td>
              <td style={styles.td}>
                <span style={{
                  ...styles.badge,
                  backgroundColor: job.status === 'active' ? '#4caf50' : '#9e9e9e'
                }}>
                  {job.status}
                </span>
              </td>
              <td style={styles.td}>{job.candidate_count}</td>
              <td style={styles.td}>{job.average_score?.toFixed(1) || 'N/A'}</td>
              <td style={styles.td}>
                <button 
                  style={styles.actionButton}
                  onClick={() => navigate(`/jobs/${job.id}`)}
                >
                  View
                </button>
                {job.status === 'active' && (
                  <button 
                    style={{...styles.actionButton, backgroundColor: '#f44336'}}
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

      {showModal && (
        <CreateJobModal 
          onClose={() => setShowModal(false)} 
          onCreated={() => {
            setShowModal(false);
            fetchJobs();
          }} 
        />
      )}
    </div>
  );
};

interface CreateJobModalProps {
  onClose: () => void;
  onCreated: () => void;
}

const CreateJobModal = ({ onClose, onCreated }: CreateJobModalProps) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState('');
  const [minExperience, setMinExperience] = useState(0);
  const [difficulty, setDifficulty] = useState('medium');
  const [questionsCount, setQuestionsCount] = useState(10);
  const [loading, setLoading] = useState(false);

  const handleAddSkill = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && skillInput.trim()) {
      e.preventDefault();
      if (!skills.includes(skillInput.trim())) {
        setSkills([...skills, skillInput.trim()]);
      }
      setSkillInput('');
    }
  };

  const removeSkill = (skill: string) => {
    setSkills(skills.filter(s => s !== skill));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiClient.post('/jobs/', {
        title,
        description,
        required_skills: skills,
        min_years_experience: minExperience,
        difficulty_level: difficulty,
        questions_count: questionsCount,
      });
      onCreated();
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
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{...styles.input, minHeight: '100px'}}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Required Skills (press Enter to add)</label>
            <input
              type="text"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={handleAddSkill}
              placeholder="Type a skill and press Enter"
              style={styles.input}
            />
            <div style={styles.skillsContainer}>
              {skills.map((skill) => (
                <span key={skill} style={styles.skillChip}>
                  {skill}
                  <button type="button" onClick={() => removeSkill(skill)} style={styles.removeSkill}>×</button>
                </span>
              ))}
            </div>
          </div>

          <div style={styles.formGroup}>
            <label>Min Years Experience</label>
            <input
              type="number"
              value={minExperience}
              onChange={(e) => setMinExperience(Number(e.target.value))}
              min="0"
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Difficulty Level</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              style={styles.input}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          <div style={styles.formGroup}>
            <label>Number of Questions</label>
            <input
              type="number"
              value={questionsCount}
              onChange={(e) => setQuestionsCount(Number(e.target.value))}
              min="1"
              max="20"
              style={styles.input}
            />
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
  container: { padding: '20px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  createButton: { backgroundColor: '#007bff', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '4px', cursor: 'pointer' },
  table: { width: '100%', borderCollapse: 'collapse', backgroundColor: 'white' },
  th: { textAlign: 'left', padding: '12px', borderBottom: '2px solid #ddd' },
  td: { padding: '12px', borderBottom: '1px solid #eee' },
  badge: { padding: '4px 8px', borderRadius: '4px', color: 'white', fontSize: '12px' },
  actionButton: { backgroundColor: '#007bff', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', marginRight: '8px' },
  loading: { textAlign: 'center', padding: '40px' },
  error: { color: '#c62828', padding: '20px', textAlign: 'center' },
  modalOverlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 },
  modal: { backgroundColor: 'white', padding: '30px', borderRadius: '8px', width: '100%', maxWidth: '500px', maxHeight: '90vh', overflow: 'auto' },
  formGroup: { marginBottom: '16px' },
  input: { width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px', marginTop: '4px', boxSizing: 'border-box' },
  skillsContainer: { display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' },
  skillChip: { backgroundColor: '#e3f2fd', padding: '4px 8px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '4px' },
  removeSkill: { background: 'none', border: 'none', cursor: 'pointer', padding: '0', fontSize: '16px' },
  modalActions: { display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' },
  cancelButton: { padding: '10px 20px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', backgroundColor: 'white' },
  submitButton: { padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' },
};
