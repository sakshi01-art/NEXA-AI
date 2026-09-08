import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Send, Square } from 'lucide-react';
import { Waveform } from './Waveform';

interface VoiceInputProps {
  isListening: boolean;
  transcript: string;
  onStartListening: () => void;
  onStopListening: () => void;
  onSendText: (text: string) => void;
  onCancel: () => void;
  isProcessing: boolean;
  audioLevel: number;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({
  isListening,
  transcript,
  onStartListening,
  onStopListening,
  onSendText,
  onCancel,
  isProcessing,
  audioLevel,
}) => {
  const [textInput, setTextInput] = useState('');
  const [showHint, setShowHint] = useState(true);

  useEffect(() => {
    if (transcript) {
      setTextInput(transcript);
      setShowHint(false);
    }
  }, [transcript]);

  const handleSubmit = () => {
    if (textInput.trim()) {
      onSendText(textInput);
      setTextInput('');
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-6 pb-8">
      {/* Waveform visualization */}
      <AnimatePresence>
        {isListening && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 80 }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4"
          >
            <Waveform audioLevel={audioLevel} isActive={isListening} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input container */}
      <div className="relative">
        <motion.div
          className="glass-panel rounded-2xl border border-gray-700/50 overflow-hidden"
          animate={{
            boxShadow: isListening
              ? '0 0 40px rgba(59, 130, 246, 0.3)'
              : '0 4px 16px rgba(0, 0, 0, 0.3)',
          }}
        >
          <div className="flex items-center gap-3 p-4">
            {/* Microphone button */}
            <motion.button
              onClick={isListening ? onStopListening : onStartListening}
              className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${
                isListening
                  ? 'bg-blue-500 hover:bg-blue-600'
                  : 'bg-indigo-500 hover:bg-indigo-600'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              disabled={isProcessing}
            >
              {isListening ? (
                <MicOff className="w-5 h-5 text-white" />
              ) : (
                <Mic className="w-5 h-5 text-white" />
              )}
            </motion.button>

            {/* Text input */}
            <div className="flex-1 relative">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
                placeholder={isListening ? 'Listening...' : 'Type or speak a command...'}
                className="w-full bg-transparent text-white placeholder-gray-500 outline-none text-lg"
                disabled={isListening || isProcessing}
              />
              
              {/* Hint text */}
              <AnimatePresence>
                {showHint && !textInput && !isListening && (
                  <motion.p
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute -bottom-6 left-0 text-xs text-gray-500"
                  >
                    Try: "Chrome kholo" or "System status bata" • Ctrl+Space to activate
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2">
              {isProcessing && (
                <motion.button
                  onClick={onCancel}
                  className="flex-shrink-0 w-10 h-10 rounded-lg bg-red-500/20 hover:bg-red-500/30 flex items-center justify-center transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Square className="w-4 h-4 text-red-400" />
                </motion.button>
              )}

              <motion.button
                onClick={handleSubmit}
                disabled={!textInput.trim() || isProcessing}
                className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center transition-colors ${
                  textInput.trim() && !isProcessing
                    ? 'bg-indigo-500 hover:bg-indigo-600'
                    : 'bg-gray-700 cursor-not-allowed opacity-50'
                }`}
                whileHover={textInput.trim() ? { scale: 1.05 } : {}}
                whileTap={textInput.trim() ? { scale: 0.95 } : {}}
              >
                <Send className="w-4 h-4 text-white" />
              </motion.button>
            </div>
          </div>

          {/* Language indicator */}
          <AnimatePresence>
            {transcript && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="px-4 pb-3 pt-1 border-t border-gray-700/50"
              >
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                  <span>Detected: Hinglish</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Keyboard shortcut indicator */}
      <div className="mt-4 flex items-center justify-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <kbd className="px-2 py-1 bg-gray-800 rounded border border-gray-700">Ctrl</kbd>
          <span>+</span>
          <kbd className="px-2 py-1 bg-gray-800 rounded border border-gray-700">Space</kbd>
          <span className="ml-1">to activate</span>
        </div>
        <div className="flex items-center gap-1">
          <kbd className="px-2 py-1 bg-gray-800 rounded border border-gray-700">Esc</kbd>
          <span className="ml-1">to cancel</span>
        </div>
      </div>
    </div>
  );
};
