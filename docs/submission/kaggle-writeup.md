# Kaggle writeup - submission copy

Replace the demo placeholder after the final public video is uploaded and
tested. The copy below is under the competition's 500-word limit.

## STILL - Watch first. Reflect later.

Video can carry testimony, doubt, humor, grief, and moral tension, but most AI
systems rush to explain before a story has room to land. That creates spoilers
and connections based on titles instead of what was actually witnessed.

**STILL is spoiler-safe Scripture reflection for story-led video.** A viewer adds
a public or unlisted YouTube story up to six minutes. STILL prepares it in
chronological audiovisual windows, then keeps the video primary. Each accepted
reflection appears automatically only after the viewer has genuinely watched
the moment that grounds it. The viewer chooses when to open the scene context,
exact passage, attribution, and connection. Full-story review remains locked
until contiguous viewing and a natural ending establish Story Complete.

The technical design makes that promise enforceable:

- **Gemini observes.** It receives bounded windows with exact offsets and
  append-only narrative state, so earlier moments never receive future
  knowledge.
- **Gloo decides Sacred Timing.** Structured decisions may accept, hold,
  reject, or remain silent. `NO_ECHO` is a successful safe outcome when a
  connection would be superficial or disproportionate.
- **YouVersion is canonical.** Only exact API-retrieved, app-licensed text with
  version and copyright metadata may be rendered as Scripture.

The production React application uses Firebase email authentication, FastAPI,
Firestore, Cloud Tasks, Cloud Run, Secret Manager, resumable jobs, model
budgets, and per-window provenance. It processes arbitrary supported videos;
it is not a prepared sample. The entrant's 5:58 test source completed all 9/9
full audiovisual windows through the hosted API in about 84 seconds and ended
honestly as `READY_NO_ECHO`.

For the final demo, Dogs Inc's 4:05 “Pip” completed 7/7 hosted windows and
produced two verified BSB reflections: Hebrews 12:1 at 2:00 and Hebrews 13:16
at 3:20. Production tests confirmed that they unlock 0 → 1 → 2 as the watched
frontier reaches those moments.

Each account also has a private My Videos library. Completed analyses and watch
progress persist across devices, and pasting the same YouTube link reopens the
stored result instead of paying to process it again.

The Free plan offers one six-minute analysis. A private Access Pass supports
bounded judge testing; payments are not integrated. Hard server-side limits, a
one-at-a-time queue, one Cloud Run instance at most, and three Gloo candidates
per project protect the live service from abuse.

STILL's initial audience is testimonies, short films, youth groups, and
discussion-led media. Its broader interaction principle is simple: do not
interrupt the story, do not outrun the viewer, and do not speak when silence is
more faithful.

**Demo:** [PUBLIC_YOUTUBE_DEMO_URL]

**Public app:** <https://still-scriptures.web.app>

**Code:** <https://github.com/PrathmeshAdsod/STILL-Scriptures>
