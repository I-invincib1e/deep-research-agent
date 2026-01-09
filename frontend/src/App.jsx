import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit } from 'lucide-react';
import ResearchForm from './components/ResearchForm';
import ReportView from './components/ReportView';
import AuroraBackground from './components/AuroraBackground';
import SettingsModal from './components/SettingsModal';

const App = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [config, setConfig] = useState({
    provider: 'groq',
    apiKey: '',
    model: '',
    baseUrl: ''
  });

  const handleSearch = async (topic) => {
    setLoading(true);
    setResult(null);
    setError(null);

    const payload = {
      topic,
      provider: config.provider,
      // Map frontend config keys to backend API expected keys
      api_key: config.apiKey || undefined,
      model: config.model || undefined,
      base_url: config.baseUrl || undefined
    };

    try {
      // Note: Use mapped payload key 'api_key' instead of 'apiKey'
      const response = await fetch('http://localhost:8000/api/research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Research failed. Please check your settings and try again.');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuroraBackground>
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
      
      <main className="relative container mx-auto px-4 py-20 flex flex-col items-center min-h-screen z-10">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-2xl mb-6 shadow-[0_0_15px_rgba(203,164,93,0.3)]">
            <BrainCircuit className="h-10 w-10 text-primary" />
          </div>
          <h1 className="text-5xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60 mb-6 tracking-tight">
            Deep Research Agent
          </h1>
          <p className="text-xl text-subtext max-w-2xl mx-auto leading-relaxed">
            Enter a topic and let our AI automate web search, analysis, and report generation in seconds.
          </p>
        </motion.div>

        <ResearchForm 
          onSearch={handleSearch} 
          isLoading={loading} 
          onOpenSettings={() => setIsSettingsOpen(true)}
        />

        <AnimatePresence>
          {loading && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mt-12 text-center"
            >
              <div className="text-primary text-lg font-medium animate-pulse">Running Deep Analysis...</div>
              <p className="text-subtext text-sm mt-2">Searching web • Scraping content • Synthesizing insights</p>
            </motion.div>
          )}

          {error && (
             <motion.div 
             initial={{ opacity: 0 }}
             animate={{ opacity: 1 }}
             exit={{ opacity: 0 }}
             className="mt-12 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 max-w-lg mx-auto"
           >
             {error}
           </motion.div>
          )}
        </AnimatePresence>

        <ReportView 
          data={result} 
          onFollowupClick={(question) => handleSearch(question)}
        />
      </main>

      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)}
        config={config}
        onSave={setConfig}
      />
    </AuroraBackground>
  );
};

export default App;
