import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

export default function Employees({ token, assets = [] }) {
  const API_URL = process.env.REACT_APP_API_URL || '/api';

  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const headers = {
    Authorization: `Bearer ${token}`
  };

  const loadEmployees = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.get(
        `${API_URL}/admin/users?limit=200`,
        { headers }
      );

      setUsers(response.data || []);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        'Unable to load employees.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmployees();
  }, [token]);

  const getStatus = (user) => {
    if (!user.is_active) {
      return 'inactive';
    }

    if (!user.is_verified) {
      return 'invited';
    }

    return 'active';
  };

  const getAssignedAssetCount = (user) => {
    return assets.filter(
      (asset) =>
        Number(asset.assigned_user_id) === Number(user.id)
    ).length;
  };

  const filteredUsers = useMemo(() => {
    const query = search.trim().toLowerCase();

    return users.filter((user) => {
      const status = getStatus(user);

      if (
        statusFilter !== 'all' &&
        status !== statusFilter
      ) {
        return false;
      }

      if (!query) {
        return true;
      }

      return [
        user.full_name,
        user.email,
        user.phone,
        user.location,
        user.role
      ]
        .filter(Boolean)
        .some((value) =>
          String(value)
            .toLowerCase()
            .includes(query)
        );
    });
  }, [users, search, statusFilter, assets]);

  const stats = useMemo(() => {
    return {
      total: users.length,
      active: users.filter(
        (user) => getStatus(user) === 'active'
      ).length,
      invited: users.filter(
        (user) => getStatus(user) === 'invited'
      ).length,
      inactive: users.filter(
        (user) => getStatus(user) === 'inactive'
      ).length
    };
  }, [users]);

  return (
    <div className="apex-user-management">

      {/* PAGE HEADER */}

      <div className="apex-page-heading">

        <div>
          <div className="apex-eyebrow">
            PEOPLE & ACCESS
          </div>

          <h1>
            Employees
          </h1>

          <p>
            View staff accounts, locations, access status and
            assigned company assets.
          </p>
        </div>

        <div className="apex-user-count">
          <span>
            Employees
          </span>

          <strong>
            {stats.total}
          </strong>
        </div>

      </div>


      {/* STAT CARDS */}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            'repeat(auto-fit, minmax(160px, 1fr))',
          gap: '14px',
          marginBottom: '24px'
        }}
      >

        <StatCard
          label="Total"
          value={stats.total}
        />

        <StatCard
          label="Active"
          value={stats.active}
        />

        <StatCard
          label="Invited"
          value={stats.invited}
        />

        <StatCard
          label="Inactive"
          value={stats.inactive}
        />

      </div>


      {/* FILTERS */}

      <section className="apex-admin-card">

        <div
          style={{
            display: 'grid',
            gridTemplateColumns:
              'minmax(250px, 1fr) 180px',
            gap: '14px'
          }}
        >

          <div className="apex-field">

            <label>
              Search Employees
            </label>

            <input
              type="search"
              placeholder="Search name, email, phone or location..."
              value={search}
              onChange={(e) =>
                setSearch(e.target.value)
              }
            />

          </div>


          <div className="apex-field">

            <label>
              Status
            </label>

            <select
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(e.target.value)
              }
            >
              <option value="all">
                All Employees
              </option>

              <option value="active">
                Active
              </option>

              <option value="invited">
                Invited
              </option>

              <option value="inactive">
                Inactive
              </option>
            </select>

          </div>

        </div>

      </section>


      {/* ERROR */}

      {error && (
        <div className="apex-message apex-message-error">

          <div className="apex-message-icon">
            !
          </div>

          <div>
            <strong>
              Unable to load employees
            </strong>

            <div className="apex-message-text">
              {error}
            </div>
          </div>

        </div>
      )}


      {/* EMPLOYEE TABLE */}

      <section className="apex-admin-card">

        <div className="apex-card-heading">

          <div>
            <span className="apex-card-label">
              EMPLOYEE DIRECTORY
            </span>

            <h2>
              Staff
            </h2>

            <p>
              {filteredUsers.length} employee
              {filteredUsers.length === 1 ? '' : 's'} displayed.
            </p>
          </div>

        </div>


        {loading ? (

          <div
            style={{
              padding: '45px',
              textAlign: 'center',
              color: '#777'
            }}
          >
            Loading employees...
          </div>

        ) : (

          <div className="apex-table-wrapper">

            <table className="apex-user-table">

              <thead>

                <tr>
                  <th>EMPLOYEE</th>
                  <th>CONTACT</th>
                  <th>LOCATION</th>
                  <th>ROLE</th>
                  <th>ASSETS</th>
                  <th>STATUS</th>
                </tr>

              </thead>

              <tbody>

                {filteredUsers.length === 0 && (

                  <tr>

                    <td
                      colSpan="6"
                      className="apex-empty-row"
                    >
                      No employees match your search.
                    </td>

                  </tr>

                )}


                {filteredUsers.map((user) => {

                  const status = getStatus(user);
                  const assetCount =
                    getAssignedAssetCount(user);

                  return (
                    <tr key={user.id}>

                      {/* EMPLOYEE */}

                      <td>

                        <div className="apex-user-name">
                          {user.full_name}
                        </div>

                      </td>


                      {/* CONTACT */}

                      <td>

                        <div>
                          <span className="apex-user-email">
                            {user.email}
                          </span>
                        </div>

                        {user.phone && (
                          <div
                            style={{
                              marginTop: '4px',
                              color: '#666',
                              fontSize: '11px'
                            }}
                          >
                            {user.phone}
                          </div>
                        )}

                      </td>


                      {/* LOCATION */}

                      <td>
                        {user.location || 'APEX HUB'}
                      </td>


                      {/* ROLE */}

                      <td>

                        <span className="apex-role-badge">
                          {user.role}
                        </span>

                      </td>


                      {/* ASSETS */}

                      <td>

                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            minWidth: '30px',
                            padding: '4px 8px',
                            background: '#171717',
                            border: '1px solid #303030',
                            borderRadius: '3px',
                            color:
                              assetCount > 0
                                ? '#ff5500'
                                : '#777',
                            fontSize: '11px',
                            fontWeight: 800
                          }}
                        >
                          {assetCount}
                        </span>

                      </td>


                      {/* STATUS */}

                      <td>

                        <span
                          className={`apex-status ${
                            status === 'active'
                              ? 'status-active'
                              : status === 'invited'
                                ? 'status-invited'
                                : 'status-inactive'
                          }`}
                        >

                          <span className="apex-status-dot" />

                          {status}

                        </span>

                      </td>

                    </tr>
                  );
                })}

              </tbody>

            </table>

          </div>

        )}

      </section>

    </div>
  );
}


/* =========================================================
   STAT CARD
   ========================================================= */

function StatCard({ label, value }) {
  return (
    <div
      style={{
        background: '#0c0c0c',
        border: '1px solid #252525',
        borderRadius: '6px',
        padding: '18px 20px'
      }}
    >

      <div
        style={{
          color: '#777',
          fontSize: '10px',
          fontWeight: 800,
          letterSpacing: '0.12em',
          textTransform: 'uppercase'
        }}
      >
        {label}
      </div>

      <div
        style={{
          marginTop: '7px',
          color: '#ff5500',
          fontSize: '25px',
          fontWeight: 700
        }}
      >
        {value}
      </div>

    </div>
  );
}