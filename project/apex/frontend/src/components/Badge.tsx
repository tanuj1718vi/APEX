interface BadgeProps {
  kind: string;
  label?: string;
}

export function Badge({ kind, label }: BadgeProps) {
  return <span className={`badge badge-${kind}`}>{label ?? kind}</span>;
}
