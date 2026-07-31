# Kaggle writeup - submission copy

The copy below remains under the competition's 500-word limit. Replace only the
demo placeholder after the final public video is uploaded and tested.

## STILL - Watch first. Reflect later.

Video can carry testimony, doubt, humor, grief, and moral tension - but most AI
systems rush to explain before a story has room to land. That creates two
failures at once: spoilers, and Scripture matched to a title or theme instead of
to what was actually witnessed.

**STILL is a spoiler-safe reflection layer for story-led video.** A viewer adds
a video they have the right to use or a public YouTube story. STILL prepares it
chronologically, then keeps the first watch quiet. A reflection can appear only
after the viewer has genuinely watched the moment that grounds it. Full-story
reflection stays locked until contiguous viewing and a natural ending establish
Story Complete.

The technical design makes that promise enforceable:

- **Gemini is the audiovisual observer.** It receives bounded, chronological
  windows with exact offsets and append-only narrative state. A live 9-window
  run completed on our selected source, including safe resume after an RPM
  pause.
- **Gloo provides Sacred Timing.** Required structured decisions can accept,
  hold, abstain, reject, or remain silent. Our live paid probe returned
  `NO_ECHO` for sensitive real-world footage - evidence that STILL does not
  force a verse where silence is more faithful.
- **YouVersion is the canonical Scripture source.** Only an exact API-retrieved,
  app-licensed passage with version and copyright metadata may be rendered as
  Scripture. A live retrieval through Bible 3034 passed.

The product is a React experience backed by FastAPI, with Firestore-compatible
storage, resumable jobs, model budgets, and provenance for every bounded window.
The public Firebase Spark site is intentionally a credential-free static
showcase; the real provider flow runs locally in the demo and repository because
the production server architecture requires billing. It never simulates a live
backend or places provider keys in the browser.

STILL's immediate wedge is reflective short-form video: testimonies, short
films, youth-group stories, and discussion-led media. Its broader vision is a
new interaction pattern for AI and Scripture: do not interrupt the story, do
not outrun the viewer, and do not speak when silence is more faithful.

**Demo:** [PUBLIC_YOUTUBE_DEMO_URL]

**Public showcase:** <https://still-scriptures.web.app>

**Code:** <https://github.com/PrathmeshAdsod/STILL-Scriptures>
