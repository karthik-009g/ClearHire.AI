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
  const canvasRef = useRef(null);
  const pairRef = useRef(null);
  const leftPanelRef = useRef(null);
  const rightPanelRef = useRef(null);

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

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return undefined;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      return undefined;
    }

    let width = 0;
    let height = 0;
    let frameId = 0;
    let hue = 165;
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let shards = [];

    const resize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const spawnShards = (x, y) => {
      for (let index = 0; index < 14; index += 1) {
        const angle = Math.random() * Math.PI * 2;
        const speed = 2.5 + Math.random() * 4.5;
        shards.push({
          x,
          y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed - 1.5,
          rot: Math.random() * Math.PI * 2,
          vr: Math.random() * 0.3 - 0.15,
          sides: [3, 4, 5][Math.floor(Math.random() * 3)],
          size: 5 + Math.random() * 13,
          hueOff: Math.random() * 100 - 50,
          life: 1,
        });
      }
    };

    const particles = Array.from({ length: 74 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      base: Math.random() * 0.33 + 0.08,
      r: Math.random() * 1.4 + 0.5,
    }));

    const crystals = Array.from({ length: 20 }, () => {
      const sides = [5, 6, 7, 8][Math.floor(Math.random() * 4)];
      return {
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        vx: (Math.random() - 0.5) * 0.14,
        vy: (Math.random() - 0.5) * 0.14,
        vr: (Math.random() - 0.5) * 0.003,
        rot: Math.random() * Math.PI * 2,
        size: 14 + Math.random() * 44,
        sides,
        hueOff: Math.random() * 70 - 35,
        alpha: Math.random() * 0.34 + 0.08,
        innerAlpha: Math.random() * 0.2 + 0.05,
        pulsePhase: Math.random() * Math.PI * 2,
        pulseSpeed: 0.007 + Math.random() * 0.01,
        innerRot: Math.random() * Math.PI * 2,
        innerSides: sides === 5 ? 3 : 4,
      };
    });

    const polygon = (cx, cy, radius, sides, rot) => {
      context.beginPath();
      for (let i = 0; i < sides; i += 1) {
        const angle = rot + (i / sides) * Math.PI * 2;
        const px = cx + Math.cos(angle) * radius;
        const py = cy + Math.sin(angle) * radius;
        if (i === 0) {
          context.moveTo(px, py);
        } else {
          context.lineTo(px, py);
        }
      }
      context.closePath();
    };

    const drawCrystal = (crystal) => {
      const dx = mouseX - crystal.x;
      const dy = mouseY - crystal.y;
      const distance = Math.hypot(dx, dy);
      const proximity = Math.max(0, 1 - distance / 220);
      const pulse = 1 + 0.12 * Math.sin(crystal.pulsePhase);
      const size = crystal.size * pulse;
      const alpha = crystal.alpha + proximity * 0.2;

      const glow = context.createRadialGradient(crystal.x, crystal.y, 0, crystal.x, crystal.y, size * 1.6);
      glow.addColorStop(0, `hsla(${hue + crystal.hueOff}, 90%, 75%, ${alpha * 0.16})`);
      glow.addColorStop(1, "transparent");
      context.fillStyle = glow;
      context.fillRect(crystal.x - size * 1.7, crystal.y - size * 1.7, size * 3.4, size * 3.4);

      polygon(crystal.x, crystal.y, size, crystal.sides, crystal.rot);
      const outerGradient = context.createLinearGradient(
        crystal.x - size,
        crystal.y - size,
        crystal.x + size,
        crystal.y + size,
      );
      outerGradient.addColorStop(0, `hsla(${hue + crystal.hueOff}, 84%, 88%, ${alpha * 0.52})`);
      outerGradient.addColorStop(0.45, `hsla(${hue + crystal.hueOff + 20}, 70%, 70%, ${alpha * 0.24})`);
      outerGradient.addColorStop(1, `hsla(${hue + crystal.hueOff - 20}, 90%, 60%, ${alpha * 0.4})`);
      context.fillStyle = outerGradient;
      context.fill();
      context.strokeStyle = `hsla(${hue + crystal.hueOff}, 90%, 92%, ${alpha * 0.62})`;
      context.lineWidth = 0.8;
      context.stroke();

      context.save();
      context.globalAlpha = alpha * 0.28;
      for (let i = 0; i < crystal.sides; i += 1) {
        const spoke = crystal.rot + (i / crystal.sides) * Math.PI * 2;
        context.beginPath();
        context.moveTo(crystal.x, crystal.y);
        context.lineTo(crystal.x + Math.cos(spoke) * size, crystal.y + Math.sin(spoke) * size);
        context.strokeStyle = `hsla(${hue + crystal.hueOff}, 80%, 95%, 1)`;
        context.lineWidth = 0.45;
        context.stroke();
      }
      context.restore();

      const innerSize = size * 0.42;
      polygon(crystal.x, crystal.y, innerSize, crystal.innerSides, crystal.innerRot);
      const innerGradient = context.createLinearGradient(
        crystal.x - innerSize,
        crystal.y - innerSize,
        crystal.x + innerSize,
        crystal.y + innerSize,
      );
      innerGradient.addColorStop(
        0,
        `hsla(${hue + crystal.hueOff + 34}, 100%, 95%, ${crystal.innerAlpha + proximity * 0.14})`,
      );
      innerGradient.addColorStop(1, `hsla(${hue + crystal.hueOff}, 80%, 70%, ${crystal.innerAlpha * 0.48})`);
      context.fillStyle = innerGradient;
      context.fill();
      context.strokeStyle = `hsla(${hue + crystal.hueOff}, 100%, 100%, ${alpha * 0.45})`;
      context.lineWidth = 0.55;
      context.stroke();
    };

    const drawFrame = () => {
      context.clearRect(0, 0, width, height);
      hue = 160 + 20 * Math.sin(Date.now() * 0.0003);

      const bgGradient = context.createRadialGradient(width * 0.4, height * 0.35, 0, width * 0.5, height * 0.5, width * 0.85);
      bgGradient.addColorStop(0, `hsl(${hue}, 58%, 5%)`);
      bgGradient.addColorStop(0.5, `hsl(${hue}, 52%, 3%)`);
      bgGradient.addColorStop(1, "#020608");
      context.fillStyle = bgGradient;
      context.fillRect(0, 0, width, height);

      const ambient = context.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 280);
      ambient.addColorStop(0, `hsla(${hue}, 100%, 62%, 0.085)`);
      ambient.addColorStop(1, "transparent");
      context.fillStyle = ambient;
      context.fillRect(0, 0, width, height);

      crystals.forEach((crystal) => {
        crystal.pulsePhase += crystal.pulseSpeed;
        crystal.rot += crystal.vr;
        crystal.innerRot -= crystal.vr * 0.7;
        const dx = mouseX - crystal.x;
        const dy = mouseY - crystal.y;
        const distance = Math.hypot(dx, dy);
        if (distance < 260 && distance > 0) {
          const force = (crystal.size > 34 ? 0.0001 : -0.00013) * (1 - distance / 260);
          crystal.vx += dx * force;
          crystal.vy += dy * force;
        }
        crystal.vx *= 0.986;
        crystal.vy *= 0.986;
        crystal.x += crystal.vx;
        crystal.y += crystal.vy;

        if (crystal.x < -70) crystal.x = width + 70;
        if (crystal.x > width + 70) crystal.x = -70;
        if (crystal.y < -70) crystal.y = height + 70;
        if (crystal.y > height + 70) crystal.y = -70;

        drawCrystal(crystal);
      });

      for (let index = shards.length - 1; index >= 0; index -= 1) {
        const shard = shards[index];
        shard.vy += 0.06;
        shard.vx *= 0.94;
        shard.vy *= 0.94;
        shard.x += shard.vx;
        shard.y += shard.vy;
        shard.rot += shard.vr;
        shard.life -= 0.024;

        if (shard.life <= 0) {
          shards.splice(index, 1);
          continue;
        }

        context.save();
        context.globalAlpha = shard.life * 0.9;
        context.translate(shard.x, shard.y);
        context.rotate(shard.rot);
        context.beginPath();
        for (let sideIndex = 0; sideIndex < shard.sides; sideIndex += 1) {
          const angle = (sideIndex / shard.sides) * Math.PI * 2;
          const px = Math.cos(angle) * shard.size;
          const py = Math.sin(angle) * shard.size;
          if (sideIndex === 0) {
            context.moveTo(px, py);
          } else {
            context.lineTo(px, py);
          }
        }
        context.closePath();
        const shardGradient = context.createLinearGradient(-shard.size, -shard.size, shard.size, shard.size);
        shardGradient.addColorStop(0, `hsla(${hue + shard.hueOff}, 85%, 88%, ${shard.life * 0.7})`);
        shardGradient.addColorStop(1, `hsla(${hue + shard.hueOff + 25}, 70%, 65%, ${shard.life * 0.3})`);
        context.fillStyle = shardGradient;
        context.fill();
        context.strokeStyle = `hsla(${hue + shard.hueOff}, 100%, 95%, ${shard.life * 0.8})`;
        context.lineWidth = 0.7;
        context.stroke();
        context.restore();
      }

      particles.forEach((particle) => {
        const dx = mouseX - particle.x;
        const dy = mouseY - particle.y;
        const distance = Math.hypot(dx, dy);
        const repel = Math.max(0, 1 - distance / 150);
        if (distance > 0) {
          particle.vx += (-(dx / distance) * repel) * 0.16;
          particle.vy += (-(dy / distance) * repel) * 0.16;
        }
        particle.vx *= 0.96;
        particle.vy *= 0.96;
        particle.x += particle.vx;
        particle.y += particle.vy;

        if (particle.x < 0) particle.x = width;
        if (particle.x > width) particle.x = 0;
        if (particle.y < 0) particle.y = height;
        if (particle.y > height) particle.y = 0;

        const near = Math.max(0, 1 - distance / 160);
        context.beginPath();
        context.arc(particle.x, particle.y, particle.r * (1 + near * 0.7), 0, Math.PI * 2);
        context.fillStyle = `hsla(${hue}, 75%, 72%, ${particle.base + near * 0.4})`;
        context.fill();
      });

      for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
          const distance = Math.hypot(particles[i].x - particles[j].x, particles[i].y - particles[j].y);
          if (distance < 86) {
            context.beginPath();
            context.moveTo(particles[i].x, particles[i].y);
            context.lineTo(particles[j].x, particles[j].y);
            context.strokeStyle = `hsla(${hue}, 80%, 70%, ${(1 - distance / 86) * 0.09})`;
            context.lineWidth = 0.5;
            context.stroke();
          }
        }
      }

      frameId = window.requestAnimationFrame(drawFrame);
    };

    const onMove = (event) => {
      mouseX = event.clientX;
      mouseY = event.clientY;
    };

    const onClick = (event) => {
      console.log("CLICK", event.clientX, event.clientY);
      spawnShards(event.clientX, event.clientY);
    };

    resize();
    drawFrame();
    window.addEventListener("resize", resize);
    document.addEventListener("mousemove", onMove);
    document.addEventListener("click", onClick);

    return () => {
      window.cancelAnimationFrame(frameId);
      window.removeEventListener("resize", resize);
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("click", onClick);
    };
  }, []);

  useEffect(() => {
    const leftPanel = leftPanelRef.current;
    const rightPanel = rightPanelRef.current;
    if (!leftPanel || !rightPanel) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      leftPanel.classList.add("collide");
      rightPanel.classList.add("collide");
      window.setTimeout(() => {
        leftPanel.classList.remove("collide");
        rightPanel.classList.remove("collide");
      }, 520);
    }, 980);

    return () => {
      window.clearTimeout(timer);
    };
  }, []);

  if (!ready) {
    return (
      <div className="mp-auth-shell mp-auth-neon" style={shellStyle} onMouseMove={onShellMouseMove}>
        <canvas ref={canvasRef} className="mp-auth-canvas" aria-hidden="true" />
        <div className="mp-auth-stage">
          <article className="mp-auth-panel mp-panel-left" aria-hidden="true" ref={leftPanelRef}>
            <div className="mp-glow-line" />
            <div className="mp-scanlines" />
            <p className="mp-auth-kicker">clearhire.ai</p>
            <h2>Resume and Job Match Intelligence</h2>
            <p>
              Unified automation workspace for resume parsing, matching, and application workflow management.
            </p>
          </article>
          <div className="mp-auth-panel mp-panel-right" ref={rightPanelRef}>
            <div className="mp-glow-line" />
            <div className="mp-scanlines" />
            <h1>Checking session...</h1>
            <p>Please wait while we verify your account.</p>
          </div>
        </div>
      </div>
    );
  }

  const emailHint = !form.email ? "" : form.email.includes("@") ? "valid" : "keep typing";
  const passHint = !form.password
    ? ""
    : form.password.length < 6
      ? `${form.password.length}/8 weak`
      : form.password.length < 10
        ? "good"
        : "strong";

  const onShellMouseLeave = () => {
    const leftPanel = leftPanelRef.current;
    const rightPanel = rightPanelRef.current;
    if (leftPanel) {
      leftPanel.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg)";
    }
    if (rightPanel) {
      rightPanel.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg)";
    }
  };

  const onPanelMouseMove = (event) => {
    onShellMouseMove(event);
    const pair = pairRef.current;
    const leftPanel = leftPanelRef.current;
    const rightPanel = rightPanelRef.current;

    if (!pair || !leftPanel || !rightPanel) {
      return;
    }

    const pairRect = pair.getBoundingClientRect();
    const px = event.clientX - pairRect.left - pairRect.width / 2;
    const py = event.clientY - pairRect.top - pairRect.height / 2;
    const rotX = (py / pairRect.height) * -5;
    const rotY = (px / pairRect.width) * 5;

    leftPanel.style.transform = `perspective(900px) rotateX(${rotX}deg) rotateY(${rotY * 0.5}deg)`;
    rightPanel.style.transform = `perspective(900px) rotateX(${rotX}deg) rotateY(${rotY * 0.5}deg)`;

    const leftRect = leftPanel.getBoundingClientRect();
    const rightRect = rightPanel.getBoundingClientRect();
    leftPanel.style.setProperty("--lx", `${(((event.clientX - leftRect.left) / leftRect.width) * 100).toFixed(1)}%`);
    leftPanel.style.setProperty("--ly", `${(((event.clientY - leftRect.top) / leftRect.height) * 100).toFixed(1)}%`);
    rightPanel.style.setProperty("--lx", `${(((event.clientX - rightRect.left) / rightRect.width) * 100).toFixed(1)}%`);
    rightPanel.style.setProperty("--ly", `${(((event.clientY - rightRect.top) / rightRect.height) * 100).toFixed(1)}%`);
  };

  return (
    <div className="mp-auth-shell mp-auth-neon" style={shellStyle} onMouseMove={onShellMouseMove}>
      <canvas ref={canvasRef} className="mp-auth-canvas" aria-hidden="true" />
      <div className="mp-auth-stage">
        <div className="mp-auth-pair" ref={pairRef} onMouseMove={onPanelMouseMove} onMouseLeave={onShellMouseLeave}>
          <article className="mp-auth-panel mp-panel-left" ref={leftPanelRef}>
            <div className="mp-glow-line" />
            <div className="mp-scanlines" />
            <div>
              <p className="mp-logo">clear<span>hire</span>.ai</p>
              <p className="mp-logo-sub">AI Career Workspace</p>
              <p className="mp-project-badge">secure platform</p>
              <h2>Resume and Job Match Intelligence</h2>
              <p className="mp-project-desc">
                Streamline resume analysis, role matching, and application tracking in one secure dashboard.
              </p>
            </div>

            <div>
              <div className="mp-metric-row">
                <div className="mp-metric">
                  <p className="mp-metric-value">Real-Time</p>
                  <p className="mp-metric-label">Updates</p>
                </div>
                <div className="mp-metric">
                  <p className="mp-metric-value">Unified</p>
                  <p className="mp-metric-label">Modules</p>
                </div>
                <div className="mp-metric">
                  <p className="mp-metric-value">Secure</p>
                  <p className="mp-metric-label">Access</p>
                </div>
              </div>
              <div className="mp-status-row">
                <span className="mp-status-dot" />
                <span className="mp-status-text">Backend connection active</span>
              </div>
            </div>
          </article>

          <div className="mp-auth-panel mp-panel-right" ref={rightPanelRef}>
            <div className="mp-glow-line" />
            <div className="mp-scanlines" />
            <div>
              <p className="mp-eyebrow">secure access</p>
              <h1>{mode === "login" ? "Welcome Back" : "Create Account"}</h1>
              <p className="mp-welcome-sub">Sign in to continue to your ClearHire workspace.</p>

              <form className="mp-auth-form" onSubmit={onSubmit}>
                <label>
                  <span>Email</span>
                  <span className="mp-label-hint">{emailHint}</span>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
                    placeholder="name@email.com"
                    autoComplete="email"
                  />
                </label>

                <label>
                  <span>Password</span>
                  <span className="mp-label-hint">{passHint}</span>
                  <input
                    type="password"
                    value={form.password}
                    onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
                    placeholder="Enter password"
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                  />
                </label>

                {mode === "register" && (
                  <label>
                    <span>Confirm password</span>
                    <span className="mp-label-hint">required</span>
                    <input
                      type="password"
                      value={form.confirmPassword}
                      onChange={(event) => setForm((prev) => ({ ...prev, confirmPassword: event.target.value }))}
                      placeholder="Repeat password"
                      autoComplete="new-password"
                    />
                  </label>
                )}

                {error && <p className="mp-error">{error}</p>}

                <button type="submit" disabled={busy}>
                  {busy ? "Authenticating..." : mode === "login" ? "Login ->" : "Register and Login"}
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

            <p className="mp-footer-line">ClearHire platform access</p>
          </div>
        </div>
      </div>
    </div>
  );
}
