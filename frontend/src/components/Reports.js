import React, { useState } from 'react';
import axios from 'axios';
import './Reports.css';

const reports = [
  ['assets.csv','Asset Inventory','Complete asset register including lifecycle, health, warranty and replacement information.'],
  ['maintenance.csv','Maintenance Report','Maintenance schedules, completion history, technicians and costs.'],
  ['warranty.csv','Warranty Report','Warranty providers, references, expiry dates and current status.'],
  ['replacements.csv','Replacement Report','Assets due for replacement, priorities and estimated costs.'],
  ['assignments.csv','Assignment Report','Assignment and return history across the asset estate.']
];

function Reports({ apiUrl, token }) {
  const [downloading, setDownloading] = useState('');
  const [error, setError] = useState('');
  const download = async (file, label) => {
    setDownloading(file); setError('');
    try {
      const response = await axios.get(`${apiUrl}/reports/${file}`, { headers: { Authorization: `Bearer ${token}` }, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a'); link.href = url; link.download = `APEX-${file}`; document.body.appendChild(link); link.click(); link.remove(); window.URL.revokeObjectURL(url);
    } catch (e) { setError(e.response?.data?.detail || `Unable to generate ${label}.`); } finally { setDownloading(''); }
  };
  return <div className="reports-page"><div className="reports-heading"><div><span className="apex-eyebrow">APEX REPORTING</span><h1>Reports & Exports</h1><p>Download operational data in CSV format for finance, management and administration.</p></div></div>{error && <div className="apex-form-message apex-form-error">{error}</div>}<div className="reports-grid">{reports.map(([file,label,description]) => <article key={file} className="report-card"><div><span className="report-icon">CSV</span><h2>{label}</h2><p>{description}</p></div><button className="apex-orange-button" disabled={!!downloading} onClick={() => download(file,label)}>{downloading === file ? 'Generating…' : 'Download CSV'}</button></article>)}</div></div>;
}
export default Reports;
