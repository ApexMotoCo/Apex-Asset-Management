import React,{useEffect,useState} from 'react';
import axios from 'axios';
export default function ManagementDashboard({apiUrl,token}){
 const [d,setD]=useState(null),[error,setError]=useState(''); const h={Authorization:`Bearer ${token}`};
 const load=async()=>{try{const r=await axios.get(`${apiUrl}/management/summary`,{headers:h});setD(r.data)}catch(e){setError(e.response?.data?.detail||'Unable to load management dashboard.')}};
 useEffect(()=>{load()},[token]);
 if(error)return <div style={err}>{error}</div>; if(!d)return <div>Loading management dashboard…</div>;
 const cards=[['Employees',d.employees],['Active employees',d.active_employees],['Inactive accounts',d.inactive_employees],['Assigned assets',d.assigned_assets],['Unassigned assets',d.unassigned_assets],['Open issues',d.open_issues],['Overdue maintenance',d.overdue_maintenance],['Warranty alerts',d.warranty_alerts],['Replacement alerts',d.replacement_alerts],['Unread notifications',d.unread_notifications]];
 return <div><div style={{marginBottom:24}}><h1>Management Overview</h1><div style={{color:'#999'}}>Operational KPIs and items requiring management attention.</div></div><div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(190px,1fr))',gap:14}}>{cards.map(([l,v])=><div key={l} style={card}><div style={{color:'#888',fontSize:12,textTransform:'uppercase'}}>{l}</div><div style={{fontSize:30,fontWeight:900,marginTop:7}}>{v}</div></div>)}</div><div style={{marginTop:25,...card}}><div style={{fontWeight:800,marginBottom:12}}>Asset value</div><div style={{fontSize:28,fontWeight:900}}>£{Number(d.asset_value||0).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}</div><div style={{color:'#777',marginTop:6}}>Total recorded asset value</div></div></div>;
}
const card={background:'#101010',border:'1px solid #252525',borderRadius:10,padding:18};const err={background:'#2a1212',color:'#ffb3b3',padding:15,borderRadius:8};
