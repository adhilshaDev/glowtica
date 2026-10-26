import { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import "./Routine.css";

import { API_BASE } from "../config";

function Routine() {
  const [period, setPeriod] = useState("AM"); // "AM" or "PM"
  const [routine, setRoutine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchRoutine() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`${API_BASE}/api/routine/${period}`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setRoutine(data.routine);
        } else {
          setError("Failed to fetch routine.");
        }
      } catch {
        setError("Cannot connect to backend server.");
      } finally {
        setLoading(false);
      }
    }

    fetchRoutine();
  }, [period]);

  async function handleGenerateRoutine() {
    setGenerating(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/routine/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ period }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to generate routine.");
      } else {
        setRoutine(data.routine);
      }
    } catch {
      setError("Network error while generating routine.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleToggleStep(stepNumber, currentStatus) {
    const newStatus = !currentStatus;

    // Optimistic UI update
    setRoutine((prev) => {
      if (!prev) return prev;
      const updatedSteps = prev.steps.map((s) =>
        s.step_number === stepNumber ? { ...s, applied_today: newStatus } : s
      );
      return { ...prev, steps: updatedSteps };
    });

    try {
      await fetch(`${API_BASE}/api/routine/apply-step`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          period,
          step_number: stepNumber,
          applied: newStatus,
        }),
      });
    } catch (err) {
      console.error("Failed to update step status:", err);
    }
  }

  const steps = routine?.steps || [];
  const appliedCount = steps.filter((s) => s.applied_today).length;
  const totalCount = steps.length;
  const progressPercent = totalCount > 0 ? Math.round((appliedCount / totalCount) * 100) : 0;

  return (
    <DashboardLayout>
      <div className="routine-container">
        {/* HEADER & AM/PM TOGGLE */}
        <div className="routine-header-row">
          <div>
            <h1>Skincare Routine</h1>
            <p className="page-subtitle">Custom AI-crafted daily regimen tailored to your skin profile</p>
          </div>

          <div className="period-toggle-shell">
            <button
              className={`toggle-btn ${period === "AM" ? "active-am" : ""}`}
              onClick={() => setPeriod("AM")}
            >
              <span>☀️</span> AM Routine
            </button>
            <button
              className={`toggle-btn ${period === "PM" ? "active-pm" : ""}`}
              onClick={() => setPeriod("PM")}
            >
              <span>🌙</span> PM Routine
            </button>
          </div>
        </div>

        {/* MAIN THEME CARD SHELL */}
        <div className={`routine-card-shell ${period === "AM" ? "theme-am" : "theme-pm"}`}>
          {/* BANNER WITH CELESTIAL ANIMATION */}
          <div className="theme-banner">
            <div className="banner-info">
              <h2>{period === "AM" ? "Morning Glow Routine" : "Evening Recovery Routine"}</h2>
              <p className="banner-subtitle">
                {period === "AM"
                  ? "Protect, hydrate, and energize your skin for the day ahead."
                  : "Deeply cleanse, repair, and nourish your skin overnight."}
              </p>
            </div>

            <div className="celestial-graphic">
              {period === "AM" ? (
                <div className="sun-icon" title="Sun Animation" />
              ) : (
                <div className="moon-wrapper" title="Moon & Stars Animation">
                  <div className="moon-icon" />
                  <span className="star star-1" />
                  <span className="star star-2" />
                  <span className="star star-3" />
                </div>
              )}
            </div>
          </div>

          {error && <div className="error-banner">{error}</div>}

          {loading ? (
            <p className="empty-group-text">Loading routine steps...</p>
          ) : routine && steps.length > 0 ? (
            <>
              {/* PROGRESS TRACKER */}
              <div className="progress-box">
                <div className="progress-labels">
                  <span>Daily Checklist</span>
                  <span>
                    {appliedCount} of {totalCount} steps completed ({progressPercent}%)
                  </span>
                </div>
                <div className="progress-track-shell">
                  <div
                    className="progress-fill-bar"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              {/* STEPS LIST */}
              <div className="steps-checklist">
                {steps.map((step) => (
                  <div
                    key={step.step_number}
                    className={`step-card ${step.applied_today ? "applied" : ""}`}
                  >
                    <div className="step-number-badge">
                      {step.step_number}
                    </div>

                    <div className="step-content">
                      <h4 className="step-product-name">{step.product_name}</h4>
                      <p className="step-instruction">{step.instruction}</p>
                    </div>

                    <button
                      className={`step-checkbox-btn ${step.applied_today ? "checked" : ""}`}
                      onClick={() => handleToggleStep(step.step_number, step.applied_today)}
                    >
                      {step.applied_today ? "✓ Applied" : "Mark Applied"}
                    </button>
                  </div>
                ))}
              </div>

              {/* REGENERATE ACTION */}
              <div className="routine-actions-footer">
                <button
                  className="generate-routine-btn"
                  onClick={handleGenerateRoutine}
                  disabled={generating}
                >
                  {generating ? "Regenerating..." : "↻ Regenerate Routine"}
                </button>
              </div>
            </>
          ) : (
            /* EMPTY STATE */
            <div className="empty-routine-box">
              <h3>No {period} Routine Generated Yet</h3>
              <p>
                Click below to let Gemini AI analyze your skin profile and product collection to design a personalized {period} routine.
              </p>
              <button
                className="generate-routine-btn"
                onClick={handleGenerateRoutine}
                disabled={generating}
              >
                {generating ? "Designing Routine with Gemini..." : "✨ Generate My Routine"}
              </button>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

export default Routine;
