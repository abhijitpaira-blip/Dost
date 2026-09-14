/**
 * Hand-written, matching database/migrations/0001_init_profiles.sql and
 * 0002_guardian_consent.sql. Once the Supabase CLI is set up, replace with
 * generated types:
 *   supabase gen types typescript --project-id <ref> > src/types/database.ts
 */
export interface Profile {
  id: string;
  auth_user_id: string;
  name: string | null;
  age: number | null;
  preferred_language: string;
  avatar: string | null;
  guardian_name: string | null;
  guardian_email: string | null;
  guardian_consent_given: boolean;
  guardian_consented_at: string | null;
  onboarding_completed_at: string | null;
  created_at: string;
  updated_at: string;
}
