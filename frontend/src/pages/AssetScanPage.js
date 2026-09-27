import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { QRCodeSVG } from 'qrcode.react';

export default function AssetScanPage({ apiUrl, token, onBack, onUpdated }) {
  const [asset, setAsset] = useState(null);
  const [users, setUsers] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const qrToken = decodeURIComponent(window.location.pathname.split('/scan/')[1] || '');

  const headers = {Authorization:`Bearer ${token}`};

  useEffect(() => {
    const load = async () => {
      try {
        const [a,u] = await Promise.all([
          axios.get(`${apiUrl}/assets/qr/${encodeURIComponent(qrToken)}`, {headers}),
          axios.get(`${apiUrl}/admin/users?limit=200`, {headers})
        ]);
        setAsset(a.data);
        setUsers(u.data);
        setSelectedUser(a.data.assigned_user_id || '');
        const h = await axios.get(`${apiUrl}/assets/${a.data.id}/assignments`, {headers});
        setHistory(h.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Asset could not be loaded.');
      } finally { setLoading(false); }
    };
    load();
  }, [apiUrl, qrToken, token]);

  const assign = async () => {
    try {
      const r = await axios.post(`${apiUrl}/assets/${asset.id}/assign`, {
        user_id: selectedUser ? Number(selectedUser) : null,
        location: asset.location || 'APEX HUB'
      }, {headers});
      setAsset(r.data);
      const h = await axios.get(`${apiUrl}/assets/${asset.id}/assignments`, {headers});
      setHistory(h.data);
      if (onUpdated) onUpdated();
    } catch (err) {
      setError(err.response?.data?.detail || 'Assignment failed.');
    }
  };

  if (loading) return <div style={{padding:'2rem',textAlign:'center'}}>Loading asset...</div>;
  if (error) return <div style={{padding:'2rem',maxWidth:'700px',margin:'auto'}}><button className="btn btn-secondary" onClick={onBack}>Back</button><div style={{marginTop:'1rem',color:'#ef4444'}}>{error}</div></div>;

  return (
    <div style={{maxWidth:'700px',margin:'2rem auto',padding:'1rem'}}>
      <button className="btn btn-secondary btn-sm" onClick={onBack}>Back</button>
      <div style={{background:'#0a0a0a',border:'2px solid #ff5500',borderRadius:'8px',padding:'1.5rem',marginTop:'1rem'}}>
        <div style={{display:'flex',justifyContent:'space-between',gap:'1rem',flexWrap:'wrap'}}>
          <div>
            <h1 style={{color:'#ff5500',marginTop:0}}>{asset.name}</h1>
            <p><strong>Asset ID:</strong> {asset.asset_tag}</p>
            <p><strong>Serial:</strong> {asset.serial_number}</p>
            <p><strong>Category:</strong> {asset.category?.name || 'Uncategorized'}</p>
            <p><strong>Location:</strong> {asset.location || 'APEX HUB'}</p>
            <p><strong>Current user:</strong> {asset.assigned_user?.full_name || 'Unassigned'}</p>
          </div>
          <QRCodeSVG value={`${window.location.origin}/scan/${asset.qr_token}`} size={150} bgColor="#fff" />
        </div>

        <hr style={{borderColor:'#222',margin:'1.5rem 0'}} />
        <h2 style={{color:'#ff5500'}}>Assign Asset</h2>
        <select value={selectedUser} onChange={e=>setSelectedUser(e.target.value)}
          style={{width:'100%',padding:'.9rem',background:'#111',color:'#fff',border:'2px solid #333',borderRadius:'4px'}}>
          <option value="">Unassigned</option>
          {users.filter(u=>u.is_active).map(u=><option key={u.id} value={u.id}>{u.full_name} - {u.email}</option>)}
        </select>
        <button className="btn btn-primary" style={{width:'100%',marginTop:'1rem'}} onClick={assign}>Save Assignment</button>

        <h2 style={{color:'#ff5500',marginTop:'2rem'}}>Assignment History</h2>
        {history.length ? history.map(h=><div key={h.id} style={{padding:'.8rem 0',borderBottom:'1px solid #222'}}>
          <strong>{h.action}</strong> - {h.user?.full_name || 'Unassigned'}<br/>
          <small style={{color:'#888'}}>{new Date(h.assigned_at).toLocaleString('en-GB')} | {h.location}</small>
        </div>) : <p style={{color:'#888'}}>No assignment history.</p>}
      </div>
    </div>
  );
}
