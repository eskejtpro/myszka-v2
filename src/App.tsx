import React, { useState } from 'react';
import {
  Mic,
  Languages,
  ScanText,
  ClipboardList,
  StickyNote,
  Zap,
  Terminal,
  CheckCircle2,
  ShieldCheck,
  Cpu,
  Monitor,
  Sparkles,
  Command,
  ArrowRight,
  Copy,
  CornerDownLeft,
  RotateCcw,
  Globe,
  X,
  Layers,
  MousePointer,
  Pin,
  Trash2,
  Search,
  Plus,
  Play,
  Pause,
  Edit3,
  Activity,
  Settings
} from 'lucide-react';

interface ModuleConfig {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  angleDeg: number;
  accentColor: string;
  status: 'READY' | 'WORKING' | 'ERROR' | 'DISABLED';
  description: string;
  versionStage: string;
}

const MODULES: ModuleConfig[] = [
  {
    id: 'speech',
    title: 'MIKROFON',
    subtitle: 'Mowa → Tekst',
    icon: <Mic className="w-5 h-5" />,
    angleDeg: 270,
    accentColor: '#0284C7',
    status: 'READY',
    description: 'Zamiana mowy na tekst (STT) przez Gemini 3.5 Transcribe z bezpośrednim wklejaniem.',
    versionStage: 'v0.5 (Zrealizowane)',
  },
  {
    id: 'translate',
    title: 'TŁUMACZ',
    subtitle: 'AI Translation',
    icon: <Languages className="w-5 h-5" />,
    angleDeg: 330,
    accentColor: '#2DD4BF',
    status: 'READY',
    description: 'Tłumaczenie zaznaczonego tekstu przez Gemini 3.7 Flash z fallbackiem do 3.6 Flash.',
    versionStage: 'v0.3 (Zrealizowane)',
  },
  {
    id: 'ocr',
    title: 'OCR',
    subtitle: 'Tekst z ekranu',
    icon: <ScanText className="w-5 h-5" />,
    angleDeg: 30,
    accentColor: '#38BDF8',
    status: 'READY',
    description: 'Wycinek ekranu (Snipping Tool) i odczyt tekstu za pomocą Gemini Vision OCR.',
    versionStage: 'v0.4 (Zrealizowane)',
  },
  {
    id: 'clipboard',
    title: 'SCHOWEK',
    subtitle: 'Historia & Notes',
    icon: <ClipboardList className="w-5 h-5" />,
    angleDeg: 90,
    accentColor: '#10B981',
    status: 'READY',
    description: 'Lokalna historia schowka SQLite z zabezpieczeniem Self-Change Suppression i wyszukiwarką.',
    versionStage: 'v0.6 (Zrealizowane)',
  },
  {
    id: 'notes',
    title: 'NOTATKI',
    subtitle: 'Szybki notes',
    icon: <StickyNote className="w-5 h-5" />,
    angleDeg: 150,
    accentColor: '#F59E0B',
    status: 'READY',
    description: 'Podręczny notes z przypinaniem, edycją i natychmiastowym wklejaniem pod kursor.',
    versionStage: 'v0.6 (Zrealizowane)',
  },
  {
    id: 'actions',
    title: 'AKCJE',
    subtitle: 'Tekst / Windows',
    icon: <Zap className="w-5 h-5" />,
    angleDeg: 210,
    accentColor: '#818CF8',
    status: 'READY',
    description: 'Menu szybkich operacji tekstowych (Kopiuj, Wklej, Zastąp, Formatuj).',
    versionStage: 'v0.2 (Zrealizowane)',
  },
];

type AppView = 'hud' | 'clipboard' | 'processes' | 'ram' | 'settings' | 'speech-overlay' | 'speech-result' | 'snipping' | 'ocr-result' | 'translation';

interface MockClipItem {
  id: number;
  isNote: boolean;
  title?: string;
  text: string;
  sourceApp?: string;
  timeStr: string;
  pinned: boolean;
}

export default function App() {
  const [currentView, setCurrentView] = useState<AppView>('hud');
  const [selectedModule, setSelectedModule] = useState<ModuleConfig>(MODULES[0]); // Microphone by default
  const [hoveredModule, setHoveredModule] = useState<string | null>(null);

  // Speech state simulation
  const [speechText, setSpeechText] = useState(
    'Dzień dobry, proszę przygotować raport z testów modułu Speech-to-Text dla wersji v0.5 MyszkaHUD.'
  );
  const [recordingSeconds, setRecordingSeconds] = useState(3);

  // OCR state simulation
  const [extractedText, setExtractedText] = useState(
    'const ocrService = new OCRService({\n  provider: "gemini-3.7-flash",\n  fallback: "gemini-3.6-flash"\n});'
  );
  const [translatedText, setTranslatedText] = useState(
    'stała uslugaOCR = nowa UslugaOCR({\n  dostawca: "gemini-3.7-flash",\n  zapasowy: "gemini-3.6-flash"\n});'
  );

  // Drag snipping simulation
  const [isSnipping, setIsSnipping] = useState(false);
  const [snipRect, setSnipRect] = useState<{ x: number; y: number; w: number; h: number } | null>({
    x: 90,
    y: 80,
    w: 260,
    h: 120,
  });

  const radius = 150;
  const centerX = 220;
  const centerY = 220;

  // Clipboard & Notes state simulation
  const [clipboardItems, setClipboardItems] = useState<MockClipItem[]>([
    {
      id: 1,
      isNote: true,
      title: 'Klucze API i Konfiguracja',
      text: 'GEMINI_API_KEY=AIzaSy...\nMODEL=gemini-3.7-flash\nDB_PATH=%LOCALAPPDATA%/KursorAssist/myszkahud.db',
      timeStr: 'dzisiaj 14:15',
      pinned: true,
    },
    {
      id: 2,
      isNote: false,
      text: 'PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"',
      sourceApp: 'Code.exe',
      timeStr: '10 min temu',
      pinned: true,
    },
    {
      id: 3,
      isNote: false,
      text: 'from myszkahud.services.clipboard.monitor import ClipboardMonitor',
      sourceApp: 'WindowsTerminal.exe',
      timeStr: '25 min temu',
      pinned: false,
    },
    {
      id: 4,
      isNote: true,
      title: 'TODO: Release v0.6',
      text: '1. Testy SQLite (102/102 zaliczone)\n2. Monitor zdarzeniowy QClipboard\n3. Self-change write guard',
      timeStr: 'wczoraj',
      pinned: false,
    },
    {
      id: 5,
      isNote: false,
      text: 'https://ai.google.dev/gemini-api/docs/rate-limits',
      sourceApp: 'chrome.exe',
      timeStr: '2 dni temu',
      pinned: false,
    },
  ]);

  const [clipFilter, setClipFilter] = useState<'all' | 'pinned' | 'clip' | 'notes'>('all');
  const [clipSearch, setClipSearch] = useState('');
  const [isClipPaused, setIsClipPaused] = useState(false);
  const [editingNote, setEditingNote] = useState<{ id?: number; title: string; content: string; pinned: boolean } | null>(null);

  // Process Manager state simulation
  const [processItems, setProcessItems] = useState([
    { pid: 1000, name: 'Code.exe', title: 'MyszkaHUD - Visual Studio Code', ramMb: 450.2, cpu: 2.5, isProtected: false },
    { pid: 1001, name: 'chrome.exe', title: 'Google AI Studio - Google Chrome', ramMb: 820.5, cpu: 4.8, isProtected: false },
    { pid: 1002, name: 'python.exe', title: 'MyszkaHUD (Runtime)', ramMb: 92.4, cpu: 0.8, isProtected: true, isCurrent: true },
    { pid: 100, name: 'explorer.exe', title: 'Eksplorator Windows', ramMb: 245.0, cpu: 0.2, isProtected: true },
    { pid: 4, name: 'System', title: '', ramMb: 110.0, cpu: 0.1, isProtected: true },
    { pid: 1040, name: 'spotify.exe', title: 'Spotify Free', ramMb: 310.8, cpu: 1.2, isProtected: false },
  ]);
  const [procFilterOnlyWindows, setProcFilterOnlyWindows] = useState(false);
  const [procSearch, setProcSearch] = useState('');
  const [settingsCategory, setSettingsCategory] = useState<number>(0);
  const [isTrayMenuOpen, setIsTrayMenuOpen] = useState(false);
  const [isAutostartEnabled, setIsAutostartEnabled] = useState(false);

  const handleModuleClick = (mod: ModuleConfig) => {
    setSelectedModule(mod);
    if (mod.id === 'speech') {
      setCurrentView('speech-overlay');
    } else if (mod.id === 'ocr') {
      setCurrentView('snipping');
    } else if (mod.id === 'translate') {
      setCurrentView('translation');
    } else if (mod.id === 'clipboard' || mod.id === 'notes') {
      setCurrentView('clipboard');
    }
  };

  const handleTogglePin = (id: number) => {
    setClipboardItems((prev) =>
      prev.map((it) => (it.id === id ? { ...it, pinned: !it.pinned } : it))
    );
  };

  const handleDeleteItem = (id: number) => {
    setClipboardItems((prev) => prev.filter((it) => it.id !== id));
  };

  const handleSaveNote = () => {
    if (!editingNote || !editingNote.title.trim()) return;
    if (editingNote.id) {
      setClipboardItems((prev) =>
        prev.map((it) =>
          it.id === editingNote.id
            ? { ...it, title: editingNote.title, text: editingNote.content, pinned: editingNote.pinned }
            : it
        )
      );
    } else {
      const newId = Date.now();
      setClipboardItems((prev) => [
        {
          id: newId,
          isNote: true,
          title: editingNote.title,
          text: editingNote.content,
          timeStr: 'przed chwilą',
          pinned: editingNote.pinned,
        },
        ...prev,
      ]);
    }
    setEditingNote(null);
  };

  const filteredItems = clipboardItems.filter((it) => {
    if (clipFilter === 'pinned' && !it.pinned) return false;
    if (clipFilter === 'clip' && it.isNote) return false;
    if (clipFilter === 'notes' && !it.isNote) return false;
    if (clipSearch.trim()) {
      const q = clipSearch.toLowerCase();
      const matchText = it.text.toLowerCase().includes(q);
      const matchTitle = it.title?.toLowerCase().includes(q);
      const matchApp = it.sourceApp?.toLowerCase().includes(q);
      if (!matchText && !matchTitle && !matchApp) return false;
    }
    return true;
  });

  const handleSnipComplete = () => {
    setIsSnipping(false);
    setCurrentView('ocr-result');
  };

  const handleFinishRecording = () => {
    setCurrentView('speech-result');
  };

  return (
    <div className="min-h-screen bg-[#070a13] text-slate-100 flex flex-col items-center p-6 select-none font-sans">
      {/* Header */}
      <header className="w-full max-w-5xl flex items-center justify-between pb-6 mb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 font-black shadow-[0_0_15px_rgba(37,99,235,0.3)]">
            M
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-100 tracking-wide">MyszkaHUD</h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 font-semibold">
                v0.14 (Walidacja, Packaging EXE & Stability)
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Windows 10 x64 Desktop Radial Utility & AI Assistant (PySide6)
            </p>
          </div>
        </div>

        {/* Windows System Tray Simulator Button */}
        <div className="relative">
          <button
            id="btn-tray-icon-simulator"
            onClick={() => setIsTrayMenuOpen(!isTrayMenuOpen)}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-sky-500/40 rounded-xl text-xs font-semibold text-sky-400 shadow-md transition-all"
            title="Kliknij, aby otworzyć menu zasobnika systemowego Windows"
          >
            <div className="w-2.5 h-2.5 rounded-full bg-sky-400 animate-pulse" />
            Tray Icon (v0.10)
          </button>

          {/* Tray Context Menu Popover */}
          {isTrayMenuOpen && (
            <div className="absolute right-0 top-10 w-64 bg-[#030712] border border-sky-500/60 rounded-xl shadow-2xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150 text-xs">
              <div className="px-3 py-1.5 text-[10px] font-bold text-sky-400 border-b border-slate-800 flex items-center justify-between">
                <span>MyszkaHUD v0.10</span>
                <span className="text-slate-500 font-mono">Tray Menu</span>
              </div>
              <div className="py-1 space-y-0.5">
                <button
                  onClick={() => {
                    setCurrentView('hud');
                    setIsTrayMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-slate-200 hover:bg-sky-600 hover:text-white rounded-lg flex items-center justify-between"
                >
                  <span>Otwórz MyszkaHUD</span>
                  <span className="text-[10px] text-slate-500 font-mono">Alt+Q</span>
                </button>
                <button
                  onClick={() => {
                    setCurrentView('clipboard');
                    setIsTrayMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-slate-200 hover:bg-sky-600 hover:text-white rounded-lg flex items-center justify-between"
                >
                  <span>Historia Schowka</span>
                  <span className="text-[10px] text-slate-500 font-mono">Alt+V</span>
                </button>
                <button
                  onClick={() => {
                    setCurrentView('processes');
                    setIsTrayMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-slate-200 hover:bg-sky-600 hover:text-white rounded-lg"
                >
                  Menedżer Procesów
                </button>
                <button
                  onClick={() => {
                    setCurrentView('ram');
                    setIsTrayMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-slate-200 hover:bg-sky-600 hover:text-white rounded-lg"
                >
                  Monitor RAM & Zwalnianie
                </button>
                <div className="my-1 border-t border-slate-800" />
                <button
                  onClick={() => {
                    setCurrentView('settings');
                    setIsTrayMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-slate-200 hover:bg-sky-600 hover:text-white rounded-lg"
                >
                  Centrum Ustawień...
                </button>
                <button
                  onClick={() => setIsAutostartEnabled(!isAutostartEnabled)}
                  className="w-full text-left px-3 py-1.5 text-slate-200 hover:bg-sky-600 hover:text-white rounded-lg flex items-center justify-between"
                >
                  <span>Uruchamiaj z Windows</span>
                  <span className="text-[10px] font-bold text-sky-400 font-mono">
                    {isAutostartEnabled ? '✓ WŁ' : 'WYŁ'}
                  </span>
                </button>
                <div className="my-1 border-t border-slate-800" />
                <button
                  onClick={() => {
                    alert('Symulacja zamknięcia aplikacji MyszkaHUD.');
                    setIsTrayMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-red-400 hover:bg-red-950/80 hover:text-red-300 rounded-lg"
                >
                  Zakończ MyszkaHUD
                </button>
              </div>
            </div>
          )}
        </div>

        {/* View Switcher Tabs (Preview Simulation Only) */}
        <div className="flex items-center gap-1.5 bg-slate-900/90 p-1 rounded-xl border border-slate-800 flex-wrap">
          <button
            id="tab-hud-preview"
            onClick={() => setCurrentView('hud')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all ${
              currentView === 'hud'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Radial HUD
          </button>
          <button
            id="tab-clipboard-preview"
            onClick={() => setCurrentView('clipboard')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all flex items-center gap-1 ${
              currentView === 'clipboard'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-400 hover:text-emerald-300'
            }`}
          >
            <ClipboardList className="w-3.5 h-3.5" />
            Schowek & Notes (v0.6)
          </button>
          <button
            id="tab-processes-preview"
            onClick={() => setCurrentView('processes')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all flex items-center gap-1 ${
              currentView === 'processes'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-sky-400 hover:text-sky-300'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Procesy (v0.7)
          </button>
          <button
            id="tab-ram-preview"
            onClick={() => setCurrentView('ram')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all flex items-center gap-1 ${
              currentView === 'ram'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-indigo-400 hover:text-indigo-300'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            RAM Monitor (v0.8)
          </button>
          <button
            id="tab-settings-preview"
            onClick={() => setCurrentView('settings')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all flex items-center gap-1 ${
              currentView === 'settings'
                ? 'bg-slate-700 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
            Ustawienia (v0.9)
          </button>
          <button
            id="tab-speech-overlay-preview"
            onClick={() => setCurrentView('speech-overlay')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all ${
              currentView === 'speech-overlay'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Speech Overlay
          </button>
          <button
            id="tab-speech-result-preview"
            onClick={() => setCurrentView('speech-result')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all ${
              currentView === 'speech-result'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Speech Result Window
          </button>
          <button
            id="tab-snipping-preview"
            onClick={() => setCurrentView('snipping')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all ${
              currentView === 'snipping'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Snipping Overlay
          </button>
          <button
            id="tab-ocr-result-preview"
            onClick={() => setCurrentView('ocr-result')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all ${
              currentView === 'ocr-result'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            OCR Result Window
          </button>
          <button
            id="tab-translation-preview"
            onClick={() => setCurrentView('translation')}
            className={`px-3 py-1 text-xs rounded-lg font-medium transition-all ${
              currentView === 'translation'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Translation Window
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Column: Active Window Simulation */}
        <div className="lg:col-span-7 flex flex-col items-center justify-center min-h-[460px] p-4 bg-slate-950/40 rounded-2xl border border-slate-900">
          
          {/* VIEW 1: RADIAL HUD */}
          {currentView === 'hud' && (
            <div className="relative w-[440px] h-[440px] flex items-center justify-center animate-in fade-in duration-200">
              <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 440 440">
                {MODULES.map((m) => {
                  const rad = (m.angleDeg * Math.PI) / 180;
                  const x1 = centerX + 45 * Math.cos(rad);
                  const y1 = centerY + 45 * Math.sin(rad);
                  const x2 = centerX + (radius - 35) * Math.cos(rad);
                  const y2 = centerY + (radius - 35) * Math.sin(rad);
                  const isHovered = hoveredModule === m.id;
                  const isSelected = selectedModule.id === m.id;

                  return (
                    <line
                      key={`line-${m.id}`}
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke={isSelected || isHovered ? m.accentColor : 'rgba(51, 65, 85, 0.4)'}
                      strokeWidth={isSelected || isHovered ? 1.5 : 1}
                      strokeDasharray={isSelected ? undefined : '2,2'}
                    />
                  );
                })}

                <circle
                  cx={centerX}
                  cy={centerY}
                  r={radius}
                  fill="none"
                  stroke="rgba(56, 189, 248, 0.2)"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />

                <circle
                  cx={centerX}
                  cy={centerY}
                  r={radius + 40}
                  fill="none"
                  stroke="rgba(30, 41, 59, 0.4)"
                  strokeWidth="1"
                />
              </svg>

              {/* Center Card */}
              <div
                className="absolute z-10 w-[140px] h-[78px] rounded-[14px] bg-[rgba(13,20,36,0.95)] border border-[#2563EB] shadow-[0_0_25px_rgba(37,99,235,0.35)] flex flex-col items-center justify-center p-2 cursor-pointer transition-all hover:scale-105"
                onClick={() => handleModuleClick(MODULES[2])}
              >
                <span className="text-[13px] font-extrabold text-[#38BDF8] tracking-wider">
                  MyszkaHUD
                </span>
                <div className="flex items-center gap-1.5 mt-1 text-[9px] font-bold text-slate-400">
                  <span>ALT + Q</span>
                  <span className="text-slate-600">•</span>
                  <span className="text-[#10B981]">GOTOWY</span>
                </div>
              </div>

              {/* 6 Radial Module Cards */}
              {MODULES.map((m) => {
                const rad = (m.angleDeg * Math.PI) / 180;
                const posX = centerX + radius * Math.cos(rad) - 54;
                const posY = centerY + radius * Math.sin(rad) - 36;
                const isSelected = selectedModule.id === m.id;
                const isHovered = hoveredModule === m.id;

                return (
                  <button
                    key={m.id}
                    id={`btn-hud-${m.id}`}
                    onClick={() => handleModuleClick(m)}
                    onMouseEnter={() => setHoveredModule(m.id)}
                    onMouseLeave={() => setHoveredModule(null)}
                    style={{
                      left: `${posX}px`,
                      top: `${posY}px`,
                      borderColor: isSelected || isHovered ? m.accentColor : 'rgba(51, 65, 85, 0.65)',
                      boxShadow: isSelected || isHovered ? `0 0 16px ${m.accentColor}33` : '0 4px 12px rgba(0,0,0,0.5)',
                    }}
                    className={`absolute w-[108px] h-[72px] rounded-[12px] p-1.5 flex flex-col items-center justify-center text-center transition-all duration-150 cursor-pointer ${
                      isSelected
                        ? 'bg-[rgba(30,41,59,0.98)] scale-105 border-[1.5px]'
                        : isHovered
                        ? 'bg-[rgba(24,34,50,0.98)] scale-102 border-[1.5px]'
                        : 'bg-[rgba(15,23,42,0.96)] border'
                    }`}
                  >
                    <div style={{ color: m.accentColor }} className="mb-0.5">
                      {m.icon}
                    </div>
                    <span className="text-[11px] font-bold text-slate-100 tracking-wide leading-tight">
                      {m.title}
                    </span>
                    <span className="text-[9px] text-slate-400 leading-tight">
                      {m.subtitle}
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {/* VIEW: SMART CLIPBOARD & NOTES (v0.6) */}
          {currentView === 'clipboard' && (
            <div className="w-full max-w-[500px] h-[480px] rounded-[16px] bg-[rgba(10,15,29,0.98)] border-[1.5px] border-[#10B981] p-4 shadow-[0_0_35px_rgba(0,0,0,0.85)] flex flex-col justify-between animate-in fade-in duration-200">
              {/* Header */}
              <div>
                <div className="flex items-center justify-between pb-2.5 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                      <ClipboardList className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-black tracking-wider text-emerald-400">
                      INTELIGENTNY SCHOWEK & NOTES
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      id="btn-clip-pause"
                      onClick={() => setIsClipPaused(!isClipPaused)}
                      className={`px-2 py-0.5 text-[10px] font-bold rounded flex items-center gap-1 border transition-colors ${
                        isClipPaused
                          ? 'bg-amber-950/80 text-amber-300 border-amber-800'
                          : 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                      }`}
                    >
                      {isClipPaused ? <Pause className="w-2.5 h-2.5" /> : <Play className="w-2.5 h-2.5" />}
                      {isClipPaused ? 'Pauza' : 'Aktywny'}
                    </button>
                    <button
                      id="btn-clip-add-note"
                      onClick={() => setEditingNote({ title: '', content: '', pinned: false })}
                      className="px-2.5 py-0.5 text-[10px] font-bold bg-amber-600 hover:bg-amber-500 text-slate-950 rounded flex items-center gap-1 shadow-sm"
                    >
                      <Plus className="w-3 h-3" />
                      Nowa notatka
                    </button>
                  </div>
                </div>

                {/* Search Bar & Filter Tabs */}
                <div className="mt-2.5 space-y-2">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-slate-500" />
                    <input
                      id="input-clip-search"
                      type="text"
                      placeholder="Szukaj w historii i notatkach..."
                      value={clipSearch}
                      onChange={(e) => setClipSearch(e.target.value)}
                      className="w-full bg-[#0E1626] border border-slate-700/80 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
                    />
                  </div>

                  <div className="flex items-center gap-1 text-[10px] font-semibold">
                    {(['all', 'pinned', 'clip', 'notes'] as const).map((f) => (
                      <button
                        key={f}
                        onClick={() => setClipFilter(f)}
                        className={`px-2.5 py-0.5 rounded transition-all ${
                          clipFilter === f
                            ? 'bg-emerald-600 text-white shadow-sm font-bold'
                            : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                        }`}
                      >
                        {f === 'all' && 'Wszystkie'}
                        {f === 'pinned' && 'Przypięte 📌'}
                        {f === 'clip' && 'Schowek'}
                        {f === 'notes' && 'Notatki 📝'}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Cards List */}
              <div className="flex-1 my-2 overflow-y-auto space-y-2 pr-1 max-h-[260px] custom-scrollbar">
                {filteredItems.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs py-8">
                    Brak wpisów pasujących do kryteriów.
                  </div>
                ) : (
                  filteredItems.map((item) => (
                    <div
                      key={item.id}
                      className={`p-2.5 rounded-xl border transition-all ${
                        item.isNote
                          ? 'bg-[#181d2d] border-amber-500/40 hover:border-amber-400'
                          : 'bg-[#0E1626] border-slate-800 hover:border-emerald-500/50'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                        <div className="flex items-center gap-1.5 font-semibold">
                          {item.isNote ? (
                            <span className="text-amber-400 flex items-center gap-1">
                              <StickyNote className="w-3 h-3" />
                              {item.title || 'Notatka'}
                            </span>
                          ) : (
                            <span className="text-emerald-400 flex items-center gap-1">
                              <ClipboardList className="w-3 h-3" />
                              {item.sourceApp || 'Schowek'}
                            </span>
                          )}
                          <span className="text-slate-600">•</span>
                          <span className="text-slate-500">{item.timeStr}</span>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleTogglePin(item.id)}
                            title="Przypnij"
                            className={`p-1 rounded hover:bg-slate-800 ${
                              item.pinned ? 'text-amber-400' : 'text-slate-500'
                            }`}
                          >
                            <Pin className="w-3 h-3" />
                          </button>
                          {item.isNote && (
                            <button
                              onClick={() =>
                                setEditingNote({
                                  id: item.id,
                                  title: item.title || '',
                                  content: item.text,
                                  pinned: item.pinned,
                                })
                              }
                              title="Edytuj notatkę"
                              className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                            >
                              <Edit3 className="w-3 h-3" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteItem(item.id)}
                            title="Usuń"
                            className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>

                      <p className="text-xs text-slate-200 font-mono whitespace-pre-wrap line-clamp-2 bg-black/30 p-1.5 rounded border border-slate-800/60">
                        {item.text}
                      </p>

                      <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-800/60">
                        <span className="text-[9px] text-slate-500 font-mono">{item.text.length} zn.</span>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => alert(`Skopiowano: ${item.text.substring(0, 30)}...`)}
                            className="px-2 py-0.5 text-[9px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded flex items-center gap-1"
                          >
                            <Copy className="w-2.5 h-2.5" />
                            Kopiuj
                          </button>
                          <button
                            onClick={() => alert(`Wklejono pod kursor: ${item.text.substring(0, 30)}...`)}
                            className="px-2 py-0.5 text-[9px] font-bold bg-emerald-600 hover:bg-emerald-500 text-white rounded flex items-center gap-1"
                          >
                            Wklej (Enter)
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Note Dialog Modal (Simulated) */}
              {editingNote && (
                <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
                  <div className="w-full max-w-sm rounded-xl bg-[#0A0F1D] border border-amber-500/80 p-4 shadow-2xl space-y-3">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                      <span className="text-xs font-bold text-amber-400">
                        {editingNote.id ? 'EDYTUJ NOTATKĘ' : 'NOWA PODRĘCZNA NOTATKA'}
                      </span>
                      <button
                        onClick={() => setEditingNote(null)}
                        className="text-slate-400 hover:text-white"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    <input
                      type="text"
                      placeholder="Tytuł notatki..."
                      value={editingNote.title}
                      onChange={(e) => setEditingNote({ ...editingNote, title: e.target.value })}
                      className="w-full bg-[#0E1626] border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white focus:border-amber-500 focus:outline-none"
                    />

                    <textarea
                      placeholder="Treść notatki..."
                      rows={4}
                      value={editingNote.content}
                      onChange={(e) => setEditingNote({ ...editingNote, content: e.target.value })}
                      className="w-full bg-[#0E1626] border border-slate-700 rounded-lg p-2 text-xs text-slate-100 font-mono focus:border-amber-500 focus:outline-none resize-none"
                    />

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                      <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={editingNote.pinned}
                          onChange={(e) => setEditingNote({ ...editingNote, pinned: e.target.checked })}
                          className="rounded text-amber-500"
                        />
                        Przypnij na górze
                      </label>

                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => setEditingNote(null)}
                          className="px-2.5 py-1 text-xs text-slate-400 hover:text-white"
                        >
                          Anuluj
                        </button>
                        <button
                          onClick={handleSaveNote}
                          className="px-3 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded shadow"
                        >
                          Zapisz
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Bottom Footer bar */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[9px] text-slate-500 font-mono">
                <span>SQLite DB: %LOCALAPPDATA%/KursorAssist/myszkahud.db</span>
                <span>Esc: Zamknij | Pod kursor: Automatycznie</span>
              </div>
            </div>
          )}

          {/* VIEW: PROCESS MANAGER (v0.7) */}
          {currentView === 'processes' && (
            <div className="w-full max-w-[560px] h-[480px] rounded-[16px] bg-[rgba(3,7,18,0.98)] border-[1.5px] border-[#0284C7] p-4 shadow-[0_0_35px_rgba(0,0,0,0.85)] flex flex-col justify-between animate-in fade-in duration-200">
              {/* Header */}
              <div>
                <div className="flex items-center justify-between pb-2.5 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-sky-500/20 text-sky-400 flex items-center justify-center">
                      <Activity className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-black tracking-wider text-sky-400">
                      AKTYWNE APLIKACJE & PROCESY (v0.7)
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      id="btn-proc-refresh"
                      onClick={() => alert('Odświeżono listę procesów.')}
                      className="px-2.5 py-0.5 text-[10px] font-bold bg-sky-950/80 text-sky-300 border border-sky-800 hover:bg-sky-900 rounded flex items-center gap-1 shadow-sm"
                    >
                      Odśwież
                    </button>
                    <button
                      onClick={() => setCurrentView('hud')}
                      className="text-slate-400 hover:text-white p-1"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Search Bar & Filter Tabs */}
                <div className="mt-2.5 space-y-2">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-slate-500" />
                    <input
                      id="input-proc-search"
                      type="text"
                      placeholder="Szukaj po nazwie, PID lub oknie..."
                      value={procSearch}
                      onChange={(e) => setProcSearch(e.target.value)}
                      className="w-full bg-[#0B1120] border border-slate-800 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
                    />
                  </div>

                  <div className="flex items-center gap-1 text-[10px] font-semibold">
                    <button
                      onClick={() => setProcFilterOnlyWindows(false)}
                      className={`px-3 py-1 rounded transition-all ${
                        !procFilterOnlyWindows
                          ? 'bg-sky-600 text-white shadow-sm font-bold'
                          : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                      }`}
                    >
                      Wszystkie procesy
                    </button>
                    <button
                      onClick={() => setProcFilterOnlyWindows(true)}
                      className={`px-3 py-1 rounded transition-all ${
                        procFilterOnlyWindows
                          ? 'bg-sky-600 text-white shadow-sm font-bold'
                          : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                      }`}
                    >
                      Tylko z oknami
                    </button>
                  </div>
                </div>
              </div>

              {/* Process Cards List */}
              <div className="flex-1 my-2 overflow-y-auto space-y-1.5 pr-1 max-h-[260px] custom-scrollbar">
                {processItems
                  .filter((p) => {
                    if (procFilterOnlyWindows && !p.title) return false;
                    if (procSearch) {
                      const q = procSearch.toLowerCase();
                      return (
                        p.name.toLowerCase().includes(q) ||
                        p.title.toLowerCase().includes(q) ||
                        p.pid.toString().includes(q)
                      );
                    }
                    return true;
                  })
                  .map((p) => (
                    <div
                      key={p.pid}
                      className="p-2.5 rounded-lg border border-slate-800 bg-[#0B1120] hover:border-sky-500/50 flex items-center justify-between transition-all"
                    >
                      <div className="space-y-0.5 max-w-[240px]">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold text-slate-100 truncate">
                            {p.title || p.name}
                          </span>
                          {p.isProtected && (
                            <span className="px-1.5 py-0.2 bg-slate-800 text-slate-400 text-[8px] font-bold rounded border border-slate-700">
                              {p.isCurrent ? 'MYSZKAHUD' : 'CHRONIONY'}
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          PID: {p.pid} • {p.name}
                        </div>
                      </div>

                      <div className="text-right font-mono text-[10px] pr-2">
                        <div className="text-sky-400 font-bold">{p.ramMb} MB</div>
                        <div className="text-slate-500">CPU {p.cpu}%</div>
                      </div>

                      <div className="flex items-center gap-1">
                        {p.title && (
                          <button
                            onClick={() => alert(`Aktywowano okno: ${p.title}`)}
                            className="px-2 py-0.5 text-[9px] font-bold bg-slate-900 border border-sky-600/60 text-sky-300 hover:bg-sky-950 rounded"
                          >
                            Aktywuj
                          </button>
                        )}
                        {!p.isProtected && (
                          <>
                            <button
                              onClick={() => {
                                setProcessItems((prev) => prev.filter((x) => x.pid !== p.pid));
                              }}
                              className="px-2 py-0.5 text-[9px] bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700"
                            >
                              Zamknij
                            </button>
                            <button
                              onClick={() => {
                                if (confirm(`Czy na pewno wymusić zabicie procesu PID ${p.pid}?`)) {
                                  setProcessItems((prev) => prev.filter((x) => x.pid !== p.pid));
                                }
                              }}
                              className="px-2 py-0.5 text-[9px] font-bold bg-red-950/80 hover:bg-red-900 text-red-300 rounded border border-red-800"
                            >
                              Kill
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
              </div>

              {/* Bottom Footer bar */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[9px] text-slate-500 font-mono">
                <span>Widoczne procesy: {processItems.length} | Ochrona procesów systemowych: WŁĄCZONA</span>
                <span>Esc: Zamknij</span>
              </div>
            </div>
          )}

          {/* VIEW: RAM MONITOR & SAFE RELEASE (v0.8) */}
          {currentView === 'ram' && (
            <div className="w-full max-w-[500px] h-[450px] rounded-[16px] bg-[rgba(3,7,18,0.98)] border-[1.5px] border-[#6366F1] p-4 shadow-[0_0_35px_rgba(0,0,0,0.85)] flex flex-col justify-between animate-in fade-in duration-200">
              {/* Header */}
              <div>
                <div className="flex items-center justify-between pb-2.5 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
                      <Cpu className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-black tracking-wider text-indigo-400">
                      MONITOR PAMIĘCI RAM (v0.8)
                    </span>
                  </div>

                  <button
                    onClick={() => setCurrentView('hud')}
                    className="text-slate-400 hover:text-white p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Gauge Box */}
                <div className="mt-3 p-3 rounded-xl bg-[#0B1120] border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-100">Zużycie: 48.5%</span>
                    <span className="text-xs font-mono font-bold text-indigo-400">7.8 GB / 16.0 GB</span>
                  </div>
                  <div className="w-full h-3 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                    <div className="h-full bg-indigo-500 rounded-full transition-all duration-500" style={{ width: '48.5%' }} />
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>Dostępne: 8.2 GB</span>
                    <span>Plik stronicowania: 2.1 GB / 20.0 GB</span>
                  </div>
                </div>
              </div>

              {/* Top Processes */}
              <div className="flex-1 my-2 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                <div className="text-[10px] font-bold text-slate-400 mb-1">TOP PROCESY WG ZUŻYCIA RAM</div>
                {[
                  { name: 'chrome.exe', title: 'Google AI Studio', mb: 820.5 },
                  { name: 'Code.exe', title: 'Visual Studio Code', mb: 450.2 },
                  { name: 'spotify.exe', title: 'Spotify Free', mb: 310.8 },
                  { name: 'explorer.exe', title: 'Eksplorator Windows', mb: 245.0 },
                  { name: 'python.exe', title: 'MyszkaHUD (Runtime)', mb: 92.4 },
                ].map((p, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded-lg bg-[#0B1120] border border-slate-800/80 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-slate-500 font-mono text-[10px]">#{idx + 1}</span>
                      <span className="text-slate-200 font-semibold">{p.title || p.name}</span>
                    </div>
                    <span className="font-mono text-indigo-400 font-bold text-[11px]">{p.mb} MB</span>
                  </div>
                ))}
              </div>

              {/* Action Button & Footer */}
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="flex items-center gap-2">
                  <button
                    id="btn-release-ram"
                    onClick={() => alert('Zwolniono bezpiecznie: 284.5 MB (Working set trimming + Python GC). Wszystkie aplikacje pozostały otwarte.')}
                    className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg shadow-md transition-all flex items-center justify-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Zwolnij pamięć (Bezpieczne)
                  </button>
                </div>
                <div className="flex items-center justify-between text-[9px] text-slate-500 font-mono">
                  <span>Bezpieczeństwo: Bez zamykania aplikacji | Realny pomiar</span>
                  <span>Esc: Zamknij</span>
                </div>
              </div>
            </div>
          )}

          {/* VIEW: SETTINGS CENTER (v0.9) */}
          {currentView === 'settings' && (
            <div className="w-full max-w-[620px] h-[480px] rounded-[16px] bg-[rgba(3,7,18,0.98)] border-[1.5px] border-[#38BDF8] p-4 shadow-[0_0_35px_rgba(0,0,0,0.85)] flex flex-col justify-between animate-in fade-in duration-200">
              {/* Header */}
              <div>
                <div className="flex items-center justify-between pb-2.5 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-sky-500/20 text-sky-400 flex items-center justify-center">
                      <Settings className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-black tracking-wider text-sky-400">
                      CENTRUM USTAWIEŃ (v0.9)
                    </span>
                  </div>

                  <button
                    onClick={() => setCurrentView('hud')}
                    className="text-slate-400 hover:text-white p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Main Content (Sidebar + Category content) */}
              <div className="flex-1 my-3 flex gap-3 overflow-hidden">
                {/* Categories sidebar */}
                <div className="w-[180px] space-y-1 overflow-y-auto pr-1 custom-scrollbar">
                  {[
                    'Skróty Klawiszowe',
                    'Wygląd & HUD',
                    'Mowa (STT)',
                    'OCR (Vision)',
                    'Schowek & Notes',
                    'System & Ochrona',
                    'Monitor RAM',
                  ].map((cat, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSettingsCategory(idx)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                        settingsCategory === idx
                          ? 'bg-sky-600 text-white font-bold shadow-sm'
                          : 'bg-[#0B1120] text-slate-400 hover:text-slate-200 border border-slate-800'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {/* Form fields */}
                <div className="flex-1 bg-[#0B1120] border border-slate-800 rounded-xl p-3 overflow-y-auto custom-scrollbar text-xs space-y-3">
                  {settingsCategory === 0 && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-slate-400 mb-1 font-semibold">Skrót wywołania HUD:</label>
                        <input
                          type="text"
                          defaultValue="Alt+Q"
                          className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-400 mb-1 font-semibold">Skrót otwarcia Schowka:</label>
                        <input
                          type="text"
                          defaultValue="Alt+V"
                          className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200"
                        />
                      </div>
                    </div>
                  )}

                  {settingsCategory === 1 && (
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-slate-300">
                        <input type="checkbox" defaultChecked className="rounded accent-sky-500" />
                        Włącz płynne animacje HUD (motion)
                      </label>
                      <label className="flex items-center gap-2 text-slate-300">
                        <input type="checkbox" defaultChecked className="rounded accent-sky-500" />
                        Automatycznie zamykaj HUD po wybraniu akcji
                      </label>
                    </div>
                  )}

                  {settingsCategory === 2 && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-slate-400 mb-1 font-semibold">Język rozpoznawania:</label>
                        <select className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200">
                          <option value="pl-PL">Polski (pl-PL)</option>
                          <option value="en-US">English (en-US)</option>
                        </select>
                      </div>
                      <label className="flex items-center gap-2 text-slate-300">
                        <input type="checkbox" defaultChecked className="rounded accent-sky-500" />
                        Automatycznie wklejaj transkrypcję pod kursor
                      </label>
                    </div>
                  )}

                  {settingsCategory === 3 && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-slate-400 mb-1 font-semibold">Silnik OCR:</label>
                        <select className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200">
                          <option value="gemini_vision">Gemini 2.5 Flash Vision (Chmura/Wysoka precyzja)</option>
                          <option value="windows_ocr">Windows Media OCR (Lokalny/Offline)</option>
                        </select>
                      </div>
                      <label className="flex items-center gap-2 text-slate-300">
                        <input type="checkbox" defaultChecked className="rounded accent-sky-500" />
                        Automatycznie kopiuj odczytany tekst do schowka
                      </label>
                    </div>
                  )}

                  {settingsCategory === 4 && (
                    <div className="space-y-3">
                      <label className="flex items-center gap-2 text-slate-300">
                        <input type="checkbox" defaultChecked className="rounded accent-sky-500" />
                        Włącz rejestrowanie historii schowka
                      </label>
                      <div>
                        <label className="block text-slate-400 mb-1 font-semibold">Maksymalna liczba wpisów w historii:</label>
                        <input
                          type="number"
                          defaultValue={200}
                          className="w-24 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200"
                        />
                      </div>
                    </div>
                  )}

                  {settingsCategory === 5 && (
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 text-slate-300">
                        <input type="checkbox" className="rounded accent-sky-500" />
                        Uruchamiaj MyszkaHUD przy starcie Windows (Autostart)
                      </label>
                      <label className="flex items-center gap-2 text-slate-300">
                        <input type="checkbox" defaultChecked className="rounded accent-sky-500" />
                        Chroń krytyczne procesy systemowe (Zabezpieczenie przed zabiciem)
                      </label>
                    </div>
                  )}

                  {settingsCategory === 6 && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-slate-400 mb-1 font-semibold">Interwał odświeżania RAM (ms):</label>
                        <input
                          type="number"
                          defaultValue={2000}
                          className="w-24 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <button
                  onClick={() => alert('Przywrócono wartości domyślne ustawień.')}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700"
                >
                  Przywróć domyślne
                </button>
                <button
                  id="btn-save-settings"
                  onClick={() => alert('Zapisano konfigurację w %LOCALAPPDATA%/KursorAssist/settings.json!')}
                  className="px-4 py-1.5 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-lg shadow-sm"
                >
                  Zapisz ustawienia
                </button>
              </div>
            </div>
          )}

          {/* VIEW 2: SNIPPING OVERLAY SIMULATION */}
          {currentView === 'snipping' && (
            <div className="relative w-full max-w-md h-[340px] rounded-xl overflow-hidden border border-slate-700 bg-slate-900 shadow-2xl flex flex-col">
              {/* Simulated desktop app background */}
              <div className="p-4 bg-[#1e1e1e] text-slate-300 font-mono text-xs h-full relative">
                <div className="text-blue-400">import <span className="text-white">{"{ OCRService }"}</span> from <span className="text-emerald-300">"myszkahud"</span>;</div>
                <div className="mt-2 text-slate-400">// Visual snippet sample</div>
                <div className="text-purple-400">const <span className="text-yellow-200">result</span> = await ocr.extract();</div>
                <div className="text-slate-300">console.log(result.text);</div>

                {/* Dark snipping dim layer */}
                <div className="absolute inset-0 bg-black/60 cursor-crosshair flex flex-col justify-between p-3">
                  <div className="flex items-center justify-between text-[11px] text-slate-300 bg-slate-900/80 px-2 py-1 rounded border border-slate-700 self-start">
                    <MousePointer className="w-3.5 h-3.5 text-blue-400 mr-1.5" />
                    Zaznacz obszar LPM (lub naciśnij Esc by anulować)
                  </div>

                  {/* Cutout selection rect */}
                  <div
                    style={{
                      left: `${snipRect?.x}px`,
                      top: `${snipRect?.y}px`,
                      width: `${snipRect?.w}px`,
                      height: `${snipRect?.h}px`,
                    }}
                    className="absolute border-2 border-[#38BDF8] bg-transparent shadow-[0_0_0_9999px_rgba(0,0,0,0.55)] flex items-end justify-end p-1 pointer-events-none"
                  >
                    <span className="text-[9px] bg-sky-950/90 text-sky-300 px-1 rounded font-mono border border-sky-700">
                      {snipRect?.w} x {snipRect?.h} px
                    </span>
                  </div>

                  <div className="self-center">
                    <button
                      id="btn-simulate-snip-capture"
                      onClick={handleSnipComplete}
                      className="px-4 py-1.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs rounded-lg shadow-lg flex items-center gap-1.5 transition-transform active:scale-95"
                    >
                      <ScanText className="w-4 h-4" />
                      Wykonaj zrzut zaznaczenia → OCR
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* VIEW 3: OCR RESULT WINDOW */}
          {currentView === 'ocr-result' && (
            <div className="w-[440px] rounded-[14px] bg-[rgba(10,15,29,0.96)] border-[1.5px] border-[#38BDF8] p-4 shadow-[0_0_30px_rgba(0,0,0,0.8)] animate-in fade-in duration-200">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <ScanText className="w-4 h-4 text-[#38BDF8]" />
                  <span className="text-[11px] font-extrabold text-[#38BDF8] tracking-wider">
                    ROZPOZNANY TEKST (OCR)
                  </span>
                </div>
                <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  Rozpoznano pomyślnie
                </span>
              </div>

              {/* Editable Text Area */}
              <textarea
                id="txt-ocr-result-preview"
                value={extractedText}
                onChange={(e) => setExtractedText(e.target.value)}
                className="w-full h-32 mt-3 bg-[#0E1626] border border-slate-700/80 rounded-lg p-2.5 text-xs text-slate-100 font-mono focus:border-[#38BDF8] focus:outline-none resize-none"
              />

              {/* Action Buttons Row */}
              <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/80">
                <div className="flex items-center gap-1.5">
                  <button
                    id="btn-ocr-copy"
                    onClick={() => alert('Skopiowano do schowka')}
                    className="px-2.5 py-1 text-[10px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3 text-slate-400" />
                    Kopiuj
                  </button>
                  <button
                    id="btn-ocr-paste"
                    onClick={() => alert('Wklejono do okna docelowego')}
                    className="px-2.5 py-1 text-[10px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700"
                  >
                    Wklej
                  </button>
                  <button
                    id="btn-ocr-paste-enter"
                    onClick={() => alert('Wklejono z Enterem')}
                    className="px-2.5 py-1 text-[10px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 flex items-center gap-1"
                  >
                    <CornerDownLeft className="w-3 h-3 text-slate-400" />
                    + Enter
                  </button>
                  <button
                    id="btn-ocr-to-translate"
                    onClick={() => setCurrentView('translation')}
                    className="px-3 py-1 text-[10px] font-bold bg-[#2563EB] hover:bg-blue-600 text-white rounded flex items-center gap-1 shadow-sm"
                  >
                    <Globe className="w-3 h-3" />
                    Tłumacz
                  </button>
                </div>
                <span className="text-[9px] text-slate-500 font-mono">Esc: Zamknij</span>
              </div>
            </div>
          )}

          {/* VIEW 5: SPEECH RECORDING OVERLAY */}
          {currentView === 'speech-overlay' && (
            <div className="w-[360px] rounded-[12px] bg-[rgba(10,15,29,0.96)] border-[1.5px] border-[#0284C7] p-3.5 shadow-[0_0_25px_rgba(0,0,0,0.8)] animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                  </span>
                  <span className="text-xs font-bold text-slate-100 tracking-wide">
                    NAGRYWANIE GŁOSU...
                  </span>
                </div>
                <span className="text-xs font-mono font-bold text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800/60">
                  00:0{recordingSeconds}
                </span>
              </div>

              {/* Simulated waveform / audio level meter */}
              <div className="flex items-center justify-center gap-1 my-3.5 h-6">
                {[40, 75, 100, 60, 85, 45, 90, 65, 30, 80, 95, 50, 70].map((h, i) => (
                  <div
                    key={i}
                    style={{ height: `${h}%` }}
                    className="w-1 bg-sky-400/80 rounded-full transition-all duration-150 animate-pulse"
                  />
                ))}
              </div>

              {/* Controls */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
                <div className="flex items-center gap-2">
                  <button
                    id="btn-speech-stop"
                    onClick={handleFinishRecording}
                    className="px-3 py-1 bg-[#0284C7] hover:bg-sky-500 text-white text-xs font-bold rounded flex items-center gap-1 shadow-sm"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Zakończ (Enter)
                  </button>
                  <button
                    id="btn-speech-cancel"
                    onClick={() => setCurrentView('hud')}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded border border-slate-700"
                  >
                    Anuluj (Esc)
                  </button>
                </div>
                <span className="text-[9px] text-slate-500 font-mono">Max: 60s | 16kHz / 48kHz auto</span>
              </div>
            </div>
          )}

          {/* VIEW 6: SPEECH RESULT WINDOW */}
          {currentView === 'speech-result' && (
            <div className="w-[440px] rounded-[14px] bg-[rgba(10,15,29,0.96)] border-[1.5px] border-[#0284C7] p-4 shadow-[0_0_30px_rgba(0,0,0,0.8)] animate-in fade-in duration-200">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Mic className="w-4 h-4 text-[#0284C7]" />
                  <span className="text-[11px] font-extrabold text-[#0284C7] tracking-wider">
                    WYNIK TRANSKRYPCJI (STT)
                  </span>
                </div>
                <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  Gemini 3.5 Transcribe
                </span>
              </div>

              {/* Editable Transcription Area */}
              <textarea
                id="txt-speech-result-preview"
                value={speechText}
                onChange={(e) => setSpeechText(e.target.value)}
                className="w-full h-32 mt-3 bg-[#0E1626] border border-slate-700/80 rounded-lg p-2.5 text-xs text-slate-100 font-sans focus:border-[#0284C7] focus:outline-none resize-none leading-relaxed"
              />

              {/* Action Buttons Row */}
              <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/80">
                <div className="flex items-center gap-1.5">
                  <button
                    id="btn-speech-copy"
                    onClick={() => alert('Skopiowano transkrypcję')}
                    className="px-2.5 py-1 text-[10px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3 text-slate-400" />
                    Kopiuj
                  </button>
                  <button
                    id="btn-speech-paste"
                    onClick={() => alert('Wklejono transkrypcję')}
                    className="px-2.5 py-1 text-[10px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700"
                  >
                    Wklej
                  </button>
                  <button
                    id="btn-speech-paste-enter"
                    onClick={() => alert('Wklejono z Enterem')}
                    className="px-2.5 py-1 text-[10px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 flex items-center gap-1"
                  >
                    <CornerDownLeft className="w-3 h-3 text-slate-400" />
                    + Enter
                  </button>
                  <button
                    id="btn-speech-to-translate"
                    onClick={() => {
                      setExtractedText(speechText);
                      setCurrentView('translation');
                    }}
                    className="px-3 py-1 text-[10px] font-bold bg-[#2563EB] hover:bg-blue-600 text-white rounded flex items-center gap-1 shadow-sm"
                  >
                    <Globe className="w-3 h-3" />
                    Tłumacz
                  </button>
                </div>
                <span className="text-[9px] text-slate-500 font-mono">Esc: Zamknij</span>
              </div>
            </div>
          )}

        </div>

        {/* Right Column: Module Detail & Status Inspector */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* Selected Module Detail */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${selectedModule.accentColor}22`, color: selectedModule.accentColor }}
                >
                  {selectedModule.icon}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100">{selectedModule.title}</h3>
                  <p className="text-xs text-slate-400">{selectedModule.subtitle}</p>
                </div>
              </div>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  selectedModule.status === 'READY'
                    ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                ● {selectedModule.status}
              </span>
            </div>

            <p className="text-xs text-slate-300 my-3 leading-relaxed">
              {selectedModule.description}
            </p>

            <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-slate-800/80">
              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/50">
                <span className="text-slate-500 block text-[10px]">Etap Roadmapy</span>
                <span className="font-semibold text-sky-400">{selectedModule.versionStage}</span>
              </div>
              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/50">
                <span className="text-slate-500 block text-[10px]">Kąt radialny</span>
                <span className="font-mono text-slate-200">{selectedModule.angleDeg}° (co 60°)</span>
              </div>
            </div>
          </div>

          {/* Quick Windows Run Instructions */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-bold text-slate-200">Uruchomienie w Windows CMD</h4>
            </div>
            <div className="bg-black/60 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] text-emerald-400 overflow-x-auto">
              <code>run.bat</code>
              <span className="text-slate-500 block mt-1">
                lub: python -m myszkahud
              </span>
            </div>
          </div>

          {/* System Architecture Highlights */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 flex items-start gap-2.5">
              <Cpu className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200 block text-[11px]">Natywny PySide6</span>
                <span className="text-slate-400 text-[10px]">0% Webview, lekki QPainter i QThread</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200 block text-[11px]">Bezpieczny Klucz API</span>
                <span className="text-slate-400 text-[10px]">GEMINI_API_KEY z ENV, brak wycieków</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
