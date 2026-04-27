import { useState, useEffect } from 'react';
import { useNavigate } from "react-router";
import { Clock, Calendar, MessageSquare, PhoneCall } from "lucide-react";
import AnimatedBackground from "./AnimatedBackground";

interface ApiSession {
  session_id: string;
  created_at: string | null;
  state: Record<string, any> | null;
  artifacts: { audio?: boolean; transcript?: boolean; events?: boolean } | null;
  stages: Array<{ name: string; status: string }> | null;
  current_stage: string | null;
}

type ConversationStatus = 'Resolved' | 'In Progress' | 'Pending';

interface Conversation {
  id: string;
  customerName: string;
  date: string;
  time: string;
  summary: string;
  status: ConversationStatus;
  hasAudio: boolean;
}

function deriveStatus(session: ApiSession): ConversationStatus {
  if (session.artifacts?.audio) return 'Resolved';
  if (session.stages?.some(s => s.status === 'current')) return 'In Progress';
  return 'Pending';
}

function mapSession(session: ApiSession): Conversation {
  const state = session.state || {};
  const caller = state.caller || state.customer || state.policyholder || {};
  const incident = state.incident || {};

  const dateObj = session.created_at ? new Date(session.created_at) : null;
  const date = dateObj
    ? dateObj.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
    : 'Unknown';
  const time = dateObj
    ? dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '—';

  const customerName =
    caller.full_name || caller.caller_name || 'Unknown caller';

  const desc = incident.description || '';
  const summary = desc
    ? desc.length > 90 ? desc.slice(0, 90) + '…' : desc
    : incident.location
    ? `Incident at ${incident.location}`
    : `Stage: ${session.current_stage || 'intake'}`;

  return {
    id: session.session_id,
    customerName,
    date,
    time,
    summary,
    status: deriveStatus(session),
    hasAudio: !!session.artifacts?.audio,
  };
}

const STATUS_STYLES: Record<ConversationStatus, { bg: string; color: string }> = {
  Resolved: { bg: 'var(--primary-container)', color: 'var(--on-primary-container)' },
  'In Progress': { bg: 'var(--error-container)', color: 'var(--on-error-container)' },
  Pending: { bg: 'var(--secondary-container)', color: 'var(--on-secondary-container)' },
};

export default function ConversationOverview() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ApiSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/sessions')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        setSessions(data.sessions || []);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  const conversations = sessions.map(mapSession);
  const todayStr = new Date().toDateString();
  const resolvedCount = conversations.filter(c => c.status === 'Resolved').length;
  const inProgressCount = conversations.filter(c => c.status === 'In Progress').length;
  const todayCount = sessions.filter(
    s => s.created_at && new Date(s.created_at).toDateString() === todayStr,
  ).length;

  const glassCard = {
    background: 'rgba(239, 238, 234, 0.35)',
    border: '1px solid rgba(255, 255, 255, 0.4)',
    boxShadow: '0 4px 24px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.5)',
  };

  return (
    <div className="min-h-screen p-8 relative">
      <AnimatedBackground />
      <div className="max-w-[1400px] mx-auto relative z-10">

        {/* Header */}
        <div className="rounded-lg p-12 mb-12 backdrop-blur-2xl" style={{
          background: 'rgba(250, 249, 245, 0.4)',
          border: '1px solid rgba(255, 255, 255, 0.5)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.6)',
        }}>
          <h1 style={{
            fontFamily: 'var(--font-headline)',
            fontSize: '48px',
            fontWeight: '500',
            lineHeight: '1.2',
            letterSpacing: '-0.01em',
            color: 'var(--on-surface)',
            marginBottom: '8px',
          }}>
            Inca Call Log Manager
          </h1>
          <p style={{
            fontFamily: 'var(--font-body)',
            fontSize: '18px',
            lineHeight: '1.6',
            color: 'var(--on-surface-variant)',
          }}>
            Review and analyse insurance claims intake calls
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-6 mb-12">
          {[
            { label: 'Total Calls', value: sessions.length, icon: <MessageSquare className="w-8 h-8" style={{ color: 'var(--primary)' }} /> },
            { label: 'Resolved', value: resolvedCount, icon: <div className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm" style={{ background: 'var(--primary-container)', color: 'var(--on-primary-container)' }}>✓</div> },
            { label: 'In Progress', value: inProgressCount, icon: <PhoneCall className="w-8 h-8" style={{ color: 'var(--primary)' }} /> },
            { label: 'Today', value: todayCount, icon: <Calendar className="w-8 h-8" style={{ color: 'var(--primary)' }} /> },
          ].map(stat => (
            <div key={stat.label} className="rounded-lg p-6 backdrop-blur-2xl" style={glassCard}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="mb-1 uppercase tracking-wide" style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '12px',
                    fontWeight: '500',
                    color: 'var(--on-surface-variant)',
                  }}>
                    {stat.label}
                  </div>
                  <div style={{
                    fontFamily: 'var(--font-headline)',
                    fontSize: '32px',
                    fontWeight: '500',
                    color: 'var(--on-surface)',
                  }}>
                    {loading ? '—' : stat.value}
                  </div>
                </div>
                {stat.icon}
              </div>
            </div>
          ))}
        </div>

        {/* Session list */}
        <div className="rounded-lg p-6 backdrop-blur-2xl" style={{
          background: 'rgba(250, 249, 245, 0.4)',
          border: '1px solid rgba(255, 255, 255, 0.5)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.6)',
        }}>
          <h2 className="mb-6" style={{
            fontFamily: 'var(--font-headline)',
            fontSize: '32px',
            fontWeight: '500',
            lineHeight: '1.3',
            color: 'var(--on-surface)',
          }}>
            All Calls
          </h2>

          {loading && (
            <div style={{ textAlign: 'center', padding: '48px', fontFamily: 'var(--font-body)', color: 'var(--on-surface-variant)' }}>
              Loading sessions…
            </div>
          )}

          {error && (
            <div style={{ padding: '16px', background: 'var(--error-container)', color: 'var(--on-error-container)', borderRadius: '8px', fontFamily: 'var(--font-body)' }}>
              Failed to load sessions: {error}
            </div>
          )}

          {!loading && !error && conversations.length === 0 && (
            <div style={{ textAlign: 'center', padding: '64px', fontFamily: 'var(--font-headline)', fontStyle: 'italic', fontSize: '24px', color: 'var(--on-surface-variant)' }}>
              No sessions yet. Start a call to see it here.
            </div>
          )}

          {!loading && !error && conversations.length > 0 && (
            <div className="space-y-3">
              {conversations.map(conversation => {
                const statusStyle = STATUS_STYLES[conversation.status];
                return (
                  <div
                    key={conversation.id}
                    onClick={() => navigate(`/conversation/${conversation.id}`)}
                    className="rounded-lg p-5 cursor-pointer transition-all backdrop-blur-xl"
                    style={{
                      background: 'rgba(233, 232, 228, 0.3)',
                      border: '1px solid rgba(255, 255, 255, 0.4)',
                      boxShadow: '0 2px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.5)',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--primary)')}
                    onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.4)')}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 style={{
                            fontFamily: 'var(--font-body)',
                            fontSize: '14px',
                            fontWeight: '600',
                            letterSpacing: '0.04em',
                            color: 'var(--on-surface)',
                          }}>
                            {conversation.customerName}
                          </h3>
                          <span className="px-3 py-1 text-xs uppercase tracking-wide" style={{
                            borderRadius: 'var(--radius-xl)',
                            background: statusStyle.bg,
                            color: statusStyle.color,
                            fontFamily: 'var(--font-body)',
                            fontWeight: '500',
                          }}>
                            {conversation.status}
                          </span>
                          {conversation.hasAudio && (
                            <span className="px-3 py-1 text-xs uppercase tracking-wide" style={{
                              borderRadius: 'var(--radius-xl)',
                              background: 'var(--secondary-container)',
                              color: 'var(--on-secondary-container)',
                              fontFamily: 'var(--font-body)',
                              fontWeight: '500',
                            }}>
                              Audio
                            </span>
                          )}
                        </div>
                        <p className="mb-3" style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: '15px',
                          lineHeight: '1.5',
                          color: 'var(--on-surface-variant)',
                        }}>
                          {conversation.summary}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-2" style={{ color: 'var(--on-surface-variant)' }}>
                        <Calendar className="w-4 h-4" />
                        <span style={{ fontFamily: 'var(--font-body)', fontSize: '13px' }}>
                          {conversation.date}
                        </span>
                      </div>
                      <div className="flex items-center gap-2" style={{ color: 'var(--on-surface-variant)' }}>
                        <Clock className="w-4 h-4" />
                        <span style={{ fontFamily: 'var(--font-body)', fontSize: '13px' }}>
                          {conversation.time}
                        </span>
                      </div>
                      <div style={{
                        fontFamily: 'var(--font-body)',
                        fontSize: '12px',
                        color: 'var(--outline)',
                        letterSpacing: '0.04em',
                        marginLeft: 'auto',
                      }}>
                        {conversation.id}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
