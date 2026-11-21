# ClearHire Scroll Story: Reference Research

Research captured 2026-11-09 from public pages and source repositories. This is a design study, not a claim of access to private implementation details.

## Detailed public-source findings

### Bruno Simon — spatial agency, not a scroll template

- VERIFIED — Bruno's current public portfolio tells visitors to drive through a 3D world and explicitly identifies Three.js, TSL, WebGL/WebGPU, Rapier physics, Howler audio, and source code/Blender files. The official repository is MIT licensed. Sources: https://bruno-simon.com/ and https://github.com/brunosimon/folio-2025
- VERIFIED — The repository README exposes a staged frame loop: input/time, vehicle and physics, view/environment, interaction points, audio/UI, rendering, and monitoring. Its build notes preserve raw assets and create compressed variants for delivery. Source: https://github.com/brunosimon/folio-2025
- DESIGN INFERENCE — Take the sense that movement controls discovery and that the 3D world owns the experience. ClearHire's linear scroll remains the control because its resume-to-outcome story has a required order; do not add vehicle controls or Bruno's art direction.

### Lusion — Oryzo as the closest scroll-story reference

- VERIFIED — Lusion's official Oryzo behind-the-scenes series describes Oryzo as a linear scrolling web experience. Lusion's stated principles include a believable setting, product-centred framing, seamless transitions, and restrained UI. Sources: https://blog.lusion.co/oryzo-bts-part-1-7-concept-and-creative-direction and https://blog.lusion.co/oryzo-bts-part-3-7-website-ux-ui-and-illustrations
- VERIFIED — Lusion reports using Gaussian splats selectively for Oryzo props and desk reflections: about 78,233 splats on desktop and 44,683 on mobile. The full-scene test at roughly 900,000 splats still showed defects in fine wood detail, so the rest used conventional texture mapping with simplified geometry. The team also found hemispherical/spherical camera samples gave better coverage than rendering the exact eased scroll spline. Source: https://blog.lusion.co/oryzo-bts-part-2-7-3d-design-and-motion-graphics
- VERIFIED — The official design write-up says the scene should stay central, with fewer typefaces, colours, and competing UI ideas; transitions should feel continuous even when the composition changes. Source: https://blog.lusion.co/oryzo-bts-part-1-7-concept-and-creative-direction
- VERIFIED — Lusion says the source imagery/3D production, rather than generated imagery, defines the final look. This is a useful craft rule for ClearHire: use authored or licensed scene assets and treat procedural work as scene assembly, not as a substitute for asset quality. Source: https://blog.lusion.co/oryzo-bts-part-3-7-website-ux-ui-and-illustrations
- VERIFIED — The Part 3 article lists Parts 4–7 as unchecked future posts, including the promised WebGL/Three.js implementation details. Those later implementation details remain UNREAD. Source: https://blog.lusion.co/oryzo-bts-part-3-7-website-ux-ui-and-illustrations
- DESIGN INFERENCE — A persistent office scene, screen-centred camera move, grounded paper/robot interactions, and quiet caption panels are more relevant to ClearHire than a generic abstract WebGL hero.

### Igloo Inc. — scroll as the navigation system, with an accessibility trade-off

- VERIFIED — The official Webby entry credits Abeto and Bureaux. Source: https://winners.webbyawards.com/2026/websites-and-mobile-sites/features-design/best-visual-design-aesthetic/361001/igloo-inc
- UNREAD — The official Igloo page yielded no readable text to the web research tool; the official Awwwards case-study URL timed out. Detailed rendering claims are therefore not treated as verified from primary sources in this pass.
- SECONDARY REPORT — A public technical write-up describes a scroll-led camera journey, object-based portfolio content, a restrained monochrome material palette, opt-in sound, and staged loading. It also flags that hiding the entire interface in WebGL makes accessibility and navigation weaker. Source: https://rickcreates.com/r/2024-07-23-igloo-inc
- DESIGN INFERENCE — Borrow the object-led story and minimal instrument labels, but keep ClearHire's text, chapter state, buttons, and authentication controls in semantic HTML. ClearHire's visual mood remains a lived-in office, not an ice world.

## Build decisions from the research

1. Keep one persistent scene and let scroll progress drive a composed camera path and object state; avoid resetting the room between chapters.
2. Use the user's office screenshot as a spatial reference, while using independent sourced assets and original ClearHire staging. No full room model was provided, so wall/floor/ceiling remain reconstructed.
3. Keep one small caption and a thin progress cue; remove decorative chapter chrome that competes with the scene. Retain a direct sign-in shortcut and keyboard/touch scroll access.
4. Keep the robot, resume, scanner, printer, and inbox as visible story objects. The sample score is clearly labelled as illustrative, not a real employer ATS decision.
5. Preserve real DOM text and login fields, reduced-motion behavior, staged asset loading, and lower mobile render quality. Essential navigation must remain usable if WebGL fails.
6. Do not claim fidelity to a reference implementation or final resume-to-bin parity until the rendered behavior is visually confirmed at the relevant chapter and viewport.

## Evidence and limits

### Bruno Simon

- VERIFIED — The live portfolio describes the world as something visitors drive through to discover the creator's work. It exposes keyboard, touch, and gamepad controls, plus audio and quality options. Source: https://bruno-simon.com/
- VERIFIED — Bruno's public Folio 2025 repository documents a staged game loop: input and physics first, then player/view, environment systems, interaction points, audio, UI, and rendering. It also describes GLB and texture compression workflows. Source: https://github.com/brunosimon/folio-2025
- DESIGN INFERENCE — ClearHire can borrow the idea that the world itself carries navigation and that user controls remain discoverable. ClearHire should not copy the car, map, world art, or portfolio-specific interactions.

### Lusion

- VERIFIED — Lusion's public site leads with 3D visual storytelling, says “scroll to explore,” and presents featured work as immersive visual experiences. Its About page lists WebGL, interactive design, 3D asset creation, and 3D optimization among its disciplines. Sources: https://lusion.co/ and https://lusion.co/about/
- VERIFIED — The Lusion Labs project is presented as a research and development space for experimenting with technology and interactive 3D. Source: https://lusion.co/projects/lusion_labs/
- UNREAD — The public notes do not expose the exact camera rig, easing values, or full production source. The documented Oryzo workflow is evidence about that project only; it does not prove how Lusion built its other projects.
- DESIGN INFERENCE — Keep the copy short, let the scene change carry the narrative, and make each chapter feel like a deliberate composed shot.

### Igloo Inc.

- VERIFIED — The live page is publicly reachable at https://www.igloo.inc/. The web text extractor returned no readable lines, so its current page text and detailed interaction were UNREAD in this research pass.
- VERIFIED — The official Webby Awards page credits Bureaux and lists Abeto on the Igloo Inc. team. Source: https://winners.webbyawards.com/2026/websites-and-mobile-sites/features-design/best-visual-design-aesthetic/361001/igloo-inc
- SECONDARY REPORT, NOT independently verified — Public case-study summaries describe a scroll-led 3D world that turns brand content into physical objects. The official Awwwards case-study URL did not load through the research tool, so reported technical details such as shader, procedural modeling, or asset compression are not treated as verified facts here.
- DESIGN INFERENCE — Make each story beat tangible in the scene and use restrained instrument-style labels. Keep real controls and the story description in semantic HTML for accessibility; do not move essential login controls into WebGL.

## Application to ClearHire

1. Keep a single office world and make the scroll position drive the camera and the physical resume, robot, scanner, printer, and inbox.
2. Use nine readable beats: office, computer wake, intake, scan, score choice, print-or-bin outcome, HR review, waiting/no update, and sign-in.
3. The user-provided office screenshot remains the visual reference. ClearHire uses its own office scene and assets; it does not copy Bruno's or Igloo's world or branding.
4. Keep the choice at the score chapter interactive, the waiting signal brief, and the final sign-in form in ordinary HTML.
5. Keep the supplied robot asset. It has no embedded animation clips; its flight and hover are scene animations. Do not describe this as original animation embedded in the GLB.
6. The office itself is a procedural reconstruction because no complete room GLB was provided. The workstation, monitor, copier, bookshelf, office chairs, and robot load as GLB assets. The room layout is based on the user's screenshot; it is not a pixel-level copy.
7. The scene honors `prefers-reduced-motion` by snapping camera follow and removing the robot's idle bob. WebGL setup failures leave the story caption and final sign-in form in the DOM. Current evidence does not include a fresh rendered inspection of the final low-score bin contact, mobile framing, or final-stage form layout; those remain UNVERIFIED.

## Sources

- Bruno Simon, live portfolio: https://bruno-simon.com/
- Bruno Simon, public source repository: https://github.com/brunosimon/folio-2025
- Lusion, public site: https://lusion.co/
- Lusion, About: https://lusion.co/about/
- Lusion, Oryzo BTS Part 1 — concept and creative direction: https://blog.lusion.co/oryzo-bts-part-1-7-concept-and-creative-direction
- Lusion, Oryzo BTS Part 2 — 3D design and motion graphics: https://blog.lusion.co/oryzo-bts-part-2-7-3d-design-and-motion-graphics
- Lusion, Oryzo BTS Part 3 — website UX/UI and illustrations: https://blog.lusion.co/oryzo-bts-part-3-7-website-ux-ui-and-illustrations
- Lusion Labs project page: https://lusion.co/projects/lusion_labs/
- Igloo Inc, live site (unread by text extractor): https://www.igloo.inc/
- Webby Awards, Igloo Inc credits: https://winners.webbyawards.com/2026/websites-and-mobile-sites/features-design/best-visual-design-aesthetic/361001/igloo-inc
- Igloo Inc, secondary technical write-up (not primary implementation evidence): https://rickcreates.com/r/2024-07-23-igloo-inc
- Innerscene, office task chair listing: https://www.innerscene.com/tools/library/3d-parts/office-task-chair-with-mesh-back-and-armrests-73dc5abe
- Innerscene asset terms: https://www.innerscene.com/tools/library/terms
- ambientCG, Marble 021 CC0 material listing: https://ambientcg.com/view?id=Marble021
- ambientCG, Carpet 012 CC0 photogrammetry material listing: https://ambientcg.com/view?id=Carpet012
- ambientCG API documentation: https://docs.ambientcg.com/api/v2/full_json/

## Current local verification — 2026-11-09

- VERIFIED — `GET /login` returned HTTP 200 and the ClearHire page title through the local Next.js preview at `http://127.0.0.1:3000/login`.
- VERIFIED — Desktop loads the 3.74 MB desk variant and 0.79 MB monitor variant with WebP base-colour textures, plus the copier (392,352 bytes), bookshelf (1,528,144), supplied robot (608,876), and CC0 office chair (565,744); the six-model payload is 7,629,084 bytes (7.27 MiB), down from 13,299,176 bytes (12.68 MiB) using the original desk and monitor models with the same other assets. The desk/monitor pair alone is 55.6% smaller after texture optimization.
- VERIFIED — Scoped ESLint passed for `ClearHireStoryScene.js`, `login.js`, `auth.js`, and `VirtualScroll.js`.
- VERIFIED — glTF Transform 4.5.1 produced the desk and monitor WebP variants with quality 90, effort 6, and only the `baseColorTexture` slot compressed. Source GLBs remain alongside them; desk normal and metallic/roughness textures were preserved. The local Three.js `GLTFLoader` advertises `EXT_texture_webp` support. Pair savings: 5,670,092 bytes (about 55.6%).
- VERIFIED — `reducedRenderQuality` selects 1K desk and monitor variants on compact viewports or devices reporting 4 GB RAM or less. Their combined payload is 966,088 bytes; the complete six-model mobile payload is 4,061,204 bytes (3.87 MiB), about 69.5% below the original six-model payload. Both mobile variants use textures capped at 1024 px.
- VERIFIED — Local HTTP HEAD checks returned 200 for `/login`, the supplied robot GLB, the new office-chair GLB, and the mobile monitor GLB. This verifies that the preview serves these paths; it does not verify their visual rendering.
- VERIFIED — Local HTTP HEAD checks also returned 200 for all three new Carpet 012 maps and the Marble 021 color map. The dev server reported successful recompilation with no visible compile error.
- CODE CHANGE — `login.js` now queues URL-selected story chapters before `VirtualScroll` initializes and synchronizes controller position, sector, progress, and scrubber. Static inspection supports the fix; deep-link behavior remains runtime-unverified because no browser interaction was performed.
- VERIFIED — The desk finish now loads ambientCG Marble 021 color, OpenGL normal, and roughness maps from local files (1.75 MB combined). `addMarbleDeskTop` gives the stone top its own UV scale and uses a separate pale slab edge material; the generated canvas material remains only as a load-failure fallback. The official ambientCG listing identifies Marble 021 as CC0.
- VERIFIED — The office floor now loads ambientCG Carpet 012 color, OpenGL normal, and roughness maps from local WebP files (1.71 MB combined). The color map is desaturated to match the reference's gray carpet; subtle seam strips and warm accent lines sit above the PBR floor. The official listing identifies Carpet 012 as CC0 photogrammetry.
- VERIFIED — The `/ready` proxy returned HTTP 500 because the frontend dev log showed `ECONNREFUSED 127.0.0.1:8000`; no backend service is listening there, so successful login/registration is unavailable in this preview. Docker was left stopped as requested.
- UNREAD — A fresh headless Edge screenshot was not produced because the isolated GPU process crashed. The existing PNGs dated 2026-11-08 show an earlier five-stage UI, so they are not evidence of the current nine-stage page.
- UNVERIFIED — Current final-stage login geometry, mobile framing, and exact low-score paper/bin contact still need a fresh rendered visual check. Do not claim complete visual parity until those checks are done.

## Current official-source pass — 2026-11-09

- **VERIFIED — Bruno Simon current portfolio:** The official page describes a 3D world that visitors drive through; its extracted page lists keyboard, touch, and gamepad controls, plus audio, quality, respawn, reset, and renderer options. The page also exposes “Interact” and “Unstuck” controls. This is page content, not an agent-run interactive session. Source: https://bruno-simon.com/
- **VERIFIED — Bruno Simon public source:** The Folio 2025 repository is public and MIT-licensed. Its README documents a staged game loop and a compression step that writes optimized model/texture variants while preserving originals. Source: https://github.com/brunosimon/folio-2025
- **VERIFIED — Lusion current positioning:** Lusion’s homepage calls its work 3D visual storytelling and interactive web experiences, and invites visitors to scroll. The Oryzo case page lists WebGL and animation among its services. Sources: https://lusion.co/ and https://lusion.co/projects/oryzo_ai/
- **VERIFIED — Lusion Oryzo production notes:** Part 1 says visual continuity and keeping the product central mattered more than isolated flashy sections. Part 2 describes a desk-led hero scene, tests of images/video and real-time PBR, and a selective Gaussian-splat + texture-mapping solution after the full-scene splat test showed detail flaws. Sources: https://blog.lusion.co/oryzo-bts-part-1-7-concept-and-creative-direction and https://blog.lusion.co/oryzo-bts-part-2-7-3d-design-and-motion-graphics
- **UNREAD — Igloo live interactions:** The official page returned no readable lines to the public web extractor, so this pass does not claim its camera path, controls, or rendering implementation. Source: https://www.igloo.inc/
- **INFERRED — ClearHire design application:** Keep one authored office world and use scroll to move attention through one continuous application journey. Keep interaction and sign-in in semantic HTML; use the monitor itself for intake/score states so the visuals carry the explanation. Treat any score as an illustrative demo value, not a real employer ATS decision.
- **INFERRED — visual production limit:** Oryzo’s public notes emphasize authored assets and a hybrid approach. ClearHire has no full office-room GLB, so it currently uses sourced GLB furniture plus reconstructed room geometry. This is a constrained reconstruction; it cannot prove or promise pixel-level replication of the supplied room screenshot.
- **CURRENT BUILD EVIDENCE:** `frontend/src/components/ClearHireStoryScene.js` now has monitor states for workstation boot, sample resume parsing, the high/low illustrative score, and waiting inbox. Camera and paper follow use time-based damping; the supplied robot follows a curved flight path and hovers above the scanner. Four office task chair instances use clones of the sourced CC0 GLB, with only the seat and back upholstery tinted red. The desks use CC0 Marble 021 color, roughness, and normal maps with independent slab-edge material; the floor uses CC0 Carpet 012 photogrammetry maps, fine tile seams, and warm accent lines. `frontend/src/lib/VirtualScroll.js` applies time-based scroll damping.
- **RUNTIME LIMIT:** Local `/login` and required GLB paths returned HTTP 200; scoped ESLint passed after the latest change. No browser-use interaction was performed. The current final-stage, low-score bin contact, and mobile composition still need human visual review.

