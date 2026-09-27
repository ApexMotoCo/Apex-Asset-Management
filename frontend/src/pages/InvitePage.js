import React, { useState } from 'react';
import axios from 'axios';

export default function InvitePage({ apiUrl, token }) {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [state, setState] = useState({loading:false,error:'',success:''});

  const inviteToken = window.location.pathname.split('/invite/')[1] || token;

  const submit = async (e) => {
    e.preventDefault();
    setState({loading:true,error:'',success:''});
    if (password.length < 10) return setState({loading:false,error:'Password must be at least 10 characters long',success:''});
    if (password !== confirm) return setState({loading:false,error:'Passwords do not match',success:''});
    try {
      const r = await axios.post(`${apiUrl}/invitations/accept`, {token: inviteToken, password});
      setState({loading:false,error:'',success:r.data.message + ' You can now return to the login page.'});
    } catch (err) {
      setState({loading:false,error:err.response?.data?.detail || 'Invitation could not be accepted.',success:''});
    }
  };

  return (
    <div style={{minHeight:'100vh',background:'#050505',display:'flex',alignItems:'center',justifyContent:'center',padding:'1rem'}}>
      <div style={{maxWidth:'460px',width:'100%',background:'#0a0a0a',border:'2px solid #ff5500',borderRadius:'8px',padding:'2rem'}}>
        <div style={{textAlign:'center',marginBottom:'1.5rem'}}>
          <img src="/apex-logo.png" alt="APEX" style={{height:'65px'}} />
          <h1 style={{color:'#ff5500'}}>Activate your APEX account</h1>
          <p style={{color:'#aaa'}}>Your default location is APEX HUB.</p>
        </div>
        {state.error && <div style={{padding:'1rem',color:'#ef4444',background:'rgba(239,68,68,.12)',marginBottom:'1rem'}}>{state.error}</div>}
        {state.success && <div style={{padding:'1rem',color:'#22c55e',background:'rgba(34,197,94,.12)',marginBottom:'1rem'}}>{state.success}</div>}
        {!state.success && <form onSubmit={submit}>
          <label style={{color:'#ff5500',display:'block',marginBottom:'.5rem'}}>Create password</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength="10" required
            style={{width:'100%',boxSizing:'border-box',padding:'.85rem',background:'#111',color:'#fff',border:'2px solid #333',borderRadius:'4px',marginBottom:'1rem'}} />
          <label style={{color:'#ff5500',display:'block',marginBottom:'.5rem'}}>Confirm password</label>
          <input type="password" value={confirm} onChange={e=>setConfirm(e.target.value)} minLength="10" required
            style={{width:'100%',boxSizing:'border-box',padding:'.85rem',background:'#111',color:'#fff',border:'2px solid #333',borderRadius:'4px',marginBottom:'1rem'}} />
          <button className="btn btn-primary" type="submit" disabled={state.loading} style={{width:'100%'}}>
            {state.loading ? 'Activating...' : 'Activate Account'}
          </button>
        </form>}
      </div>
    </div>
  );
}
