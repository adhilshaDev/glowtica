import { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { tipsCategories } from "../data/tipsData";
import "./Tips.css";

import { API_BASE } from "../config";

function Tips() {
  const [expandedCards, setExpandedCards] = useState({
    sunscreen: true, // First expanded by default
  });
  const [progress, setProgress] = useState({});

  useEffect(() => {
    async function fetchProgress() {
      try {
        const res = await fetch(`${API_BASE}/api/tips/progress`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setProgress(data.progress || {});
        }
      } catch (err) {
        console.error("Failed to load tips progress:", err);
      }
    }

    fetchProgress();
  }, []);

  function toggleCard(id) {
    setExpandedCards((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  }

  async function handleToggleRead(categoryId, currentReadStatus) {
    const newStatus = !currentReadStatus;

    // Optimistic UI update
    setProgress((prev) => ({
      ...prev,
      [categoryId]: newStatus,
    }));

    try {
      await fetch(`${API_BASE}/api/tips/progress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          category: categoryId,
          read_complete: newStatus,
        }),
      });
    } catch (err) {
      console.error("Failed to update tips progress:", err);
    }
  }

  const completedCount = Object.values(progress).filter(Boolean).length;

  return (
    <DashboardLayout>
      <div className="tips-container">
        {/* HEADER & PROGRESS BADGE */}
        <div className="tips-header-row">
          <div>
            <h1>Skincare Tips & Guide</h1>
            <p className="page-subtitle">Expert daily advice for optimal skin health</p>
          </div>

          <span className="read-progress-badge">
            {completedCount} of {tipsCategories.length} Categories Read
          </span>
        </div>

        {/* CATEGORY CARDS GRID */}
        <div className="category-cards-grid">
          {tipsCategories.map((cat) => {
            const isExpanded = !!expandedCards[cat.id];
            const isRead = !!progress[cat.id];

            return (
              <div
                key={cat.id}
                className={`tip-card ${isExpanded ? "expanded" : ""}`}
              >
                {/* CARD HEADER */}
                <div
                  className="tip-card-header"
                  onClick={() => toggleCard(cat.id)}
                >
                  <div className="card-title-group">
                    <div className={`category-icon icon-${cat.color}`}>
                      {cat.icon}
                    </div>
                    <div>
                      <h2 className="category-title">{cat.title}</h2>
                      <p className="category-subtitle">
                        {cat.bullets.length} Essential Tips · 1 Pro Tip
                      </p>
                    </div>
                  </div>

                  <div className="header-right">
                    {isRead && <span className="read-check-pill">✓ Completed</span>}
                    <span className={`expand-chevron ${isExpanded ? "open" : ""}`}>
                      ▼
                    </span>
                  </div>
                </div>

                {/* EXPANDED CARD BODY */}
                {isExpanded && (
                  <div className="tip-card-body">
                    {/* BULLET TIPS */}
                    <ul className="bullets-list">
                      {cat.bullets.map((bullet, idx) => (
                        <li key={idx}>{bullet}</li>
                      ))}
                    </ul>

                    {/* PRO TIP CALLOUT */}
                    <div className="pro-tip-box">
                      <span className="pro-tip-badge">Pro Tip</span>
                      <p className="pro-tip-text">{cat.proTip}</p>
                    </div>

                    {/* READ COMPLETE CHECKBOX */}
                    <div className="card-footer-action">
                      <label className="mark-read-checkbox-label">
                        <input
                          type="checkbox"
                          checked={isRead}
                          onChange={() => handleToggleRead(cat.id, isRead)}
                        />
                        Read Complete
                      </label>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}

export default Tips;
