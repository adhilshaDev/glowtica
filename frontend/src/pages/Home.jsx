import { useEffect, useRef, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import SkinSummaryCard from "../components/SkinSummaryCard";
import demoPortrait from "../assets/demo-face.png";
import { getAllTipLines } from "../data/tipsData";
import "./Home.css";

import { API_BASE } from "../config";

function getDailyTip() {
  const todayStr = new Date().toISOString().slice(0, 10);
  const storedKey = "glowtica_tip_of_the_day";

  try {
    const raw = localStorage.getItem(storedKey);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && parsed.date === todayStr && parsed.tip) {
        return parsed.tip;
      }
    }
  } catch {
    // Ignore localStorage parse errors
  }

  const allLines = getAllTipLines();
  const randomPick = allLines[Math.floor(Math.random() * allLines.length)];

  try {
    localStorage.setItem(storedKey, JSON.stringify({ date: todayStr, tip: randomPick }));
  } catch {
    // Ignore localStorage write errors
  }

  return randomPick;
}

function Home() {
  const [photo, setPhoto] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [dailyTip, setDailyTip] = useState(null);

  const fileInputRef = useRef(null);

  useEffect(() => {
    setDailyTip(getDailyTip());
  }, []);

  async function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    event.target.value = "";

    const previewUrl = URL.createObjectURL(file);
    setPhoto(previewUrl);
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/api/dashboard/upload`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          setError("Your session has expired. Please log in again.");
        } else {
          setError(data.error || "Analysis failed. Please try again.");
        }
      } else {
        setAnalysisResult(data);
      }
    } catch {
      setError("Cannot connect to backend server. Please verify Flask is running.");
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setPhoto(null);
    setAnalysisResult(null);
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  return (
    <DashboardLayout>
      <div className="page-header">
        <div>
          <h1>Skin Analysis</h1>
          <p className="page-subtitle">AI-powered face zone & condition analysis</p>
        </div>
        <button
          className="new-scan-button"
          onClick={() => {
            handleReset();
            fileInputRef.current?.click();
          }}
        >
          New Scan
        </button>
      </div>

      {/* TIP OF THE DAY BANNER */}
      {dailyTip && (
        <div className="tip-of-day-banner">
          <div className="tip-banner-icon">{dailyTip.icon}</div>
          <div className="tip-banner-content">
            <div className="tip-banner-header">
              <span className="tip-banner-tag">Tip of the Day</span>
              <span className="tip-banner-category">• {dailyTip.category}</span>
            </div>
            <p className="tip-banner-text">{dailyTip.text}</p>
          </div>
        </div>
      )}

      <div className="analysis-grid">
        <section className="face-map-card">
          <div className="card-header">
            <div>
              <h2>Face Scan Frame</h2>
              <p className="card-subtitle">
                {analysisResult
                  ? `${analysisResult.detected_problems?.length || 0} top concerns identified by Gemini AI`
                  : "Upload a front-facing photo to begin analysis"}
              </p>
            </div>
            {analysisResult && (
              <span className="attention-badge">
                {analysisResult.skin_type_confidence_percentage >= 50
                  ? "Analysis Ready"
                  : "Low Confidence"}
              </span>
            )}
          </div>

          <div className="face-map-frame">
            <img
              src={photo || demoPortrait}
              alt={photo ? "Uploaded face scan" : "Demo face scan"}
              className="face-photo"
            />
          </div>
        </section>

        <div className="side-column">
          {analysisResult ? (
            <SkinSummaryCard analysisResult={analysisResult} onReset={handleReset} />
          ) : (
            <section className="upload-card">
              <div className="upload-icon">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    d="M12 16V4M12 4L7 9M12 4l5 5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M4 16v3a2 2 0 002 2h12a2 2 0 002-2v-3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <h3>Upload Photo for Scanning</h3>
              <p className="upload-hint">
                Front-facing · Good lighting
                <br />
                JPG, PNG, HEIC · Max 10 MB
              </p>

              <input
                type="file"
                accept="image/jpeg,image/png,image/heic"
                ref={fileInputRef}
                onChange={handleFileChange}
                style={{ display: "none" }}
              />

              <button
                className="choose-file-button"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
              >
                {loading ? "Analyzing..." : "Choose File"}
              </button>

              {loading ? (
                <div className="loading-state">
                  <div className="loading-spinner" />
                  <span>Analyzing skin with Gemini AI...</span>
                </div>
              ) : (
                <p className="upload-drag-hint">or select an image file</p>
              )}

              {error && <div className="error-banner">{error}</div>}
            </section>
          )}

          <section className="how-it-works-card">
            <h3>How it works</h3>
            <ol>
              <li>Upload a clear, front-facing photo in good light</li>
              <li>Gemini AI analyzes skin type and estimates concern areas</li>
              <li>View your cosmetic summary and top concern breakdown</li>
            </ol>
          </section>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default Home;