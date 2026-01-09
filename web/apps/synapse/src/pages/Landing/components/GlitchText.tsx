import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";

// Glitchy, pixelated, and retro fonts for the glitch effect
const glitchFonts = [
  "'VT323', monospace",           // Retro terminal/CRT style
  "'Press Start 2P', cursive",    // 8-bit pixelated
  "'Share Tech Mono', monospace", // Tech/hacker style
  "'Silkscreen', cursive",        // Pixel art style
  "'Major Mono Display', monospace", // Stylized mono
  "'Orbitron', sans-serif",       // Futuristic/sci-fi
  "'Courier New', monospace",     // Classic terminal
];

// Get a random font from the list
const getRandomFont = () =>
  glitchFonts[Math.floor(Math.random() * glitchFonts.length)];

interface HoverGlitchCharProps {
  char: string;
  charKey: string;
}

const HoverGlitchChar = ({ char, charKey }: HoverGlitchCharProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const [currentFont, setCurrentFont] = useState<string>("");
  const charRef = useRef<HTMLSpanElement>(null);
  const [charWidth, setCharWidth] = useState<number | null>(null);

  // Measure character width on mount to prevent layout shift
  useEffect(() => {
    if (charRef.current && charWidth === null) {
      setCharWidth(charRef.current.offsetWidth);
    }
  }, [charWidth]);

  const handleMouseEnter = () => {
    setCurrentFont(getRandomFont());
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
  };

  if (char === " ") {
    return (
      <span className="inline-block" style={{ width: "0.3em" }}>
        &nbsp;
      </span>
    );
  }

  return (
    <span
      ref={charRef}
      className="relative inline-block cursor-default"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{
        // Lock width to prevent layout shift during transition
        width: charWidth ? `${charWidth}px` : undefined,
      }}
    >
      {/* Normal character - always present to maintain layout */}
      <span className="inline-block">{char}</span>
      
      {/* Glitched overlay - absolute positioned with z-index to not affect layout */}
      {isHovered && (
        <motion.span
          key={`glitch-${charKey}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.1, ease: "easeOut" }}
          className="absolute inset-0 flex items-center justify-center text-black z-10"
          style={{
            fontFamily: currentFont,
            backgroundColor: "white",
          }}
        >
          {char}
        </motion.span>
      )}
    </span>
  );
};

// Multi-line version that handles line breaks properly
interface GlitchTextBlockProps {
  lines: string[];
  className?: string;
  lineClassName?: string;
}

export const GlitchTextBlock = ({
  lines,
  className = "",
  lineClassName = "",
}: GlitchTextBlockProps) => {
  return (
    <span className={className}>
      {lines.map((line, lineIndex) => (
        <span key={lineIndex} className={lineClassName}>
          {line.split("").map((char, charIndex) => (
            <HoverGlitchChar
              key={`${lineIndex}-${charIndex}`}
              char={char}
              charKey={`${lineIndex}-${charIndex}`}
            />
          ))}
          {lineIndex < lines.length - 1 && <br />}
        </span>
      ))}
    </span>
  );
};

// Single line version
interface GlitchTextProps {
  text: string;
  className?: string;
}

export const GlitchText = ({ text, className = "" }: GlitchTextProps) => {
  return (
    <span className={className}>
      {text.split("").map((char, index) => (
        <HoverGlitchChar key={index} char={char} charKey={`${index}`} />
      ))}
    </span>
  );
};

