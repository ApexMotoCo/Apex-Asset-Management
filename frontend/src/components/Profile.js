import React, { useEffect, useState } from 'react';
import axios from 'axios';

const card = { background:'#101010', border:'1px solid #292929', borderRadius:8, padding:22 };
const input = { width:'100%', boxSizing:'border-box', padding:11, background:'#080808', border:'1px solid #333', color:'#fff', borderRadius:5 };
const button = { padding:'10px 16px', background:'#ff5500', border:0, color:'#fff', borderRadius:5, fontWeight:700, cursor:'pointer' };

export default function Profile({ apiUrl, token, onUpdated }) {
  const [profile, setProfile] = useState({ full_name:'', email:'', phone:'', bio:'', location:'APEX HUB' });
  const [passwords, setPasswords] = useState({ current_password:'', new_password:'', confirm_password:'' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const headers = { Authorization:`Bearer ${token}` };

  useEffect(() => {
    axios.get(`${apiUrl}/users/me`, { headers }).then(r => setProfile({
      full_name:r.data.full_name || '', email:r.data.email || '', phone:r.data.phone || '',
      bio:r.data.bio || '', location:r.data.location || 'APEX HUB'
    })).catch(e => setError(e.response?.data?.detail || 'Unable to load profile.'));
  }, [token]);

  const save = async e => {
    e.preventDefault(); setError(''); setMessage('');
    try { await axios.put(`${apiUrl}/users/me`, { full_name:profile.full_name, phone:profile.phone, bio:profile.bio, location:profile.location }, {headers}); setMessage('Profile updated successfully.'); onUpdated?.(); }
    catch(e) { setError(e.response?.data?.detail || 'Unable to update profile.'); }
  };

  const changePassword = async e => {
    e.preventDefault(); setError(''); setMessage('');
    if (passwords.new_password !== passwords.confirm_password) return setError('New passwords do not match.');
    try { await axios.post(`${apiUrl}/users/me/change-password`, { current_password:passwords.current_password, new_password:passwords.new_password }, {headers}); setPasswords({current_password:'',new_password:'',confirm_password:''}); setMessage('Password changed successfully.'); }
    catch(e) { setError(e.response?.data?.detail || 'Unable to change password.'); }
  };

  return <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(320px,1fr))',gap:20}}>
    <section style={card}><h2 style={{color:'#ff5500',marginTop:0}}>My Profile</h2><p style={{color:'#999'}}>Update your account details and APEX HUB profile information.</p>
      <form onSubmit={save} style={{display:'grid',gap:12}}>
        <label>Full name<input style={input} value={profile.full_name} onChange={e=>setProfile({...profile,full_name:e.target.value})} required /></label>
        <label>Email<input style={{...input,opacity:.65}} value={profile.email} disabled /></label>
        <label>Phone<input style={input} value={profile.phone} onChange={e=>setProfile({...profile,phone:e.target.value})} /></label>
        <label>Location<input style={input} value={profile.location} onChange={e=>setProfile({...profile,location:e.target.value})} /></label>
        <label>Bio<textarea style={{...input,minHeight:100}} value={profile.bio} onChange={e=>setProfile({...profile,bio:e.target.value})} /></label>
        <button style={button}>Save Profile</button>
      </form>
    </section>
    <section style={card}><h2 style={{color:'#ff5500',marginTop:0}}>Change Password</h2><p style={{color:'#999'}}>Use a strong password and never reuse it elsewhere.</p>
      <form onSubmit={changePassword} style={{display:'grid',gap:12}}>
        <label>Current password<input style={input} type="password" value={passwords.current_password} onChange={e=>setPasswords({...passwords,current_password:e.target.value})} required /></label>
        <label>New password<input style={input} type="password" value={passwords.new_password} onChange={e=>setPasswords({...passwords,new_password:e.target.value})} minLength={10} required /></label>
        <label>Confirm new password<input style={input} type="password" value={passwords.confirm_password} onChange={e=>setPasswords({...passwords,confirm_password:e.target.value})} minLength={10} required /></label>
        <button style={button}>Change Password</button>
      </form>
    </section>
    {(message || error) && <div style={{...card,gridColumn:'1 / -1',color:error?'#ff9b9b':'#9be7a1'}}>{error || message}</div>}
  </div>;
}
