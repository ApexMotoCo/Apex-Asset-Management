import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function AdminUserManagement({ token, onBackToDashboard }) {
  const API_URL = process.env.REACT_APP_API_URL || '/api';

  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({
    email: '',
    full_name: '',
    phone: '',
    role: 'member',
    location: 'APEX HUB'
  });

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const headers = {
    Authorization: `Bearer ${token}`
  };

  const load = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/admin/users?limit=200`,
        { headers }
      );

      setUsers(response.data);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        'Unable to load users.'
      );
    }
  };

  useEffect(() => {
    load();
  }, []);

  const invite = async (e) => {
    e.preventDefault();

    setMessage('');
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/admin/users/invite`,
        form,
        { headers }
      );

      if (response.data.invite_url) {
        setMessage(
          `${response.data.message}\n\nFallback invitation link:\n${response.data.invite_url}`
        );
      } else {
        setMessage(response.data.message);
      }

      setForm({
        email: '',
        full_name: '',
        phone: '',
        role: 'member',
        location: 'APEX HUB'
      });

      load();
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        'Invitation failed.'
      );
    } finally {
      setLoading(false);
    }
  };

  const resend = async (id) => {
    setMessage('');
    setError('');

    try {
      const response = await axios.post(
        `${API_URL}/admin/users/${id}/resend-invite`,
        {},
        { headers }
      );

      if (response.data.invite_url) {
        setMessage(
          `${response.data.message}\n\nFallback invitation link:\n${response.data.invite_url}`
        );
      } else {
        setMessage(response.data.message);
      }
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        'Unable to resend invitation.'
      );
    }
  };

  const deactivate = async (id) => {
    if (!window.confirm('Deactivate this user?')) {
      return;
    }

    setMessage('');
    setError('');

    try {
      await axios.delete(
        `${API_URL}/admin/users/${id}`,
        { headers }
      );

      setMessage('User deactivated successfully.');
      load();
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        'Unable to deactivate user.'
      );
    }
  };

  const getStatus = (user) => {
    if (!user.is_active) {
      return {
        label: 'Inactive',
        className: 'status-inactive'
      };
    }

    if (!user.is_verified) {
      return {
        label: 'Invited',
        className: 'status-invited'
      };
    }

    return {
      label: 'Active',
      className: 'status-active'
    };
  };

  return (
    <div className="apex-user-management">

      {/* PAGE HEADER */}

      <div className="apex-page-heading">
        <div>
          <div className="apex-eyebrow">
            ADMINISTRATION
          </div>

          <h1>
            User Management
          </h1>

          <p>
            Manage staff access, invitations and account status.
            All new users are assigned to <strong>APEX HUB</strong>.
          </p>
        </div>

        <div className="apex-user-count">
          <span>Total Users</span>
          <strong>{users.length}</strong>
        </div>
      </div>


      {/* MESSAGES */}

      {message && (
        <div className="apex-message apex-message-success">
          <div className="apex-message-icon">
            ✓
          </div>

          <div>
            <strong>Success</strong>

            <div className="apex-message-text">
              {message}
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="apex-message apex-message-error">
          <div className="apex-message-icon">
            !
          </div>

          <div>
            <strong>Error</strong>

            <div className="apex-message-text">
              {error}
            </div>
          </div>
        </div>
      )}


      {/* INVITE USER */}

      <section className="apex-admin-card">

        <div className="apex-card-heading">
          <div>
            <span className="apex-card-label">
              ACCESS CONTROL
            </span>

            <h2>
              Invite New User
            </h2>

            <p>
              Send an invitation email allowing a staff member
              to create their account.
            </p>
          </div>
        </div>


        <form
          onSubmit={invite}
          className="apex-invite-form"
        >

          <div className="apex-field">
            <label>
              Full Name
            </label>

            <input
              required
              type="text"
              placeholder="e.g. John Smith"
              value={form.full_name}
              onChange={(e) =>
                setForm({
                  ...form,
                  full_name: e.target.value
                })
              }
            />
          </div>


          <div className="apex-field">
            <label>
              Email Address
            </label>

            <input
              required
              type="email"
              placeholder="name@company.com"
              value={form.email}
              onChange={(e) =>
                setForm({
                  ...form,
                  email: e.target.value
                })
              }
            />
          </div>


          <div className="apex-field">
            <label>
              Phone
            </label>

            <input
              type="tel"
              placeholder="Optional"
              value={form.phone}
              onChange={(e) =>
                setForm({
                  ...form,
                  phone: e.target.value
                })
              }
            />
          </div>


          <div className="apex-field">
            <label>
              Role
            </label>

            <select
              value={form.role}
              onChange={(e) =>
                setForm({
                  ...form,
                  role: e.target.value
                })
              }
            >
              <option value="member">
                Member
              </option>

              <option value="admin">
                Admin
              </option>
            </select>
          </div>


          <div className="apex-field">
            <label>
              Primary Location
            </label>

            <input
              value="APEX HUB"
              readOnly
            />

            <small>
              New users are automatically assigned to APEX HUB.
            </small>
          </div>


          <div className="apex-field apex-field-action">
            <label>
              &nbsp;
            </label>

            <button
              type="submit"
              className="apex-orange-button"
              disabled={loading}
            >
              {loading
                ? 'SENDING INVITATION...'
                : 'INVITE USER'}
            </button>
          </div>

        </form>

      </section>


      {/* USER LIST */}

      <section className="apex-admin-card">

        <div className="apex-card-heading">
          <div>
            <span className="apex-card-label">
              DIRECTORY
            </span>

            <h2>
              Users
            </h2>

            <p>
              Current staff accounts and invitation status.
            </p>
          </div>
        </div>


        <div className="apex-table-wrapper">

          <table className="apex-user-table">

            <thead>
              <tr>
                <th>
                  USER
                </th>

                <th>
                  EMAIL
                </th>

                <th>
                  ROLE
                </th>

                <th>
                  LOCATION
                </th>

                <th>
                  STATUS
                </th>

                <th>
                  ACTIONS
                </th>
              </tr>
            </thead>

            <tbody>

              {users.length === 0 && (
                <tr>
                  <td
                    colSpan="6"
                    className="apex-empty-row"
                  >
                    No users found.
                  </td>
                </tr>
              )}

              {users.map((user) => {

                const status = getStatus(user);

                return (
                  <tr key={user.id}>

                    <td>
                      <div className="apex-user-name">
                        {user.full_name}
                      </div>
                    </td>

                    <td>
                      <span className="apex-user-email">
                        {user.email}
                      </span>
                    </td>

                    <td>
                      <span className="apex-role-badge">
                        {user.role}
                      </span>
                    </td>

                    <td>
                      {user.location || 'APEX HUB'}
                    </td>

                    <td>
                      <span
                        className={`apex-status ${status.className}`}
                      >
                        <span className="apex-status-dot" />
                        {status.label}
                      </span>
                    </td>

                    <td>

                      <div className="apex-actions">

                        {!user.is_verified && (
                          <button
                            className="apex-small-button"
                            onClick={() => resend(user.id)}
                          >
                            RESEND
                          </button>
                        )}

                        {user.email !== 'support@apexingoodcompany.co.uk' &&
                          user.is_active && (
                            <button
                              className="apex-small-button apex-danger-button"
                              onClick={() =>
                                deactivate(user.id)
                              }
                            >
                              DEACTIVATE
                            </button>
                          )}

                      </div>

                    </td>

                  </tr>
                );
              })}

            </tbody>

          </table>

        </div>

      </section>

    </div>
  );
}