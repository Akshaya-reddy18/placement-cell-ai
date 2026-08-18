import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { supabase } from '@/lib/supabase';
import { useAppStore } from '@/store/useStore';
import { LogIn } from 'lucide-react';
import { api } from '@/lib/api';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setUser = useAppStore((s) => s.setUser);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (authError) throw authError;

      if (data.session) {
        localStorage.setItem('pc_token', data.session.access_token);
        
        try {
          const profile = await api.onboarding.getProfile();
          setUser(profile);
          if (profile.onboardingComplete) {
            navigate('/dashboard');
          } else {
            navigate('/');
          }
        } catch (err) {
          // Profile might not exist yet, redirect to onboarding
          navigate('/');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8 rounded-xl border border-slate-800 bg-slate-900/50 p-8 shadow-2xl backdrop-blur-sm">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10">
            <LogIn className="h-6 w-6 text-blue-400" />
          </div>
          <h2 className="mt-6 text-3xl font-bold tracking-tight text-white">Log in to your account</h2>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          {error && <div className="rounded-md bg-red-500/10 p-3 text-sm text-red-400">{error}</div>}
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-300">Email address</label>
              <Input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-300">Password</label>
              <Input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1"
                placeholder="••••••••"
              />
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </Button>
          
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-slate-700" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-900 px-2 text-slate-400">Or</span>
            </div>
          </div>
          
          <Button 
            type="button" 
            variant="outline" 
            className="w-full"
            onClick={() => {
              localStorage.setItem('pc_token', 'guest_token');
              localStorage.setItem('pc_student_id', '00000000-0000-0000-0000-000000000000');
              // Assuming guest is already onboarded
              setUser({
                id: '00000000-0000-0000-0000-000000000000',
                name: 'Guest User',
                email: 'guest@example.com',
                onboardingComplete: true,
                createdAt: new Date().toISOString()
              });
              navigate('/dashboard');
            }}
          >
            Continue as Guest
          </Button>
        </form>

        <p className="text-center text-sm text-slate-400">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold text-blue-400 hover:text-blue-300">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
