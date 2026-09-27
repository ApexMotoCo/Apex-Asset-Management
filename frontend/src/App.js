import React, { useEffect, useState } from 'react';
import axios from 'axios';

import './App.css';
import './styles/Dashboard.css';

import LoginPage from './pages/LoginPage';
import AuditLogs from './pages/AuditLogs';
import QRScanner from './pages/QRScanner';
import AssetScanPage from './pages/AssetScanPage';
import InvitePage from './pages/InvitePage';
import OperationsDashboard from './components/OperationsDashboard';
import AssetProfile from './components/AssetProfile';
import Reports from './components/Reports';
import StockManagement from './components/StockManagement';
import AssetIssues from './components/AssetIssues';
import MyAssets from './components/MyAssets';
import Notifications from './components/Notifications';
import Profile from './components/Profile';
import SystemSettings from './components/SystemSettings';
import EmployeeManagement from './components/EmployeeManagement';
import NotificationCenter from './components/NotificationCenter';
import ManagementDashboard from './components/ManagementDashboard';
import Procurement from './components/Procurement';
import ComplianceDocuments from './components/ComplianceDocuments';
import ExecutiveHub from './components/ExecutiveHub';

import AssetForm from './components/AssetForm';
import AssetList from './components/AssetList';
import CategoryForm from './components/CategoryForm';
import UserDashboard from './components/UserDashboard';
import AdminUserManagement from './components/AdminUserManagement';
import Employees from './components/Employees';
import Maintenance from './components/Maintenance';

const API_URL = process.env.REACT_APP_API_URL || '/api';

function App() {
  const [assets, setAssets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [users, setUsers] = useState([]);

  const [activeTab, setActiveTab] = useState('dashboard');

  const [loading, setLoading] = useState(false);
  const [totalAssetValue, setTotalAssetValue] = useState(0);

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [adminEmail, setAdminEmail] = useState('');
  const [token, setToken] = useState('');
  const [userRole, setUserRole] = useState('member');
  const [selectedAssetId, setSelectedAssetId] = useState(null);

  const path = window.location.pathname;

  const inviteRoute = path.startsWith('/invite/');
  const scanRoute = path.startsWith('/scan/');

  /*
   * =========================================================
   * LOAD SESSION
   * =========================================================
   */

  useEffect(() => {
    const savedToken = localStorage.getItem('admin_token');
    const savedEmail = localStorage.getItem('admin_email');
    const savedRole =
      localStorage.getItem('admin_role') || 'member';

    if (savedToken && savedEmail) {
      setToken(savedToken);
      setAdminEmail(savedEmail);
      setUserRole(savedRole);
      setIsAuthenticated(true);

      fetchAssets(savedToken);
      fetchCategories(savedToken);
      fetchUsers(savedToken);
      fetchUserRole(savedToken);
    }
  }, []);

  /*
   * =========================================================
   * API
   * =========================================================
   */

  const fetchAssets = async (authToken = token) => {
    setLoading(true);

    try {
      const response = await axios.get(
        `${API_URL}/assets`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`
          }
        }
      );

      setAssets(response.data);

      setTotalAssetValue(
        response.data.reduce(
          (sum, asset) =>
            sum + Number(asset.value || 0),
          0
        )
      );
    } catch (error) {
      if (error.response?.status === 401) {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async (authToken = token) => {
    try {
      const response = await axios.get(
        `${API_URL}/categories`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`
          }
        }
      );

      setCategories(response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const fetchUsers = async (authToken = token) => {
    try {
      const response = await axios.get(
        `${API_URL}/admin/users?limit=200`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`
          }
        }
      );

      setUsers(response.data);
    } catch (error) {
      /*
       * User-management pages handle their own
       * display/errors.
       */
    }
  };

  const fetchUserRole = async (authToken = token) => {
    try {
      const response = await axios.get(
        `${API_URL}/users/me`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`
          }
        }
      );

      const role =
        response.data.role || 'member';

      setUserRole(role);
      setAdminEmail(response.data.email);

      localStorage.setItem(
        'admin_role',
        role
      );
    } catch (error) {
      /*
       * Keep the locally stored role if the
       * endpoint isn't available.
       */
    }
  };

  /*
   * =========================================================
   * LOGIN
   * =========================================================
   */

  const handleLoginSuccess = (
    newToken,
    email,
    role = 'member'
  ) => {
    setToken(newToken);
    setAdminEmail(email);
    setUserRole(role);
    setIsAuthenticated(true);

    localStorage.setItem(
      'admin_token',
      newToken
    );

    localStorage.setItem(
      'admin_email',
      email
    );

    localStorage.setItem(
      'admin_role',
      role
    );

    fetchAssets(newToken);
    fetchCategories(newToken);
    fetchUsers(newToken);
  };

  /*
   * =========================================================
   * LOGOUT
   * =========================================================
   */

  const logout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_email');
    localStorage.removeItem('admin_role');

    setToken('');
    setAdminEmail('');
    setUserRole('member');
    setIsAuthenticated(false);

    setAssets([]);
    setCategories([]);
    setUsers([]);

    setActiveTab('dashboard');
  };

  /*
   * =========================================================
   * REFRESH
   * =========================================================
   */

  const refresh = () => {
    fetchAssets();
    fetchCategories();
    fetchUsers();
  };

  /*
   * =========================================================
   * NAVIGATION
   * =========================================================
   */

  const navigate = (tab) => {
    setActiveTab(tab);
  };

  const isAdmin = [
    'admin',
    'super_admin'
  ].includes(userRole);

  const isSuperAdmin =
    userRole === 'super_admin';

  /*
   * =========================================================
   * SPECIAL ROUTES
   * =========================================================
   */

  if (inviteRoute) {
    return (
      <InvitePage
        apiUrl={API_URL}
      />
    );
  }

  if (!isAuthenticated) {
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        apiUrl={API_URL}
      />
    );
  }

  if (scanRoute) {
    return (
      <AssetScanPage
        apiUrl={API_URL}
        token={token}
        onBack={() => {
          window.location.href = '/';
        }}
        onUpdated={refresh}
      />
    );
  }

  /*
   * =========================================================
   * HEADER
   * =========================================================
   */

  const Header = () => (
    <>
      <header
        style={{
          background:
            'linear-gradient(90deg, #180b05 0%, #120b08 55%, #0d0d0d 100%)',
          borderBottom:
            '1px solid #ff5500',
          minHeight: '92px',
          display: 'flex',
          alignItems: 'center',
          padding: '0 42px',
          boxSizing: 'border-box'
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: '1280px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '30px'
          }}
        >

          {/* LOGO */}

          <button
            onClick={() =>
              navigate('dashboard')
            }
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              background: 'transparent',
              border: '0',
              padding: 0,
              cursor: 'pointer',
              color: '#fff'
            }}
          >
            <img
              src="/apex-logo.png"
              alt="APEX"
              style={{
                width: '58px',
                height: '58px',
                objectFit: 'contain'
              }}
            />

            <span
              style={{
                textAlign: 'left'
              }}
            >
              <strong
                style={{
                  display: 'block',
                  color: '#ff5500',
                  fontSize: '22px',
                  letterSpacing: '0.04em',
                  lineHeight: 1.1
                }}
              >
                APEX
              </strong>

              <small
                style={{
                  color: '#b8b8b8',
                  fontSize: '12px'
                }}
              >
                Asset Management
              </small>
            </span>
          </button>


          {/* TAGLINE */}

          <div
            style={{
              flex: 1,
              textAlign: 'center',
              color: '#a7a7a7',
              fontSize: '13px',
              letterSpacing: '0.06em'
            }}
          >
            Enterprise-grade asset tracking and management
          </div>


          {/* ACCOUNT */}

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              whiteSpace: 'nowrap'
            }}
          >
            <span
              style={{
                color: '#ff5500',
                fontSize: '13px',
                fontWeight: 600
              }}
            >
              {adminEmail}
            </span>

            <button
              onClick={logout}
              style={{
                padding: '9px 17px',
                background: 'transparent',
                border: '1px solid #ff5500',
                color: '#ff5500',
                borderRadius: '5px',
                fontWeight: 700,
                fontSize: '12px',
                cursor: 'pointer',
                textTransform: 'uppercase'
              }}
            >
              Logout
            </button>
          </div>

        </div>
      </header>


      {/* =====================================================
          NAVIGATION
          ===================================================== */}

      <nav
        style={{
          background: '#101010',
          borderBottom: '1px solid #242424',
          padding: '15px 20px',
          boxSizing: 'border-box'
        }}
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '10px',
            flexWrap: 'wrap'
          }}
        >

          <NavButton
            label="Dashboard"
            active={
              activeTab === 'dashboard'
            }
            onClick={() =>
              navigate('dashboard')
            }
          />

          {isAdmin && (
            <>
              <NavButton label="Management" active={activeTab === 'management'} onClick={() => navigate('management')} />
              <NavButton label="Procurement" active={activeTab === 'procurement'} onClick={() => navigate('procurement')} />
              <NavButton label="Compliance" active={activeTab === 'compliance'} onClick={() => navigate('compliance')} />
              <NavButton label="Executive" active={activeTab === 'executive'} onClick={() => navigate('executive')} />
            </>
          )}

          <NavButton label="My Profile" active={activeTab === 'profile'} onClick={() => navigate('profile')} />


          {isAdmin && (
            <NavButton
              label="Employees"
              active={
                activeTab === 'employees'
              }
              onClick={() =>
                navigate('employees')
              }
            />
          )}


          {isAdmin && (
            <NavButton
              label="Assets"
              active={
                activeTab === 'assets'
              }
              onClick={() =>
                navigate('assets')
              }
            />
          )}


          <NavButton
            label="Scan QR"
            active={
              activeTab === 'scanner'
            }
            onClick={() =>
              navigate('scanner')
            }
          />


          {isAdmin && (
            <NavButton
              label="Maintenance"
              active={
                activeTab === 'maintenance'
              }
              onClick={() =>
                navigate('maintenance')
              }
            />
          )}


          {isAdmin && (
            <NavButton
              label="Reports"
              active={activeTab === 'reports'}
              onClick={() => navigate('reports')}
            />
          )}


          {isAdmin && (
            <NavButton
              label="Admin Users"
              active={
                activeTab === 'admin-users'
              }
              onClick={() =>
                navigate('admin-users')
              }
            />
          )}

          {isAdmin && (
            <NavButton label="Settings" active={activeTab === 'settings'} onClick={() => navigate('settings')} />
          )}


          <NavButton label="My Assets" active={activeTab === 'my-assets'} onClick={() => navigate('my-assets')} />

          <NavButton label="Attention" active={activeTab === 'attention'} onClick={() => navigate('attention')} />

          {isAdmin && (
            <NavButton label="Stock" active={activeTab === 'stock'} onClick={() => navigate('stock')} />
          )}

          <NavButton label="Issues" active={activeTab === 'issues'} onClick={() => navigate('issues')} />

          {isSuperAdmin && (
            <NavButton
              label="Audit Logs"
              active={
                activeTab === 'audit-logs'
              }
              onClick={() =>
                navigate('audit-logs')
              }
            />
          )}

        </div>
      </nav>
    </>
  );


  /*
   * =========================================================
   * PAGE WRAPPER
   * =========================================================
   */

  const pageStyle = {
    maxWidth: '1280px',
    margin: '0 auto',
    padding: '34px 28px 60px',
    boxSizing: 'border-box'
  };


  /*
   * =========================================================
   * MAIN APPLICATION
   * =========================================================
   */

  return (
    <div
      className="App"
      style={{
        minHeight: '100vh',
        background: '#050505'
      }}
    >

      <Header />


      {/* =====================================================
          DASHBOARD
          ===================================================== */}

      {activeTab === 'dashboard' && (
        <main style={pageStyle}>
          {isAdmin ? (
            <OperationsDashboard
              apiUrl={API_URL}
              token={token}
              assets={assets}
              onOpenAsset={(assetId) => setSelectedAssetId(assetId)}
              onRefresh={refresh}
            />
          ) : (
            <UserDashboard
              token={token}
              onLogout={logout}
            />
          )}
        </main>
      )}


      {activeTab === 'management' && isAdmin && (
        <main style={pageStyle}><ManagementDashboard apiUrl={API_URL} token={token} /></main>
      )}
      {activeTab === 'procurement' && isAdmin && (
        <main style={pageStyle}><Procurement apiUrl={API_URL} token={token} /></main>
      )}
      {activeTab === 'compliance' && isAdmin && (
        <main style={pageStyle}><ComplianceDocuments apiUrl={API_URL} token={token} assets={assets} /></main>
      )}
      {activeTab === 'executive' && isAdmin && (
        <main style={pageStyle}><ExecutiveHub apiUrl={API_URL} token={token} /></main>
      )}

      {activeTab === 'profile' && (
        <main style={pageStyle}><Profile apiUrl={API_URL} token={token} onUpdated={refresh} /></main>
      )}

      {activeTab === 'settings' && isAdmin && (
        <main style={pageStyle}><SystemSettings apiUrl={API_URL} token={token} /></main>
      )}


      {/* =====================================================
          EMPLOYEES
          ===================================================== */}

      {activeTab === 'employees' &&
        isAdmin && (
          <main style={pageStyle}>
            <EmployeeManagement apiUrl={API_URL} token={token} />
          </main>
        )}


      {/* =====================================================
          ADMIN USERS
          ===================================================== */}

      {activeTab === 'admin-users' &&
        isAdmin && (
          <main style={pageStyle}>
            <AdminUserManagement
              token={token}
              onBackToDashboard={() =>
                navigate('dashboard')
              }
            />
          </main>
        )}


      {/* =====================================================
          QR SCANNER
          ===================================================== */}

      {activeTab === 'scanner' && (
        <main style={pageStyle}>
          <QRScanner
            onBack={() =>
              navigate('dashboard')
            }
          />
        </main>
      )}


      {activeTab === 'my-assets' && (
        <main style={pageStyle}><MyAssets apiUrl={API_URL} token={token} /></main>
      )}

      {activeTab === 'attention' && (
        <main style={pageStyle}><NotificationCenter apiUrl={API_URL} token={token} /></main>
      )}

      {activeTab === 'stock' && isAdmin && (
        <main style={pageStyle}><StockManagement apiUrl={API_URL} token={token} assets={assets} users={users} onRefresh={refresh} /></main>
      )}

      {activeTab === 'issues' && (
        <main style={pageStyle}><AssetIssues apiUrl={API_URL} token={token} assets={assets} users={users} isAdmin={isAdmin} /></main>
      )}

      {/* =====================================================
          AUDIT LOGS
          ===================================================== */}

      {activeTab === 'audit-logs' &&
        isSuperAdmin && (
          <main style={pageStyle}>
            <AuditLogs
              apiUrl={API_URL}
              token={token}
              email={adminEmail}
            />
          </main>
        )}


      {/* =====================================================
          REPORTS
          ===================================================== */}

      {activeTab === 'reports' &&
        isAdmin && (
          <main style={pageStyle}>
            <Reports
              apiUrl={API_URL}
              token={token}
            />
          </main>
        )}


      {/* =====================================================
          ASSET PROFILE
          ===================================================== */}

      {selectedAssetId && (
        <AssetProfile
          apiUrl={API_URL}
          token={token}
          assetId={selectedAssetId}
          users={users}
          onClose={() => setSelectedAssetId(null)}
          onRefresh={refresh}
        />
      )}


      {/* =====================================================
          MAINTENANCE
          ===================================================== */}

      {activeTab === 'maintenance' &&
        isAdmin && (
          <main style={pageStyle}>
            <Maintenance
              apiUrl={API_URL}
              token={token}
              assets={assets}
              users={users}
              onRefresh={refresh}
            />
          </main>
        )}

      {/* =====================================================
          ASSETS
          ===================================================== */}

      {activeTab === 'assets' &&
        isAdmin && (
          <main style={pageStyle}>

            <div className="tab-content">

              <section className="form-section">

                <h2>
                  Add New Asset
                </h2>

                <AssetForm
                  categories={categories}
                  onAssetCreated={refresh}
                  apiUrl={API_URL}
                  token={token}
                />

              </section>


              <section className="list-section">

                <h2>
                  Assets ({assets.length})
                </h2>


                <div
                  style={{
                    marginBottom: '1.5rem',
                    paddingBottom: '1rem',
                    borderBottom:
                      '2px solid #1f1f1f'
                  }}
                >

                  <div
                    style={{
                      fontSize: '.9rem',
                      color: '#666'
                    }}
                  >
                    Total Asset Value
                  </div>

                  <div
                    style={{
                      fontSize: '1.8rem',
                      fontWeight: 700,
                      color: '#ff5500'
                    }}
                  >
                    £
                    {totalAssetValue.toLocaleString(
                      'en-GB',
                      {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      }
                    )}
                  </div>

                </div>


                {loading ? (
                  <p>
                    Loading assets...
                  </p>
                ) : (
                  <AssetList
                    assets={assets}
                    users={users}
                    categories={categories}
                    onAssetUpdated={refresh}
                    onAssetDeleted={(id) =>
                      setAssets(
                        (current) =>
                          current.filter(
                            (asset) =>
                              asset.id !== id
                          )
                      )
                    }
                    apiUrl={API_URL}
                    token={token}
                    onViewAsset={(asset) => setSelectedAssetId(asset.id)}
                  />
                )}

              </section>


              {/* CATEGORY MANAGEMENT */}

              <section
                className="list-section"
                style={{
                  gridColumn: '1 / -1',
                  marginTop: '20px'
                }}
              >

                <h2>
                  Categories ({categories.length})
                </h2>

                <CategoryForm
                  onCategoryCreated={refresh}
                  apiUrl={API_URL}
                  token={token}
                />

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns:
                      'repeat(auto-fill, minmax(240px, 1fr))',
                    gap: '12px',
                    marginTop: '20px'
                  }}
                >

                  {categories.map(
                    (category) => (
                      <div
                        key={category.id}
                        style={{
                          padding: '15px',
                          background: '#101010',
                          border: '1px solid #292929',
                          borderLeft:
                            '3px solid #ff5500',
                          borderRadius: '5px'
                        }}
                      >

                        <strong
                          style={{
                            color: '#ff5500'
                          }}
                        >
                          {category.name}
                        </strong>

                        <p
                          style={{
                            color: '#888',
                            fontSize: '12px',
                            marginBottom: 0
                          }}
                        >
                          {category.description ||
                            'No description'}
                        </p>

                      </div>
                    )
                  )}

                </div>

              </section>

            </div>

          </main>
        )}

    </div>
  );
}


/*
 * =========================================================
 * NAV BUTTON
 * =========================================================
 */

function NavButton({
  label,
  active,
  onClick
}) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '10px 17px',
        background: active
          ? '#ff5500'
          : '#181818',
        color: active
          ? '#ffffff'
          : '#bdbdbd',
        border: active
          ? '1px solid #ff5500'
          : '1px solid #303030',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '11px',
        fontWeight: 800,
        letterSpacing: '0.05em',
        textTransform: 'uppercase',
        transition: 'all 0.15s ease'
      }}
    >
      {label}
    </button>
  );
}


/*
 * =========================================================
 * MAINTENANCE CARD
 * =========================================================
 */

function MaintenanceCard({
  title,
  text
}) {
  return (
    <div
      style={{
        padding: '20px',
        background: '#0c0c0c',
        border: '1px solid #292929',
        borderRadius: '6px'
      }}
    >

      <div
        style={{
          color: '#ff5500',
          fontSize: '12px',
          fontWeight: 800,
          marginBottom: '8px'
        }}
      >
        {title}
      </div>

      <div
        style={{
          color: '#777',
          fontSize: '12px',
          lineHeight: 1.6
        }}
      >
        {text}
      </div>

    </div>
  );
}

export default App;