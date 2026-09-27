import React, { useEffect, useState } from 'react';
import axios from 'axios';
const card={background:'#101010',border:'1px solid #292929',borderRadius:8,padding:22};
const input={width:'100%',boxSizing:'border-box',padding:11,background:'#080808',border:'1px solid #333',color:'#fff',borderRadius:5};
const button={padding:'10px 16px',background:'#ff5500',border:0,color:'#fff',borderRadius:5,fontWeight:700,cursor:'pointer'};
export default function SystemSettings({apiUrl,token}){
 const [s,setS]=useState({default_location:'APEX HUB',user_inactivity_days:'30',maintenance_due_soon_days:'14',organisation_name:'APEX'}); const [msg,setMsg]=useState(''); const [err,setErr]=useState(''); const headers={Authorization:`Bearer ${token}`};
 useEffect(()=>{axios.get(`${apiUrl}/admin/settings`,{headers}).then(r=>setS({...s,...r.data})).catch(e=>setErr(e.response?.data?.detail||'Unable to load settings.'));},[token]);
 const save=async e=>{e.preventDefault();setMsg('');setErr('');try{await axios.put(`${apiUrl}/admin/settings`,s,{headers});setMsg('Settings saved successfully.')}catch(e){setErr(e.response?.data?.detail||'Unable to save settings.')}};
 return <section style={card}><h1 style={{color:'#ff5500',marginTop:0}}>System Settings</h1><p style={{color:'#999'}}>Configure the defaults used across APEX Asset Management.</p><form onSubmit={save} style={{display:'grid',gap:14,maxWidth:650}}>
 <label>Organisation name<input style={input} value={s.organisation_name||''} onChange={e=>setS({...s,organisation_name:e.target.value})}/></label>
 <label>Default location<input style={input} value={s.default_location||''} onChange={e=>setS({...s,default_location:e.target.value})}/></label>
 <label>User inactivity period (days)<input style={input} type="number" min="1" max="3650" value={s.user_inactivity_days||30} onChange={e=>setS({...s,user_inactivity_days:e.target.value})}/></label>
 <label>Maintenance due-soon warning (days)<input style={input} type="number" min="1" max="365" value={s.maintenance_due_soon_days||14} onChange={e=>setS({...s,maintenance_due_soon_days:e.target.value})}/></label>
 <button style={button}>Save Settings</button></form>{(msg||err)&&<p style={{color:err?'#ff9b9b':'#9be7a1'}}>{err||msg}</p>}</section>;
}
