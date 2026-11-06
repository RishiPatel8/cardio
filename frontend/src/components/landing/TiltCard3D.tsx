import React, { useState, useRef } from "react";
import { motion } from "framer-motion";

interface TiltCard3DProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  maxTilt?: number;
  glareOpacity?: number;
  onClick?: () => void;
}

export const TiltCard3D: React.FC<TiltCard3DProps> = ({
  children,
  className = "",
  style = {},
  maxTilt = 12,
  glareOpacity = 0.25,
  onClick,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [glare, setGlare] = useState({ x: 50, y: 50, opacity: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const xPct = (x / rect.width) * 100;
    const yPct = (y / rect.height) * 100;

    const tiltX = ((y / rect.height) * 2 - 1) * -maxTilt;
    const tiltY = ((x / rect.width) * 2 - 1) * maxTilt;

    setTilt({ x: tiltX, y: tiltY });
    setGlare({ x: xPct, y: yPct, opacity: glareOpacity });
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
    setGlare((prev) => ({ ...prev, opacity: 0 }));
  };

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      animate={{
        rotateX: tilt.x,
        rotateY: tilt.y,
      }}
      transition={{ type: "spring", stiffness: 350, damping: 25 }}
      style={{
        transformStyle: "preserve-3d",
        perspective: 1000,
        position: "relative",
        cursor: onClick ? "pointer" : "default",
        ...style,
      }}
      className={className}
    >
      {/* Glare specular reflection */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "inherit",
          pointerEvents: "none",
          zIndex: 3,
          background: `radial-gradient(circle at ${glare.x}% ${glare.y}%, rgba(255, 255, 255, ${glare.opacity}) 0%, rgba(255, 255, 255, 0) 65%)`,
          transition: "opacity 0.25s ease",
        }}
      />
      <div style={{ transform: "translateZ(20px)", transformStyle: "preserve-3d", position: "relative", zIndex: 2 }}>
        {children}
      </div>
    </motion.div>
  );
};

export default TiltCard3D;
