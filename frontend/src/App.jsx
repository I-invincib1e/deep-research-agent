import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { BrainCircuit, Settings } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import AuroraBackground from './components/AuroraBackground';
import SettingsModal from './components/SettingsModal';

const App = () => {
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [config, setConfig] = useState({
    provider: 'groq',
    apiKey: '',
    model: '',
    baseUrl: ''
  });

  const handleSearch = async (userMessage) => {
    setLoading(true);
    setError(null);

    // Optimistically add user message
    const newMessages = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);

    const payload = {
      messages: newMessages.map(m => ({ role: m.role, content: m.content })),
      provider: config.provider,
      api_key: config.apiKey || undefined,
      model: config.model || undefined,
      base_url: config.baseUrl || undefined
    };

    try {
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
      
      // Add agent response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.report,
        topic: data.topic,
        results: data.search_results,
        followup_questions: data.followup_questions
      }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async (reportContent, topic) => {
     try {
      const response = await fetch('http://localhost:8000/api/export/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report: reportContent, title: topic }),
      });

      if (!response.ok) throw new Error('PDF export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${topic.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (error) {
      console.error('PDF download failed:', error);
      alert('PDF download failed. Please try again.');
    }
  };

  return (
    <AuroraBackground>
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
      
      <main className="relative container mx-auto px-4 pt-6 flex flex-col h-screen z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-2 px-2">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-xl shadow-[0_0_10px_rgba(203,164,93,0.3)]">
                    <BrainCircuit className="h-6 w-6 text-primary" />
                </div>
                <h1 className="text-2xl font-bold text-white tracking-tight">
                    Aura <span className="text-primary text-lg font-normal opacity-80">Research</span>
                </h1>
            </div>
            <button
                onClick={() => setIsSettingsOpen(true)}
                className="p-2 hover:bg-white/5 rounded-lg text-subtext hover:text-white transition-colors"
            >
                <Settings className="w-5 h-5" />
            </button>
        </div>

        {/* Chat Interface */}
        <ChatInterface 
          messages={messages} 
          onSearch={handleSearch} 
          isLoading={loading} 
          error={error}
          onDownloadPDF={handleDownloadPDF}
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
