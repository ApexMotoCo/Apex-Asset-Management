import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const money = (v) => `£${Number(v || 0).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const date = (v) => v ? new Date(v).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';

function OperationsDashboard({ apiUrl, token, assets = [], onOpenAsset, onRefresh }) {
  const [summary, setSummary] = useState(null);
  const [maintenance, setMaintenance] = useState([]);
  const [loading, setLoading] = useState(true);
  const headers = { Authorization: `Bearer ${token}` };

  const load = async () => {
    setLoading(true);
    try {
      const [summaryResponse, maintenanceResponse] = await Promise.all([
        axios.get(`${apiUrl}/dashboard/summary`, { headers }),
        axios.get(`${apiUrl}/maintenance`, { headers })
      ]);
      setSummary(summaryResponse.data);
      setMaintenance(maintenanceResponse.data);
    } catch (error) {
      console.error(error);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [apiUrl, token, assets.length]);

  const attention = useMemo(() => {
    const items = [];
    maintenance.filter((m) => m.is_overdue).forEach((m) => items.push({ type: 'critical', label: 'Overdue maintenance', detail: `${m.asset_tag} — ${m.maintenance_type}`, assetId: m.asset_id }));
    assets.filter((a) => a.warranty_status === 'Expired').forEach((a) => items.push({ type: 'critical', label: 'Warranty expired', detail: `${a.asset_tag} — ${a.name}`, assetId: a.id }));
    assets.filter((a) => a.warranty_status === 'Expiring Soon').forEach((a) => items.push({ type: 'warning', label: 'Warranty expiring', detail: `${a.asset_tag} — ${date(a.warranty_expiry_date)}`, assetId: a.id }));
    assets.filter((a) => a.expected_replacement_date && new Date(a.expected_replacement_date) <= new Date()).forEach((a) => items.push({ type: 'warning', label: 'Replacement due', detail: `${a.asset_tag} — ${a.name}`, assetId: a.id }));
    assets.filter((a) => a.lifecycle_status === 'Replacement Required').forEach((a) => items.push({ type: 'critical', label: 'Replacement required', detail: `${a.asset_tag} — ${a.name}`, assetId: a.id }));
    assets.filter((a) => !a.assigned_user_id && a.lifecycle_status !== 'Retired').forEach((a) => items.push({ type: 'info', label: 'Unassigned asset', detail: `${a.asset_tag} — ${a.name}`, assetId: a.id }));
    return items.slice(0, 12);
  }, [assets, maintenance]);

  const cards = summary ? [
    ['Total Assets', summary.total_assets, ''],
    ['Asset Value', money(summary.total_asset_value), ''],
    ['Assigned', summary.assigned_assets, ''],
    ['APEX HUB', summary.hub_assets, ''],
    ['In Maintenance', summary.maintenance_assets, ''],
    ['Open Repairs', summary.open_repairs, ''],
    ['Warranty Expiring', summary.warranty_expiring, 'warning'],
    ['Replacement Due', summary.replacements_due + summary.replacement_required, 'critical']
  ] : [];

  return <div className="ops-dashboard">
    <div className="ops-heading"><div><div className="apex-eyebrow">APEX OPERATIONS</div><h1>Asset Management Dashboard</h1><p>Live operational view of the APEX asset estate.</p></div><button className="apex-orange-button" onClick={() => { load(); onRefresh?.(); }}>Refresh Data</button></div>

    <div className="ops-card-grid">
      {cards.map(([label, value, tone]) => <div className={`ops-stat-card ${tone}`} key={label}><span>{label}</span><strong>{loading ? '…' : value}</strong></div>)}
    </div>

    <div className="ops-two-column">
      <section className="ops-panel"><div className="ops-panel-heading"><div><span className="apex-eyebrow">ATTENTION REQUIRED</span><h2>Items needing action</h2></div><span>{attention.length}</span></div>{attention.length ? <div className="ops-attention-list">{attention.map((item, i) => <button key={`${item.assetId}-${item.label}-${i}`} className={`ops-attention-item ${item.type}`} onClick={() => onOpenAsset?.(item.assetId)}><span className="ops-attention-label">{item.label}</span><strong>{item.detail}</strong><span>View →</span></button>)}</div> : <div className="ops-empty">No current attention items.</div>}</section>

      <section className="ops-panel"><div className="ops-panel-heading"><div><span className="apex-eyebrow">MAINTENANCE</span><h2>Upcoming & recent</h2></div></div>{maintenance.length ? <div className="ops-maintenance-list">{maintenance.slice(0, 7).map((m) => <button key={m.id} onClick={() => onOpenAsset?.(m.asset_id)}><div><strong>{m.asset_tag}</strong><span>{m.maintenance_type}</span></div><div><span className={`ops-mini-status ${m.is_overdue ? 'critical' : m.is_due_soon ? 'warning' : ''}`}>{m.status}</span><small>{date(m.scheduled_date)}</small></div></button>)}</div> : <div className="ops-empty">No maintenance records yet.</div>}</section>
    </div>

    <section className="ops-panel"><div className="ops-panel-heading"><div><span className="apex-eyebrow">ASSET HEALTH</span><h2>Current estate</h2></div></div><div className="ops-health-grid">{['Healthy','Due Maintenance','Under Repair','End of Life'].map((status) => { const count = assets.filter((a) => a.health_status === status).length; return <div key={status}><span>{status}</span><strong>{count}</strong></div>; })}</div></section>
  </div>;
}

export default OperationsDashboard;
