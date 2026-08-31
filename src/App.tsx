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
  MousePointer
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
    subtitle: 'Historia',
    icon: <ClipboardList className="w-5 h-5" />,
    angleDeg: 90,
    accentColor: '#10B981',
    status: 'READY',
    description: 'Lokalna historia schowka z inteligentnym filtrowaniem.',
    versionStage: 'v0.6 (Planowane)',
  },
  {
    id: 'notes',
    title: 'NOTATKI',
    subtitle: 'Szybkie notatki',
    icon: <StickyNote className="w-5 h-5" />,
    angleDeg: 150,
    accentColor: '#F59E0B',
    status: 'READY',
    description: 'Pływające, szybkie notatki kontekstowe pod kursorem.',
    versionStage: 'v0.7 (Planowane)',
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

type AppView = 'hud' | 'snipping' | 'ocr-result' | 'translation' | 'speech-overlay' | 'speech-result';

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

  const handleModuleClick = (mod: ModuleConfig) => {
    setSelectedModule(mod);
    if (mod.id === 'speech') {
      setCurrentView('speech-overlay');
    } else if (mod.id === 'ocr') {
      setCurrentView('snipping');
    } else if (mod.id === 'translate') {
      setCurrentView('translation');
    }
  };

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
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-950/80 text-blue-400 border border-blue-800/60 font-semibold">
                v0.5 (Speech-to-Text & Gemini Vision OCR)
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Windows 10 x64 Desktop Radial Utility & AI Assistant (PySide6)
            </p>
          </div>
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
                    Zakończ (Spacja)
                  </button>
                  <button
                    id="btn-speech-cancel"
                    onClick={() => setCurrentView('hud')}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded border border-slate-700"
                  >
                    Anuluj (Esc)
                  </button>
                </div>
                <span className="text-[9px] text-slate-500 font-mono">16kHz / 48kHz auto</span>
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
