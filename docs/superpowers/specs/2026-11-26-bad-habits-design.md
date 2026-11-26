# Bad Habits — Design

Date: 2026-11-26 · Status: awaiting approval

## 1. Intent

Bad Habits is a fully offline mobile app (Android + iOS) that helps a person reach goals **gradually**, using the methods from James Clear's *Atomic Habits*: start small (two-minute rule), track visibly (habit tracker), never miss twice, make it obvious (implementation intentions), make it satisfying, and tie habits to identity.

It has two purposes, both equally real:

- **A personal tool** the author will use daily for goals like reading, going to the gym, saving money, and cutting down drinking. No existing tool they know handles "get there gradually".
- **A portfolio piece** demonstrating that the author produces good-quality software (with or without AI): clean architecture, typed code, a well-tested core, CI.

What kept the author going on past goals was *realizing they truly needed it for their own sake*. The app therefore keeps each habit's personal **"why"** in front of the user at the moments they're most likely to give up.

### Success looks like

- The author is still using it daily three months after first install.
- A reviewer opening the repo sees a clear domain core with thorough tests, a typed data layer with migrations, and green CI.

## 2. Goals, non-goals, anti-goals

**Goals (phase 1)**
- Three kinds of habit: build up, cut down, fixed target (§4).
- Gradual levels with forgiving miss rules for build-up and cut-down habits (§5).
- Log as things happen, at any time; backfill forgotten days (§6).
- Home, habit detail, create/edit, and completed screens (§8).
- Per-habit reminders with a one-tap log action, plus an evening check (§7).
- Satisfying feedback: log animation + haptics, level-up moment, finish moment (§5.6, §8).

**Non-goals**
- Accounts, servers, cloud sync, or live multi-device sync.
- Social features, leaderboards, points/badge economies.
- Ads, analytics, or any network calls.

**Anti-goals** (failure even if it technically works)
- Nagging, shaming, or notification spam. Copy after a miss is kind, never guilt-inducing.
- A streak or level that looks wrong (e.g. a forgotten log counted as a miss after the user backfilled it).
- Silent data loss.

**Later phases** (the phase 1 data model must already support them; see §9)
- Phase 2: export/import a backup file through the OS share sheet (for moving to a new phone); home-screen widget (needs native code).
- Phase 3: share one habit's *setup* via QR code (recipient gets a fresh copy, no history); annual recap ("In 2026 you read 94 hours…").

## 3. Constraints and decided stack

- **Fully offline.** All data on the device.
- **Android first.** The author's daily phone is an Android (Google Pixel). Every phase 1 feature, including logging straight from a notification, must work fully on Android and be tested on that device. **iOS** must build through EAS and run, but the author has no paid Apple Developer account, so iOS is tested in Expo Go only. On iOS, notification actions may fall back to opening the app and logging there.
- **No store release in phase 1.** The app is installed on the author's phone from an EAS build (internal distribution / APK). The repo and its builds are the portfolio artifact. Store listings, privacy policy, store signing, and EAS Submit are deferred to a later phase.
- **React Native with Expo**, **TypeScript**. The author develops on Windows, so iOS builds go through **EAS Build** and on-device testing through Expo Go / development builds.
- **SQLite** via `expo-sqlite`, accessed through **Drizzle ORM** with versioned migrations.
- **Expo Router** (navigation), **Zustand** (app state), **Jest** + React Native Testing Library, **ESLint + Prettier**, **GitHub Actions** CI running typecheck, lint, and tests on every push.
- `expo-notifications` for local notifications, `expo-haptics` for haptics.
- UI language **English**, with all strings going through an i18n layer so Portuguese can be added later.

(Expo, SQLite, and offline-only were decided by the author. Drizzle, Expo Router, Zustand, Jest, ESLint/Prettier, and CI were proposed by Claude and accepted.)

## 4. Habit model

Every habit has:

| Field | Notes |
|---|---|
| name, emoji | |
| kind | `build_up` · `cut_down` · `fixed` |
| measure | `check` (yes/no) · `count` · `minutes` · `money` |
| period | `day` · `week` · `month` |
| why | "Why does this matter to me?" Optional but encouraged; prompted right after the name. |
| identity | Optional "I am someone who…" line. Secondary to *why*. |
| reminder | See §7. |

**Allowed combinations** *(Claude's call)*: `check` only with `fixed` + `day` (a yes/no can't grow or shrink). `build_up` and `cut_down` require `count`, `minutes`, or `money`.

**Kind-specific settings**

- **Build up:** final goal *F* per period; start at *s*% of F (default 20%, slider).
- **Cut down:** current amount *B* per period (baseline), limit *L* (default 0). Success means staying **at or under** the target. A period with no logs counts as 0, so "didn't drink today" never needs logging.
- **Fixed:** target *T* per period, either **endless** or **until a final total** *G* (e.g. €100/week until €2,000).

**Periods.** A day is local midnight to midnight. Months are calendar months. Weeks start on the habit's own `week_start`, which is **copied from the Settings default (Monday) when the habit is created and never changes afterward**. Changing the setting affects only new habits, so past week results are never rewritten. *(Claude's call.)* *(Claude's call: dates are stored as local `YYYY-MM-DD`; time-zone travel is ignored.)*

**Pace.** For the current period: `pace = target × elapsedDays / daysInPeriod`. Shown as a marker on the progress bar and in text ("Day 4 · on pace €57 · you're at €40"). For a fixed €100/week habit, the daily guide is €100 / 7 = €14.29. The guide is advisory only; success is judged on the total when the period ends.

## 5. Rules engine

### 5.1 Approach (decided: A, recompute from history)

The database stores **only** habit settings (with revisions), log entries, and user decisions (complete/archive/level up). A **pure TypeScript rules engine** with no React, Expo, or DB imports derives everything else by replaying history period by period:

```
evaluate(habit, revisions, logs, decisions, today, settings) → HabitState
```

`HabitState` includes: the ladder of levels, current level and target, per-period results (good / miss / in progress / warm-up), the good-period counter toward the next level, the consecutive-miss count, current and best streak, the current period total and pace, the cumulative total (fixed + final total), and flags such as `finishReached`.

This approach was chosen over storing mutable state (B) or a cached hybrid (C) because:
- backfills and edits are automatically correct,
- periods that ended while the app was closed need no background job,
- the engine is easy to test exhaustively,
- the backup file and annual recap become plain reads of settings and logs.

Performance: a few years of daily logs is trivial to replay. Memoize per habit on (logs, revisions, today) if needed. A persisted per-period cache (C) is a possible later optimisation, not part of phase 1.

### 5.2 Ladders

**Build up:** levels go from the start target `T0 = s% × F` up to F in steps of **20% of F**, with the last step capped at F. Default s = 20% gives 5 levels: e.g. 6 → 12 → 18 → 24 → 30 min/day.

**Cut down:** levels go from `B − 20%·(B − L)` down to L in steps of **20% of (B − L)**. Example: B = 5, L = 0 gives 4 → 3 → 2 → 1 → 0.

**Rounding:** minutes and counts to whole units; money to the nearest 5 currency units. Adjacent levels that round to the same value are merged. Build-up targets are at least 1 unit. *(Rounding money to 5 was Claude's proposal, accepted. Merge and minimum rules are Claude's call.)*

**Fixed:** no ladder; a single target T.

### 5.3 Period results

- **Build up / fixed:** good if the period total ≥ target. **Cut down:** good if the period total ≤ target.
- A period is judged only after it ends. Exception: a cut-down period whose total has already exceeded the target is shown as a miss immediately (it can't recover).
- **Warm-up** *(Claude's call)*: if a weekly or monthly habit is created mid-period, that first partial period is neither good nor a miss. Daily habits have no warm-up.
- Periods before the habit's creation date don't exist. Logs can't be dated before creation or in the future.

### 5.4 Leveling and forgiving miss rules (build up, cut down)

The counter is the number of good periods toward the next level.

| Event | Effect |
|---|---|
| Good period | counter +1, consecutive misses reset to 0 |
| 1 miss | nothing (never miss twice): counter neither grows nor resets |
| 2 misses in a row | counter resets to 0; level stays |
| 3 misses in a row | drop one level (never below level 1); counter 0; the consecutive-miss count restarts, so another 3 in a row drops again |

**Level-up thresholds** (good periods at the current level): **14** for daily · **4** for weekly · **2** for monthly. *(Daily and weekly were proposed and accepted after the author said the first proposal felt too fast. Monthly is Claude's call.)*

**Finish:** once at the final level, hold it for **28** good days · **8** good weeks · **4** good months, with the same miss rules. Then `finishReached` is set.

Example: "Read 30 min/day" from 6 min takes 4 level-ups × 14 days + 28 days ≈ 12 weeks with no misses.

### 5.5 Fixed habits

- **Streak**: consecutive good periods with the same forgiveness: 1 miss pauses the streak; 2 misses in a row reset it.
- **Endless**: runs until the user archives it.
- **Until final total G**: cumulative total across all logs; `finishReached` when ≥ G. Overflow in one period counts toward G but **does not** carry into the next period's target. Show overall progress ("€640 of €2,000 · ~14 weeks left at this pace").

### 5.6 Finish moment and the choice

When `finishReached` first becomes true, the app shows a celebration screen with a journey summary ("You started at 6 min on Nov 5. 88 days later you read 30 a day.") and the habit's *why*. Then it asks:

- **Build up / fixed with final total → Level up:** suggest a new final goal (double, editable). The habit continues from the **current target**, without dropping back to 20%. A new revision's ladder runs from the current target to the new F in steps of 20% of the new F.
- **Cut down → Keep guarding:** stays active at the limit; the streak keeps counting.
- **Mark as completed:** moves to the Completed section.

Until the user chooses, the habit stays on the home list with a "Goal reached, choose what's next" banner. *(Claude's call.)*

### 5.7 Archived and completed habits *(Claude's call)*

Status decisions are dated, and the engine treats them as time windows:

- **Archived = paused.** Periods that fall wholly or partly inside an archived window are skipped: neither good nor miss, and counters are untouched. On **restore**, the habit resumes exactly where it left off (same level, counter, and streak). The period in which the habit is restored is treated like a warm-up.
- **Completed = frozen.** Evaluation stops at the completion date. The Completed screen shows the state as of that date. **Restart** creates a new habit; it never un-freezes the old one.

### 5.8 Revisions (editing settings without corrupting history)

Editing a habit's goal settings creates a **revision** effective from the start of the current period. The engine uses, for each period, the revision in effect then. When a new ladder takes effect, the user lands on the highest level whose target does not exceed the previous target (build up; mirrored for cut down), and the counter is kept. **Kind, measure, and period can't be edited.** To change those, create a new habit. *(Claude's call, communicated to the author.)*

## 6. Logging

- **Log anytime**, from the home card button, the detail screen, or a notification action.
  - `check`: ✓ toggles today. `count`: +1. `minutes`: enter minutes, or "Done" logs the current target. `money`: amount entry.
- **Multiple entries** per day are summed. Each entry is stored separately with its timestamp.
- **Undo / edit / delete**: tap a calendar day on the detail screen to see that day's entries and change them.
- **Backfill**: any past day since creation can receive entries; the engine recomputes.
- Storage *(Claude's call)*: minutes as integer minutes; money as integer minor units (cents). Currency is a display setting (default €).

## 7. Reminders and notifications

- **Per-habit reminder** (optional): time, days of week (default every day), and an optional **when/where** text. The create form shows the resulting implementation intention, e.g. *"I will read at 21:00 after dinner, on the couch."*
- **Action button** on the notification: "Done" (check, minutes → logs the current target), "+1" (count). Money opens the app's amount entry. Cut-down habits have reminders off by default and no log action.
- **Evening check** (optional, default 21:30): one notification only if some daily habit is still unmet today ("2 habits left today"). Implemented by scheduling it ahead and cancelling or rescheduling whenever logs change.
- **Builder risk**: background handling of notification actions differs between Android and iOS. On **Android** it must log in the background without opening the app. On **iOS**, if it can't be made reliable, the action opens the app and logs there. A tap must never be silently lost.

## 8. Screens

Visual direction: **Calm journal** (paper tones, serif titles, muted green, system sans for small text), with light and dark variants following the system or a setting. Mockups are in `.superpowers/brainstorm/` (not committed).

### 8.1 Home: "My habits"

```
My habits                      (+)
Thursday, Nov 26
TODAY                    1/1 done
┌ 📖 Read                  [✓] ┐
│ ████████████████████         │
│ 6 / 6 min      20% of 30 min │
└──────────────────────────────┘
THIS WEEK                 ends Sun
┌ 🏋️ Gym                   [+1] ┐
│ ██████░░░░│░░░░░░  (amber)    │
│ 1/3 · on pace = 2   3 of 5/wk │
└──────────────────────────────┘
THIS MONTH             ends Nov 30
┌ 💰 Save                  [+€] ┐
...
[Habits]   Completed   Settings
```

- Sections by period (Today / This week / This month), each with its end.
- Card: name, quick-log button, progress bar for the current period (green on pace, amber behind), pace tick, a level tag for the long-term journey ("3 of 5 / wk", "20% of 30 min", "4 → 0"; fixed with total: "€640 of €2,000").
- The *why* is **not** shown on home cards (clutter).
- Tap a card to open its detail screen. Tap the button for a quick log, with a small animation and haptic.

### 8.2 Habit detail

Top to bottom:
1. Header: back, name, Edit.
2. **Why** (and identity line if set).
3. **Journey**: staircase of levels showing past, current, and future steps; "Started Nov 5 · level 2 of 5". Fixed: overall progress or streak instead.
4. **Next level** meter: dots for good periods toward the threshold, plus a "1 miss allowed" note.
5. **Today / this period**: progress and the log button.
6. **Calendar** (month, swipeable): day cells marked hit / miss / level-up. For weekly and monthly habits, days with logs are dotted and each week row or month shows its result *(Claude's call)*. Tap a day to see its entries, edit or undo them, or backfill.
7. Current and best streak.

### 8.3 Create / edit habit: one form with a live preview

```
Cancel        New habit         Save
Name           [📖 Read          ]
Why            [So I finally finish the books I buy]
Kind           [Build up|Cut down|Fixed]
Measure/every  [✓ # min €] [day wk mo]
  ── fields depend on kind ──
  Build up:  Final goal [30 min] · Start at [20% slider]
  Cut down:  Current amount [5] · Limit [0]
  Fixed:     Target [€100/wk] · [Endless | Until €2,000]
Identity       [I am someone who…]     (optional)
Reminder       [Yes | No]
  At [21:00] · Days [M T W T F S S]
  When/where   [After dinner, on the couch]
  "I will read at 21:00 after dinner, on the couch."
┌ Preview ────────────────────────────────┐
│ 6 → 12 → 18 → 24 → 30 min/day           │
│ Level up every 14 good days · ~12 weeks │
└─────────────────────────────────────────┘
```

Edit opens the same form pre-filled. Kind, measure, and period are read-only (§5.8). Edit also offers **Archive** and **Delete** (with confirmation).

### 8.4 Completed

A quiet shelf of finished habits. Each shows its journey ("6 → 30 min · Nov 5 – Feb 1 · 88 days") and its *why*. Tapping one opens a read-only detail with the full calendar. **Restart** creates a new habit with the same settings and fresh history. Archived habits are listed separately here (or under a filter) and can be restored *(Claude's call)*.

### 8.5 Settings

Currency (default €), week start (default Monday), theme (system / light / dark), evening check (on/off, time). Phase 2 adds backup export/import.

### 8.6 Moments and copy

- **Log**: small check animation + light haptic.
- **Level up**: a short celebratory sheet ("Level 3: 18 min a day").
- **After a miss**: kind copy, with the *why* when set: "Missed yesterday, but today keeps your streak alive. Remember: so I finally finish the books I buy."
- **Cut-down slip** (logging a +1): shows the *why*, gently.
- **Finish**: §5.6.

## 9. Data model (phase 1)

Tables (names indicative):

- `habits`: id (UUID), name, emoji, kind, measure, period, week_start, why, identity, created_on, status (`active` · `completed` · `archived`), sort_order.
- `habit_revisions`: id, habit_id, effective_from (date), final_goal, start_percent, baseline, limit, target, final_total, endless.
- `reminders`: habit_id, enabled, time, days_mask, when_where.
- `logs`: id (UUID), habit_id, date (local `YYYY-MM-DD`), value (integer), created_at.
- `decisions`: id, habit_id, type (`level_up_goal` · `keep_guarding` · `completed` · `archived` · `restored`), at, payload.
- `settings`: key/value.

Requirements this sets up for later phases:
- **History is never pruned.** Deleting a *log* is a user edit; deleting a *habit* is explicit and confirmed. Archiving keeps everything. (Needed for the annual recap.)
- **UUIDs and a schema version** so a phase 2 backup file (habits + revisions + reminders + logs + decisions + settings, as versioned JSON) imports cleanly into any later version.
- Habit settings (without history) must be serializable on their own, for phase 3 QR sharing.

## 10. Quality bar

- The rules engine is isolated (no React/Expo/DB imports) and has thorough unit tests: every ladder and rounding rule, each miss-rule transition, warm-up, backfill changing past results, revisions, finish detection, fixed totals with overflow, week-start variations, and month lengths.
- Screen-level tests for the key flows: create habit, log, backfill, finish choice.
- TypeScript strict mode, lint and format enforced, CI on every push.

## 11. Approaches considered (for the rules engine)

| | Approach | Trade-off | Outcome |
|---|---|---|---|
| **A** | Recompute all state from settings + logs with a pure engine | Correct by construction for backfill, edits, and closed-app periods; highly testable; recomputes on load (cheap) | **Chosen by the author** |
| B | Store current level/streak and update incrementally | Simple reads, but backfill and closed-app periods need fragile catch-up logic; state can drift from the logs | Rejected |
| C | A plus a persisted per-period cache | Faster in theory, more complexity than needed | Deferred; easy upgrade from A |

## 12. Left to the builder

- Project folder structure and component breakdown.
- Exact palette, typography, spacing, icons, and animation details within the Calm journal direction.
- Test tooling beyond Jest/RNTL (e.g. property-based tests, E2E with Maestro).
- How notification scheduling is kept in sync with logs and settings.
- Exact copy, within the tone rules in §2 and §8.6.
- Empty states and onboarding (keep them minimal; the create form's preview carries most of the explanation).
