import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function EmployeeManagement({ apiUrl, token }) {
  const [employees,setEmployees]=useState([]); const [loading,setLoading]=useState(true); const [search,setSearch]=useState(''); const [error,setError]=useState('');
  const headers={Authorization:`Bearer ${token}`};
  const load=async()=>{setLoading(true);try{const r=await axios.get(`${apiUrl}/admin/employees`,{headers});setEmployees(r.data||[]);setError('')}catch(e){setError(e.response?.data?.detail||'Unable to load employees.')}finally{setLoading(false)}};
  useEffect(()=>{load()},[token]);
  const toggle=async(e)=>{if(e.email && e.email.toLowerCase()===localStorage.getItem('admin_email')?.toLowerCase()) return; try{await axios.patch(`${apiUrl}/admin/users/${e.id}/status`,{is_active:!e.is_active},{headers});load()}catch(x){setError(x.response?.data?.detail||'Unable to update employee.')}};
  const filtered=employees.filter(e=>`${e.full_name} ${e.email} ${e.location} ${e.role}`.toLowerCase().includes(search.toLowerCase()));
  return <div style={{maxWidth:1200,margin:'0 auto'}}>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'end',gap:15,flexWrap:'wrap',marginBottom:22}}><div><h1 style={{marginBottom:6}}>Employee Management</h1><div style={{color:'#999'}}>Manage account status, roles, locations and assigned equipment.</div></div><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search employees…" style={input}/></div>
    {error&&<div style={errorStyle}>{error}</div>}
    <div style={{background:'#101010',border:'1px solid #252525',borderRadius:10,overflow:'auto'}}>
      {loading?<div style={{padding:25}}>Loading employees…</div>:<table style={{width:'100%',borderCollapse:'collapse',minWidth:850}}><thead><tr>{['Employee','Role','Location','Assets','Last Login','Status','Action'].map(x=><th key={x} style={th}>{x}</th>)}</tr></thead><tbody>{filtered.map(e=><tr key={e.id}><td style={td}><div style={{fontWeight:800}}>{e.full_name}</div><div style={{fontSize:12,color:'#777'}}>{e.email}</div></td><td style={td}>{e.role}</td><td style={td}>{e.location||'APEX HUB'}</td><td style={td}>{e.asset_count}</td><td style={td}>{e.last_login?new Date(e.last_login).toLocaleString():'Never'}</td><td style={td}><span style={{padding:'5px 8px',borderRadius:12,background:e.is_active?'#12351f':'#321515',color:e.is_active?'#78e09b':'#ff9b9b',fontSize:12,fontWeight:800}}>{e.is_active?'ACTIVE':'INACTIVE'}</span></td><td style={td}><button disabled={e.role==='super_admin'} onClick={()=>toggle(e)} style={{...action,opacity:e.role==='super_admin'?0.4:1}}>{e.is_active?'Deactivate':'Reactivate'}</button></td></tr>)}</tbody></table>}
      {!loading&&!filtered.length&&<div style={{padding:25,color:'#888'}}>No employees found.</div>}
    </div>
  </div>;
}
const input={background:'#111',color:'#fff',border:'1px solid #333',borderRadius:6,padding:'11px 13px',minWidth:250};
const th={textAlign:'left',padding:13,borderBottom:'1px solid #292929',color:'#888',fontSize:12,textTransform:'uppercase'};
const td={padding:13,borderBottom:'1px solid #202020',verticalAlign:'middle'};
const action={background:'#171717',color:'#fff',border:'1px solid #444',borderRadius:6,padding:'7px 10px',cursor:'pointer'};
const errorStyle={background:'#2a1212',border:'1px solid #6d2b2b',color:'#ffb3b3',padding:12,borderRadius:7,marginBottom:15};
