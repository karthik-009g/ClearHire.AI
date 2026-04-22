import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/router";
import { getMe, loginUser, registerUser } from "../api/auth";
import { clearAuthToken, getStoredAuthToken, setAuthToken } from "../api/client";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState("login");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const [form, setForm] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [theme, setTheme] = useState({
    x: 50,
    y: 44,
  });
  const rafRef = useRef(null);

  useEffect(() => {
    let active = true;

    const checkSession = async () => {
      const token = getStoredAuthToken();
      if (!token) {
        if (active) {
          setReady(true);
        }
        return;
      }

      try {
        setAuthToken(token);
        await getMe();
        if (active) {
          router.replace("/");
        }
      } catch {
        clearAuthToken();
        if (active) {
          setReady(true);
        }
      }
    };

    checkSession();

    return () => {
      active = false;
    };
  }, [router]);

  const onSubmit = async (event) => {
    event.preventDefault();

    const email = form.email.trim().toLowerCase();
    const password = form.password;
    setError("");

    if (!email || !password) {
      setError("Email and password are required.");
      return;
    }

    if (mode === "register" && password !== form.confirmPassword) {
      setError("Password confirmation does not match.");
      return;
    }

    setBusy(true);
    try {
      if (mode === "register") {
        await registerUser(email, password);
      }

      const tokenPayload = await loginUser(email, password);
      setAuthToken(tokenPayload.access_token);
      await getMe();
      router.push("/");
    } catch (err) {
      setError(err.message || "Authentication failed.");
    } finally {
      setBusy(false);
    }
  };

  const onShellMouseMove = (event) => {
    const target = event.currentTarget;
    if (!target) {
      return;
    }

    const { clientX, clientY } = event;

    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }

    rafRef.current = requestAnimationFrame(() => {
      const rect = target.getBoundingClientRect();
      if (!rect.width || !rect.height) {
        return;
      }

      const x = ((clientX - rect.left) / rect.width) * 100;
      const y = ((clientY - rect.top) / rect.height) * 100;
      setTheme({ x, y });
    });
  };

  const shellStyle = useMemo(
    () => ({
      "--cursor-x": `${theme.x}%`,
      "--cursor-y": `${theme.y}%`,
    }),
    [theme],
  );

  if (!ready) {
    return (
      <div className="mp-auth-shell collision-theme" style={shellStyle} onMouseMove={onShellMouseMove}>
        <div className="mp-auth-stage">
          <article className="mp-auth-panel mp-panel-left" aria-hidden="true">
            <p className="mp-auth-kicker">ClearHire AI</p>
            <h2>Career Engine</h2>
            <p>
              Smart resume analysis, better job matching, and clean automation flows
              built for focused job seekers.
            </p>
          </article>
          <div className="mp-auth-panel mp-panel-right">
            <h1>Checking session...</h1>
            <p>Please wait while we verify your account.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mp-auth-shell collision-theme" style={shellStyle} onMouseMove={onShellMouseMove}>
      <div className="mp-auth-stage">
        <article className="mp-auth-panel mp-panel-left">
          <p className="mp-auth-kicker">ClearHire AI</p>
          <h2>Smarter Job Search Workspace</h2>
          <p>
            Analyze resumes, match roles, and optimize applications in one secure
            workflow. Designed to reduce manual effort and improve interview-ready
            outcomes.
          </p>
        </article>

        <div className="mp-auth-panel mp-panel-right">
          <h1>{mode === "login" ? "Welcome back" : "Create account"}</h1>
          <p>Secure login is required before opening any module route.</p>

          <form className="mp-auth-form" onSubmit={onSubmit}>
            <label>
              Email
              <input
                type="email"
                value={form.email}
                onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
                placeholder="name@email.com"
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={form.password}
                onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
                placeholder="Enter password"
              />
            </label>

            {mode === "register" && (
              <label>
                Confirm password
                <input
                  type="password"
                  value={form.confirmPassword}
                  onChange={(event) => setForm((prev) => ({ ...prev, confirmPassword: event.target.value }))}
                  placeholder="Repeat password"
                />
              </label>
            )}

            {error && <p className="mp-error">{error}</p>}

            <button type="submit" disabled={busy}>
              {busy ? "Please wait..." : mode === "login" ? "Login" : "Register and Login"}
            </button>
          </form>

          <button
            type="button"
            className="mp-link-button"
            onClick={() => {
              setMode((prev) => (prev === "login" ? "register" : "login"));
              setError("");
            }}
          >
            {mode === "login" ? "Need an account? Register" : "Already have an account? Login"}
          </button>
        </div>
      </div>
    </div>
  );
}
