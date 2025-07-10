import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set up axios defaults
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Auth Context
const AuthContext = React.createContext();

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/me`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/login`, { email, password });
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/register`, userData);
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Navigation Component
const Navigation = () => {
  const { user, logout } = React.useContext(AuthContext);

  return (
    <nav className="bg-blue-600 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold">Job Portal</h1>
        <div className="space-x-4">
          {user ? (
            <>
              <span>Welcome, {user.full_name}</span>
              <button onClick={logout} className="bg-red-500 px-4 py-2 rounded hover:bg-red-600">
                Logout
              </button>
            </>
          ) : (
            <span>Please log in</span>
          )}
        </div>
      </div>
    </nav>
  );
};

// Login Component
const Login = () => {
  const { login } = React.useContext(AuthContext);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await login(formData.email, formData.password);
    if (!result.success) {
      setError(result.error);
    }
  };

  if (showRegister) {
    return <Register onBack={() => setShowRegister(false)} />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Job Portal
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && <div className="text-red-500 text-center">{error}</div>}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <input
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
          </div>
          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Sign in
            </button>
          </div>
          <div className="text-center">
            <button
              type="button"
              onClick={() => setShowRegister(true)}
              className="font-medium text-indigo-600 hover:text-indigo-500"
            >
              Don't have an account? Sign up
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Register Component
const Register = ({ onBack }) => {
  const { register } = React.useContext(AuthContext);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'candidate',
    company_name: '',
    phone: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await register(formData);
    if (!result.success) {
      setError(result.error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create Account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && <div className="text-red-500 text-center">{error}</div>}
          <div className="space-y-4">
            <input
              type="text"
              required
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              placeholder="Full Name"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            />
            <input
              type="email"
              required
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              placeholder="Email address"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <input
              type="password"
              required
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
            <input
              type="tel"
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              placeholder="Phone Number"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
            <select
              className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            >
              <option value="candidate">Job Seeker</option>
              <option value="employer">Employer</option>
            </select>
            {formData.role === 'employer' && (
              <input
                type="text"
                required
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Company Name"
                value={formData.company_name}
                onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
              />
            )}
          </div>
          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Create Account
            </button>
          </div>
          <div className="text-center">
            <button
              type="button"
              onClick={onBack}
              className="font-medium text-indigo-600 hover:text-indigo-500"
            >
              Already have an account? Sign in
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user } = React.useContext(AuthContext);

  if (user.role === 'candidate') {
    return <CandidateDashboard />;
  } else if (user.role === 'employer') {
    return <EmployerDashboard />;
  } else {
    return <AdminDashboard />;
  }
};

// Candidate Dashboard
const CandidateDashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [applications, setApplications] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showApplicationModal, setShowApplicationModal] = useState(false);

  useEffect(() => {
    fetchJobs();
    fetchResumes();
    fetchApplications();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API}/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const fetchResumes = async () => {
    try {
      const response = await axios.get(`${API}/resumes`);
      setResumes(response.data);
    } catch (error) {
      console.error('Error fetching resumes:', error);
    }
  };

  const fetchApplications = async () => {
    try {
      const response = await axios.get(`${API}/applications`);
      setApplications(response.data);
    } catch (error) {
      console.error('Error fetching applications:', error);
    }
  };

  const handleUploadResume = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      await axios.post(`${API}/resumes/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchResumes();
      setShowUploadModal(false);
    } catch (error) {
      console.error('Error uploading resume:', error);
    }
  };

  const handleApplyToJob = async (jobId, resumeId, coverLetter) => {
    try {
      await axios.post(`${API}/applications`, {
        job_id: jobId,
        resume_id: resumeId,
        cover_letter: coverLetter
      });
      fetchApplications();
      setShowApplicationModal(false);
    } catch (error) {
      console.error('Error applying to job:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Job Listings */}
        <div className="lg:col-span-2">
          <h2 className="text-2xl font-bold mb-4">Available Jobs</h2>
          <div className="space-y-4">
            {jobs.map(job => (
              <div key={job.id} className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-xl font-semibold text-blue-600">{job.title}</h3>
                <p className="text-gray-600">{job.company} • {job.location}</p>
                {job.salary_min && job.salary_max && (
                  <p className="text-green-600 font-semibold">
                    ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}
                  </p>
                )}
                <p className="text-gray-800 mt-2">{job.description}</p>
                <div className="mt-4 flex space-x-2">
                  <button
                    onClick={() => {
                      setSelectedJob(job);
                      setShowApplicationModal(true);
                    }}
                    className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                  >
                    Apply Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Resume Section */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">My Resumes</h3>
            <button
              onClick={() => setShowUploadModal(true)}
              className="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600 mb-4"
            >
              Upload Resume
            </button>
            <div className="space-y-2">
              {resumes.map(resume => (
                <div key={resume.id} className="p-2 bg-gray-50 rounded">
                  <p className="text-sm font-medium">{resume.filename}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(resume.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Applications Section */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">My Applications</h3>
            <div className="space-y-2">
              {applications.map(app => (
                <div key={app.id} className="p-2 bg-gray-50 rounded">
                  <p className="text-sm font-medium">Applied to Job</p>
                  <p className="text-xs text-gray-500">
                    Status: <span className="font-medium">{app.status}</span>
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(app.applied_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onUpload={handleUploadResume}
        />
      )}

      {/* Application Modal */}
      {showApplicationModal && selectedJob && (
        <ApplicationModal
          job={selectedJob}
          resumes={resumes}
          onClose={() => setShowApplicationModal(false)}
          onSubmit={handleApplyToJob}
        />
      )}
    </div>
  );
};

// Employer Dashboard
const EmployerDashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [showJobModal, setShowJobModal] = useState(false);

  useEffect(() => {
    fetchJobs();
    fetchApplications();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API}/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const fetchApplications = async () => {
    try {
      const response = await axios.get(`${API}/applications`);
      setApplications(response.data);
    } catch (error) {
      console.error('Error fetching applications:', error);
    }
  };

  const handleCreateJob = async (jobData) => {
    try {
      await axios.post(`${API}/jobs`, jobData);
      fetchJobs();
      setShowJobModal(false);
    } catch (error) {
      console.error('Error creating job:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Jobs Section */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">My Job Postings</h2>
            <button
              onClick={() => setShowJobModal(true)}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Post New Job
            </button>
          </div>
          <div className="space-y-4">
            {jobs.map(job => (
              <div key={job.id} className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-xl font-semibold">{job.title}</h3>
                <p className="text-gray-600">{job.company} • {job.location}</p>
                <p className="text-gray-800 mt-2">{job.description}</p>
                <div className="mt-4 flex space-x-2">
                  <button className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600">
                    Edit
                  </button>
                  <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Applications Section */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Applications</h2>
          <div className="space-y-4">
            {applications.map(app => (
              <div key={app.id} className="bg-white p-6 rounded-lg shadow-md">
                <p className="font-semibold">Application for Job ID: {app.job_id}</p>
                <p className="text-gray-600">Status: {app.status}</p>
                <p className="text-gray-600">
                  Applied: {new Date(app.applied_at).toLocaleDateString()}
                </p>
                <div className="mt-4 flex space-x-2">
                  <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                    Accept
                  </button>
                  <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Job Modal */}
      {showJobModal && (
        <JobModal
          onClose={() => setShowJobModal(false)}
          onSubmit={handleCreateJob}
        />
      )}
    </div>
  );
};

// Admin Dashboard
const AdminDashboard = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold mb-4">Admin Dashboard</h2>
      <p>Admin features coming soon...</p>
    </div>
  );
};

// Modal Components
const UploadModal = ({ onClose, onUpload }) => {
  const [file, setFile] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg max-w-md w-full">
        <h3 className="text-lg font-semibold mb-4">Upload Resume</h3>
        <form onSubmit={handleSubmit}>
          <input
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full mb-4"
            required
          />
          <div className="flex space-x-4">
            <button
              type="submit"
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Upload
            </button>
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const ApplicationModal = ({ job, resumes, onClose, onSubmit }) => {
  const [selectedResume, setSelectedResume] = useState('');
  const [coverLetter, setCoverLetter] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedResume) {
      onSubmit(job.id, selectedResume, coverLetter);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg max-w-md w-full">
        <h3 className="text-lg font-semibold mb-4">Apply for {job.title}</h3>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Resume
            </label>
            <select
              value={selectedResume}
              onChange={(e) => setSelectedResume(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            >
              <option value="">Choose a resume</option>
              {resumes.map(resume => (
                <option key={resume.id} value={resume.id}>
                  {resume.filename}
                </option>
              ))}
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cover Letter (Optional)
            </label>
            <textarea
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              rows="4"
              placeholder="Write your cover letter here..."
            />
          </div>
          <div className="flex space-x-4">
            <button
              type="submit"
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Apply
            </button>
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const JobModal = ({ onClose, onSubmit }) => {
  const [jobData, setJobData] = useState({
    title: '',
    company: '',
    location: '',
    salary_min: '',
    salary_max: '',
    description: '',
    requirements: [],
    job_type: 'full-time'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const formattedData = {
      ...jobData,
      salary_min: jobData.salary_min ? parseInt(jobData.salary_min) : null,
      salary_max: jobData.salary_max ? parseInt(jobData.salary_max) : null,
      requirements: jobData.requirements.filter(req => req.trim() !== '')
    };
    onSubmit(formattedData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4">Post New Job</h3>
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Job Title"
              value={jobData.title}
              onChange={(e) => setJobData({ ...jobData, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
            <input
              type="text"
              placeholder="Company"
              value={jobData.company}
              onChange={(e) => setJobData({ ...jobData, company: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
            <input
              type="text"
              placeholder="Location"
              value={jobData.location}
              onChange={(e) => setJobData({ ...jobData, location: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
            <select
              value={jobData.job_type}
              onChange={(e) => setJobData({ ...jobData, job_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="full-time">Full-time</option>
              <option value="part-time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
            </select>
            <input
              type="number"
              placeholder="Minimum Salary"
              value={jobData.salary_min}
              onChange={(e) => setJobData({ ...jobData, salary_min: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
            <input
              type="number"
              placeholder="Maximum Salary"
              value={jobData.salary_max}
              onChange={(e) => setJobData({ ...jobData, salary_max: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div className="mt-4">
            <textarea
              placeholder="Job Description"
              value={jobData.description}
              onChange={(e) => setJobData({ ...jobData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              rows="4"
              required
            />
          </div>
          <div className="mt-6 flex space-x-4">
            <button
              type="submit"
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Post Job
            </button>
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = React.useContext(AuthContext);

  if (loading) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
  }

  if (!user) {
    return <Login />;
  }

  return children;
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-100">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Navigation />
                <Dashboard />
              </ProtectedRoute>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;