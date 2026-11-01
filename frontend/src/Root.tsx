import React, { useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { getSupabase } from './lib/auth';
import { getMe } from './lib/api';
import { Me } from './lib/types';
import { App } from './App';
import { AuthScreen } from './pages/AuthScreen';
import { Loader2 } from 'lucide-react';

// Shows the login screen until someone is signed in, then the app for their role
export const Root: React.FC = () => {
  const [session, setSession] = useState<Session | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let unsubscribe: (() => void) | undefined;
    getSupabase()
      .then(async (supabase) => {
        const { data } = await supabase.auth.getSession();
        setSession(data.session);
        const sub = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
        unsubscribe = () => sub.data.subscription.unsubscribe();
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Could not start the app.'))
      .finally(() => setReady(true));
    return () => unsubscribe?.();
  }, []);

  // Load the account (role) whenever the signed-in user changes
  const userId = session?.user.id;
  useEffect(() => {
    setMe(null);
    if (!userId) return;
    getMe()
      .then(setMe)
      .catch((e) => setError(e instanceof Error ? e.message : 'Could not load your account.'));
  }, [userId]);

  const signOut = async () => {
    const supabase = await getSupabase();
    await supabase.auth.signOut();
    setMe(null);
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 text-center">
        <div className="space-y-3">
          <p className="text-sm text-rose-700">{error}</p>
          <button onClick={() => window.location.reload()} className="text-xs font-semibold text-emerald-700">
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (!ready || (session && !me)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-emerald-600 animate-spin" />
      </div>
    );
  }

  if (!session || !me) return <AuthScreen />;

  // key: a different account gets a completely fresh app state
  return <App key={me.user_id} me={me} onSignOut={signOut} />;
};
