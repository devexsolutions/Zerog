import React from 'react';

export default function Logo({ className = "w-12 h-12", showText = true }: { className?: string, showText?: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center" suppressHydrationWarning>
      {/* Container with background color */}
      <div className={`relative ${className} bg-[#0F172A] rounded-xl flex items-center justify-center p-2`} suppressHydrationWarning>
        <svg
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-full h-full"
        >
            {/* L Shape */}
            <path
            d="M25 20V80H60"
            stroke="white"
            strokeWidth="12"
            strokeLinecap="butt"
            strokeLinejoin="miter"
            />
            
            {/* V Shape */}
            <path
            d="M55 20L75 80L95 20"
            stroke="white"
            strokeWidth="12"
            strokeLinecap="butt"
            strokeLinejoin="miter"
            />

            {/* Arrow Element - The 'Arrow' integrated into the V */}
            <path
            d="M65 45L75 20L85 45"
            fill="white"
            />
            <path
            d="M75 20L75 55"
            stroke="white"
            strokeWidth="6"
            />
        </svg>
      </div>
      
      {showText && (
        <span className="mt-3 text-2xl font-bold tracking-[0.2em] text-[#0F172A] uppercase font-sans">
          Leva
        </span>
      )}
    </div>
  );
}
