# Kaggle writeup - submission copy

Replace the demo placeholder after the final public video is uploaded and
tested. The copy below is under the competition's 500-word limit.

## STILL - Watch first. Reflect later.

Video can carry testimony, doubt, humor, grief, and moral tension, but most AI
systems rush to explain before a story has room to land. That creates spoilers
and connections based on titles instead of what was actually witnessed.

**STILL is a spoiler-safe reflection layer for story-led video.** A viewer adds
a public or unlisted YouTube story up to six minutes. STILL prepares it in
chronological audiovisual windows, then keeps the first watch quiet. A
reflection appears only after the viewer has genuinely watched the moment that
grounds it. Full-story reflection remains locked until contiguous viewing and a
natural ending establish Story Complete.

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

The Free plan offers one six-minute analysis. A private competition Access Pass
allows two analyses per UTC day. Payments are not integrated in this release.
Hard server-side limits, a one-at-a-time queue, one Cloud Run instance at most,
and one paid Gloo candidate per project protect the live service from abuse.

STILL's initial audience is testimonies, short films, youth groups, and
discussion-led media. Its broader interaction principle is simple: do not
interrupt the story, do not outrun the viewer, and do not speak when silence is
more faithful.

**Demo:** [PUBLIC_YOUTUBE_DEMO_URL]

**Public app:** <https://still-scriptures.web.app>

**Code:** <https://github.com/PrathmeshAdsod/STILL-Scriptures>
