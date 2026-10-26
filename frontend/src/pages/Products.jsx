import { useEffect, useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import SkinSummaryCard from "../components/SkinSummaryCard";
import "./Products.css";

import { API_BASE } from "../config";

function Products() {
  const [latestAnalysis, setLatestAnalysis] = useState(null);
  const [skinType, setSkinType] = useState("normal");
  const [recommended, setRecommended] = useState([]);
  const [myProducts, setMyProducts] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Modal Form State
  const [formName, setFormName] = useState("");
  const [formType, setFormType] = useState("serum");
  const [formIngredients, setFormIngredients] = useState("");
  const [formTiming, setFormTiming] = useState("both");
  const [modalError, setModalError] = useState("");

  useEffect(() => {
    async function fetchData() {
      try {
        const [recRes, mineRes] = await Promise.all([
          fetch(`${API_BASE}/api/products/recommended`, { credentials: "include" }),
          fetch(`${API_BASE}/api/products/mine`, { credentials: "include" }),
        ]);

        if (recRes.ok) {
          const recData = await recRes.json();
          setSkinType(recData.skin_type || "normal");
          setLatestAnalysis(recData.latest_analysis);
          setRecommended(recData.recommended || []);
        }

        if (mineRes.ok) {
          const mineData = await mineRes.json();
          setMyProducts(mineData || []);
        }
      } catch (err) {
        console.error("Failed to load products data:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  async function handleAddProduct(e) {
    e.preventDefault();
    if (!formName.trim()) {
      setModalError("Product name is required.");
      return;
    }

    setSubmitting(true);
    setModalError("");

    try {
      const res = await fetch(`${API_BASE}/api/products/mine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: formName.trim(),
          type: formType,
          ingredients: formIngredients.trim(),
          timing: formTiming,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setModalError(data.error || "Failed to add product.");
      } else {
        setMyProducts((prev) => [data, ...prev]);
        setShowModal(false);
        setFormName("");
        setFormType("serum");
        setFormIngredients("");
        setFormTiming("both");
      }
    } catch {
      setModalError("Network error while adding product.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteProduct(productId) {
    try {
      const res = await fetch(`${API_BASE}/api/products/mine/${productId}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (res.ok) {
        setMyProducts((prev) => prev.filter((p) => p.id !== productId));
      }
    } catch (err) {
      console.error("Failed to delete product:", err);
    }
  }

  // Filter user products by timing
  const morningProducts = myProducts.filter((p) => p.timing === "morning");
  const nightProducts = myProducts.filter((p) => p.timing === "night");
  const bothProducts = myProducts.filter((p) => p.timing === "both");

  return (
    <DashboardLayout>
      <div className="page-header">
        <div>
          <h1>My Skincare Products</h1>
          <p className="page-subtitle">Personalized recommendations & custom routine product tracker</p>
        </div>
      </div>

      <div className="products-page">
        {/* TOP SECTION: Skin Type & Analysis Summary */}
        <SkinSummaryCard analysisResult={latestAnalysis} showResetButton={false} />

        {/* MIDDLE SECTION: Recommended for You */}
        <section className="recommended-section">
          <div className="section-title-row">
            <h2>Recommended for You</h2>
            <span className="skin-type-tag">Matches {skinType} Skin</span>
          </div>

          {loading ? (
            <p className="upload-hint">Loading recommendations...</p>
          ) : (
            <div className="recommended-grid">
              {recommended.map((item) => (
                <div key={item.id} className="recommended-card">
                  <div>
                    <div className="card-top">
                      <p className="product-brand">{item.brand}</p>
                      <span className="category-badge">{item.category}</span>
                    </div>
                    <h3 className="product-name">{item.name}</h3>
                    <p className="product-desc">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* BOTTOM SECTION: Your Products */}
        <section className="user-products-section">
          <div className="section-title-row">
            <h2>Your Products</h2>
            <button className="add-product-btn" onClick={() => setShowModal(true)}>
              + Add New Product
            </button>
          </div>

          <div className="timing-groups-container">
            {/* Morning Group */}
            <div className="timing-group">
              <div className="group-header">
                <span className="group-icon">☀️</span>
                <h3 className="group-title">Morning Routine</h3>
                <span className="group-count">{morningProducts.length}</span>
              </div>
              {morningProducts.length > 0 ? (
                <div className="user-products-grid">
                  {morningProducts.map((prod) => (
                    <UserProductCard key={prod.id} product={prod} onDelete={handleDeleteProduct} />
                  ))}
                </div>
              ) : (
                <p className="empty-group-text">No morning products added yet.</p>
              )}
            </div>

            {/* Night Group */}
            <div className="timing-group">
              <div className="group-header">
                <span className="group-icon">🌙</span>
                <h3 className="group-title">Night Routine</h3>
                <span className="group-count">{nightProducts.length}</span>
              </div>
              {nightProducts.length > 0 ? (
                <div className="user-products-grid">
                  {nightProducts.map((prod) => (
                    <UserProductCard key={prod.id} product={prod} onDelete={handleDeleteProduct} />
                  ))}
                </div>
              ) : (
                <p className="empty-group-text">No night products added yet.</p>
              )}
            </div>

            {/* Both Group */}
            <div className="timing-group">
              <div className="group-header">
                <span className="group-icon">🔄</span>
                <h3 className="group-title">Both (Morning & Night)</h3>
                <span className="group-count">{bothProducts.length}</span>
              </div>
              {bothProducts.length > 0 ? (
                <div className="user-products-grid">
                  {bothProducts.map((prod) => (
                    <UserProductCard key={prod.id} product={prod} onDelete={handleDeleteProduct} />
                  ))}
                </div>
              ) : (
                <p className="empty-group-text">No dual-use products added yet.</p>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* MODAL: Add New Product */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Add New Skincare Product</h3>
              <button className="close-modal-btn" onClick={() => setShowModal(false)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleAddProduct} className="modal-form">
              <div className="form-group">
                <label htmlFor="prod-name">Product Name *</label>
                <input
                  id="prod-name"
                  type="text"
                  placeholder="e.g. CeraVe Foaming Cleanser"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="prod-type">Product Type</label>
                <select
                  id="prod-type"
                  value={formType}
                  onChange={(e) => setFormType(e.target.value)}
                >
                  <option value="serum">Serum</option>
                  <option value="moisturizer">Moisturizer</option>
                  <option value="sunscreen">Sunscreen</option>
                  <option value="facewash">Facewash</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="prod-ingredients">Key Ingredients</label>
                <textarea
                  id="prod-ingredients"
                  placeholder="e.g. Niacinamide, Hyaluronic Acid, Zinc PCA"
                  value={formIngredients}
                  onChange={(e) => setFormIngredients(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="prod-timing">Usage Timing</label>
                <select
                  id="prod-timing"
                  value={formTiming}
                  onChange={(e) => setFormTiming(e.target.value)}
                >
                  <option value="morning">Morning</option>
                  <option value="night">Night</option>
                  <option value="both">Both (Morning & Night)</option>
                </select>
              </div>

              {modalError && <div className="error-banner">{modalError}</div>}

              <div className="modal-actions">
                <button
                  type="button"
                  className="cancel-btn"
                  onClick={() => setShowModal(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="save-btn" disabled={submitting}>
                  {submitting ? "Analyzing..." : "Save Product"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

function UserProductCard({ product, onDelete }) {
  return (
    <div className="user-product-card">
      <div>
        <div className="user-prod-header">
          <span className="type-pill">{product.type}</span>
          <button
            className="delete-prod-btn"
            title="Delete product"
            onClick={() => onDelete(product.id)}
          >
            ✕
          </button>
        </div>
        <h4 className="user-prod-name">{product.name}</h4>
        {product.ingredients && (
          <p className="ingredients-label">
            <strong>Ingredients:</strong> {product.ingredients}
          </p>
        )}
      </div>

      {product.suitability_suggestion && (
        <div className="suitability-badge">
          💡 {product.suitability_suggestion}
        </div>
      )}
    </div>
  );
}

export default Products;
