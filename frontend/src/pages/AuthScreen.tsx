import React, { useState } from 'react';
import { getSupabase } from '../lib/auth';
import { HeartPulse, Loader2, LogIn, UserPlus } from 'lucide-react';

type Mode = 'signin' | 'signup';
type Role = 'parent' | 'clinician';

const MIN_PASSWORD = 8;

export const AuthScreen: React.FC = () => {
  const [mode, setMode] = useState<Mode>('signin');
  const [role, setRole] = useState<Role>('parent');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      const supabase = await getSupabase();
      if (mode === 'signin') {
        const { error: err } = await supabase.auth.signInWithPassword({ email, password });
        if (err) throw err;
        // App switches to the signed-in view via onAuthStateChange
      } else {
        if (password.length < MIN_PASSWORD) {
          throw new Error(`Please use at least ${MIN_PASSWORD} characters for the password.`);
        }
        const { data, error: err } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: window.location.origin,
            // Checked by the server; only a correct code makes this account a clinician
            data: role === 'clinician' ? { clinician_invite_code: inviteCode.trim() } : {},
          },
        });
        if (err) throw err;
        if (!data.session) {
          setNotice('Account created. Please open the confirmation email we sent you, then sign in here.');
          setMode('signin');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  const inputClass =
    'w-full px-3 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500';

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center text-center gap-3">
          <div className="p-3 bg-emerald-600 text-white rounded-2xl shadow-sm">
            <HeartPulse className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">NutriScan</h1>
            <p className="text-xs text-slate-500">Trust-First AI Nutrition Risk System</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 space-y-5">
          <div className="grid grid-cols-2 bg-slate-100 p-1 rounded-2xl text-xs font-semibold">
            {(['signin', 'signup'] as Mode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => {
                  setMode(m);
                  setError(null);
                }}
                className={`py-2 rounded-xl transition-all ${
                  mode === m ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
                }`}
              >
                {m === 'signin' ? 'Sign in' : 'Create account'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            {mode === 'signup' && (
              <div>
                <label className="block font-medium text-slate-700 mb-1">I am a</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['parent', 'clinician'] as Role[]).map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setRole(r)}
                      aria-pressed={role === r}
                      className={`py-2.5 rounded-xl border font-semibold capitalize transition-colors ${
                        role === r
                          ? 'bg-emerald-600 border-emerald-600 text-white'
                          : 'bg-white border-slate-200 text-slate-600'
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div>
              <label htmlFor="auth-email" className="block font-medium text-slate-700 mb-1">Email</label>
              <input
                id="auth-email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
              />
            </div>

            <div>
              <label htmlFor="auth-password" className="block font-medium text-slate-700 mb-1">Password</label>
              <input
                id="auth-password"
                type="password"
                required
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputClass}
              />
            </div>

            {mode === 'signup' && role === 'clinician' && (
              <div>
                <label htmlFor="auth-invite" className="block font-medium text-slate-700 mb-1">
                  Clinician invite code
                </label>
                <input
                  id="auth-invite"
                  type="text"
                  required
                  autoComplete="off"
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value)}
                  className={inputClass}
                />
                <p className="text-[11px] text-slate-400 mt-1">Given to you by the project team.</p>
              </div>
            )}

            {error && <div className="text-rose-700 bg-rose-50 p-2.5 rounded-xl">{error}</div>}
            {notice && <div className="text-emerald-800 bg-emerald-50 p-2.5 rounded-xl">{notice}</div>}

            <button
              type="submit"
              disabled={busy}
              className="w-full flex items-center justify-center gap-2 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-2xl shadow-sm transition-colors disabled:opacity-50"
            >
              {busy ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : mode === 'signin' ? (
                <LogIn className="w-4 h-4" />
              ) : (
                <UserPlus className="w-4 h-4" />
              )}
              {mode === 'signin' ? 'Sign in' : 'Create account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
