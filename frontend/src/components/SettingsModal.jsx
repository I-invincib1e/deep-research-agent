import React, { useState } from 'react';
import { Settings, X, Save, Key, Globe, Cpu } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const SettingsModal = ({ isOpen, onClose, config, onSave }) => {
  const [localConfig, setLocalConfig] = useState(config);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setLocalConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = () => {
    onSave(localConfig);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-0 m-auto z-50 w-full max-w-md h-fit bg-surface border border-white/10 rounded-2xl shadow-2xl p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Settings className="w-5 h-5 text-primary" />
                Configuration
              </h2>
              <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                <X className="w-5 h-5 text-subtext" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Provider Selection */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-subtext">AI Provider</label>
                <div className="relative">
                  <Cpu className="absolute left-3 top-3 w-4 h-4 text-subtext" />
                  <select
                    name="provider"
                    value={localConfig.provider}
                    onChange={handleChange}
                    className="w-full bg-background border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-primary/50 appearance-none"
                  >
                    <option value="groq">Groq (Llama 3.3)</option>
                    <option value="openai">OpenAI (GPT-4)</option>
                    <option value="anthropic">Anthropic (Claude 3)</option>
                    <option value="custom">Custom (Local/OpenAI Compatible)</option>
                  </select>
                </div>
              </div>

              {/* API Key */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-subtext">API Key</label>
                <div className="relative">
                  <Key className="absolute left-3 top-3 w-4 h-4 text-subtext" />
                  <input
                    type="password"
                    name="apiKey"
                    value={localConfig.apiKey}
                    onChange={handleChange}
                    placeholder={localConfig.provider === 'custom' ? 'Optional for local' : 'Enter your API Key'}
                    className="w-full bg-background border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white placeholder-subtext/50 focus:outline-none focus:border-primary/50"
                  />
                </div>
              </div>

              {/* Box URL (Custom Only) */}
              <AnimatePresence>
                {localConfig.provider === 'custom' && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="space-y-2 overflow-hidden"
                  >
                    <label className="text-sm font-medium text-subtext">Base URL</label>
                    <div className="relative">
                      <Globe className="absolute left-3 top-3 w-4 h-4 text-subtext" />
                      <input
                        type="text"
                        name="baseUrl"
                        value={localConfig.baseUrl}
                        onChange={handleChange}
                        placeholder="http://localhost:11434/v1"
                        className="w-full bg-background border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white placeholder-subtext/50 focus:outline-none focus:border-primary/50"
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Model Name */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-subtext">Model Name (Optional)</label>
                <input
                  type="text"
                  name="model"
                  value={localConfig.model}
                  onChange={handleChange}
                  placeholder={localConfig.provider === 'groq' ? 'llama-3.3-70b-versatile' : 'gpt-4o'}
                  className="w-full bg-background border border-white/10 rounded-xl py-2.5 px-4 text-white placeholder-subtext/50 focus:outline-none focus:border-primary/50"
                />
              </div>
            </div>

            <div className="mt-8">
              <button
                onClick={handleSave}
                className="w-full flex items-center justify-center gap-2 bg-primary text-background font-semibold py-3 rounded-xl hover:bg-primary/90 transition-colors"
                >
                <Save className="w-5 h-5" />
                Save Configuration
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SettingsModal;
