import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://xjsluqmnuypygckwnyaf.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_hlG2Es0RBnmIUE7CDmHAGA_1djnIycQ';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
