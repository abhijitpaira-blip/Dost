/**
 * Hand-written for Phase 1, matching database/migrations/0001_init_profiles.sql.
 * Once the Supabase CLI is set up, replace with generated types:
 *   supabase gen types typescript --project-id <ref> > src/types/database.ts
 */
export interface Profile {
  id: string;
  auth_user_id: string;
  name: string | null;
  age: number | null;
  preferred_language: string;
  avatar: string | null;
  created_at: string;
  updated_at: string;
}
