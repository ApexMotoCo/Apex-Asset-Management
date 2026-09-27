import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function NotificationCenter({ apiUrl, token }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');

  const headers = { Authorization: `Bearer ${token}` };

  const load = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${apiUrl}/notifications`, { headers });
      setItems(r.data || []);
      setError('');
    } catch (e) {
      setError(e.response?.data?.detail || 'Unable to load notifications.');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [token]);

  const markRead = async (id) => {
    try {
      await axios.post(`${apiUrl}/notifications/${id}/read`, {}, { headers });
      setItems(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (e) { setError(e.response?.data?.detail || 'Unable to update notification.'); }
  };

  const markAll = async () => {
    try {
      await axios.post(`${apiUrl}/notifications/read-all`, {}, { headers });
      setItems(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (e) { setError(e.response?.data?.detail || 'Unable to update notifications.'); }
  };

  const visible = items.filter(n => filter === 'unread' ? !n.is_read : true);
  const unread = items.filter(n => !n.is_read).length;

  return <div style={{maxWidth:1100, margin:'0 auto'}}>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:15,flexWrap:'wrap',marginBottom:24}}>
      <div><h1 style={{marginBottom:6}}>Notifications</h1><div style={{color:'#999'}}>Alerts, reminders and actions that need attention.</div></div>
      <button onClick={markAll} disabled={!unread} style={buttonStyle(!unread)}>Mark all read</button>
    </div>
    <div style={{display:'flex',gap:8,marginBottom:18}}>
      <button onClick={()=>setFilter('all')} style={pill(filter==='all')}>All ({items.length})</button>
      <button onClick={()=>setFilter('unread')} style={pill(filter==='unread')}>Unread ({unread})</button>
      <button onClick={load} style={pill(false)}>Refresh</button>
    </div>
    {error && <div style={errorStyle}>{error}</div>}
    {loading ? <div style={card}>Loading notifications…</div> : visible.length === 0 ? <div style={card}>You're all caught up.</div> : visible.map(n => (
      <div key={n.id} style={{...card, borderLeft:`4px solid ${priorityColor(n.notification_type)}`, opacity:n.is_read?0.7:1}}>
        <div style={{display:'flex',justifyContent:'space-between',gap:15}}>
          <div>
            <div style={{fontWeight:800,fontSize:16}}>{n.title}</div>
            <div style={{color:'#ccc',marginTop:7,lineHeight:1.5}}>{n.message}</div>
            <div style={{color:'#777',fontSize:12,marginTop:10}}>{new Date(n.created_at).toLocaleString()} · {n.notification_type}</div>
          </div>
          {!n.is_read && <button onClick={()=>markRead(n.id)} style={buttonStyle(false)}>Mark read</button>}
        </div>
      </div>
    ))}
  </div>;
}

const card={background:'#101010',border:'1px solid #252525',borderRadius:10,padding:18,marginBottom:12};
const buttonStyle=disabled=>({background:disabled?'#171717':'#ff5500',color:disabled?'#666':'#fff',border:'none',borderRadius:6,padding:'9px 13px',fontWeight:800,cursor:disabled?'not-allowed':'pointer'});
const pill=active=>({background:active?'#ff5500':'#171717',color:'#fff',border:'1px solid #333',borderRadius:20,padding:'8px 13px',cursor:'pointer'});
const errorStyle={background:'#2a1212',border:'1px solid #6d2b2b',color:'#ffb3b3',padding:12,borderRadius:7,marginBottom:15};
const priorityColor=t=>t==='Critical'?'#ff3333':t==='Warning'?'#ff9900':t==='Success'?'#36c275':'#777';
