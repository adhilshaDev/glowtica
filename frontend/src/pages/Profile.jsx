import { useEffect, useRef, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import "./Profile.css";

import { API_BASE } from "../config";

function Profile() {
  const [user, setUser] = useState(null);
  const [usernameInput, setUsernameInput] = useState("");
  
  // Password form state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Feedback states
  const [photoLoading, setPhotoLoading] = useState(false);
  const [nameLoading, setNameLoading] = useState(false);
  const [passLoading, setPassLoading] = useState(false);

  const [nameMessage, setNameMessage] = useState("");
  const [nameError, setNameError] = useState("");

  const [passMessage, setPassMessage] = useState("");
  const [passError, setPassError] = useState("");

  const fileInputRef = useRef(null);

  useEffect(() => {
    async function fetchMe() {
      try {
        const res = await fetch(`${API_BASE}/api/me`, { credentials: "include" });
        if (res.ok) {
          const data = await res.json();
          setUser(data);
          setUsernameInput(data.name || "");
        } else {
          window.location.replace("/");
        }
      } catch {
        window.location.replace("/");
      }
    }

    fetchMe();
  }, []);

  async function handlePhotoChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    setPhotoLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/account/photo`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        setUser((prev) => ({ ...prev, avatar_base64: data.avatar_base64 }));
      }
    } catch (err) {
      console.error("Failed to upload profile photo:", err);
    } finally {
      setPhotoLoading(false);
    }
  }

  async function handleSaveName(e) {
    e.preventDefault();
    if (!usernameInput.trim()) {
      setNameError("Username cannot be empty.");
      return;
    }

    setNameLoading(true);
    setNameError("");
    setNameMessage("");

    try {
      const res = await fetch(`${API_BASE}/api/account/username`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name: usernameInput.trim() }),
      });

      const data = await res.json();
      if (!res.ok) {
        setNameError(data.error || "Failed to update username.");
      } else {
        setUser((prev) => ({ ...prev, name: data.name }));
        setNameMessage("Username updated successfully.");
      }
    } catch {
      setNameError("Network error while updating username.");
    } finally {
      setNameLoading(false);
    }
  }

  async function handleChangePassword(e) {
    e.preventDefault();
    setPassError("");
    setPassMessage("");

    if (!currentPassword || !newPassword) {
      setPassError("Please fill in all password fields.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPassError("New password and confirm password do not match.");
      return;
    }

    if (newPassword.length < 6) {
      setPassError("New password must be at least 6 characters.");
      return;
    }

    setPassLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/account/password`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setPassError(data.error || "Failed to update password.");
      } else {
        setPassMessage("Password updated successfully.");
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
      }
    } catch {
      setPassError("Network error while changing password.");
    } finally {
      setPassLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await fetch(`${API_BASE}/api/account/logout`, {
        method: "POST",
        credentials: "include",
      });
    } finally {
      window.location.replace("/");
    }
  }

  return (
    <DashboardLayout>
      <div className="page-header">
        <div>
          <h1>My Profile & Account</h1>
          <p className="page-subtitle">Manage your credentials, profile photo, and security preferences</p>
        </div>
      </div>

      <div className="profile-container">
        {/* AVATAR SECTION */}
        <section className="profile-card">
          <h3>Profile Picture</h3>
          <div className="avatar-section-inner">
            <div className="circular-avatar-frame">
              {user?.avatar_base64 ? (
                <img
                  src={user.avatar_base64}
                  alt={user.name || "Profile avatar"}
                  className="avatar-img"
                />
              ) : (
                <span>{user?.name ? user.name.charAt(0).toUpperCase() : "?"}</span>
              )}
            </div>

            <div className="avatar-controls">
              <input
                type="file"
                ref={fileInputRef}
                accept="image/jpeg,image/png,image/webp"
                onChange={handlePhotoChange}
                style={{ display: "none" }}
              />
              <button
                className="change-photo-btn"
                onClick={() => fileInputRef.current?.click()}
                disabled={photoLoading}
              >
                {photoLoading ? "Uploading..." : "Change Photo"}
              </button>
              <p className="avatar-hint">JPG, PNG, WebP · Max 5 MB</p>
            </div>
          </div>
        </section>

        {/* ACCOUNT DETAILS SECTION */}
        <section className="profile-card">
          <h3>Account Information</h3>
          <form onSubmit={handleSaveName} className="profile-form">
            <div className="field-row">
              <div className="field-group">
                <label htmlFor="user-name-input">Full Name</label>
                <input
                  id="user-name-input"
                  type="text"
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  required
                />
              </div>
              <button className="save-action-btn" type="submit" disabled={nameLoading}>
                {nameLoading ? "Saving..." : "Save Name"}
              </button>
            </div>

            <div className="field-group">
              <label htmlFor="user-email-input">Email Address (Read-only)</label>
              <input
                id="user-email-input"
                type="email"
                value={user?.email || ""}
                readOnly
                disabled
              />
            </div>

            {nameMessage && <div className="success-banner">{nameMessage}</div>}
            {nameError && <div className="error-banner">{nameError}</div>}
          </form>
        </section>

        {/* CHANGE PASSWORD SECTION */}
        <section className="profile-card">
          <h3>Security & Password</h3>
          <form onSubmit={handleChangePassword} className="profile-form">
            <div className="field-group">
              <label htmlFor="curr-pass">Current Password *</label>
              <input
                id="curr-pass"
                type="password"
                placeholder="Enter your current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>

            <div className="field-group">
              <label htmlFor="new-pass">New Password *</label>
              <input
                id="new-pass"
                type="password"
                placeholder="Enter new password (min 6 characters)"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={6}
                required
              />
            </div>

            <div className="field-group">
              <label htmlFor="confirm-new-pass">Confirm New Password *</label>
              <input
                id="confirm-new-pass"
                type="password"
                placeholder="Re-enter new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={6}
                required
              />
            </div>

            {passMessage && <div className="success-banner">{passMessage}</div>}
            {passError && <div className="error-banner">{passError}</div>}

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 4 }}>
              <button className="save-action-btn" type="submit" disabled={passLoading}>
                {passLoading ? "Updating..." : "Update Password"}
              </button>
            </div>
          </form>
        </section>

        {/* LOGOUT CARD */}
        <section className="profile-card logout-card">
          <div className="logout-info">
            <h4>Sign Out</h4>
            <p>End your current session on this device.</p>
          </div>
          <button className="account-logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </section>
      </div>
    </DashboardLayout>
  );
}

export default Profile;
