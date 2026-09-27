import React, { useState, useEffect } from "react";
import axios from "axios";
import "../styles/Dashboard.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const UserDashboard = ({ token, onLogout }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    full_name: "",
    phone: "",
    bio: "",
    location: "",
    bike_interests: "",
  });

  useEffect(() => {
    fetchUserProfile();
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(response.data);
      setFormData({
        full_name: response.data.full_name || "",
        phone: response.data.phone || "",
        bio: response.data.bio || "",
        location: response.data.location || "",
        bike_interests: response.data.bike_interests || "",
      });
      setError("");
    } catch (err) {
      setError("Failed to load profile. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.put(`${API_URL}/users/me`, formData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(response.data);
      setEditMode(false);
      setSuccess("Profile updated successfully.");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError("Failed to update profile. Please try again.");
      console.error(err);
    }
  };

  const getMembershipColor = (tier) => {
    const colors = {
      bronze: "#daa520",
      silver: "#c0c0c0",
      gold: "#ffd700",
      platinum: "#e5e4e2",
    };
    return colors[tier] || "#ff5500";
  };

  const getMembershipBenefits = (tier) => {
    const benefits = {
      bronze: ["Access to community events", "Basic member profile"],
      silver: ["All Bronze benefits", "Exclusive workshops", "10% store discount"],
      gold: ["All Silver benefits", "Priority event access", "20% store discount"],
      platinum: [
        "All Gold benefits",
        "VIP event access",
        "30% store discount",
        "Personal concierge",
      ],
    };
    return benefits[tier] || [];
  };

  if (loading) {
    return (
      <div className="dashboard-shell">
        <div className="loading">
          <div className="spinner" />
          <p>Loading your profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="dashboard-shell">
        <div className="empty-state">
          <div className="empty-icon">Profile</div>
          <p>Unable to load user profile.</p>
          <button className="btn btn-primary" onClick={onLogout}>
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-shell">
      <div className="dashboard-container">
        <div className="dashboard-header">
          <div>
            <h1 className="dashboard-title">My Profile</h1>
            <p className="dashboard-subtitle">ApexMoto&Co Member Dashboard</p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={onLogout}>
            Logout
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <div className="dashboard-grid">
          <div className="dashboard-card">
            <div className="card-header">
              <h2 className="card-title">Profile Information</h2>
            </div>
            <div className="card-body">
              {!editMode ? (
                <>
                  <div className="card-field">
                    <span className="card-label">Email</span>
                    <span className="card-value">{user.email}</span>
                  </div>
                  <div className="card-field">
                    <span className="card-label">Full Name</span>
                    <span className="card-value">{user.full_name}</span>
                  </div>
                  <div className="card-field">
                    <span className="card-label">Phone</span>
                    <span className="card-value">{user.phone || "Not provided"}</span>
                  </div>
                  <div className="card-field">
                    <span className="card-label">Location</span>
                    <span className="card-value">{user.location || "Not provided"}</span>
                  </div>
                  <div className="card-field">
                    <span className="card-label">Bio</span>
                    <span className="card-value">{user.bio || "Not provided"}</span>
                  </div>
                  <button
                    className="btn btn-primary"
                    onClick={() => setEditMode(true)}
                    style={{ marginTop: "15px", width: "100%" }}
                  >
                    Edit Profile
                  </button>
                </>
              ) : (
                <form onSubmit={handleSaveProfile}>
                  <div className="form-group">
                    <label className="form-label">Full Name</label>
                    <input
                      type="text"
                      name="full_name"
                      className="form-input"
                      value={formData.full_name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Phone</label>
                    <input
                      type="tel"
                      name="phone"
                      className="form-input"
                      value={formData.phone}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Location</label>
                    <input
                      type="text"
                      name="location"
                      className="form-input"
                      placeholder="Your location or region"
                      value={formData.location}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Bike Interests</label>
                    <input
                      type="text"
                      name="bike_interests"
                      className="form-input"
                      placeholder="e.g., Harley-Davidson, Yamaha, Street Bikes"
                      value={formData.bike_interests}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Bio</label>
                    <textarea
                      name="bio"
                      className="form-textarea"
                      value={formData.bio}
                      onChange={handleInputChange}
                      placeholder="Tell us about yourself and your motorcycle journey"
                    />
                  </div>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                      Save Changes
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setEditMode(false)}
                      style={{ flex: 1 }}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>

          <div className="dashboard-card">
            <div className="card-header">
              <h2 className="card-title">Membership Tier</h2>
            </div>
            <div className="card-body">
              <div className="card-field">
                <span className="card-label">Current Tier</span>
                <span
                  className={`badge badge-${user.membership_tier}`}
                  style={{
                    color: getMembershipColor(user.membership_tier),
                    borderColor: getMembershipColor(user.membership_tier),
                    background: `rgba(${parseInt(getMembershipColor(user.membership_tier).slice(1, 3), 16)}, ${parseInt(getMembershipColor(user.membership_tier).slice(3, 5), 16)}, ${parseInt(getMembershipColor(user.membership_tier).slice(5, 7), 16)}, 0.2)`,
                  }}
                >
                  {user.membership_tier}
                </span>
              </div>
              <div
                style={{
                  marginTop: "15px",
                  paddingTop: "15px",
                  borderTop: "1px solid rgba(255,255,255,0.1)",
                }}
              >
                <p
                  style={{
                    fontSize: "0.85rem",
                    fontWeight: "600",
                    color: "#ff5500",
                    marginBottom: "10px",
                  }}
                >
                  Benefits
                </p>
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {getMembershipBenefits(user.membership_tier).map((benefit, idx) => (
                    <li
                      key={idx}
                      style={{ fontSize: "0.85rem", color: "#a0a0a0", marginBottom: "6px" }}
                    >
                      {benefit}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="dashboard-card">
            <div className="card-header">
              <h2 className="card-title">Account Status</h2>
            </div>
            <div className="card-body">
              <div className="card-field">
                <span className="card-label">Status</span>
                <span
                  className="badge"
                  style={{
                    background: user.is_active
                      ? "rgba(0, 217, 111, 0.2)"
                      : "rgba(255, 51, 51, 0.2)",
                    color: user.is_active ? "#00d96f" : "#ff3333",
                    border: `1px solid ${user.is_active ? "#00d96f" : "#ff3333"}`,
                  }}
                >
                  {user.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              <div className="card-field">
                <span className="card-label">Verified</span>
                <span
                  className="badge"
                  style={{
                    background: user.is_verified
                      ? "rgba(0, 217, 111, 0.2)"
                      : "rgba(255, 165, 0, 0.2)",
                    color: user.is_verified ? "#00d96f" : "#ffa500",
                    border: `1px solid ${user.is_verified ? "#00d96f" : "#ffa500"}`,
                  }}
                >
                  {user.is_verified ? "Verified" : "Unverified"}
                </span>
              </div>
              <div className="card-field">
                <span className="card-label">Member Since</span>
                <span className="card-value">
                  {new Date(user.join_date).toLocaleDateString("en-GB", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </span>
              </div>
              <div className="card-field">
                <span className="card-label">Last Login</span>
                <span className="card-value">
                  {user.last_login
                    ? new Date(user.last_login).toLocaleDateString("en-GB", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "First login"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;
