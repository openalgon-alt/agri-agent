import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Bot, User, ChevronDown, ChevronUp, Loader2, MessageSquare, Database, Settings, Upload, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';

// --- TYPES ---
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  thought?: string; // The "Glass Box" reasoning
  timestamp: number;
}

interface DebugLog {
  timestamp: string;
  node: string;
  output: any;
}

// --- COMPONENTS ---

const Sidebar = ({ activeTab, onTabChange }: { activeTab: string, onTabChange: (tab: string) => void }) => (
  <div className="w-16 bg-[#F5F2EB] border-r border-[#E6E1D6] flex flex-col items-center py-6 gap-6 fixed left-0 top-0 h-full z-30">
    <div className="w-8 h-8 bg-black text-white rounded-lg flex items-center justify-center font-serif font-bold mb-4">M</div>

    <button onClick={() => onTabChange('chat')} className={clsx("p-2 rounded-lg transition-colors", activeTab === 'chat' ? "bg-mw-primary/10 text-mw-primary" : "text-gray-500 hover:bg-black/5")}>
      <MessageSquare size={24} />
    </button>

    <button onClick={() => onTabChange('admin')} className={clsx("p-2 rounded-lg transition-colors", activeTab === 'admin' ? "bg-mw-primary/10 text-mw-primary" : "text-gray-500 hover:bg-black/5")}>
      <Database size={24} />
    </button>

    <button onClick={() => onTabChange('debug')} className={clsx("p-2 rounded-lg transition-colors", activeTab === 'debug' ? "bg-mw-primary/10 text-mw-primary" : "text-gray-500 hover:bg-black/5")}>
      <div className="relative">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="8" height="14" x="8" y="6" rx="4" /><path d="m19 7-3 2" /><path d="m5 7 3 2" /><path d="m19 19-3-2" /><path d="m5 19 3-2" /><path d="M20 13h-4" /><path d="M4 13h4" /><path d="m10 4 1 2" /><path d="m14 4-1 2" /></svg>
      </div>
    </button>

    <button onClick={() => onTabChange('settings')} className={clsx("p-2 rounded-lg transition-colors", activeTab === 'settings' ? "bg-mw-primary/10 text-mw-primary" : "text-gray-500 hover:bg-black/5")}>
      <Settings size={24} />
    </button>
  </div>
);

const DebugView = ({ logs }: { logs: DebugLog[] }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="flex flex-col h-screen bg-[#1E1E1E] text-gray-300 font-mono text-sm">
      <div className="p-4 border-b border-gray-700 bg-[#252526] flex justify-between items-center sticky top-0 z-10">
        <h2 className="font-bold text-white flex items-center gap-2">
          <span className="text-green-500">●</span> Live Workflow Console
        </h2>
        <span className="text-xs px-2 py-1 bg-gray-800 rounded">{logs.length} Events</span>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {logs.length === 0 && (
          <div className="text-center text-gray-600 mt-20 italic">Waiting for graph events...</div>
        )}
        {logs.map((log, i) => (
          <div key={i} className="border-l-2 border-gray-600 pl-4 py-1 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs text-gray-500">{new Date(parseFloat(log.timestamp) * 1000).toLocaleTimeString()}</span>
              <span className={clsx(
                "text-xs font-bold px-2 py-0.5 rounded uppercase",
                log.node === "Supervisor" ? "bg-blue-900 text-blue-200" :
                  log.node === "Librarian" ? "bg-purple-900 text-purple-200" :
                    log.node === "Analyst" ? "bg-amber-900 text-amber-200" :
                      "bg-gray-700"
              )}>{log.node}</span>
            </div>
            <div className="bg-[#000000] p-3 rounded-md overflow-x-auto border border-gray-800">
              <pre className="text-xs leading-relaxed text-green-400">
                {JSON.stringify(log.output, null, 2)}
              </pre>
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
      </div>
    </div>
  );
};

const SettingsView = () => (
  <div className="p-8 max-w-2xl mx-auto">
    <h1 className="font-serif text-3xl font-bold mb-8">System Settings</h1>

    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm mb-6">
      <h3 className="font-semibold mb-4 text-lg">AI Model Source</h3>
      <div className="space-y-3">
        {["Local (Llama 3.2)", "Local (Qwen 3 VL)", "Cloud (Gemini)"].map(model => (
          <label key={model} className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
            <input type="radio" name="model" defaultChecked={model.includes("Qwen")} className="w-4 h-4 text-mw-primary" />
            <span>{model}</span>
          </label>
        ))}
      </div>
    </div>

    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm mb-6">
      <h3 className="font-semibold mb-4 text-lg">Hardware Acceleration</h3>
      <div className="flex items-center justify-between p-4 bg-green-50 text-green-800 rounded-lg border border-green-200 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="font-medium">GPU Active (Vulkan/ROCm)</span>
        </div>
        <span className="text-xs uppercase tracking-wide font-bold">Online</span>
      </div>

      <button className="w-full py-2 border-2 border-mw-primary text-mw-primary font-semibold rounded-lg hover:bg-mw-primary hover:text-white transition-colors">
        ⚡ Force GPU Reload
      </button>
    </div>
  </div>
);

interface Document {
  filename: string;
  title: string;
  authors: string[];
}

const AdminView = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState("");
  const [progress, setProgress] = useState(0);

  const fetchDocs = () => {
    setLoading(true);
    fetch('http://localhost:8000/documents')
      .then(res => res.json())
      .then(data => {
        setDocuments(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch documents", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    setSyncStatus("Starting sync...");
    setProgress(0);
    try {
      const response = await fetch('http://localhost:8000/documents/sync', { method: 'POST' });

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(line => line.trim() !== '');

        for (const line of lines) {
          try {
            const data = JSON.parse(line);

            // If the inner status is also a JSON string, parse it again
            let innerData = data;
            if (typeof data.status === 'string' && data.status.startsWith('{')) {
              try { innerData = JSON.parse(data.status); } catch (e) { }
            }

            setSyncStatus(innerData.status || data.status);
            if (innerData.percent !== undefined) setProgress(innerData.percent);

          } catch (e) {
            console.error("Parse error", e);
          }
        }
      }

      fetchDocs();
    } catch (e) {
      setSyncStatus("Sync failed.");
    } finally {
      setSyncing(false);
      setTimeout(() => {
        setSyncStatus("");
        setProgress(0);
      }, 3000);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="font-serif text-3xl font-bold mb-2">Knowledge Base</h1>
      <p className="text-gray-500 mb-8">Manage PDF documents and RAG indexing.</p>

      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex flex-col gap-4 mb-6">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold">Indexed Documents ({documents.length})</h3>
            <div className="flex gap-2">
              <button
                onClick={handleSync}
                disabled={syncing}
                className="flex items-center gap-2 px-3 py-1 bg-mw-primary text-white text-sm rounded hover:bg-opacity-90 disabled:opacity-50"
              >
                {syncing ? <Loader2 size={14} className="animate-spin" /> : <Database size={14} />}
                {syncing ? "Syncing..." : "Sync New Files"}
              </button>
              <button onClick={fetchDocs} className="text-sm text-mw-primary hover:underline">Refresh</button>
            </div>
          </div>

          {(syncing || syncStatus) && (
            <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-mw-primary h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
              <div className="text-xs text-center text-gray-500 mt-1">{syncStatus} ({progress}%)</div>
            </div>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="animate-spin text-gray-400" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-500 font-medium">
                <tr>
                  <th className="px-4 py-3 rounded-vl">Title</th>
                  <th className="px-4 py-3">Authors</th>
                  <th className="px-4 py-3 rounded-vr">Filename</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {documents.map((doc, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{doc.title}</td>
                    <td className="px-4 py-3 text-gray-600">{doc.authors.join(", ")}</td>
                    <td className="px-4 py-3 text-gray-400 font-mono text-xs truncate max-w-[200px]">{doc.filename}</td>
                  </tr>
                ))}
                {documents.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-gray-500">No documents found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

const ThoughtBlock = ({ thought }: { thought: string }) => {
  const [isOpen, setIsOpen] = useState(true);

  if (!thought) return null;

  return (
    <div className="mb-4 bg-mw-card rounded-lg overflow-hidden border border-gray-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider hover:bg-gray-200 transition-colors"
      >
        <span>Thinking Process</span>
        {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="px-4 py-3 text-sm text-gray-600 font-mono bg-white/50 border-t border-gray-200 whitespace-pre-wrap"
          >
            {thought}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const ChatBubble = ({ msg }: { msg: Message }) => {
  const isAi = msg.role === 'assistant';

  return (
    <div className={clsx("flex gap-4 mb-8", isAi ? "" : "flex-row-reverse")}>
      {/* Avatar */}
      <div className={clsx(
        "w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm",
        isAi ? "bg-black text-white" : "bg-mw-primary text-white"
      )}>
        {isAi ? <Bot size={20} /> : <span className="font-serif font-bold">E</span>}
      </div>

      {/* Content */}
      <div className={clsx("max-w-[85%]", isAi ? "" : "text-right")}>
        <div className="font-serif font-bold mb-1 text-mw-text text-sm">
          {isAi ? "AgriCatalogues AI" : "You"}
        </div>

        {/* Final Answer */}
        <div className={clsx(
          "prose prose-sm max-w-none leading-relaxed prose-headings:font-serif prose-headings:font-bold prose-a:text-mw-primary",
          isAi ? "text-gray-800 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm" : "bg-[#F5F2EB] p-4 rounded-2xl text-gray-900 font-medium inline-block"
        )}>
          {msg.content ? <ReactMarkdown>{msg.content}</ReactMarkdown> : <span className="animate-pulse">_</span>}
        </div>
      </div>
    </div>
  );
};


function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1', role: 'assistant', timestamp: Date.now(),
      content: "Hello! I'm your Agricultural Assistant. I can help with crop yields, market prices, and more.",
      thought: "Initializing system... Loading RAG engine... Ready."
    }
  ]);
  const [isThinking, setIsThinking] = useState(false);
  const [debugLogs, setDebugLogs] = useState<DebugLog[]>([]); // NEW STATE
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTab]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsThinking(true);

    // Connect to Backend Streaming
    try {
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          history: messages.map(m => ({ role: m.role, content: m.content }))
        })
      });

      if (!response.body) throw new Error("No body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Create a placeholder message for AI
      const aiMsgId = (Date.now() + 1).toString();
      setMessages(prev => [...prev, {
        id: aiMsgId,
        role: 'assistant',
        content: '',
        thought: '',
        timestamp: Date.now()
      }]);

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep incomplete line

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '');
            if (dataStr === '[DONE]') {
              setIsThinking(false);
              break;
            }

            try {
              const data = JSON.parse(dataStr);

              // --- HANDLE DEBUG EVENTS ---
              if (data.type === 'debug') {
                setDebugLogs(prev => [...prev, data]);
                continue; // Skip the regular message processing
              }
              // ---------------------------

              setMessages(prev => prev.map(msg => {
                if (msg.id === aiMsgId) {
                  if (data.type === 'thought') {
                    return {
                      ...msg,
                      thought: msg.thought ? msg.thought + '\n > ' + data.content : ' > ' + data.content
                    };
                  }
                  if (data.type === 'answer') {
                    return { ...msg, content: data.content };
                  }
                }
                return msg;
              }));

            } catch (e) {
              console.error("Parse error", e);
            }
          }
        }
      }

    } catch (e) {
      console.error(e);
      setIsThinking(false);
      setMessages(prev => [...prev, {
        id: Date.now().toString(), role: 'assistant', content: "Error connecting to AI.", timestamp: Date.now()
      }]);
    }
  };

  return (
    <div className="min-h-screen flex bg-[#FDFBF7]">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex-1 ml-16 relative">

        {/* HEADER */}
        <header className="h-16 flex items-center justify-between px-8 border-b border-gray-200/50 bg-[#FDFBF7]/80 backdrop-blur sticky top-0 z-10">
          <h2 className="font-semibold tracking-tight text-lg">
            {activeTab === 'chat' && "AgriCatalogues AI"}
            {activeTab === 'admin' && "Knowledge Base"}
            {activeTab === 'settings' && "Settings"}
            {activeTab === 'debug' && "Debug Console"}
          </h2>
        </header>

        {/* CONTENT */}
        {activeTab === 'debug' && <DebugView logs={debugLogs} />}

        {activeTab === 'chat' && (
          <>
            <div className="pt-8 pb-32 px-8 max-w-4xl mx-auto min-h-screen">
              {messages.map((msg, i) => (
                <ChatBubble key={msg.id} msg={msg} />
              ))}
              <div ref={bottomRef} />
            </div>

            {/* Sticky Input Area */}
            <div className="fixed bottom-0 left-16 right-0 bg-gradient-to-t from-[#FDFBF7] via-[#FDFBF7] to-transparent pb-6 pt-10 px-8 z-20 flex justify-center">
              <div className="w-full max-w-4xl bg-white rounded-2xl shadow-lg border border-gray-200 flex items-center p-2 focus-within:ring-2 ring-black/5 transition-shadow">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Ask across the enterprise..."
                  className="flex-1 bg-transparent border-none focus:ring-0 px-4 py-3 text-lg outline-none placeholder:text-gray-300"
                />
                <button
                  onClick={handleSend}
                  className="p-3 bg-mw-card hover:bg-gray-200 rounded-xl transition-colors text-gray-600"
                >
                  {isThinking ? <Loader2 className="animate-spin" /> : <Send size={20} />}
                </button>
              </div>
            </div>
          </>
        )}

        {activeTab === 'settings' && <SettingsView />}
        {activeTab === 'admin' && <AdminView />}

      </main>
    </div>
  );
}

export default App;
