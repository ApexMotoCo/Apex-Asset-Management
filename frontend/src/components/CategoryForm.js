import React, { useState } from 'react';
import axios from 'axios';

function CategoryForm({ onCategoryCreated, apiUrl, token }) {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await axios.post(`${apiUrl}/categories`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFormData({ name: '', description: '' });
      setSuccess('Category created successfully! ');
      onCategoryCreated();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create category. Please check your inputs.');
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <div style={{
          padding: '1rem',
          background: 'rgba(239, 68, 68, 0.15)',
          border: '2px solid #ef4444',
          borderRadius: '4px',
          color: '#ef4444',
          fontWeight: '600',
          marginBottom: '1rem'
        }}>
          WARNING: {error}
        </div>
      )}
      {success && (
        <div style={{
          padding: '1rem',
          background: 'rgba(34, 197, 94, 0.15)',
          border: '2px solid #22c55e',
          borderRadius: '4px',
          color: '#22c55e',
          fontWeight: '600',
          marginBottom: '1rem'
        }}>
          OK: {success}
        </div>
      )}

      <div className="form-group">
        <label>Category Name</label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          placeholder="e.g., Electronics, Furniture, Vehicles"
        />
      </div>

      <div className="form-group">
        <label>Description</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Describe what this category contains..."
          rows="3"
          style={{ resize: 'vertical' }}
        />
      </div>

      <button type="submit" disabled={loading} style={{ marginTop: '0.5rem' }}>
        {loading ? 'Creating...' : 'Create Category'}
      </button>
    </form>
  );
}

export default CategoryForm;
