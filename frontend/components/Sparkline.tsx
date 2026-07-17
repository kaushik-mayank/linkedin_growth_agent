// Dependency-free inline SVG sparkline.
export function Sparkline({
  values,
  width = 120,
  height = 32,
  tone = "brand",
}: {
  values: number[];
  width?: number;
  height?: number;
  tone?: "brand" | "positive" | "negative";
}) {
  const clean = values.filter((v) => typeof v === "number" && !isNaN(v));
  if (clean.length < 2) {
    return (
      <div
        style={{ width, height }}
        className="flex items-center justify-center text-xs text-muted"
      >
        —
      </div>
    );
  }

  const min = Math.min(...clean);
  const max = Math.max(...clean);
  const range = max - min || 1;
  const stepX = width / (clean.length - 1);
  const pad = 3;
  const usableH = height - pad * 2;

  const points = clean.map((v, i) => {
    const x = i * stepX;
    const y = pad + usableH - ((v - min) / range) * usableH;
    return [x, y] as const;
  });

  const path = points
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");

  const areaPath =
    `${path} L${width},${height} L0,${height} Z`;

  const strokeColor = `rgb(var(--${tone}))`;
  const [lastX, lastY] = points[points.length - 1];

  return (
    <svg width={width} height={height} className="overflow-visible">
      <path d={areaPath} fill={strokeColor} opacity={0.08} />
      <path d={path} fill="none" stroke={strokeColor} strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lastX} cy={lastY} r={2.5} fill={strokeColor} />
    </svg>
  );
}
