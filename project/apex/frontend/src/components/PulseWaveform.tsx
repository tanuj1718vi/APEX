export type PulseTone = "idle" | "live" | "success" | "critical";

interface PulseWaveformProps {
  tone: PulseTone;
  label: string;
}

const LABELS: Record<PulseTone, string> = {
  idle: "STANDBY",
  live: "LIVE",
  success: "NOMINAL",
  critical: "FAULT",
};

/**
 * The signature element of the Signal Deck design: a live telemetry
 * line whose shape and motion are driven by real state, not
 * decoration layered on top of it.
 *
 *   idle     - flat line, no motion (nothing running)
 *   live     - active waveform, travels continuously (a run is in
 *              progress)
 *   success  - a settled waveform, static (run completed)
 *   critical - a jagged waveform that flickers (run failed/aborted)
 */
export function PulseWaveform({ tone, label }: PulseWaveformProps) {
  const path =
    tone === "critical"
      ? "M0,12 L10,12 L14,2 L18,22 L22,4 L26,20 L30,12 L40,12 L44,3 L48,21 L52,12 L64,12"
      : tone === "idle"
        ? "M0,12 L64,12"
        : "M0,12 L8,12 C11,12 11,4 14,4 C17,4 17,20 20,20 C23,20 23,12 26,12 L38,12 C41,12 41,4 44,4 C47,4 47,20 50,20 C53,20 53,12 56,12 L64,12";

  return (
    <div className={`pulse-waveform tone-${tone}`}>
      <svg width="64" height="24" viewBox="0 0 64 24">
        <path
          className="pulse-line"
          d={path}
          strokeDasharray={tone === "live" ? "6 4" : undefined}
        />
      </svg>
      <span className="pulse-waveform-label">{LABELS[tone]} · {label}</span>
    </div>
  );
}
