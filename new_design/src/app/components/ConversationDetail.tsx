import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router';
import { Play, Pause, ArrowLeft } from 'lucide-react';
import { motion } from 'motion/react';
import AnimatedBackground from './AnimatedBackground';

interface ApiSession {
  session_id: string;
  created_at: string | null;
  state: Record<string, any> | null;
  artifacts: { audio?: boolean; transcript?: boolean; events?: boolean } | null;
  stages: Array<{ name: string; status: string; missing_fields?: string[] }> | null;
  current_stage: string | null;
}

interface ApiEvent {
  role: string;
  content?: string;
  text?: string;
  type?: string;
}

interface TranscriptLine {
  speaker: 'Agent' | 'Caller';
  text: string;
  index: number;
}

function buildTranscript(events: ApiEvent[]): TranscriptLine[] {
  const messages = events.filter(
    e => (e.role === 'user' || e.role === 'agent' || e.role === 'model') && (e.content || e.text),
  );

  // Group consecutive same-role messages
  const groups: { role: string; texts: string[] }[] = [];
  for (const msg of messages) {
    const text = msg.content || msg.text || '';
    const last = groups[groups.length - 1];
    if (last && last.role === msg.role) {
      last.texts.push(text);
    } else {
      groups.push({ role: msg.role, texts: [text] });
    }
  }

  return groups.map((g, i) => ({
    speaker: g.role === 'user' ? 'Caller' : 'Agent',
    text: g.texts.join(' '),
    index: i,
  }));
}

function formatLabel(key: string): string {
  return key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function buildExtractedData(state: Record<string, any> | null): Record<string, { label: string; value: string }[]> {
  if (!state) return {};

  const SECTION_ORDER = ['caller', 'customer', 'policyholder', 'incident', 'damage', 'safety', 'third_parties', 'services'];
  const SECTION_LABELS: Record<string, string> = {
    caller: 'Caller Information',
    customer: 'Customer Information',
    policyholder: 'Policyholder',
    incident: 'Incident Details',
    damage: 'Damage',
    safety: 'Safety',
    third_parties: 'Third Parties',
    services: 'Services',
  };

  const result: Record<string, { label: string; value: string }[]> = {};

  const keys = [
    ...SECTION_ORDER.filter(k => k in state),
    ...Object.keys(state).filter(k => !SECTION_ORDER.includes(k) && k !== 'session_id'),
  ];

  for (const key of keys) {
    const section = state[key];
    if (!section || typeof section !== 'object' || Array.isArray(section)) continue;

    const items: { label: string; value: string }[] = [];
    for (const [field, val] of Object.entries(section)) {
      if (val === null || val === undefined || val === '') continue;
      let displayVal: string;
      if (typeof val === 'boolean') {
        displayVal = val ? 'Yes' : 'No';
      } else if (Array.isArray(val)) {
        if (val.length === 0) continue;
        displayVal = val.join(', ');
      } else {
        displayVal = String(val);
      }
      items.push({ label: formatLabel(field), value: displayVal });
    }

    if (items.length > 0) {
      const sectionLabel = SECTION_LABELS[key] || formatLabel(key);
      result[sectionLabel] = items;
    }
  }

  return result;
}

function WaveBar({ isPlaying, delay }: { isPlaying: boolean; delay: number }) {
  return (
    <motion.div
      className="w-1 rounded-full"
      style={{ background: 'var(--primary)' }}
      animate={{ height: isPlaying ? ['20%', '100%', '40%', '80%', '30%'] : '20%' }}
      transition={{ duration: 1.5, repeat: Infinity, delay, ease: 'easeInOut' }}
    />
  );
}

function AudioPlayer({ src, hasAudio }: { src: string; hasAudio: boolean }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const formatTime = (s: number) => {
    if (!s || isNaN(s)) return '0:00';
    return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  };

  const togglePlay = () => {
    const a = audioRef.current;
    if (!a || !hasAudio) return;
    if (isPlaying) { a.pause(); } else { a.play(); }
  };

  const seek = (e: React.MouseEvent<HTMLDivElement>) => {
    const a = audioRef.current;
    if (!a || !hasAudio || !a.duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    a.currentTime = ((e.clientX - rect.left) / rect.width) * a.duration;
  };

  return (
    <div className="rounded-lg p-6 backdrop-blur-2xl" style={{
      background: 'rgba(239, 238, 234, 0.35)',
      border: '1px solid rgba(255, 255, 255, 0.4)',
      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.5)',
    }}>
      {hasAudio && (
        <audio
          ref={audioRef}
          src={src}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => { setIsPlaying(false); setProgress(0); setCurrentTime(0); }}
          onTimeUpdate={() => {
            const a = audioRef.current;
            if (a?.duration) {
              setCurrentTime(a.currentTime);
              setProgress((a.currentTime / a.duration) * 100);
            }
          }}
          onLoadedMetadata={() => {
            if (audioRef.current) setDuration(audioRef.current.duration);
          }}
        />
      )}

      <div className="flex items-center gap-6">
        <button
          onClick={togglePlay}
          disabled={!hasAudio}
          className="w-14 h-14 flex items-center justify-center transition-all"
          style={{
            borderRadius: 'var(--radius-full)',
            background: hasAudio ? 'var(--primary)' : 'var(--surface-container-high)',
            color: hasAudio ? 'var(--on-primary)' : 'var(--outline)',
            cursor: hasAudio ? 'pointer' : 'default',
            border: 'none',
          }}
        >
          {isPlaying ? <Pause className="w-6 h-6 fill-current" /> : <Play className="w-6 h-6 fill-current ml-1" />}
        </button>

        <div className="flex-1">
          <div className="flex items-end justify-center h-16 gap-1 mb-3">
            {Array.from({ length: 50 }).map((_, i) => (
              <WaveBar key={i} isPlaying={isPlaying} delay={i * 0.05} />
            ))}
          </div>
          <div
            className="relative h-1.5 rounded-full overflow-hidden"
            style={{ background: 'var(--surface-container-high)', cursor: hasAudio ? 'pointer' : 'default' }}
            onClick={seek}
          >
            <div
              className="absolute top-0 left-0 h-full rounded-full transition-all"
              style={{ width: `${progress}%`, background: 'var(--primary)' }}
            />
          </div>
        </div>

        <div style={{ fontFamily: 'var(--font-body)', fontSize: '14px', fontWeight: '500', color: 'var(--on-surface)', whiteSpace: 'nowrap' }}>
          {formatTime(currentTime)} / {duration ? formatTime(duration) : '—'}
        </div>
      </div>

      {!hasAudio && (
        <div style={{ textAlign: 'center', marginTop: '8px', fontFamily: 'var(--font-body)', fontSize: '12px', color: 'var(--outline)' }}>
          No audio recording for this session
        </div>
      )}
    </div>
  );
}

export default function ConversationDetail() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [session, setSession] = useState<ApiSession | null>(null);
  const [events, setEvents] = useState<ApiEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      fetch(`/api/sessions/${id}`).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }),
      fetch(`/api/sessions/${id}/events`)
        .then(r => r.ok ? r.json() : { events: [] })
        .catch(() => ({ events: [] })),
    ])
      .then(([sessionData, eventsData]) => {
        setSession(sessionData);
        setEvents(eventsData.events || []);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message);
        setLoading(false);
      });
  }, [id]);

  const transcript = buildTranscript(events);
  const extractedData = buildExtractedData(session?.state ?? null);
  const hasAudio = !!session?.artifacts?.audio;
  const audioSrc = `/api/sessions/${id}/audio`;

  const state = session?.state || {};
  const caller = state.caller || state.customer || state.policyholder || {};
  const incident = state.incident || {};
  const dateObj = session?.created_at ? new Date(session.created_at) : null;

  const glassPanel = {
    background: 'rgba(250, 249, 245, 0.4)',
    border: '1px solid rgba(255, 255, 255, 0.5)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.6)',
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8 relative flex items-center justify-center">
        <AnimatedBackground />
        <div style={{ fontFamily: 'var(--font-body)', color: 'var(--on-surface-variant)', fontSize: '16px' }}>
          Loading session…
        </div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="min-h-screen p-8 relative">
        <AnimatedBackground />
        <div className="max-w-[1600px] mx-auto relative z-10">
          <button onClick={() => navigate('/')} className="flex items-center gap-2 mb-6" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--on-surface)', fontFamily: 'var(--font-body)', fontSize: '14px' }}>
            <ArrowLeft className="w-5 h-5" /> Back
          </button>
          <div style={{ padding: '16px', background: 'var(--error-container)', color: 'var(--on-error-container)', borderRadius: '8px', fontFamily: 'var(--font-body)' }}>
            {error || 'Session not found'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 relative">
      <AnimatedBackground />
      <div className="max-w-[1600px] mx-auto relative z-10">

        {/* Back */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 mb-6 px-4 py-2 rounded-lg transition-all backdrop-blur-xl"
          style={{
            background: 'rgba(239, 238, 234, 0.35)',
            border: '1px solid rgba(255, 255, 255, 0.4)',
            color: 'var(--on-surface)',
            fontFamily: 'var(--font-body)',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            boxShadow: '0 2px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.5)',
          }}
          onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--primary)')}
          onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.4)')}
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Overview</span>
        </button>

        {/* Metadata */}
        <div className="rounded-lg p-6 mb-6 backdrop-blur-2xl" style={glassPanel}>
          <div className="grid grid-cols-5 gap-6 mb-6">
            {[
              { label: 'Session ID', value: session.session_id },
              { label: 'Date', value: dateObj ? dateObj.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '—' },
              { label: 'Time', value: dateObj ? dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—' },
              { label: 'Caller', value: caller.full_name || caller.caller_name || '—' },
              { label: 'Policy Number', value: caller.policy_number || '—' },
            ].map(({ label, value }) => (
              <div key={label}>
                <div className="mb-1 uppercase tracking-wide" style={{ fontFamily: 'var(--font-body)', fontSize: '12px', fontWeight: '500', color: 'var(--on-surface-variant)' }}>
                  {label}
                </div>
                <div style={{ fontFamily: 'var(--font-body)', fontSize: '14px', fontWeight: '600', color: 'var(--on-surface)', wordBreak: 'break-all' }}>
                  {value}
                </div>
              </div>
            ))}
          </div>

          {incident.location && (
            <div style={{ paddingTop: '16px', borderTop: '1px solid var(--outline-variant)', fontFamily: 'var(--font-body)', fontSize: '14px', color: 'var(--on-surface-variant)' }}>
              <strong style={{ color: 'var(--on-surface)' }}>Incident:</strong>{' '}
              {[incident.date, incident.time, incident.location].filter(Boolean).join(' · ')}
              {incident.description && ` — ${incident.description}`}
            </div>
          )}

          <div style={{ paddingTop: '16px', borderTop: '1px solid var(--outline-variant)', marginTop: '16px' }}>
            <a
              href="https://www.get-inca.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-3 inline-block transition-all"
              style={{
                borderRadius: 'var(--radius-xl)',
                background: 'var(--primary)',
                color: 'var(--on-primary)',
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
                fontWeight: '600',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                textDecoration: 'none',
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.background = 'var(--primary-container)';
                (e.currentTarget as HTMLElement).style.color = 'var(--on-primary-container)';
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.background = 'var(--primary)';
                (e.currentTarget as HTMLElement).style.color = 'var(--on-primary)';
              }}
            >
              Start Case Processing
            </a>
          </div>
        </div>

        {/* Audio */}
        <div className="mb-6">
          <AudioPlayer src={audioSrc} hasAudio={hasAudio} />
        </div>

        {/* Transcript + Extracted Data */}
        <div className="grid grid-cols-3 gap-6">

          {/* Transcript (2/3) */}
          <div className="col-span-2">
            <div className="rounded-lg p-6 backdrop-blur-2xl" style={glassPanel}>
              <h2 className="mb-4" style={{
                fontFamily: 'var(--font-headline)',
                fontSize: '32px',
                fontWeight: '500',
                lineHeight: '1.3',
                color: 'var(--on-surface)',
              }}>
                Conversation Transcript
              </h2>

              {transcript.length === 0 ? (
                <div style={{ padding: '32px', textAlign: 'center', fontFamily: 'var(--font-body)', color: 'var(--on-surface-variant)', fontStyle: 'italic' }}>
                  No transcript available for this session.
                </div>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                  {transcript.map(msg => (
                    <div
                      key={msg.index}
                      className="p-4 rounded-lg backdrop-blur-xl"
                      style={{
                        background: msg.speaker === 'Agent' ? 'rgba(221, 228, 178, 0.3)' : 'rgba(233, 232, 228, 0.3)',
                        border: '1px solid rgba(255, 255, 255, 0.4)',
                        marginLeft: msg.speaker === 'Agent' ? '0' : '48px',
                        marginRight: msg.speaker === 'Agent' ? '48px' : '0',
                        boxShadow: '0 2px 12px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.4)',
                      }}
                    >
                      <div className="mb-2" style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: '14px',
                        fontWeight: '600',
                        letterSpacing: '0.05em',
                        color: msg.speaker === 'Agent' ? 'var(--on-secondary-container)' : 'var(--on-surface)',
                      }}>
                        {msg.speaker === 'Agent' ? 'Lisa (Agent)' : 'Caller'}
                      </div>
                      <p style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: '16px',
                        lineHeight: '1.5',
                        color: msg.speaker === 'Agent' ? 'var(--on-secondary-container)' : 'var(--on-surface)',
                      }}>
                        {msg.text}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Extracted Data (1/3) */}
          <div className="col-span-1">
            <div className="rounded-lg p-6 backdrop-blur-2xl" style={glassPanel}>
              <h2 className="mb-4" style={{
                fontFamily: 'var(--font-headline)',
                fontSize: '32px',
                fontWeight: '500',
                lineHeight: '1.3',
                color: 'var(--on-surface)',
              }}>
                Extracted Data
              </h2>

              {Object.keys(extractedData).length === 0 ? (
                <div style={{ padding: '32px 0', fontFamily: 'var(--font-body)', color: 'var(--on-surface-variant)', fontStyle: 'italic' }}>
                  No claim data collected yet.
                </div>
              ) : (
                <div className="space-y-5 max-h-[600px] overflow-y-auto pr-2">
                  {Object.entries(extractedData).map(([category, items]) => (
                    <div key={category}>
                      <h3 className="mb-2 px-2 uppercase tracking-wide" style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: '12px',
                        fontWeight: '600',
                        letterSpacing: '0.05em',
                        color: 'var(--on-surface-variant)',
                      }}>
                        {category}
                      </h3>
                      <div className="space-y-2">
                        {items.map((item, i) => (
                          <div key={i} className="p-3 rounded-lg backdrop-blur-xl" style={{
                            background: 'rgba(239, 238, 234, 0.3)',
                            border: '1px solid rgba(255, 255, 255, 0.4)',
                            boxShadow: '0 2px 12px rgba(0, 0, 0, 0.03), inset 0 1px 0 rgba(255, 255, 255, 0.4)',
                          }}>
                            <div className="mb-1 uppercase tracking-wide" style={{ fontFamily: 'var(--font-body)', fontSize: '11px', fontWeight: '500', color: 'var(--on-surface-variant)' }}>
                              {item.label}
                            </div>
                            <div style={{ fontFamily: 'var(--font-body)', fontSize: '14px', fontWeight: '600', color: 'var(--on-surface)' }}>
                              {item.value}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Stage progress */}
              {session.stages && session.stages.length > 0 && (
                <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--outline-variant)' }}>
                  <div className="mb-3 uppercase tracking-wide" style={{ fontFamily: 'var(--font-body)', fontSize: '11px', fontWeight: '600', color: 'var(--on-surface-variant)' }}>
                    Intake Progress
                  </div>
                  <div className="space-y-1">
                    {session.stages.map(stage => (
                      <div key={stage.name} className="flex items-center gap-2">
                        <div style={{
                          width: '7px', height: '7px', borderRadius: '50%', flexShrink: 0,
                          background: stage.status === 'completed' ? 'var(--primary)' : stage.status === 'current' ? 'var(--primary-fixed-dim)' : 'var(--outline-variant)',
                        }} />
                        <span style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: '12px',
                          textTransform: 'capitalize',
                          color: stage.status === 'completed' ? 'var(--on-surface)' : stage.status === 'current' ? 'var(--primary)' : 'var(--outline)',
                          fontWeight: stage.status === 'current' ? '600' : '400',
                        }}>
                          {stage.name.replace(/_/g, ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
