const MODELS = [
  { value: 'tiny', label: 'Tiny', desc: 'Fastest, least accurate (~1GB VRAM)' },
  { value: 'base', label: 'Base', desc: 'Good balance (~1GB VRAM)' },
  { value: 'small', label: 'Small', desc: 'Better accuracy (~2GB VRAM)' },
  { value: 'medium', label: 'Medium', desc: 'High accuracy (~5GB VRAM)' },
  { value: 'large', label: 'Large', desc: 'Best accuracy (~10GB VRAM)' },
];

export default function ModelSelector({ value, onChange }) {
  return (
    <div className="model-selector">
      <label htmlFor="model-select">Whisper Model</label>
      <select id="model-select" value={value} onChange={(e) => onChange(e.target.value)}>
        {MODELS.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label} — {m.desc}
          </option>
        ))}
      </select>
    </div>
  );
}
