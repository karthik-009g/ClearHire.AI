import { useCallback, useEffect, useState } from "react";
import ModuleLayout from "../components/ModuleLayout";
import {
  getDigestHistory,
  getFunnelAnalytics,
  getMorningDigestPreview,
  sendMorningDigest,
} from "../api/digest";

export default function FunnelAnalyticsPage() {
  const [funnel, setFunnel] = useState(null);
  const [preview, setPreview] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [previewUnavailable, setPreviewUnavailable] = useState(false);
  const [dispatching, setDispatching] = useState(false);
  const [activePreviewTab, setActivePreviewTab] = useState("telegram"); // "telegram" | "whatsapp" | "email"
  const [selectedChannels, setSelectedChannels] = useState({
    email: false,
    telegram: false,
    whatsapp: false,
  });
  const [channelInputs, setChannelInputs] = useState({
    email: "",
    telegram_chat_id: "",
    whatsapp_number: "",
  });
  const [dispatchResults, setDispatchResults] = useState(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [fData, pData, hData] = await Promise.all([
        getFunnelAnalytics().catch(() => null),
        getMorningDigestPreview().catch(() => null),
        getDigestHistory().catch(() => []),
      ]);
      if (!fData && !pData) {
        throw new Error("Pipeline and briefing data are unavailable. Check the backend connection and retry.");
      }
      setFunnel(fData);
      setPreview(pData);
      setPreviewUnavailable(!pData);
      setHistory(Array.isArray(hData) ? hData : []);
    } catch (err) {
      setError(err.message || "Could not load your search activity.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(loadData, 0);
    return () => clearTimeout(timer);
  }, [loadData]);

  const onToggleChannel = (channel) => {
    setSelectedChannels((prev) => ({ ...prev, [channel]: !prev[channel] }));
  };

  const onSendDigest = async () => {
    const channels = Object.keys(selectedChannels).filter((k) => selectedChannels[k]);
    if (!channels.length) {
      setError("Please select at least one notification channel.");
      return;
    }
    const missingRecipients = channels.filter((channel) => {
      if (channel === "email") return !channelInputs.email.trim();
      if (channel === "telegram") return !channelInputs.telegram_chat_id.trim();
      return !channelInputs.whatsapp_number.trim();
    });
    if (missingRecipients.length) {
      setError(`Enter a recipient for each selected channel: ${missingRecipients.join(", ")}.`);
      return;
    }

    setDispatching(true);
    setError("");
    setInfo("");
    setDispatchResults(null);

    try {
      const payload = {
        channels,
        email: channelInputs.email.trim() || null,
        telegram_chat_id: channelInputs.telegram_chat_id.trim() || null,
        whatsapp_number: channelInputs.whatsapp_number.trim() || null,
      };
      const res = await sendMorningDigest(payload);
      const results = Array.isArray(res.dispatched) ? res.dispatched : [];
      setDispatchResults(results);
      setInfo("The dispatch request finished. Review each channel's delivery status below.");
      const nextHistory = await getDigestHistory().catch(() => []);
      setHistory(nextHistory);
    } catch (err) {
      setError(err.message || "Failed to send the role briefing.");
    } finally {
      setDispatching(false);
    }
  };

  return (
    <ModuleLayout
      title="Search progress & role digest"
      subtitle="Review your application activity, preview current role matches, and request a briefing when you choose."
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="m-0 text-xs text-[#706e68]" role="status" aria-live="polite">
          {loading ? "Loading your search activity…" : "Activity reflects the records saved in your ClearHire account."}
        </p>
        <button type="button" onClick={loadData} disabled={loading} className="rounded-full border border-[#24231f]/15 px-4 py-2 font-mono text-[10px] text-[#24231f] disabled:opacity-50">
          {loading ? "Refreshing…" : "Refresh data"}
        </button>
      </div>
      {error && <p className="mb-4 rounded-xl border border-red-400/30 bg-red-400/10 p-3 text-xs text-red-200" role="alert">{error}</p>}
      {/* 1. Hero KPI Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "14px",
          marginBottom: "24px",
        }}
      >
        <div className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-soft)", letterSpacing: "1px" }}>Total tracked</span>
          <h2 style={{ margin: "6px 0 2px", color: "var(--brand)" }}>{funnel ? funnel.total_tracked : "--"}</h2>
          <span style={{ fontSize: "12px", color: "#5369d9" }}>{funnel ? `${funnel.applied} submitted or in later stages` : "--"}</span>
        </div>

        <div className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-soft)", letterSpacing: "1px" }}>Screen Conversion</span>
          <h2 style={{ margin: "6px 0 2px", color: "#8d9cf2" }}>{funnel ? `${funnel.screen_conversion_rate}%` : "--%"}</h2>
          <span style={{ fontSize: "12px", color: "#706e68" }}>{funnel ? `${funnel.screening} screens secured` : "--"}</span>
        </div>

        <div className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-soft)", letterSpacing: "1px" }}>Offer Conversion</span>
          <h2 style={{ margin: "6px 0 2px", color: "#5b7f6a" }}>{funnel ? `${funnel.offer_rate}%` : "--%"}</h2>
          <span style={{ fontSize: "12px", color: "#5b7f6a" }}>{funnel ? `${funnel.offer} final offers` : "--"}</span>
        </div>

        <div
          className={`mp-card rounded-2xl p-6 backdrop-blur-xl shadow-sm ${
            funnel?.ghosting_rate > 20
              ? "bg-[#fef2f2]/90 border border-[#bd7652]/35"
              : "bg-[#faf7f0]/85 border border-[#24231f]/12"
          }`}
        >
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: funnel?.ghosting_rate > 20 ? "#bd7652" : "var(--text-soft)", letterSpacing: "1px" }}>
            14+ day no-update rate
          </span>
          <h2 style={{ margin: "6px 0 2px", color: funnel?.ghosting_rate > 20 ? "#bd7652" : "#bd7652" }}>
            {funnel ? `${funnel.ghosting_rate}%` : "--%"}
          </h2>
          <span style={{ fontSize: "12px", color: "var(--text-soft)" }}>
            {funnel ? `${funnel.ghosted} of ${funnel.applied} applications` : "--"}
          </span>
        </div>

        <div className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-soft)", letterSpacing: "1px" }}>Average record age</span>
          <h2 style={{ margin: "6px 0 2px", color: "#5369d9" }}>{funnel ? `${funnel.avg_days_to_response}d` : "--"}</h2>
          <span style={{ fontSize: "12px", color: "#706e68" }}>Days since last update for progressed or closed records</span>
        </div>
      </div>

      {/* 2. Visual Funnel Progression Bar */}
      {funnel && funnel.total_tracked > 0 && (
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm" style={{ marginBottom: "24px" }}>
          <h3 style={{ margin: "0 0 14px 0" }}>Pipeline Conversion Progression</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {[
              { label: "1. Saved & Prepped", count: funnel.saved + funnel.applied, color: "#5369d9" },
              { label: "2. Submitted (confirmed)", count: funnel.applied, color: "#15803d" },
              { label: "3. Recruiter Screens Secured", count: funnel.screening, color: "#8d9cf2" },
              { label: "4. Technical Interview Rounds", count: funnel.interviewing, color: "#4052b3" },
              { label: "5. Job Offers Received", count: funnel.offer, color: "#166534" },
            ].map((step, idx) => {
              const maxVal = Math.max(funnel.total_tracked, 1);
              const pct = Math.round((step.count / maxVal) * 100);
              return (
                <div key={idx} style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.4fr) minmax(64px, 2fr) auto", alignItems: "center", gap: "12px" }}>
                  <span style={{ minWidth: 0, fontSize: "13px", fontWeight: 600 }}>{step.label}</span>
                  <div style={{ background: "rgba(36, 35, 31, 0.08)", borderRadius: "8px", height: "18px", overflow: "hidden", display: "flex" }}>
                    <div
                      style={{
                        width: `${Math.max(pct, 3)}%`,
                        background: step.color,
                        borderRadius: "8px",
                        transition: "width 0.4s ease",
                      }}
                    />
                  </div>
                  <span style={{ whiteSpace: "nowrap", fontSize: "13px", color: "var(--text-soft)", textAlign: "right" }}>
                    {step.count} ({pct}%)
                  </span>
                </div>
              );
            })}
          </div>
        </article>
      )}

      {/* 3. Morning Briefing & Multi-Channel Dispatch Center */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 340px), 1fr))", gap: "20px", marginBottom: "24px" }}>
        {/* Left: Dispatch Settings */}
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <h3 style={{ margin: "0 0 10px 0" }}>Role digest</h3>
          <p className="mp-muted" style={{ margin: "0 0 16px 0", fontSize: "13px" }}>
            Send the current briefing to channels you select. Source labels and no-update reminders are signals from saved records, not guarantees of employer activity.
          </p>

          <div style={{ marginBottom: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <span style={{ fontSize: "13px", fontWeight: 600 }}>
                Choose where to send this briefing:
              </span>
            </div>
            <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer", fontSize: "13px" }}>
                <input
                  type="checkbox"
                  checked={selectedChannels.email}
                  onChange={() => onToggleChannel("email")}
                />
                ✉️ Email (HTML Briefing)
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer", fontSize: "13px" }}>
                <input
                  type="checkbox"
                  checked={selectedChannels.telegram}
                  onChange={() => onToggleChannel("telegram")}
                />
                ✈️ Telegram Bot Alert
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer", fontSize: "13px" }}>
                <input
                  type="checkbox"
                  checked={selectedChannels.whatsapp}
                  onChange={() => onToggleChannel("whatsapp")}
                />
                💬 WhatsApp Notification
              </label>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "16px" }}>
            {selectedChannels.email && (
              <label style={{ fontSize: "12px", fontFamily: "var(--mono)", textTransform: "uppercase", letterSpacing: "0.05em", color: "#706e68", fontWeight: 600 }}>
                Candidate Email
                <input
                  type="email"
                  placeholder="e.g. candidate@domain.com"
                  value={channelInputs.email}
                  onChange={(e) => setChannelInputs({ ...channelInputs, email: e.target.value })}
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "10px", marginTop: "4px", background: "#ffffff", border: "1px solid rgba(36, 35, 31, 0.15)", color: "#24231f", fontSize: "13px" }}
                />
              </label>
            )}
            {selectedChannels.telegram && (
              <label style={{ fontSize: "12px", fontFamily: "var(--mono)", textTransform: "uppercase", letterSpacing: "0.05em", color: "#706e68", fontWeight: 600 }}>
                Telegram Chat ID / Username
                <input
                  type="text"
                  placeholder="e.g. @your_telegram_handle"
                  value={channelInputs.telegram_chat_id}
                  onChange={(e) => setChannelInputs({ ...channelInputs, telegram_chat_id: e.target.value })}
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "10px", marginTop: "4px", background: "#ffffff", border: "1px solid rgba(36, 35, 31, 0.15)", color: "#24231f", fontSize: "13px" }}
                />
              </label>
            )}
            {selectedChannels.whatsapp && (
              <label style={{ fontSize: "12px", fontFamily: "var(--mono)", textTransform: "uppercase", letterSpacing: "0.05em", color: "#706e68", fontWeight: 600 }}>
                WhatsApp Number (with country code)
                <input
                  type="text"
                  placeholder="e.g. +919876543210"
                  value={channelInputs.whatsapp_number}
                  onChange={(e) => setChannelInputs({ ...channelInputs, whatsapp_number: e.target.value })}
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "10px", marginTop: "4px", background: "#ffffff", border: "1px solid rgba(36, 35, 31, 0.15)", color: "#24231f", fontSize: "13px" }}
                />
              </label>
            )}
          </div>

          <button
            type="button"
            onClick={onSendDigest}
            disabled={dispatching}
            style={{
              background: "var(--brand)",
              color: "#ffffff",
              border: "none",
              padding: "11px 22px",
              borderRadius: "999px",
              fontWeight: 600,
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            {dispatching ? "Sending briefing…" : "Send briefing now"}
          </button>

          {info && <p className="mp-ok" style={{ marginTop: "12px" }}>{info}</p>}
          {error && <p className="mp-error" style={{ marginTop: "12px" }}>{error}</p>}

          {/* Dispatch Results Breakdown */}
          {dispatchResults && (
            <div style={{ marginTop: "16px", padding: "12px", background: "#ffffff", border: "1px solid rgba(36, 35, 31, 0.1)", boxShadow: "0 2px 6px rgba(36, 35, 31, 0.03)", borderRadius: "8px" }}>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#5b7f6a", display: "block", marginBottom: "6px" }}>
                Dispatch Receipt:
              </span>
              {dispatchResults.map((res, i) => (
                <div key={i} style={{ fontSize: "12px", margin: "4px 0", color: res.status === "failed" ? "#bd7652" : "#5369d9" }}>
                  <strong>{res.channel.toUpperCase()}</strong>: {res.status} &bull; {res.recipient} &mdash; <em>{res.detail}</em>
                </div>
              ))}
            </div>
          )}
        </article>

        {/* Right: Multi-Format Live Preview */}
        <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <h3 style={{ margin: 0 }}>Live Briefing Preview</h3>
            <div style={{ display: "flex", gap: "6px" }}>
              <button
                type="button"
                onClick={() => setActivePreviewTab("telegram")}
                style={{
                  background: activePreviewTab === "telegram" ? "#24231f" : "#eeece2",
                  color: activePreviewTab === "telegram" ? "#ffffff" : "#525048",
                  border: "1px solid rgba(36, 35, 31, 0.12)",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontFamily: "var(--mono)",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Telegram
              </button>
              <button
                type="button"
                onClick={() => setActivePreviewTab("whatsapp")}
                style={{
                  background: activePreviewTab === "whatsapp" ? "#24231f" : "#eeece2",
                  color: activePreviewTab === "whatsapp" ? "#ffffff" : "#525048",
                  border: "1px solid rgba(36, 35, 31, 0.12)",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontFamily: "var(--mono)",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                WhatsApp
              </button>
              <button
                type="button"
                onClick={() => setActivePreviewTab("email")}
                style={{
                  background: activePreviewTab === "email" ? "#24231f" : "#eeece2",
                  color: activePreviewTab === "email" ? "#ffffff" : "#525048",
                  border: "1px solid rgba(36, 35, 31, 0.12)",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontFamily: "var(--mono)",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Email
              </button>
            </div>
          </div>

          {preview ? (
            <div style={{ maxHeight: "380px", overflowY: "auto", borderRadius: "8px" }}>
              {activePreviewTab === "telegram" && (
                <pre
                  style={{
                    background: "#ffffff",
                    padding: "16px",
                    borderRadius: "12px",
                    fontSize: "12px",
                    lineHeight: "1.6",
                    whiteSpace: "pre-wrap",
                    color: "var(--ink)",
                    fontFamily: "var(--mono)",
                    border: "1px solid rgba(36, 35, 31, 0.12)",
                    boxShadow: "0 2px 8px rgba(36, 35, 31, 0.03)",
                  }}
                >
                  {preview.telegram_text}
                </pre>
              )}
              {activePreviewTab === "whatsapp" && (
                <pre
                  style={{
                    background: "#ffffff",
                    padding: "16px",
                    borderRadius: "12px",
                    fontSize: "12px",
                    lineHeight: "1.6",
                    whiteSpace: "pre-wrap",
                    color: "var(--ink)",
                    fontFamily: "var(--mono)",
                    border: "1px solid rgba(36, 35, 31, 0.12)",
                    boxShadow: "0 2px 8px rgba(36, 35, 31, 0.03)",
                  }}
                >
                  {preview.whatsapp_text}
                </pre>
              )}
              {activePreviewTab === "email" && (
                <iframe
                  title="Email briefing preview"
                  sandbox=""
                  referrerPolicy="no-referrer"
                  srcDoc={preview.email_html || "<p>No email preview is available.</p>"}
                  style={{ width: "100%", height: "380px", background: "#ffffff", borderRadius: "8px", border: "1px solid var(--line)" }}
                />
              )}
            </div>
          ) : (
            <p style={{ color: "var(--text-soft)", fontSize: "13px" }}>
              {loading ? "Loading preview…" : previewUnavailable ? "Preview is unavailable. Refresh the data to retry." : "No preview is available yet."}
            </p>
          )}
        </article>
      </div>

      {/* 4. Past Delivery Logs Table */}
      <article className="mp-card rounded-2xl p-6 bg-[#faf7f0]/85 backdrop-blur-xl border border-[#24231f]/12 shadow-sm">
        <h3 style={{ margin: "0 0 12px 0" }}>Past Briefing Delivery Log</h3>
        {history && history.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--line)", textAlign: "left", color: "var(--text-soft)" }}>
                  <th style={{ padding: "8px" }}>Date</th>
                  <th style={{ padding: "8px" }}>Channel</th>
                  <th style={{ padding: "8px" }}>Recipient</th>
                  <th style={{ padding: "8px" }}>Subject / Summary</th>
                  <th style={{ padding: "8px" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map((log) => (
                  <tr key={log.id} style={{ borderBottom: "1px solid rgba(36, 35, 31, 0.08)" }}>
                    <td style={{ padding: "8px", color: "var(--text-soft)" }}>
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td style={{ padding: "8px" }}>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "4px",
                          background: log.channel === "telegram" ? "#5369d9" : log.channel === "whatsapp" ? "#15803d" : "#bd7652",
                          color: "#ffffff",
                        }}
                      >
                        {log.channel.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: "8px" }}>{log.recipient}</td>
                    <td style={{ padding: "8px" }}>{log.subject}</td>
                    <td style={{ padding: "8px" }}>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 600,
                          color: log.status === "failed" ? "#b91c1c" : log.status === "sent" ? "#15803d" : "#5369d9",
                        }}
                      >
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: "var(--text-soft)", fontSize: "13px" }}>No previous digests recorded yet.</p>
        )}
      </article>
    </ModuleLayout>
  );
}
