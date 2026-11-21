# ShelfLife demo video: transcript

Video: `team_hari_demo_video.mp4` · length 4:36.6 · 1920×866, 30 fps.

The video has no spoken audio (the audio track is silent), so this is a narration transcript of what happens on screen: the ShelfLife guided walkthrough, all 26 steps. Times come from scene-change detection on the video, so each line starts when its step appears. The matching subtitle files (`team_hari_demo_video.srt`, `team_hari_demo_video.vtt`) carry the same text and timings for any video player.

| Time | Section | On screen | Narration |
|---|---|---|---|
| 0:00.0–0:06.4 | Opening | The ShelfLife home page, “Check an answer”, scrolled from top to bottom; then “Replay tour” is clicked (0:05.5). | This is ShelfLife, which checks whether the claims in an AI answer are still true. Let's start the guided tour. |
| 0:06.4–0:15.3 | Step 1 · Welcome to ShelfLife | The tour's welcome card on the Check page. | AI answers state prices, versions and office holders with full confidence, even after they change. This tour walks through the whole system on its own. |
| 0:15.3–0:23.5 | Step 2 · Everything in three groups | The sidebar is highlighted. | The sidebar groups everything: verify answers and compare apps, keep them fresh downstream, and see the results in the dashboard. |
| 0:23.5–0:32.7 | Step 3 · Start with any AI answer | The “Release notes” example fills the answer box. | Here's an assistant's answer about the latest Orion release, and which versions are unsupported. Paste from any model, use the bookmarklet, or call the API. |
| 0:32.7–0:43.3 | Step 4 · Freshness policies | The Freshness policy picker is highlighted. | Different apps need different shelf lives. A freshness policy sets how fast evidence ages and what holds an answer back. |
| 0:43.3–0:46.1 | Step 5 · Every claim checked against live sources | “Check freshness” is clicked and the results load. | Now we run the check. |
| 0:46.1–0:56.2 | Step 5 · Every claim checked against live sources | Results: three claims, each with a verdict and a score. | The answer is split into self-contained claims. Each one is searched, every source's stance is judged with a verified quote, and the freshness score is calculated in code. |
| 0:56.2–1:05.7 | Step 6 · A score, and advice for the app | The answer scores 1 out of 100, with “hold this answer back”. | The answer scores 1 out of 100, and apps get clear advice: show it, warn, or hold it back. Here, hold it back. |
| 1:05.7–1:07.1 | Step 7 · Details that ride on a changed value | The release-date claim is selected. | Look at the release date. |
| 1:07.1–1:18.0 | Step 7 · Details that ride on a changed value | The claim panel shows it was re-checked as “Orion 4.4 was launched on March 4, 2025”. | On its own, “Orion 4.2 was launched on March 4, 2025” is true forever. But it describes the latest release, so ShelfLife re-checked the date for 4.4 and found October 11, 2026. |
| 1:18.0–1:29.2 | Step 8 · One consistent correction | The Corrected answer tab shows the changes as a diff, with sources. | The corrected answer changes the version and its date together, each with a source, and adds 3.x to the unsupported versions. Everything else stays word for word. |
| 1:29.2–1:32.7 | Step 9 · Every claim on its own timeline | The “Timeline question” example is checked. | Next, an answer about June 2025. |
| 1:32.7–1:44.8 | Step 9 · Every claim on its own timeline | “Correct for its time” and “Wrong for its time” verdicts, “As of June 2025”. | Each claim is judged on its own timeline. “In June 2025 the latest release was 4.2” is correct for its time, while a June 2025 price that was wrong even then is corrected for that time. |
| 1:44.8–1:48.4 | Step 10 · Answers build on facts | The “Cloud recommendation” example is checked and the Dependencies tab opens. | Now a cloud hosting recommendation. |
| 1:48.4–1:58.4 | Step 10 · Answers build on facts | The Dependencies tab: the recommendation and the claims it rests on. | It rests on two prices, a calculated total, a hidden seat-limit assumption and an API call. When a price changes, the total is recalculated and the advice is re-judged. |
| 1:58.4–2:00.9 | Step 11 · Link rot | The Links tab opens and the sources are checked. | Sources go away too. |
| 2:00.9–2:07.8 | Step 11 · Link rot | Each source link with its status. | ShelfLife revisits every page it relied on and flags pages that moved, were deleted, or no longer contain the quote. |
| 2:07.8–2:15.7 | Step 12 · Every model call through Bifrost | Run metrics: calls, tokens, cost and cache hits per stage. | Every model call goes through Bifrost, with fallbacks, caching and a budget. Calls, tokens, cost and cache hits are shown for each stage. |
| 2:15.7–2:17.2 | Step 13 · Downstream impact | The Impact page opens. | On to downstream impact. |
| 2:17.2–2:27.2 | Step 13 · Downstream impact | Stale claims ranked by blast radius, such as $20 → $28 per seat. | A stale fact rarely stays in one answer. The old $20 price was also used in a proposal, a budget and an email. Each stale claim is traced to everything built on it. |
| 2:27.2–2:36.9 | Step 14 · Affected documents, corrected | A registered document with its linked claims. | Every affected document gets a corrected version with sources: prices replaced, totals recalculated and advice re-judged. Apply it yourself, or let Autopilot do it. |
| 2:36.9–2:47.5 | Step 15 · The dependency freshness graph | The Dependency graph page: claims and documents, coloured by verdict. | The dependency graph shows every claim, what it relies on, and the documents built on it, across all answers. Dashed lines are declared dependencies. |
| 2:47.5–2:54.2 | Step 16 · Blast radius | A load-bearing claim is selected and everything downstream of it lights up. | Select a load-bearing claim, and everything downstream of it lights up: what may be wrong if it changes. |
| 2:54.2–3:04.4 | Step 17 · Policies per app | The Policies page with its presets. | Policies come as presets for developer assistants, production APIs, business intelligence and research, or save your own. |
| 3:04.4–3:10.8 | Step 18 · Manual or fully autonomous | The Autopilot page, still in Manual mode. | In manual mode checks run when you ask. In auto mode, ShelfLife runs end to end on its own. |
| 3:10.8–3:14.4 | Step 19 · Autopilot at work | Auto mode is switched on and a cycle starts. | Let's switch on auto mode. |
| 3:14.4–3:26.3 | Step 19 · Autopilot at work | The activity log fills with the agent's actions. | Autopilot re-verifies due claims, revisits sources, verifies new documents, traces newly stale claims, corrects the documents built on them and runs regression tests. Every action is logged. |
| 3:26.3–3:33.2 | Step 20 · Always one click away | The Manual/Auto switch at the bottom of the sidebar is highlighted. | The same switch sits at the bottom of the sidebar on every page. |
| 3:33.2–3:37.0 | Step 21 · Compare AI apps | The Compare page loads an example and runs it. | Now let's compare AI apps. |
| 3:37.0–3:45.9 | Step 21 · Compare AI apps | Three assistants' answers about Acme Vault, side by side with verdicts. | Three assistants gave different numbers for the same question. Every version is judged against the same sources, so you see which app is current. |
| 3:45.9–3:52.1 | Step 22 · Dashboard | The Dashboard: totals, checks per day, verdicts by kind of fact. | The dashboard shows checks over time, verdicts by kind of fact, answers held back and usage. |
| 3:52.1–4:00.1 | Step 23 · Verification passports | The Claims page lists every claim checked. | Every claim gets a verification passport: a stable ID and a record of every check, its sources and how its verdict changed. |
| 4:00.1–4:07.2 | Step 24 · Monitors | The Monitors page with a regression test. | Monitors cover regression tests that re-ask a model, link checks, batch checks and context profiles. |
| 4:07.2–4:18.4 | Step 25 · Plugs into any agent | The System page: integrations (MCP, answer guard, webhook). | ShelfLife plugs into any agent. It's a tool server over MCP, a guard in front of any app's answers, a webhook source, and an autonomous agent of its own. |
| 4:18.4–4:27.1 | Step 26 · That's ShelfLife | The tour's closing card on the Check page. | That's ShelfLife: find what went stale, fix it consistently, follow it downstream, and keep everything fresh on its own. |
| 4:27.1–4:36.6 | Closing | The tour closes; the Check page is ready for a new answer. | Thanks for watching. |
