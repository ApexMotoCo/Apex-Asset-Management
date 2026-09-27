import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { QRCodeSVG } from 'qrcode.react';

const STATUS_LABELS = {
  active: 'Active',
  inactive: 'Inactive',
  maintenance: 'Maintenance',
  retired: 'Retired'
};

function AssetList({ assets, categories, users, onAssetUpdated, onAssetDeleted, onViewAsset, apiUrl, token }) {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('all');
  const [category, setCategory] = useState('all');
  const [expanded, setExpanded] = useState(null);
  const [assigning, setAssigning] = useState(null);
  const [editing, setEditing] = useState(null);
  const [selectedUser, setSelectedUser] = useState({});
  const [editForm, setEditForm] = useState({});
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const getCategoryName = (id) => categories.find((item) => item.id === id)?.name || 'Uncategorized';
  const scanUrl = (asset) => `${window.location.origin}/scan/${asset.qr_token}`;

  const filteredAssets = useMemo(() => {
    const query = search.trim().toLowerCase();
    return assets.filter((asset) => {
      const matchesSearch = !query || [
        asset.asset_tag,
        asset.name,
        asset.serial_number,
        asset.location,
        asset.assigned_user?.full_name,
        asset.assigned_user?.email,
        getCategoryName(asset.category_id)
      ].some((value) => String(value || '').toLowerCase().includes(query));
      const matchesStatus = status === 'all' || asset.status === status;
      const matchesCategory = category === 'all' || String(asset.category_id) === String(category);
      return matchesSearch && matchesStatus && matchesCategory;
    });
  }, [assets, search, status, category, categories]);

  const clearMessages = () => { setError(''); setNotice(''); };

  const assignAsset = async (asset) => {
    clearMessages();
    try {
      await axios.post(`${apiUrl}/assets/${asset.id}/assign`, {
        user_id: selectedUser[asset.id] ? Number(selectedUser[asset.id]) : null,
        location: asset.location || 'APEX HUB'
      }, { headers: { Authorization: `Bearer ${token}` } });
      setAssigning(null);
      setNotice(`${asset.asset_tag} assignment updated.`);
      onAssetUpdated();
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to update the assignment.');
    }
  };

  const openEdit = (asset) => {
    setEditing(asset);
    setEditForm({
      name: asset.name || '',
      description: asset.description || '',
      category_id: asset.category_id || '',
      serial_number: asset.serial_number || '',
      purchase_date: asset.purchase_date ? new Date(asset.purchase_date).toISOString().slice(0, 16) : '',
      value: asset.value ?? 0,
      location: asset.location || 'APEX HUB',
      status: asset.status || 'active'
    });
    clearMessages();
  };

  const updateEditField = (event) => {
    const { name, value } = event.target;
    setEditForm((current) => ({ ...current, [name]: value }));
  };

  const saveEdit = async (event) => {
    event.preventDefault();
    clearMessages();
    try {
      await axios.put(`${apiUrl}/assets/${editing.id}`, {
        ...editForm,
        category_id: Number(editForm.category_id),
        value: Number(editForm.value || 0),
        purchase_date: editForm.purchase_date || null,
        location: editForm.location.trim() || 'APEX HUB'
      }, { headers: { Authorization: `Bearer ${token}` } });
      setEditing(null);
      setNotice(`${editing.asset_tag} updated successfully.`);
      onAssetUpdated();
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to update the asset.');
    }
  };

  const handleDelete = async (asset) => {
    if (!window.confirm(`Delete ${asset.asset_tag} — ${asset.name}? This cannot be undone.`)) return;
    clearMessages();
    try {
      await axios.delete(`${apiUrl}/assets/${asset.id}`, { headers: { Authorization: `Bearer ${token}` } });
      onAssetDeleted(asset.id);
      setNotice(`${asset.asset_tag} deleted.`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Only a super administrator can delete assets.');
    }
  };

  const copyScanLink = async (asset) => {
    try {
      await navigator.clipboard.writeText(scanUrl(asset));
      setNotice('QR scan link copied to clipboard.');
    } catch {
      setError('Unable to copy the scan link.');
    }
  };

  const printQr = (asset) => {
    const popup = window.open('', '_blank', 'width=520,height=650');
    if (!popup) return;
    popup.document.write(`<!doctype html><html><head><title>${asset.asset_tag} QR</title><style>body{font-family:Arial;text-align:center;padding:35px;color:#111}h1{margin-bottom:4px}p{color:#555}svg{margin:20px auto;width:280px;height:280px}</style></head><body><h1>APEX</h1><h2>${asset.asset_tag}</h2><p>${asset.name}</p><div id="qr"></div><p>${scanUrl(asset)}</p></body></html>`);
    popup.document.close();
    const svg = document.querySelector(`[data-apex-qr="${asset.id}"] svg`);
    if (svg) popup.document.getElementById('qr').innerHTML = svg.outerHTML;
    popup.focus();
    setTimeout(() => popup.print(), 300);
  };

  useEffect(() => {
    if (notice) {
      const timer = window.setTimeout(() => setNotice(''), 4000);
      return () => window.clearTimeout(timer);
    }
  }, [notice]);

  if (!assets.length) {
    return (
      <div className="apex-empty-assets">
        <div className="apex-empty-icon">+</div>
        <h3>No assets registered</h3>
        <p>Use the form above to register your first company asset.</p>
      </div>
    );
  }

  return (
    <div className="apex-assets-panel">
      {(error || notice) && (
        <div className={`apex-form-message ${error ? 'apex-form-error' : 'apex-form-success'}`}>{error || notice}</div>
      )}

      <div className="apex-asset-toolbar">
        <div className="apex-search-wrap">
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search asset ID, name, serial, location..." aria-label="Search assets" />
        </div>
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status">
          <option value="all">All statuses</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Filter by category">
          <option value="all">All categories</option>
          {categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </div>

      <div className="apex-asset-results-line">Showing <strong>{filteredAssets.length}</strong> of <strong>{assets.length}</strong> assets</div>

      {!filteredAssets.length ? (
        <div className="apex-empty-assets compact"><h3>No matching assets</h3><p>Try changing the search or filters.</p></div>
      ) : (
        <div className="apex-asset-grid">
          {filteredAssets.map((asset) => (
            <article key={asset.id} className="apex-asset-card">
              <div className="apex-asset-card-top">
                <div>
                  <div className="apex-asset-tag">{asset.asset_tag}</div>
                  <h3>{asset.name}</h3>
                  <span className={`apex-asset-status status-${asset.status}`}>{STATUS_LABELS[asset.status] || asset.status}</span>
                </div>
                <div className="apex-asset-value">£{Number(asset.value || 0).toLocaleString('en-GB', { minimumFractionDigits: 2 })}</div>
              </div>

              <div className="apex-asset-details">
                <div><span>Serial</span><strong>{asset.serial_number || '—'}</strong></div>
                <div><span>Category</span><strong>{getCategoryName(asset.category_id)}</strong></div>
                <div><span>Location</span><strong>{asset.location || 'APEX HUB'}</strong></div>
                <div><span>Assigned</span><strong>{asset.assigned_user?.full_name || 'Unassigned'}</strong></div>
              </div>

              <div className="apex-asset-qr" data-apex-qr={asset.id}>
                <QRCodeSVG value={scanUrl(asset)} size={142} bgColor="#ffffff" fgColor="#000000" includeMargin />
                <div><strong>Scan asset</strong><small>{asset.asset_tag}</small></div>
              </div>

              <div className="apex-asset-actions">
                <button className="apex-small-button apex-highlight-button" onClick={() => onViewAsset?.(asset)}>View Profile</button><button className="apex-small-button" onClick={() => openEdit(asset)}>Edit</button>
                <button className="apex-small-button" onClick={() => setAssigning(assigning === asset.id ? null : asset.id)}>Assign</button>
                <button className="apex-small-button" onClick={() => setExpanded(expanded === asset.id ? null : asset.id)}>History</button>
                <button className="apex-small-button" onClick={() => copyScanLink(asset)}>Copy QR Link</button>
                <button className="apex-small-button" onClick={() => printQr(asset)}>Print QR</button>
                <button className="apex-small-button apex-danger-button" onClick={() => handleDelete(asset)}>Delete</button>
              </div>

              {assigning === asset.id && (
                <div className="apex-inline-panel">
                  <label>Assign to employee</label>
                  <select value={selectedUser[asset.id] || ''} onChange={(e) => setSelectedUser((current) => ({ ...current, [asset.id]: e.target.value }))}>
                    <option value="">Unassigned</option>
                    {users.filter((user) => user.is_active).map((user) => <option key={user.id} value={user.id}>{user.full_name} — {user.email}</option>)}
                  </select>
                  <button className="apex-orange-button" onClick={() => assignAsset(asset)}>Save Assignment</button>
                </div>
              )}

              {expanded === asset.id && <AssignmentHistory assetId={asset.id} apiUrl={apiUrl} token={token} />}
            </article>
          ))}
        </div>
      )}

      {editing && (
        <div className="apex-modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && setEditing(null)}>
          <form className="apex-modal" onSubmit={saveEdit}>
            <div className="apex-modal-heading"><div><span className="apex-eyebrow">ASSET RECORD</span><h2>Edit {editing.asset_tag}</h2></div><button type="button" className="apex-modal-close" onClick={() => setEditing(null)}>×</button></div>
            <div className="apex-form-grid">
              <div className="apex-form-field apex-form-wide"><label>Asset name</label><input name="name" value={editForm.name} onChange={updateEditField} required /></div>
              <div className="apex-form-field"><label>Category</label><select name="category_id" value={editForm.category_id} onChange={updateEditField} required>{categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></div>
              <div className="apex-form-field"><label>Serial number</label><input name="serial_number" value={editForm.serial_number} onChange={updateEditField} required /></div>
              <div className="apex-form-field"><label>Value (£)</label><input type="number" min="0" step="0.01" name="value" value={editForm.value} onChange={updateEditField} /></div>
              <div className="apex-form-field"><label>Purchase date</label><input type="datetime-local" name="purchase_date" value={editForm.purchase_date} onChange={updateEditField} /></div>
              <div className="apex-form-field"><label>Location</label><input name="location" value={editForm.location} onChange={updateEditField} /></div>
              <div className="apex-form-field"><label>Status</label><select name="status" value={editForm.status} onChange={updateEditField}>{Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
              <div className="apex-form-field apex-form-wide"><label>Description</label><textarea name="description" value={editForm.description} onChange={updateEditField} rows="4" /></div>
            </div>
            <div className="apex-modal-footer"><button type="button" className="apex-small-button" onClick={() => setEditing(null)}>Cancel</button><button type="submit" className="apex-orange-button">Save Changes</button></div>
          </form>
        </div>
      )}
    </div>
  );
}

function AssignmentHistory({ assetId, apiUrl, token }) {
  const [history, setHistory] = useState(null);
  useEffect(() => {
    axios.get(`${apiUrl}/assets/${assetId}/assignments`, { headers: { Authorization: `Bearer ${token}` } }).then((response) => setHistory(response.data)).catch(() => setHistory([]));
  }, [assetId, apiUrl, token]);

  if (history === null) return <div className="apex-inline-panel">Loading assignment history...</div>;
  if (!history.length) return <div className="apex-inline-panel">No assignment history yet.</div>;

  return (
    <div className="apex-history-panel">
      <div className="apex-history-heading">Assignment History</div>
      {history.map((entry) => (
        <div className="apex-history-row" key={entry.id}>
          <strong>{entry.action}</strong><span>{entry.user?.full_name || 'Unassigned'}</span><small>{new Date(entry.assigned_at).toLocaleString('en-GB')} · {entry.location || 'APEX HUB'}</small>
        </div>
      ))}
    </div>
  );
}

export default AssetList;
