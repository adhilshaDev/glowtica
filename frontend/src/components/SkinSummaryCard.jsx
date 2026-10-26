const problemLabels = {
  tanned: "Tanned Skin",
  oily: "Excess Oil",
  uneven_tone: "Uneven Tone",
  redness: "Redness",
  acne: "Acne / Breakouts",
  dark_circles: "Dark Circles",
  dullness: "Dullness",
  visible_pores: "Visible Pores",
};

function formatProblemName(name) {
  if (problemLabels[name]) return problemLabels[name];
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function SkinSummaryCard({ analysisResult, onReset, showResetButton = true }) {
  if (!analysisResult) {
    return (
      <section className="analysis-results-card">
        <div className="card-header">
          <div>
            <h2>Skin Profile</h2>
            <p className="card-subtitle">No skin scan recorded yet</p>
          </div>
        </div>
        <p className="no-problems-text">
          Upload a front-facing photo on the Dashboard to get your personalized AI skin analysis.
        </p>
      </section>
    );
  }

  return (
    <section className="analysis-results-card">
      <div className="card-header">
        <div>
          <h2>Skin Profile Summary</h2>
          <p className="skin-type-badge">
            Skin Type:{" "}
            <strong style={{ textTransform: "capitalize" }}>
              {analysisResult.skin_type}
            </strong>{" "}
            ({analysisResult.skin_type_confidence_percentage}%)
          </p>
        </div>
        {showResetButton && onReset && (
          <button className="reset-button" onClick={onReset}>
            Analyze Another Photo
          </button>
        )}
      </div>

      {analysisResult.skin_type_confidence_percentage < 50 && (
        <div className="confidence-warning">
          ⚠️ Low confidence estimate ({analysisResult.skin_type_confidence_percentage}%).
          Please try uploading a front-facing photo under brighter, more balanced light.
        </div>
      )}

      {analysisResult.concern_notes && (
        <div className="concern-notes-box">
          <p className="notes-label">Cosmetic Summary</p>
          <p className="notes-text">{analysisResult.concern_notes}</p>
        </div>
      )}

      <div className="problems-section">
        <h3>Top Detected Concerns</h3>
        {analysisResult.detected_problems &&
        analysisResult.detected_problems.length > 0 ? (
          <div className="problems-list">
            {analysisResult.detected_problems.slice(0, 4).map((prob) => (
              <div key={prob.name} className="problem-row">
                <div className="problem-info">
                  <span className="problem-name">
                    {formatProblemName(prob.name)}
                  </span>
                  <span className="problem-percentage">
                    {prob.percentage}%
                  </span>
                </div>
                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(0, prob.percentage)
                      )}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-problems-text">
            No major skin concerns detected.
          </p>
        )}
      </div>
    </section>
  );
}

export default SkinSummaryCard;
