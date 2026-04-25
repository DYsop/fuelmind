interface StatCardProps {
  label: string;
  value: string;
  hint?: string;
}

export function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <article className="card stat-card">
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </article>
  );
}

