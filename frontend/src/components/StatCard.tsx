interface Props {
  label: string;
  value: string | number;
  hint?: string;
}

export function StatCard({ label, value, hint }: Props) {
  return (
    <div className="bg-ink-800 rounded-lg p-4 border border-ink-700">
      <div className="text-xs uppercase tracking-wide text-ink-300">{label}</div>
      <div className="text-2xl font-bold text-white mt-1">{value}</div>
      {hint ? <div className="text-xs text-ink-300 mt-1">{hint}</div> : null}
    </div>
  );
}