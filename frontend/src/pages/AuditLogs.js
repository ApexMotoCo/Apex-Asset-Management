import React, { useState, useEffect } from 'react';
import axios from 'axios';

function AuditLogs({ apiUrl, token, email }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterEmail, setFilterEmail] = useState('');

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${apiUrl}/audit-logs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLogs(response.data);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch audit logs');
    }
    setLoading(false);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'CREATE':
        return '#22c55e';
      case 'UPDATE':
        return '#3b82f6';
      case 'DELETE':
        return '#ef4444';
      case 'LOGIN':
        return '#f59e0b';
      default:
        return '#ff5500';
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchesAction = !filterAction || log.action === filterAction;
    const matchesEmail = !filterEmail || log.email.toLowerCase().includes(filterEmail.toLowerCase());
    return matchesAction && matchesEmail;
  });

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ color: '#ff5500', fontSize: '1.8rem', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Audit Logs (Super User Only)
      </h1>

      {error && (
        <div style={{
          padding: '1rem',
          background: 'rgba(239, 68, 68, 0.15)',
          border: '2px solid #ef4444',
          borderRadius: '4px',
          color: '#ef4444',
          marginBottom: '1rem',
          fontWeight: '600'
        }}>
          WARNING: {error}
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr auto',
        gap: '1rem',
        marginBottom: '2rem',
        padding: '1rem',
        background: '#0a0a0a',
        border: '2px solid #1f1f1f',
        borderRadius: '6px'
      }}>
        <div>
          <label style={{ color: '#ff5500', fontWeight: '600', display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', textTransform: 'uppercase' }}>
            Filter by Action
          </label>
          <select
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            style={{
              width: '100%',
              padding: '0.8rem',
              border: '2px solid #1f1f1f',
              borderRadius: '4px',
              background: '#111111',
              color: '#e5e5e5',
              fontSize: '0.9rem'
            }}
          >
            <option value="">All Actions</option>
            <option value="CREATE">Create</option>
            <option value="UPDATE">Update</option>
            <option value="DELETE">Delete</option>
            <option value="LOGIN">Login</option>
          </select>
        </div>

        <div>
          <label style={{ color: '#ff5500', fontWeight: '600', display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', textTransform: 'uppercase' }}>
            Filter by Email
          </label>
          <input
            type="text"
            value={filterEmail}
            onChange={(e) => setFilterEmail(e.target.value)}
            placeholder="Search email..."
            style={{
              width: '100%',
              padding: '0.8rem',
              border: '2px solid #1f1f1f',
              borderRadius: '4px',
              background: '#111111',
              color: '#e5e5e5',
              fontSize: '0.9rem',
              boxSizing: 'border-box'
            }}
          />
        </div>

        <button
          onClick={fetchAuditLogs}
          style={{
            padding: '0.8rem 1.5rem',
            background: 'linear-gradient(135deg, #ff5500 0%, #ff7722 100%)',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '0.9rem',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            transition: 'all 0.3s ease',
            height: 'fit-content',
            alignSelf: 'flex-end'
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-2px)';
            e.target.style.boxShadow = '0 10px 28px rgba(255, 85, 0, 0.45)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = 'none';
          }}
        >
          RefreshRefresh
        </button>
      </div>

      <div style={{ color: '#b8b8b8', marginBottom: '1rem', fontSize: '0.95rem' }}>
        Showing {filteredLogs.length} of {logs.length} log entries
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>Loading audit logs...</div>
      ) : filteredLogs.length === 0 ? (
        <div style={{
          textAlign: 'center',
          background: '#111111',
          border: '2px dashed #1f1f1f',
          borderRadius: '6px',
          padding: '3rem 2rem',
          color: '#666'
        }}>
          No audit logs found
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            background: '#0a0a0a',
            border: '2px solid #1f1f1f',
            borderRadius: '6px',
            overflow: 'hidden'
          }}>
            <thead>
              <tr style={{ background: '#111111', borderBottom: '2px solid #1f1f1f' }}>
                <th style={{ padding: '1rem', textAlign: 'left', color: '#ff5500', fontWeight: '600', textTransform: 'uppercase', fontSize: '0.85rem' }}>Date & Time</th>
                <th style={{ padding: '1rem', textAlign: 'left', color: '#ff5500', fontWeight: '600', textTransform: 'uppercase', fontSize: '0.85rem' }}>User</th>
                <th style={{ padding: '1rem', textAlign: 'left', color: '#ff5500', fontWeight: '600', textTransform: 'uppercase', fontSize: '0.85rem' }}>Action</th>
                <th style={{ padding: '1rem', textAlign: 'left', color: '#ff5500', fontWeight: '600', textTransform: 'uppercase', fontSize: '0.85rem' }}>Resource</th>
                <th style={{ padding: '1rem', textAlign: 'left', color: '#ff5500', fontWeight: '600', textTransform: 'uppercase', fontSize: '0.85rem' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log, index) => (
                <tr
                  key={log.id}
                  style={{
                    borderBottom: '1px solid #1f1f1f',
                    background: index % 2 === 0 ? '#0a0a0a' : '#111111',
                    transition: 'all 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#151515';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = index % 2 === 0 ? '#0a0a0a' : '#111111';
                  }}
                >
                  <td style={{ padding: '1rem', color: '#b8b8b8', fontSize: '0.9rem', whiteSpace: 'nowrap' }}>
                    {formatDate(log.created_at)}
                  </td>
                  <td style={{ padding: '1rem', color: '#b8b8b8', fontSize: '0.9rem' }}>
                    <code style={{ background: '#1f1f1f', padding: '0.3rem 0.6rem', borderRadius: '3px', fontSize: '0.85rem' }}>
                      {log.email}
                    </code>
                  </td>
                  <td style={{ padding: '1rem', fontSize: '0.9rem' }}>
                    <span style={{
                      background: `${getActionColor(log.action)}22`,
                      color: getActionColor(log.action),
                      padding: '0.4rem 0.8rem',
                      borderRadius: '3px',
                      fontWeight: '600',
                      textTransform: 'uppercase',
                      fontSize: '0.8rem',
                      display: 'inline-block'
                    }}>
                      {log.action}
                    </span>
                  </td>
                  <td style={{ padding: '1rem', color: '#b8b8b8', fontSize: '0.9rem' }}>
                    <div><strong>{log.resource_type}</strong></div>
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>{log.resource_name}</div>
                  </td>
                  <td style={{ padding: '1rem', color: '#b8b8b8', fontSize: '0.9rem', maxWidth: '300px', wordBreak: 'break-word' }}>
                    {log.details}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AuditLogs;
