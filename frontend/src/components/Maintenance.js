import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import './Maintenance.css';

function toInputDate(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function toApiDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function formatMoney(value) {
  return `£${Number(value || 0).toLocaleString('en-GB', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

const emptyForm = {
  asset_id: '',
  maintenance_type: 'Service',
  status: 'Scheduled',
  scheduled_date: '',
  completed_date: '',
  next_service_date: '',
  assigned_user_id: '',
  cost: '',
  notes: ''
};

function Maintenance({ token, apiUrl, assets = [], users = [] }) {
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState({
    overdue: 0,
    due_soon: 0,
    open_repairs: 0,
    completed: 0,
    total: 0
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const headers = { Authorization: `Bearer ${token}` };

  const loadMaintenance = async () => {
    setLoading(true);
    setError('');

    try {
      const [recordsResponse, summaryResponse] = await Promise.all([
        axios.get(`${apiUrl}/maintenance`, { headers }),
        axios.get(`${apiUrl}/maintenance/summary`, { headers })
      ]);

      setRecords(recordsResponse.data || []);
      setSummary(summaryResponse.data || {});
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load maintenance records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMaintenance();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const filteredRecords = useMemo(() => {
    const query = search.trim().toLowerCase();

    return records.filter((record) => {
      const matchesStatus = statusFilter === 'All' || record.status === statusFilter;
      const matchesType = typeFilter === 'All' || record.maintenance_type === typeFilter;
      const haystack = [
        record.asset_tag,
        record.asset_name,
        record.maintenance_type,
        record.status,
        record.assigned_user_name,
        record.assigned_user_email,
        record.notes
      ].filter(Boolean).join(' ').toLowerCase();

      return matchesStatus && matchesType && (!query || haystack.includes(query));
    });
  }, [records, search, statusFilter, typeFilter]);

  const openCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setError('');
    setMessage('');
    setShowForm(true);
  };

  const openEdit = (record) => {
    setEditingId(record.id);
    setForm({
      asset_id: String(record.asset_id || ''),
      maintenance_type: record.maintenance_type || 'Service',
      status: record.status || 'Scheduled',
      scheduled_date: toInputDate(record.scheduled_date),
      completed_date: toInputDate(record.completed_date),
      next_service_date: toInputDate(record.next_service_date),
      assigned_user_id: record.assigned_user_id ? String(record.assigned_user_id) : '',
      cost: record.cost ?? '',
      notes: record.notes || ''
    });
    setError('');
    setMessage('');
    setShowForm(true);
  };

  const updateField = (name, value) => {
    setForm((current) => ({ ...current, [name]: value }));
  };

  const submitForm = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');

    if (!form.asset_id) {
      setError('Please select an asset.');
      setSaving(false);
      return;
    }

    const payload = {
      asset_id: Number(form.asset_id),
      maintenance_type: form.maintenance_type,
      status: form.status,
      scheduled_date: toApiDate(form.scheduled_date),
      completed_date: toApiDate(form.completed_date),
      next_service_date: toApiDate(form.next_service_date),
      assigned_user_id: form.assigned_user_id ? Number(form.assigned_user_id) : null,
      cost: Number(form.cost || 0),
      notes: form.notes.trim() || null
    };

    try {
      if (editingId) {
        await axios.put(`${apiUrl}/maintenance/${editingId}`, payload, { headers });
        setMessage('Maintenance record updated successfully.');
      } else {
        await axios.post(`${apiUrl}/maintenance`, payload, { headers });
        setMessage('Maintenance record created successfully.');
      }

      setShowForm(false);
      setEditingId(null);
      setForm(emptyForm);
      await loadMaintenance();
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to save maintenance record.');
    } finally {
      setSaving(false);
    }
  };

  const deleteRecord = async (record) => {
    if (!window.confirm(`Delete the maintenance record for ${record.asset_tag || record.asset_name || 'this asset'}?`)) {
      return;
    }

    setError('');
    setMessage('');

    try {
      await axios.delete(`${apiUrl}/maintenance/${record.id}`, { headers });
      setMessage('Maintenance record deleted.');
      await loadMaintenance();
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to delete maintenance record.');
    }
  };

  return (
    <div className="apex-maintenance">
      <div className="apex-page-heading">
        <div>
          <div className="apex-eyebrow">ASSET OPERATIONS</div>
          <h1>Maintenance</h1>
          <p>Plan servicing, repairs and inspections across the APEX asset estate.</p>
        </div>
        <button className="apex-orange-button" onClick={openCreate}>+ Add Maintenance</button>
      </div>

      {message && <div className="apex-maintenance-message success">{message}</div>}
      {error && <div className="apex-maintenance-message error">{error}</div>}

      <div className="apex-maintenance-stats">
        <StatCard label="Total Records" value={summary.total || 0} />
        <StatCard label="Overdue" value={summary.overdue || 0} tone="danger" />
        <StatCard label="Due Soon" value={summary.due_soon || 0} tone="warning" />
        <StatCard label="Open Repairs" value={summary.open_repairs || 0} />
        <StatCard label="Completed" value={summary.completed || 0} tone="success" />
      </div>

      <section className="apex-admin-card apex-maintenance-list-card">
        <div className="apex-card-heading maintenance-heading">
          <div>
            <h2>Maintenance Records</h2>
            <span>{filteredRecords.length} record{filteredRecords.length === 1 ? '' : 's'} shown</span>
          </div>
        </div>

        <div className="apex-maintenance-filters">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search asset, employee, notes..."
          />
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="All">All statuses</option>
            <option value="Scheduled">Scheduled</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
            <option value="Cancelled">Cancelled</option>
          </select>
          <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
            <option value="All">All types</option>
            <option value="Service">Service</option>
            <option value="Repair">Repair</option>
            <option value="Inspection">Inspection</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {loading ? (
          <div className="apex-maintenance-empty">Loading maintenance records...</div>
        ) : filteredRecords.length === 0 ? (
          <div className="apex-maintenance-empty">
            <strong>No maintenance records found</strong>
            <span>Create your first service, repair or inspection using <b>+ Add Maintenance</b>.</span>
          </div>
        ) : (
          <div className="apex-maintenance-table-wrap">
            <table className="apex-maintenance-table">
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Scheduled</th>
                  <th>Next Service</th>
                  <th>Technician</th>
                  <th>Cost</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((record) => (
                  <tr key={record.id} className={record.is_overdue ? 'maintenance-row-overdue' : ''}>
                    <td>
                      <strong className="maintenance-asset-tag">{record.asset_tag || '—'}</strong>
                      <span>{record.asset_name || 'Unknown asset'}</span>
                    </td>
                    <td>{record.maintenance_type}</td>
                    <td>
                      <StatusBadge record={record} />
                    </td>
                    <td>{formatDate(record.scheduled_date)}</td>
                    <td>{formatDate(record.next_service_date)}</td>
                    <td>{record.assigned_user_name || 'Unassigned'}</td>
                    <td>{formatMoney(record.cost)}</td>
                    <td>
                      <div className="maintenance-actions">
                        <button className="apex-small-button" onClick={() => openEdit(record)}>Edit</button>
                        <button className="apex-small-button apex-danger-button" onClick={() => deleteRecord(record)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {showForm && (
        <div className="apex-maintenance-modal-backdrop" onMouseDown={() => !saving && setShowForm(false)}>
          <div className="apex-maintenance-modal" onMouseDown={(event) => event.stopPropagation()}>
            <div className="maintenance-modal-header">
              <div>
                <div className="apex-eyebrow">MAINTENANCE RECORD</div>
                <h2>{editingId ? 'Edit Maintenance' : 'Add Maintenance'}</h2>
              </div>
              <button className="maintenance-close" onClick={() => setShowForm(false)} disabled={saving}>×</button>
            </div>

            <form onSubmit={submitForm} className="apex-maintenance-form">
              <div className="maintenance-form-grid">
                <label>
                  Asset
                  <select value={form.asset_id} onChange={(event) => updateField('asset_id', event.target.value)} required>
                    <option value="">Select asset...</option>
                    {assets.map((asset) => (
                      <option key={asset.id} value={asset.id}>
                        {asset.asset_tag || `APEX-${String(asset.id).padStart(6, '0')}`} — {asset.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Maintenance Type
                  <select value={form.maintenance_type} onChange={(event) => updateField('maintenance_type', event.target.value)}>
                    <option>Service</option>
                    <option>Repair</option>
                    <option>Inspection</option>
                    <option>Other</option>
                  </select>
                </label>

                <label>
                  Status
                  <select value={form.status} onChange={(event) => updateField('status', event.target.value)}>
                    <option>Scheduled</option>
                    <option>In Progress</option>
                    <option>Completed</option>
                    <option>Cancelled</option>
                  </select>
                </label>

                <label>
                  Assigned Technician
                  <select value={form.assigned_user_id} onChange={(event) => updateField('assigned_user_id', event.target.value)}>
                    <option value="">Unassigned</option>
                    {users.filter((user) => user.is_active !== false).map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.full_name || user.email}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Scheduled Date
                  <input type="datetime-local" value={form.scheduled_date} onChange={(event) => updateField('scheduled_date', event.target.value)} />
                </label>

                <label>
                  Completed Date
                  <input type="datetime-local" value={form.completed_date} onChange={(event) => updateField('completed_date', event.target.value)} />
                </label>

                <label>
                  Next Service Date
                  <input type="datetime-local" value={form.next_service_date} onChange={(event) => updateField('next_service_date', event.target.value)} />
                </label>

                <label>
                  Cost (£)
                  <input type="number" min="0" step="0.01" value={form.cost} onChange={(event) => updateField('cost', event.target.value)} placeholder="0.00" />
                </label>
              </div>

              <label className="maintenance-notes-field">
                Work Carried Out / Notes
                <textarea rows="5" value={form.notes} onChange={(event) => updateField('notes', event.target.value)} placeholder="Record the work completed, parts used, findings or other notes..." />
              </label>

              <div className="maintenance-form-actions">
                <button type="button" className="apex-small-button" onClick={() => setShowForm(false)} disabled={saving}>Cancel</button>
                <button type="submit" className="apex-orange-button" disabled={saving}>
                  {saving ? 'Saving...' : editingId ? 'Save Changes' : 'Create Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, tone = '' }) {
  return (
    <div className={`apex-maintenance-stat ${tone ? `stat-${tone}` : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusBadge({ record }) {
  let className = 'maintenance-status';
  if (record.is_overdue) className += ' status-overdue';
  else if (record.status === 'Completed') className += ' status-completed';
  else if (record.status === 'In Progress') className += ' status-progress';
  else if (record.status === 'Cancelled') className += ' status-cancelled';
  else if (record.is_due_soon) className += ' status-due-soon';
  else className += ' status-scheduled';

  const label = record.is_overdue ? 'Overdue' : record.is_due_soon && record.status === 'Scheduled' ? 'Due Soon' : record.status;
  return <span className={className}>{label}</span>;
}

export default Maintenance;
