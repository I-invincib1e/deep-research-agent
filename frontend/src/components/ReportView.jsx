import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion } from 'framer-motion';
import { FileText, ExternalLink, Copy, Check } from 'lucide-react';

const ReportView = ({ data }) => {
  const [copied, setCopied] = useState(false);

  if (!data) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(data.report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className="w-full max-w-4xl mx-auto mt-12 bg-surface/30 backdrop-blur-md rounded-2xl border border-white/5 p-8 md:p-12 shadow-2xl relative overflow-hidden"
    >
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent" />

      <div className="flex items-center justify-between gap-3 mb-8 border-b border-white/5 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary/10 rounded-lg">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">{data.topic}</h2>
            <p className="text-sm text-subtext">Deep Intelligence Report</p>
          </div>
        </div>
        <button 
          onClick={handleCopy}
          className="p-2 hover:bg-white/5 rounded-lg transition-colors border border-transparent hover:border-white/10 group"
          title="Copy Report"
        >
          {copied ? <Check className="h-5 w-5 text-green-400" /> : <Copy className="h-5 w-5 text-subtext group-hover:text-white" />}
        </button>
      </div>

      <div className="prose prose-invert prose-lg max-w-none font-serif leading-relaxed text-gray-300">
        <ReactMarkdown>{data.report}</ReactMarkdown>
      </div>

      {data.search_results && data.search_results.length > 0 && (
        <div className="mt-12 pt-8 border-t border-white/5">
          <h3 className="text-lg font-sans font-semibold text-white mb-6 flex items-center gap-2">
            <span className="w-1 h-6 bg-primary rounded-full"/>
            Sources Analyzed
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {data.search_results.map((source, idx) => (
              <a 
                key={idx} 
                href={source.href} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-start p-4 bg-surface/40 rounded-xl hover:bg-surface/80 border border-white/5 hover:border-primary/20 transition-all duration-300 group relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="flex-1 min-w-0 z-10">
                  <p className="text-sm font-medium text-gray-200 truncate group-hover:text-primary transition-colors pr-2">
                    {source.title}
                  </p>
                  <p className="text-xs text-subtext truncate font-mono opacity-60 mt-1">
                    {new URL(source.href).hostname}
                  </p>
                </div>
                <ExternalLink className="h-4 w-4 text-subtext group-hover:text-primary ml-3 flex-shrink-0 mt-0.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </a>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default ReportView;
