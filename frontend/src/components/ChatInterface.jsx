import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, User, Bot, Loader2, Sparkles, AlertCircle, Copy, Check, Download } from 'lucide-react';

const ChatInterface = ({ onSearch, isLoading, error, messages, onDownloadPDF }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const [copiedId, setCopiedId] = useState(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSearch(input.trim());
      setInput('');
    }
  };

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const MessageBubble = ({ message, idx }) => {
    const isUser = message.role === 'user';
    const isError = message.role === 'error';
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className={`flex w-full mb-8 ${isUser ? 'justify-end' : 'justify-start'}`}
      >
        <div className={`flex max-w-[90%] md:max-w-[80%] gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          {/* Avatar */}
          <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-lg ${
            isUser ? 'bg-primary/20' : isError ? 'bg-red-500/10' : 'bg-secondary/20'
          }`}>
            {isUser ? <User className="w-5 h-5 text-primary" /> : isError ? <AlertCircle className="w-5 h-5 text-red-400" /> : <Bot className="w-5 h-5 text-secondary" />}
          </div>

          {/* Content */}
          <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
            <div className={`
              rounded-2xl p-6 shadow-xl backdrop-blur-sm border 
              ${isUser 
                ? 'bg-primary/10 border-primary/20 text-white rounded-tr-sm' 
                : isError
                  ? 'bg-red-500/5 border-red-500/20 text-red-200'
                  : 'bg-surface/40 border-white/5 text-gray-200 rounded-tl-sm'
              }
            `}>
              {isUser ? (
                <p className="text-lg">{message.content}</p>
              ) : (
                <div className="prose prose-invert prose-lg max-w-none font-serif leading-relaxed">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}
            </div>

            {/* Actions for Assistant Messages */}
            {!isUser && !isError && (
              <div className="flex items-center gap-2 mt-2 ml-2">
                <button 
                  onClick={() => handleCopy(message.content, idx)}
                  className="p-1.5 hover:bg-white/5 rounded-lg transition-colors text-subtext hover:text-white"
                  title="Copy"
                >
                  {copiedId === idx ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                </button>
                {message.topic && (
                    <button
                        onClick={() => onDownloadPDF(message.content, message.topic)}
                        className="p-1.5 hover:bg-white/5 rounded-lg transition-colors text-subtext hover:text-white"
                        title="Download PDF"
                    >
                        <Download className="w-4 h-4" />
                    </button>
                )}
                {message.results && (
                  <span className="text-xs text-subtext px-2 py-0.5 bg-white/5 rounded-full border border-white/5">
                    {message.results.length} sources
                  </span>
                )}
              </div>
            )}

            {/* Follow-up Questions */}
            {!isUser && message.followup_questions && (
              <div className="mt-4 flex flex-wrap gap-2">
                {message.followup_questions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => onSearch(q)}
                    className="text-xs px-3 py-1.5 bg-primary/5 hover:bg-primary/15 border border-primary/10 hover:border-primary/30 rounded-full text-primary/80 hover:text-primary transition-colors flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3 h-3" />
                    {q}
                  </button>
                ))}
              </div>
            )}
            
            {/* Sources Preview */}
             {!isUser && message.results && message.results.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2 max-w-2xl">
                    {message.results.slice(0, 3).map((source, i) => (
                        <a 
                            key={i} 
                            href={source.href}
                            target="_blank"
                            rel="noreferrer" 
                            className="text-xs text-subtext hover:text-primary flex items-center gap-1 bg-black/20 px-2 py-1 rounded truncate max-w-[150px]"
                        >
                            <img 
                                src={`https://www.google.com/s2/favicons?domain=${new URL(source.href).hostname}`} 
                                alt="" 
                                className="w-3 h-3 opacity-50"
                            />
                            <span className="truncate">{new URL(source.href).hostname}</span>
                        </a>
                    ))}
                </div>
            )}
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col h-[calc(100vh-140px)]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-60">
            <Sparkles className="w-16 h-16 text-primary mb-6 animate-pulse" />
            <h3 className="text-2xl font-bold text-white mb-2">Hello, I'm Aura.</h3>
            <p className="text-subtext max-w-md">
              I'm your advanced research companion. Ask me anything, and I'll explore the web to find comprehensive answers for you.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} idx={idx} />
          ))
        )}
        
        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex w-full mb-8 justify-start">
             <div className="flex gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
                    <Loader2 className="w-5 h-5 text-secondary animate-spin" />
                </div>
                <div className="flex items-center gap-2 text-subtext text-sm pt-2">
                    <span className="animate-pulse">Thinking...</span>
                </div>
             </div>
          </div>
        )}
        
        {/* Error Message */}
        {error && (
             <MessageBubble message={{role: 'error', content: error}} idx="error" />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-surface/30 backdrop-blur-md border-t border-white/5">
        <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything..."
            disabled={isLoading}
            className="w-full bg-black/20 border border-white/10 rounded-2xl py-4 pl-6 pr-14 text-lg text-white placeholder-white/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-primary hover:bg-primary/90 rounded-xl text-background transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
