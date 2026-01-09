import React from 'react';
import { motion } from 'framer-motion';

const AuroraBackground = ({ children }) => {
  return (
    <div className="relative min-h-screen bg-background text-text selection:bg-primary/30 overflow-hidden">
      {/* Aurora Effects */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <motion.div 
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
            rotate: [0, 90, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="absolute -top-[50%] -left-[10%] w-[70vw] h-[70vw] rounded-full bg-primary/10 blur-[120px]"
        />
        <motion.div 
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.2, 0.4, 0.2],
            x: [0, 100, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear", delay: 2 }}
          className="absolute top-[20%] -right-[20%] w-[60vw] h-[60vw] rounded-full bg-accent/10 blur-[100px]"
        />
        <motion.div 
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{ duration: 18, repeat: Infinity, ease: "easeInOut", delay: 5 }}
          className="absolute -bottom-[20%] left-[20%] w-[50vw] h-[50vw] rounded-full bg-primary/5 blur-[80px]"
        />
      </div>

      {/* Grid Overlay */}
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />

      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default AuroraBackground;
