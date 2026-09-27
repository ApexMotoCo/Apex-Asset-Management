import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './AssetProfile.css';

const money = (v) => `£${Number(v || 0).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const date = (v) => v ? new Date(v).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—';
const dateInput = (v) => v ? new Date(v).toISOString().slice(0,16) : '';

function AssetProfile({ apiUrl, token, assetId, users, onClose, onRefresh }) {
  const [asset, setAsset] = useState(null);
  const [lifecycle, setLifecycle] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const headers = { Authorization: `Bearer ${token}` };

  const load = async () => {
    try {
      const [a, l, m] = await Promise.all([
        axios.get(`${apiUrl}/assets/${assetId}`, { headers }),
        axios.get(`${apiUrl}/assets/${assetId}/lifecycle`, { headers }),
        axios.get(`${apiUrl}/assets/${assetId}/maintenance`, { headers })
      ]);
      setAsset(a.data); setLifecycle(l.data); setMaintenance(m.data);
      setForm({ lifecycle_status: a.data.lifecycle_status || 'In Stock', warranty_provider: a.data.warranty_provider || '', warranty_start_date: dateInput(a.data.warranty_start_date), warranty_expiry_date: dateInput(a.data.warranty_expiry_date), warranty_reference: a.data.warranty_reference || '', warranty_notes: a.data.warranty_notes || '', expected_replacement_date: dateInput(a.data.expected_replacement_date), replacement_priority: a.data.replacement_priority || 'Normal', replacement_reason: a.data.replacement_reason || '', estimated_replacement_cost: a.data.estimated_replacement_cost || 0, replacement_notes: a.data.replacement_notes || '' });
    } catch (e) { setError(e.response?.data?.detail || 'Unable to load asset profile.'); }
  };
  useEffect(() => { load(); }, [assetId]);

  const change = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  const save = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      await axios.put(`${apiUrl}/assets/${assetId}`, { lifecycle_status: form.lifecycle_status, warranty_provider: form.warranty_provider || null, warranty_start_date: form.warranty_start_date || null, warranty_expiry_date: form.warranty_expiry_date || null, warranty_reference: form.warranty_reference || null, warranty_notes: form.warranty_notes || null, expected_replacement_date: form.expected_replacement_date || null, replacement_priority: form.replacement_priority, replacement_reason: form.replacement_reason || null, estimated_replacement_cost: Number(form.estimated_replacement_cost || 0), replacement_notes: form.replacement_notes || null }, { headers });
      setEditing(false); await load(); onRefresh?.();
    } catch (e) { setError(e.response?.data?.detail || 'Unable to save asset profile.'); } finally { setSaving(false); }
  };

  if (!asset) return <div className="apex-modal-backdrop"><div className="apex-modal asset-profile-modal"><p>{error || 'Loading asset profile...'}</p><button className="apex-small-button" onClick={onClose}>Close</button></div></div>;

  return <div className="apex-modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
    <div className="asset-profile-modal">
      <div className="asset-profile-head"><div><span className="apex-eyebrow">ASSET PROFILE</span><h1>{asset.asset_tag}</h1><p>{asset.name}</p></div><button className="apex-modal-close" onClick={onClose}>×</button></div>
      {error && <div className="apex-form-message apex-form-error">{error}</div>}
      <div className="asset-profile-status-row"><span className="profile-pill">{asset.lifecycle_status}</span><span className="profile-pill">{asset.health_status}</span><span className={`profile-pill ${asset.warranty_status === 'Expired' ? 'danger' : asset.warranty_status === 'Expiring Soon' ? 'warning' : ''}`}>Warranty: {asset.warranty_status}</span><span className="profile-pill">{asset.location || 'APEX HUB'}</span></div>

      {!editing ? <>
        <div className="profile-grid">
          <section><span>Serial Number</span><strong>{asset.serial_number || '—'}</strong></section><section><span>Category</span><strong>{asset.category?.name || 'Uncategorised'}</strong></section><section><span>Value</span><strong>{money(asset.value)}</strong></section><section><span>Assigned To</span><strong>{asset.assigned_user?.full_name || 'Unassigned'}</strong></section>
          <section><span>Warranty Provider</span><strong>{asset.warranty_provider || '—'}</strong></section><section><span>Warranty Expiry</span><strong>{date(asset.warranty_expiry_date)}</strong></section><section><span>Replacement Date</span><strong>{date(asset.expected_replacement_date)}</strong></section><section><span>Replacement Priority</span><strong>{asset.replacement_priority || 'Normal'}</strong></section>
        </div>
        <div className="profile-sections"><section><div className="profile-section-title">Maintenance History</div>{maintenance.length ? maintenance.slice(0,8).map((m) => <div className="profile-history-row" key={m.id}><strong>{m.maintenance_type}</strong><span>{m.status}</span><small>{date(m.scheduled_date)} · {money(m.cost)}</small></div>) : <p>No maintenance history.</p>}</section><section><div className="profile-section-title">Lifecycle History</div>{lifecycle.length ? lifecycle.slice(0,8).map((e) => <div className="profile-history-row" key={e.id}><strong>{e.to_status}</strong><span>{e.reason || 'Status change'}</span><small>{date(e.created_at)} · {e.changed_by || 'System'}</small></div>) : <p>No lifecycle history.</p>}</section></div>
        <div className="asset-profile-footer"><button className="apex-small-button" onClick={() => setEditing(true)}>Edit Lifecycle / Warranty</button><button className="apex-orange-button" onClick={onClose}>Close</button></div>
      </> : <form onSubmit={save} className="profile-edit-form">
        <div className="apex-form-grid"><div className="apex-form-field"><label>Lifecycle</label><select name="lifecycle_status" value={form.lifecycle_status} onChange={change}>{['In Stock','Assigned','In Maintenance','Returned','Repaired','Replacement Required','Retired'].map(v => <option key={v}>{v}</option>)}</select></div><div className="apex-form-field"><label>Warranty provider</label><input name="warranty_provider" value={form.warranty_provider} onChange={change}/></div><div className="apex-form-field"><label>Warranty start</label><input type="datetime-local" name="warranty_start_date" value={form.warranty_start_date} onChange={change}/></div><div className="apex-form-field"><label>Warranty expiry</label><input type="datetime-local" name="warranty_expiry_date" value={form.warranty_expiry_date} onChange={change}/></div><div className="apex-form-field"><label>Warranty reference</label><input name="warranty_reference" value={form.warranty_reference} onChange={change}/></div><div className="apex-form-field"><label>Replacement date</label><input type="datetime-local" name="expected_replacement_date" value={form.expected_replacement_date} onChange={change}/></div><div className="apex-form-field"><label>Replacement priority</label><select name="replacement_priority" value={form.replacement_priority} onChange={change}>{['Low','Normal','High','Critical'].map(v => <option key={v}>{v}</option>)}</select></div><div className="apex-form-field"><label>Estimated replacement cost (£)</label><input type="number" min="0" step="0.01" name="estimated_replacement_cost" value={form.estimated_replacement_cost} onChange={change}/></div><div className="apex-form-field apex-form-wide"><label>Replacement reason</label><input name="replacement_reason" value={form.replacement_reason} onChange={change}/></div><div className="apex-form-field apex-form-wide"><label>Warranty notes</label><textarea name="warranty_notes" rows="3" value={form.warranty_notes} onChange={change}/></div><div className="apex-form-field apex-form-wide"><label>Replacement notes</label><textarea name="replacement_notes" rows="3" value={form.replacement_notes} onChange={change}/></div></div><div className="asset-profile-footer"><button type="button" className="apex-small-button" onClick={() => setEditing(false)}>Cancel</button><button className="apex-orange-button" disabled={saving}>{saving ? 'Saving…' : 'Save Profile'}</button></div>
      </form>}
    </div>
  </div>;
}
export default AssetProfile;
