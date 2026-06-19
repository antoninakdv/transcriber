import { useState } from 'react';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import SettingsPanel from './pages/SettingsPanel';

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="app">
      <Navbar onToggleSettings={() => setSettingsOpen((o) => !o)} settingsOpen={settingsOpen} />
      <div className="app-layout">
        <main className="main-content">
          <HomePage />
        </main>
        <aside className={`settings-panel ${settingsOpen ? 'settings-panel--open' : ''}`}>
          <SettingsPanel />
        </aside>
      </div>
      {settingsOpen && <div className="settings-overlay" onClick={() => setSettingsOpen(false)} />}
    </div>
  );
}
