import { useState } from 'react';
import { X, Send, Bot, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface MockInterviewModalProps {
  onClose: () => void;
}

interface Message {
  role: 'assistant' | 'user';
  content: string;
}

export function MockInterviewModal({ onClose }: MockInterviewModalProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I am your AI interviewer. Are you ready to begin our mock interview session?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage: Message = { role: 'user', content: input };
    const newHistory = [...messages, userMessage];
    setMessages(newHistory);
    setInput('');
    setIsLoading(true);
    
    try {
      const reply = await api.interview.chat(newHistory);
      setMessages([...newHistory, { role: 'assistant', content: reply }]);
    } catch (error) {
      console.error(error);
      setMessages([...newHistory, { role: 'assistant', content: 'Sorry, I encountered an error. Could you repeat that?' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="flex h-[80vh] w-full max-w-2xl flex-col rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-700 p-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">Mock Interview Session</h3>
            <p className="text-xs text-slate-400">Technical & Behavioral Interview</p>
          </div>
          <button onClick={onClose} className="rounded p-1 hover:bg-slate-800 text-slate-400 transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={cn('flex items-start gap-3', msg.role === 'user' ? 'flex-row-reverse' : '')}>
              <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", msg.role === 'user' ? 'bg-indigo-500' : 'bg-slate-700')}>
                {msg.role === 'user' ? <User className="h-4 w-4 text-white" /> : <Bot className="h-4 w-4 text-emerald-400" />}
              </div>
              <div className={cn("rounded-lg p-3 max-w-[80%] text-sm", msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-200')}>
                {msg.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700">
                <Bot className="h-4 w-4 text-emerald-400" />
              </div>
              <div className="rounded-lg bg-slate-800 p-3 text-sm text-slate-400 italic">
                Thinking...
              </div>
            </div>
          )}
        </div>
        
        <div className="border-t border-slate-700 p-4">
          <form 
            onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your answer..."
              className="flex-1 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={isLoading}
            />
            <Button type="submit" disabled={!input.trim() || isLoading} size="sm">
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
