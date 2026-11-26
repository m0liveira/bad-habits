# Bad Habits — Design System (Master)

> **How to use:** before building a screen, check `design-system/bad-habits/pages/<screen>.md`.
> If it exists, its rules override this file. Otherwise follow this file.
> Source spec: `docs/superpowers/specs/2026-11-26-bad-habits-design.md` (§2, §8). Where this file and the spec disagree, the spec wins.

**Direction:** Calm journal: paper tones, serif titles, muted green, system sans for small text. Light and dark themes (follow the system or a setting).
**Stack:** React Native (Expo, TypeScript). Tokens live in `tokens.json`. Components read semantic tokens through a theme hook and never use raw hex.
**Dials:** Variance 3 (centered, minimal) · Motion 3 (subtle) · Density 3 (spacious)

## Provenance

Generated with UI/UX Pro Max (`--design-system`, query "habit tracker journal calm wellness mobile", product match **Habit Tracker**), then fitted to the spec by hand. Kept from the generated output: the Lora serif for headings, a warm paper background, green for "done" and amber for streak/behind, and the accessibility and touch rules. Changed:

| Generated | Changed to | Why |
|---|---|---|
| Amber primary `#D97706`, green accent | Muted green primary; amber only means "behind pace" | Spec §8: muted green; spec §8.1: amber means behind |
| Raleway body font | System sans (Roboto / SF Pro) | Spec §8: system sans for small text; no extra font to load |
| "Avoid: muted colors, low energy" | Removed | Contradicts Calm journal. Energy comes from moments (§8.6), not saturation |
| Web rules (hover, `cursor:pointer`, GSAP scroll reveal, landing-page pattern, 375–1440px breakpoints) | Replaced with native touch, Reanimated, and safe-area rules | Mobile-only RN app |
| Light palette only | Light and dark palettes, each checked for contrast | Spec §8: system/light/dark |
| Drop shadows on cards | Hairline borders on paper; elevation only on sheets | Paper look |
| 24px standard padding | 16 / 20 / 24 scale tuned for phone screens | Generated spacing was sized for web hero layouts |

Search coverage: `--domain color`, `typography`, `style`, `ux` (touch, contrast, reduced motion, forms, progress, confirmation) and `--stack react-native` (touch, a11y, lists, animation, feedback, loading). The React Native searches for **dark mode** and **safe area** returned nothing, even after a narrower retry. Those rules come from the skill's `references/pro-rules.md`.

---

## 1. Color tokens

Semantic names only. Every pair below was checked against WCAG 2.x: text needs ≥ 4.5:1, bars/dots/ticks need ≥ 3:1.

| Token | Light | Dark | Use | Contrast (light / dark) |
|---|---|---|---|---|
| `bg` | `#F6F1E7` | `#191815` | Screen background (paper) | — |
| `surface` | `#FBF8F2` | `#23211D` | Cards, sheets, inputs | — |
| `surfaceSunken` | `#EDE6D8` | `#2D2A25` | Segmented controls, calendar day background, preview box | — |
| `border` | `#DDD3C1` | `#3B372F` | Hairline card/input borders, dividers | 1.4 / 1.36 on surface |
| `ink` | `#2B2722` | `#EDE7DA` | Primary text, titles | 14.0 / 13.0 on surface |
| `inkMuted` | `#625A4E` | `#ABA392` | Secondary text, labels, captions | 6.4 / 6.4 on surface |
| `primary` | `#3F6B4C` | `#8FB998` | On-pace bar fill, done state, primary buttons, links, focus ring | 5.8 / 7.3 on surface |
| `onPrimary` | `#FFFFFF` | `#14221A` | Text/icons on `primary` | 6.1 / 7.5 |
| `primarySoft` | `#DCE7DA` | `#2B3B30` | Done-button background, current-level chip, hit-day fill | primary on it 4.8 / 5.4 |
| `track` | `#E6DFD1` | `#36322B` | Empty part of progress bars | primary fill 4.6 / 5.8 |
| `behind` | `#A06C18` | `#D6A24A` | Bar fill when behind pace (non-text) | 3.4 / 5.5 on track |
| `behindText` | `#865A12` | `#E0B160` | "Behind pace" text | 5.7 / 8.1 on surface |
| `miss` | `#A0644E` | `#CB8D76` | Miss markers (hollow ring), cut-down over-limit fill. Soft clay, never alarm red. | 4.47 / 5.8 on surface |
| `danger` | `#A63A2B` | `#E37E6C` | **Only** destructive actions (Delete habit, delete log) | 6.1 / 5.7 on surface |
| `scrim` | `rgba(27,24,20,0.45)` | `rgba(0,0,0,0.6)` | Behind sheets and dialogs | — |

Rules:
- State is never shown by color alone. Pace has a tick mark plus text ("on pace 2"). Calendar states have distinct shapes (§5). Done shows a ✓ glyph.
- No pure `#000` / `#FFF` backgrounds. No gradients or glass effects.
- The dark theme is its own palette, not an inverted light one. Re-check contrast whenever a token changes (the script is in §9).
- Habit emoji are user content, so they're fine on cards. Structural icons (tabs, add, back, edit) use one vector set: **Lucide** (`lucide-react-native`), 1.75 stroke, 24dp.

## 2. Typography

| Role | Font | Size / line height (dp) | Weight | Use |
|---|---|---|---|---|
| `display` | Lora | 30 / 38 | 600 | Screen titles ("My habits"), finish screen headline |
| `title` | Lora | 22 / 30 | 600 | Detail header, sheet titles, level-up headline |
| `heading` | Lora | 18 / 26 | 500 | Card habit name, section titles in Detail |
| `why` | Lora *italic* | 17 / 26 | 400 | The habit's *why* and identity line |
| `body` | System | 16 / 24 | 400 | Body text, inputs (16 minimum, so iOS doesn't zoom) |
| `label` | System | 14 / 20 | 500 | Card meta ("1/3 · on pace 2"), form labels, buttons |
| `overline` | System | 12 / 16 | 600, +0.8 letter spacing, uppercase | Section headers (TODAY, THIS WEEK) |
| `caption` | System | 13 / 18 | 400 | Helper text, calendar footnotes. Never below 12. |

- Load Lora with `@expo-google-fonts/lora` (400, 400 italic, 500, 600). The font files ship inside the app bundle, so there are no network calls (spec §2). Keep the splash screen up until fonts are loaded so text never flashes in another font.
- All numbers (totals, pace, counters, money) use `fontVariant: ['tabular-nums']` so digits don't shift width when values change.
- Respect OS font scaling (`allowFontScaling` on). Cap at `maxFontSizeMultiplier = 1.6` on dense card rows only, and check layouts at 1.3×.
- Serif is for titles and the *why* only. All controls, numbers, and small text use system sans.

## 3. Spacing, radius, elevation

4dp base grid.

| Token | dp | Use |
|---|---|---|
| `xs` | 4 | Icon to text gap, bar to meta gap |
| `sm` | 8 | Minimum gap between touch targets, chip padding |
| `md` | 12 | Card internal row gap |
| `lg` | 16 | Card padding, gap between cards |
| `xl` | 20 | Screen horizontal padding |
| `2xl` | 24 | Space between sections |
| `3xl` | 32 | Space above section titles in Detail, sheet top padding |
| `4xl` | 48 | Finish / empty-state vertical breathing room |

| Radius | dp | Use |
|---|---|---|
| `sm` | 8 | Inputs, segmented control items, calendar cells |
| `md` | 14 | Cards, preview box |
| `lg` | 20 | Bottom sheets (top corners) |
| `pill` | 999 | Chips, quick-log button, progress bars |

Elevation: cards are flat (`surface` plus a 1dp `border`). Only bottom sheets and dialogs get elevation (Android `elevation: 8`; iOS shadow `0 8 24 rgba(0,0,0,0.12)`).

## 4. Layout and interaction rules

- **Touch targets:** 48×48dp minimum on Android, 44×44pt on iOS. Use 48 everywhere. Leave ≥ 8dp between targets. Use `hitSlop` on small icons.
- **Pressables:** use `Pressable` with visible feedback: `android_ripple` (color `primarySoft`) on Android, opacity 0.7 on iOS. No hover styles.
- **Safe areas:** use `react-native-safe-area-context` on every screen. The tab bar, sheet footers, and the Save bar sit above the gesture area.
- **Navigation:** bottom tabs **Habits · Completed · Settings** (3 items, Lucide icons plus text labels). Detail and Create/Edit are stack screens with a predictable back. Create/Edit opens as a modal with Cancel/Save.
- **Lists:** Home uses `SectionList` (Today / This week / This month). Use `React.memo` cards and a stable `keyExtractor`.
- **Accessibility:** every interactive element gets an `accessibilityLabel` and `accessibilityRole`. A quick-log button reads like "Log 1 for Gym. 1 of 3 this week." Progress bars use `accessibilityRole="progressbar"` with `accessibilityValue`. Test with TalkBack on the Pixel (the primary device).
- **Loading:** reads are local SQLite and near-instant. Show skeleton cards only if a load passes 300ms, and never show a blank screen.
- **Confirm destructive actions:** confirm before Delete habit. Deleting a log is undoable with a 5s "Undo" snackbar instead of a dialog (less friction).
- **Feedback on success:** every log gives visual confirmation (check animation plus updated numbers) and a light haptic. Never log silently.

## 5. Components

**Habit card (Home)**: `surface`, `md` radius, `lg` padding, 1dp border.
- Row 1: emoji + name (`heading`) on the left; quick-log button on the right (48dp circle, `primarySoft` background, `primary` glyph: ✓ / +1 / +€). When done today: `primary` fill with an `onPrimary` ✓.
- Row 2: progress bar 8dp tall, `pill`. Fill is `primary` when on pace and `behind` when behind. The pace tick is a 2×14dp mark in `ink` at 60% opacity, centered on the bar. A cut-down bar fills up toward the limit and turns `miss` once the limit is passed.
- Row 3: `label` in `inkMuted`. Left: period status ("1/3 · on pace 2"). Right: level tag ("3 of 5 / wk", "€640 of €2,000").
- No *why* on home cards.

**Section header**: `overline` in `inkMuted`, with the period end on the right ("ends Sun").

**Level staircase (Detail)**: horizontal steps that rise left to right (they descend for cut down). Past steps: `primary`. Current step: `primary` with a 2dp `ink` outline and a "You are here" caption. Future steps: `track`. Each step is labeled with its target in `caption`.

**Next-level meter**: a row of dots, one per required good period (wrap after 14). Filled dots = `primary`, empty = `track` ring. Beside it, in `caption`: "1 miss allowed". Never "0 lives left".

**Calendar (Detail)**: 7 columns, cells ≥ 44dp, swipe between months, with month arrows as an accessible alternative to swiping.

| Day state | Visual |
|---|---|
| Hit | `primarySoft` filled cell, `primary` dot |
| Miss | Hollow `miss` ring (no ✕, no red) |
| Level-up | Hit cell plus a small Lucide `chevrons-up` |
| Warm-up / archived / before creation | `inkMuted` number only, 50% opacity |
| Today | 2dp `ink` outline |
| Future | Not tappable, 40% opacity |
| Has logs (weekly/monthly habits) | Small `ink` dot; the week row or month result shows at the row end |

Tapping a day opens a bottom sheet with that day's entries (edit, delete, add for backfill).

**Create/Edit form**: every field has a visible label above it, never placeholder-only. Kind/measure/period use segmented controls. On edit they're shown read-only (`surfaceSunken` background, Lucide `lock` glyph, and the caption "To change this, create a new habit."), not greyed-out controls that look broken. Validate on blur and show errors directly under the field, in kind words. The **Preview** box (`surfaceSunken`, `md` radius) updates live. The implementation-intention sentence appears in the `why` style.

**Bottom sheets** (day entries, amount entry, level-up): `lg` top radius, a drag handle, and the primary action in the thumb zone.

## 6. Motion and haptics

Library: `react-native-reanimated`. Haptics: `expo-haptics`.

| Moment | Motion | Duration | Haptic |
|---|---|---|---|
| Quick log | Button scales 0.92 → 1 (spring), ✓ stroke draws, bar fill animates to its new width with `transform: scaleX` | 180–240ms | `impactAsync(Light)` |
| Undo / delete log | Reverse fill | 150ms | none |
| Level up | Sheet slides up, new step on the staircase fills | 300ms enter / 200ms exit | `notificationAsync(Success)` |
| Finish | Fade-in of journey summary, staircase fills step by step (stagger 60ms) | ≤ 900ms total | `notificationAsync(Success)` |
| Screen transitions | Platform default stack transitions | — | — |

- Exits are faster than enters. Animate `transform` and `opacity` only, never layout width or height.
- **Reduced motion:** with `useReducedMotion()` (Reanimated) or `AccessibilityInfo.isReduceMotionEnabled`, replace all of the above with a 120ms opacity crossfade and jump to the final state. Haptics stay.
- No looping, idle, or attention-seeking animation. No confetti storms; at most one restrained burst on Finish, and none under reduced motion.

## 7. Voice and copy

Kind, specific, and quiet. The *why* appears at the moments people are most likely to give up (spec §8.6).

| Situation | Do | Don't |
|---|---|---|
| After a miss | "Missed yesterday. Today keeps your streak alive. *So I finally finish the books I buy.*" | "You broke your streak!" / "Don't give up!!" |
| Cut-down slip | "Logged. Still well under last month. *Why: I want clear mornings.*" | "Oops, over the limit ❌" |
| Two misses (counter reset) | "Fresh start on this level. One good day gets you going." | "Progress lost." |
| Level drop | "Stepping back to 12 min for now. Small steps still count." | "Demoted." |
| Evening check | "2 habits left today." | "You haven't done your habits yet!" |
| Read-only field | "To change this, create a new habit." | "Not allowed." |

- No exclamation marks except in celebrations. No guilt, no comparisons with other people.
- All strings go through i18n keys (spec §3). Leave room for Portuguese, which runs about 30% longer, so labels can't depend on fixed widths.

## 8. Anti-patterns (do NOT use)

- ❌ Red or alarm styling for misses or slips (`danger` is for Delete only).
- ❌ Showing the *why* on home cards (clutter, spec §8.1).
- ❌ Color-only state: pace, hit/miss, and done always have a shape or text too.
- ❌ Emoji as structural icons (tabs, actions). Habit emoji as user content are fine.
- ❌ Raw hex or ad-hoc font sizes in components. Use tokens.
- ❌ Placeholder-only inputs, or errors shown only at the top of the form.
- ❌ Greyed-out controls with no explanation for read-only fields.
- ❌ Touch targets under 48dp, or packed buttons with less than 8dp between them.
- ❌ Text under 12dp, or gray-on-gray contrast below 4.5:1 in either theme.
- ❌ Pure black or white surfaces, gradients, glassmorphism, heavy drop shadows.
- ❌ Points, badges, leaderboards, streak-freeze shops, or loss-aversion language (spec §2).
- ❌ Notification spam: one reminder per habit, plus at most one evening check.
- ❌ Animating layout properties, looping animations, or ignoring reduced motion.
- ❌ Content under the notch, status bar, or gesture bar.
- ❌ Proportional digits in changing numbers (layout jitter).

## 9. Pre-delivery checklist (per screen)

- [ ] Only semantic tokens are used; the screen is checked in **both** light and dark.
- [ ] Text ≥ 4.5:1 and bars/dots/rings ≥ 3:1 in both themes (`python design-system/bad-habits/contrast.py` after any token change).
- [ ] Every target ≥ 48dp with ≥ 8dp spacing; tested by thumb on the Pixel.
- [ ] Safe areas respected (top, tab bar, sheet footers).
- [ ] `accessibilityLabel`/`Role`/`Value` on all interactive elements and progress bars; TalkBack pass done.
- [ ] Reduced motion tested: final states appear and nothing animates beyond the crossfade.
- [ ] Font scale 1.3× doesn't clip or overlap.
- [ ] Copy follows §7; no shaming words; all strings go through i18n.
- [ ] Lucide icons only, one stroke width.
