export default function Navbar({ onToggleSettings, settingsOpen }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">Whisper Transcriber</div>
      <button
        className={`btn btn-settings ${settingsOpen ? 'active' : ''}`}
        onClick={onToggleSettings}
      >
        Settings
      </button>
    </nav>
  );
}
