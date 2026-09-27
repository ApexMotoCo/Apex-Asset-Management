import React, { useMemo, useState } from 'react';
import axios from 'axios';

const EMPTY_FORM = {
  name: '',
  description: '',
  category_id: '',
  serial_number: '',
  purchase_date: '',
  value: '',
  location: 'APEX HUB',
  status: 'active'
};

function AssetForm({ categories = [], onAssetCreated, apiUrl, token }) {
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const sortedCategories = useMemo(
    () => [...categories].sort((a, b) => String(a.name).localeCompare(String(b.name))),
    [categories]
  );

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const payload = {
        ...formData,
        category_id: Number(formData.category_id),
        value: Number(formData.value),
        purchase_date: formData.purchase_date || null,
        location: formData.location.trim() || 'APEX HUB'
      };

      await axios.post(`${apiUrl}/assets`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setFormData(EMPTY_FORM);
      setSuccess('Asset created successfully. APEX asset ID and QR token were generated automatically.');
      if (onAssetCreated) await onAssetCreated();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create asset. Please check the information entered.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="apex-asset-form" onSubmit={handleSubmit}>
      {error && <div className="apex-form-message error">{error}</div>}
      {success && <div className="apex-form-message success">{success}</div>}

      <div className="apex-form-section-label">Asset Details</div>

      <div className="apex-form-grid">
        <div className="apex-field apex-field-wide">
          <label htmlFor="asset-name">Asset Name</label>
          <input id="asset-name" name="name" value={formData.name} onChange={handleChange} required placeholder="e.g. Dell Latitude 7450" />
        </div>

        <div className="apex-field">
          <label htmlFor="asset-category">Category</label>
          <select id="asset-category" name="category_id" value={formData.category_id} onChange={handleChange} required>
            <option value="">Select category...</option>
            {sortedCategories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
        </div>

        <div className="apex-field">
          <label htmlFor="asset-serial">Serial Number</label>
          <input id="asset-serial" name="serial_number" value={formData.serial_number} onChange={handleChange} required placeholder="Unique serial number" />
        </div>

        <div className="apex-field">
          <label htmlFor="asset-date">Purchase Date</label>
          <input id="asset-date" type="datetime-local" name="purchase_date" value={formData.purchase_date} onChange={handleChange} />
        </div>

        <div className="apex-field">
          <label htmlFor="asset-value">Asset Value (£)</label>
          <input id="asset-value" type="number" name="value" value={formData.value} onChange={handleChange} required min="0" step="0.01" placeholder="0.00" />
        </div>

        <div className="apex-field">
          <label htmlFor="asset-location">Location</label>
          <input id="asset-location" name="location" value={formData.location} onChange={handleChange} required placeholder="APEX HUB" />
        </div>

        <div className="apex-field">
          <label htmlFor="asset-status">Status</label>
          <select id="asset-status" name="status" value={formData.status} onChange={handleChange}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="maintenance">Maintenance</option>
            <option value="retired">Retired</option>
          </select>
        </div>

        <div className="apex-field apex-field-wide">
          <label htmlFor="asset-description">Description</label>
          <textarea id="asset-description" name="description" value={formData.description} onChange={handleChange} rows="4" placeholder="Optional asset details, specifications or notes..." />
        </div>
      </div>

      <div className="apex-form-footer">
        <div className="apex-form-hint">Asset ID and QR code are generated automatically after creation.</div>
        <button className="apex-orange-button" type="submit" disabled={loading || !categories.length}>
          {loading ? 'Creating Asset...' : 'Create Asset'}
        </button>
      </div>
    </form>
  );
}

export default AssetForm;
