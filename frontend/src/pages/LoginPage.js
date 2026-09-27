import React, { useState } from 'react';
import axios from 'axios';

function LoginPage({ onLoginSuccess, apiUrl }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail) {
      setError('Please enter your email address.');
      return;
    }
    setLoading(true);

    try {
      const response = await axios.post(`${apiUrl}/login`, { email: normalizedEmail, password: password || undefined });
      localStorage.setItem('admin_token', response.data.access_token);
      localStorage.setItem('admin_email', response.data.email);
      localStorage.setItem('admin_role', response.data.role || 'member');
      setSuccess('Login successful! Redirecting...');
      onLoginSuccess(response.data.access_token, response.data.email, response.data.role || 'member');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string'
        ? detail
        : 'Login failed. Please use an authorized email address.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#050505',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem'
    }}>
      <div style={{
        maxWidth: '400px',
        width: '100%',
        background: '#0a0a0a',
        border: '2px solid #ff5500',
        borderRadius: '6px',
        padding: '2rem',
        boxShadow: '0 8px 32px rgba(255, 85, 0, 0.3)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ color: '#ff5500', margin: '0 0 0.5rem 0', fontSize: '1.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Admin Login
          </h1>
          <p style={{ color: '#b8b8b8', margin: 0, fontSize: '0.9rem' }}>
            APEX Asset Management
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div style={{
              padding: '1rem',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid #ef4444',
              borderRadius: '4px',
              color: '#ef4444',
              marginBottom: '1rem',
              fontSize: '0.9rem',
              fontWeight: '600'
            }}>
              WARNING: {error}
            </div>
          )}
          {success && (
            <div style={{
              padding: '1rem',
              background: 'rgba(34, 197, 94, 0.15)',
              border: '1px solid #22c55e',
              borderRadius: '4px',
              color: '#22c55e',
              marginBottom: '1rem',
              fontSize: '0.9rem',
              fontWeight: '600'
            }}>
              OK: {success}
            </div>
          )}

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block',
              color: '#ff5500',
              fontWeight: '600',
              marginBottom: '0.5rem',
              fontSize: '0.9rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="support@apexingoodcompany.co.uk"
              required
              style={{
                width: '100%',
                padding: '0.8rem',
                border: '2px solid #1f1f1f',
                borderRadius: '4px',
                background: '#111111',
                color: '#e5e5e5',
                fontSize: '0.95rem',
                fontFamily: 'inherit',
                boxSizing: 'border-box',
                transition: 'all 0.3s ease'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#ff5500';
                e.target.style.background = '#0a0a0a';
                e.target.style.boxShadow = '0 0 0 3px rgba(255, 85, 0, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#1f1f1f';
                e.target.style.background = '#111111';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{
              display: 'block', color: '#ff5500', fontWeight: '600',
              marginBottom: '0.5rem', fontSize: '0.9rem',
              textTransform: 'uppercase', letterSpacing: '0.05em'
            }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password (invited users)"
              style={{
                width: '100%', padding: '0.8rem', border: '2px solid #1f1f1f',
                borderRadius: '4px', background: '#111111', color: '#e5e5e5',
                fontSize: '0.95rem', boxSizing: 'border-box'
              }}
            />
            <small style={{display:'block',marginTop:'.4rem',color:'#777'}}>
              Existing APEX administrators can leave this blank.
            </small>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '0.85rem',
              background: 'linear-gradient(135deg, #ff5500 0%, #ff7722 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.9rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
              boxShadow: '0 6px 20px rgba(255, 85, 0, 0.3)',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 10px 28px rgba(255, 85, 0, 0.45)';
                e.target.style.background = 'linear-gradient(135deg, #ff6b2c 0%, #ff8033 100%)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0px)';
              e.target.style.boxShadow = '0 6px 20px rgba(255, 85, 0, 0.3)';
              e.target.style.background = 'linear-gradient(135deg, #ff5500 0%, #ff7722 100%)';
            }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div style={{
          marginTop: '1.5rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid #1f1f1f',
          textAlign: 'center',
          color: '#666',
          fontSize: '0.85rem'
        }}>
          Authorized email addresses only<br />
          support@apexingoodcompany.co.uk<br />
          business@apexingoodcompany.co.uk
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
