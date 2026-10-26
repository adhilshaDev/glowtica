import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Auth.css";

import portrait1 from "../assets/portraits/portrait1.png";
import portrait2 from "../assets/portraits/portrait2.png";
import portrait3 from "../assets/portraits/portrait3.png";

const slides = [
  {
    image: portrait1,
    title: (
      <>
        Care for your <span>skin.</span>
      </>
    ),
    description: "Every glow begins with a routine made for you.",
  },
  {
    image: portrait2,
    title: (
      <>
        Know your <span>skin.</span>
      </>
    ),
    description: "Understand your unique skin needs with confidence.",
  },
  {
    image: portrait3,
    title: (
      <>
        Reveal your <span>confidence.</span>
      </>
    ),
    description: "Small moments of self-care can make a real difference.",
  },
];

import { API_BASE } from "../config";

function Auth() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [currentSlide, setCurrentSlide] = useState(0);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((previousSlide) => {
        return (previousSlide + 1) % slides.length;
      });
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  function switchMode(newMode) {
    setMode(newMode);
    setMessage("");
    setName("");
    setEmail("");
    setPassword("");
    setConfirmPassword("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setMessage("");

    if (mode === "signup" && password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }

    setLoading(true);

    const endpoint =
      mode === "login"
        ? `${API_BASE}/api/login`
        : `${API_BASE}/api/signup`;

    const body =
      mode === "login"
        ? { email, password }
        : { name, email, password };

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.error || "Something went wrong. Please try again.");
        setLoading(false);
        return;
      }

      setName("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");

      navigate("/home");
    } catch {
      setMessage(
        "Cannot connect to the backend. Make sure Flask is running."
      );
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-layout">
        <div className="auth-form-side">
          <div className="brand-mark">
            <span></span>
          </div>

          <div className="form-content">
            <p className="brand-name">GLOWTICA</p>

            <h1>
              {mode === "login"
                ? "Sign in to your account"
                : "Create your account"}
            </h1>

            <p className="form-subtitle">
              {mode === "login"
                ? "Your personalized skincare journey is waiting."
                : "Start discovering skincare made for you."}
            </p>

            <form onSubmit={handleSubmit}>
              {mode === "signup" && (
                <>
                  <label htmlFor="name">Full name</label>
                  <input
                    id="name"
                    type="text"
                    placeholder="Enter your full name"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    required
                  />
                </>
              )}

              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />

              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength="6"
                required
              />

              {mode === "signup" && (
                <>
                  <label htmlFor="confirm-password">Confirm password</label>
                  <input
                    id="confirm-password"
                    type="password"
                    placeholder="Re-enter your password"
                    value={confirmPassword}
                    onChange={(event) =>
                      setConfirmPassword(event.target.value)
                    }
                    minLength="6"
                    required
                  />
                </>
              )}

              {mode === "login" && (
                <div className="form-options">
                  <button type="button" className="text-button">
                    Forgot password?
                  </button>
                </div>
              )}

              <button
                className="submit-button"
                type="submit"
                disabled={loading}
              >
                {loading
                  ? "Please wait..."
                  : mode === "login"
                    ? "Sign in"
                    : "Create account"}
              </button>
            </form>

            {message && <p className="auth-message">{message}</p>}

            <div className="switch-mode">
              {mode === "login" ? (
                <>
                  <span>Don't have an account?</span>
                  <button
                    type="button"
                    className="text-button"
                    onClick={() => switchMode("signup")}
                  >
                    Sign up
                  </button>
                </>
              ) : (
                <>
                  <span>Already have an account?</span>
                  <button
                    type="button"
                    className="text-button"
                    onClick={() => switchMode("login")}
                  >
                    Sign in
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="portrait-side">
          {slides.map((slide, index) => (
            <img
              key={slide.image}
              src={slide.image}
              alt="Glowtica skincare portrait"
              className={`portrait-image ${
                index === currentSlide ? "portrait-active" : ""
              }`}
            />
          ))}

          <div className="portrait-overlay">
            <p key={`title-${currentSlide}`} className="slide-title">
              {slides[currentSlide].title}
            </p>

            <span
              key={`description-${currentSlide}`}
              className="slide-description"
            >
              {slides[currentSlide].description}
            </span>
          </div>

          <div className="slide-dots">
            {slides.map((_, index) => (
              <button
                key={index}
                type="button"
                className={index === currentSlide ? "active" : ""}
                onClick={() => setCurrentSlide(index)}
                aria-label={`Show slide ${index + 1}`}
              />
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

export default Auth;