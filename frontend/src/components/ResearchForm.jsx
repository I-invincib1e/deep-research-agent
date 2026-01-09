import React, { useState } from 'react';
import { Search, Loader2, Settings } from 'lucide-react';
import { motion } from 'framer-motion';

const ResearchForm = ({ onSearch, isLoading, onOpenSettings }) => {
  const [topic, setTopic] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim() && !isLoading) {
      onSearch(topic);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <motion.form 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        onSubmit={handleSubmit} 
        className="relative group"
      >
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          {isLoading ? (
            <Loader2 className="h-6 w-6 text-primary animate-spin" />
          ) : (
            <Search className="h-6 w-6 text-subtext group-hover:text-primary transition-colors duration-300" />
          )}
        </div>
        <input
          type="text"
          className="block w-full pl-12 pr-12 py-4 bg-surface/50 border border-white/10 rounded-xl 
                     text-lg text-white placeholder-subtext focus:outline-none focus:ring-2 focus:ring-primary/50 
                     focus:border-primary/50 transition-all duration-300 backdrop-blur-sm shadow-xl"
          placeholder="What do you want to research?"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          disabled={isLoading}
        />
        <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
            <button 
                type="button" 
                onClick={onOpenSettings}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors group/settings"
                title="Settings"
            >
                <Settings className="w-5 h-5 text-subtext group-hover/settings:text-white" />
            </button>
        </div>
        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary/20 via-accent/20 to-primary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none -z-10 blur-xl" />
      </motion.form>
    </div>
  );
};

export default ResearchForm;
