"use client";

interface CuraMindLogoProps {
  /** "full" = icon + name + tagline (login page), "sidebar" = icon + name only */
  variant?: "full" | "sidebar";
}

export default function CuraMindLogo({ variant = "full" }: CuraMindLogoProps) {
  if (variant === "sidebar") {
    return (
      <div className="flex items-center gap-2.5">
        <LogoIcon size={34} />
        <div>
          <p className="font-extrabold text-[#1e3a6b] text-[15px] tracking-wide leading-tight">
            CuraMind
          </p>
          <p className="text-[8.5px] text-[#2b6cb0] font-semibold tracking-widest leading-tight uppercase">
            Evidence-Based Care
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <LogoIcon size={72} />
      <div className="text-center">
        <p
          className="font-black tracking-[0.18em] text-[#1e3a6b]"
          style={{ fontSize: "28px", letterSpacing: "0.18em" }}
        >
          CURAMIND
        </p>
        <p
          className="font-semibold text-[#2b6cb0] tracking-widest mt-0.5"
          style={{ fontSize: "10px", letterSpacing: "0.22em" }}
        >
          EMPOWERING EVIDENCE-BASED CARE
        </p>
      </div>
    </div>
  );
}

function LogoIcon({ size }: { size: number }) {
  const cx = size / 2;
  const cy = size / 2;
  const s = size / 48; // scale factor relative to 48x48 design

  // Arc helper: draw a C opening to the right
  // Returns SVG path string for an arc centered at (cx,cy) with given radius and gap half-angle
  const arcPath = (r: number, gapDeg: number) => {
    const gapRad = (gapDeg * Math.PI) / 180;
    const x1 = cx + r * Math.cos(-gapRad);
    const y1 = cy + r * Math.sin(-gapRad);
    const x2 = cx + r * Math.cos(gapRad);
    const y2 = cy + r * Math.sin(gapRad);
    // large arc, counterclockwise (sweep=0)
    return `M${x1.toFixed(2)} ${y1.toFixed(2)} A${r} ${r} 0 1 0 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
  };

  const r1 = 21 * s, r2 = 15.5 * s, r3 = 10 * s;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Outer arc */}
      <path d={arcPath(r1, 45)} stroke="#1e3a6b" strokeWidth={3.8 * s} strokeLinecap="round" />
      {/* Middle arc */}
      <path d={arcPath(r2, 44)} stroke="#1e5ca0" strokeWidth={2.8 * s} strokeLinecap="round" />
      {/* Inner arc */}
      <path d={arcPath(r3, 43)} stroke="#4a90d9" strokeWidth={2 * s} strokeLinecap="round" />

      {/* Brain / neural icon */}
      <g transform={`translate(${cx - 8 * s}, ${cy - 9 * s}) scale(${s})`}>
        {/* left lobe */}
        <path
          d="M8 9 C6 7.5 2.5 8 1 10.5 C-0.5 13 1 16 3 17 C2 18.5 2 20.5 3.5 21.5 C5 22.5 7 22 8 21"
          stroke="#1e3a6b" strokeWidth="1.4" fill="none" strokeLinecap="round"
        />
        {/* right lobe */}
        <path
          d="M8 9 C10 7.5 13.5 8 15 10.5 C16.5 13 15 16 13 17 C14 18.5 14 20.5 12.5 21.5 C11 22.5 9 22 8 21"
          stroke="#1e3a6b" strokeWidth="1.4" fill="none" strokeLinecap="round"
        />
        {/* center line */}
        <line x1="8" y1="9" x2="8" y2="21" stroke="#2b6cb0" strokeWidth="0.9" strokeDasharray="2,1.5" />
        {/* nodes */}
        <circle cx="3.5" cy="12" r="1.3" fill="#4a90d9" />
        <circle cx="5" cy="17" r="1.3" fill="#4a90d9" />
        <circle cx="12.5" cy="12" r="1.3" fill="#4a90d9" />
        <circle cx="11" cy="17" r="1.3" fill="#4a90d9" />
        {/* bulb base */}
        <line x1="5" y1="22" x2="11" y2="22" stroke="#1e3a6b" strokeWidth="1.2" strokeLinecap="round" />
        <line x1="6" y1="24" x2="10" y2="24" stroke="#2b6cb0" strokeWidth="1.2" strokeLinecap="round" />
      </g>
    </svg>
  );
}
