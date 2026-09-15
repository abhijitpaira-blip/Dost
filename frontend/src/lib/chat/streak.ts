/**
 * Daily chat streak — how many consecutive calendar days (ending today or
 * yesterday) the user has exchanged at least one message with DOST. This
 * is the first genuinely persisted piece of core.md's Section 10
 * ("GAMIFICATION"): until now the AI could only ever *talk about* streaks
 * in a reply, nothing was actually tracked. Kept deliberately single-player
 * and effort-based per that section — no leaderboard, no penalty framing,
 * just a count read back from the same public.messages the AI already
 * writes to (see services/memory/store.py).
 */

/**
 * `now` is injectable for testability — omit it in real use, where it
 * defaults to the current moment.
 *
 * "Ending yesterday" (not only today) matters: someone who talked every
 * day up to and including yesterday, but hasn't opened the app yet today,
 * should still see their streak intact — it only breaks once a full
 * calendar day is skipped entirely, the convention most habit-streak
 * features use (and matches core.md's "a missed day is 'let's pick it back
 * up', never a loss" — a streak here is generous, not punitive).
 *
 * Calendar days are computed via Date.toDateString(), i.e. in whatever
 * timezone the code runs in (the user's own browser, since this is called
 * from a Server Component reading the *server's* clock — see the caveat
 * in dashboard/page.tsx). A day right at midnight can therefore land on
 * either side depending on server vs. user timezone; acceptable for a
 * lightweight motivational number, not something to build precise logic
 * like reminders or notifications on top of.
 */
export function computeStreak(messageDates: Set<string>, now: Date = new Date()): number {
  const cursor = new Date(now);
  if (!messageDates.has(cursor.toDateString())) {
    cursor.setDate(cursor.getDate() - 1);
  }

  let streak = 0;
  while (messageDates.has(cursor.toDateString())) {
    streak++;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

/** Collapses a list of message timestamps down to the distinct calendar
 * days they fall on — the only thing computeStreak() needs. */
export function toDateStrings(isoTimestamps: string[]): Set<string> {
  return new Set(isoTimestamps.map((iso) => new Date(iso).toDateString()));
}
