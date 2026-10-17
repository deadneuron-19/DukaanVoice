import { useState } from "react";
import { Check, CircleHelp, Headphones, Languages, Moon, Sun, Wifi, WifiOff } from "lucide-react";
import { Button, ErrorPanel, LoadingPanel } from "../components/ui";
import { useRemoteData } from "../hooks/use-remote-data";
import { useTheme, type ThemeChoice } from "../hooks/use-theme";
import { api, apiBaseUrl } from "../lib/api-client";

const themeOptions: Array<{ value: ThemeChoice; label: string; icon: typeof Sun }> = [
  { value: "light", label: "Daylight", icon: Sun },
  { value: "dark", label: "After hours", icon: Moon },
  { value: "system", label: "Follow device", icon: Check },
];

export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { data, loading, error, reload } = useRemoteData(api.health);
  const [language, setLanguage] = useState(localStorage.getItem("dukaanvoice-language") || "English");
  const chooseLanguage = (value: string) => {
    setLanguage(value);
    localStorage.setItem("dukaanvoice-language", value);
  };
  return (
    <div className="page-wrap interior-page settings-page">
      <div className="page-heading"><div><span className="eyebrow">MAKE YOURSELF AT HOME</span><h1>Settings</h1><p>A few small choices to make ordering feel like yours.</p></div></div>
      <div className="settings-layout">
        <section className="settings-group">
          <div className="settings-group-title"><span className="settings-icon"><Sun size={18} /></span><div><h2>Appearance</h2><p>Give the shop a little daylight, or settle in for the evening.</p></div></div>
          <div className="theme-options" role="group" aria-label="Theme preference">
            {themeOptions.map(({ value, label, icon: Icon }) => <button key={value} className={`theme-option ${theme === value ? "selected" : ""}`} onClick={() => setTheme(value)} aria-pressed={theme === value}><Icon size={18} /><span>{label}</span>{theme === value && <Check size={16} className="option-check" />}</button>)}
          </div>
        </section>
        <section className="settings-group">
          <div className="settings-group-title"><span className="settings-icon"><Languages size={18} /></span><div><h2>Language preference</h2><p>The ordering assistant may understand Hindi, Hinglish and English when LLM extraction is configured. This preference does not change browser transcription.</p></div></div>
          <label className="settings-select-label" htmlFor="language-setting">Your preferred language</label>
          <select id="language-setting" className="settings-select" value={language} onChange={(event) => chooseLanguage(event.target.value)}><option>English</option><option>Hindi</option><option>Hinglish</option></select>
        </section>
        <section className="settings-group">
          <div className="settings-group-title"><span className="settings-icon"><Wifi size={18} /></span><div><h2>Connection to the shop</h2><p>API health is checked when you open this page. No credentials are sent from the browser.</p></div></div>
          <div className={`connection-card ${data ? "connected" : error ? "disconnected" : ""}`}>
            {loading ? <LoadingPanel label="Checking the backend…" /> : error ? <><WifiOff size={19} /><div><strong>Can’t connect right now</strong><small>{error}</small></div><Button size="small" variant="secondary" onClick={() => void reload()}>Retry</Button></> : <><Wifi size={19} /><div><strong>{data?.app} is responding</strong><small>{data?.environment} · {apiBaseUrl === "/api" ? "Vite API proxy" : apiBaseUrl}</small></div><span className="connection-dot" /></>}
          </div>
          {error && <ErrorPanel message={error} retry={() => void reload()} />}
        </section>
        <section className="settings-group">
          <div className="settings-group-title"><span className="settings-icon"><Headphones size={18} /></span><div><h2>Voice & microphone</h2><p>Microphone permission is not requested. Recording stays disabled until audio upload is supported.</p></div></div>
          <div className="feature-note"><CircleHelp size={18} /><p>Live transcription and spoken replies are unavailable. The backend has no verified Gnani audio-upload request contract yet, so recording cannot be sent for transcription. Type your grocery list on the home page instead.</p></div>
        </section>
      </div>
      <div className="settings-footnote">This service does not have accounts or sign-in yet. Order history is available to anyone who can reach this backend; avoid exposing it publicly before access controls are added.</div>
    </div>
  );
}
