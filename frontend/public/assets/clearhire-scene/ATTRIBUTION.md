# 3D scene assets

These models are bundled locally so the ClearHire story does not depend on cross-origin model loading.

- `office-copier.glb` — “Copy Tower - Office Copier”, Innerscene library. The listing identifies the asset as CC0/public domain. Source: https://www.innerscene.com/tools/library/3d-parts/copy-tower-office-copier-c07038f9
- `steel-office-desk.glb` — “Steel office desk”, Ulan Cabanilla / Poly Haven. The listing identifies the asset as CC0. Source: https://www.innerscene.com/tools/library/3d-parts/steel-office-desk-16158a62
- `desktop-monitor.glb` — “Desktop Monitor 27 inch, Height Adjustable Stand”, Innerscene library. The listing identifies the asset as CC0. Source: https://www.innerscene.com/tools/library/3d-parts/desktop-monitor-27-inch-height-adjustable-stand-1fbbebd1
- `filled-bookshelf.glb` — “Filled bookshelf large - Original Interior Furnishing”, Innerscene library. The listing identifies the 1.5 × 0.32 × 2.1 m model as CC0/public domain. Source: https://www.innerscene.com/tools/library/3d-parts/filled-bookshelf-large-original-interior-furnishing-584afc77
- `office-task-chair.glb` — “Office task chair with mesh back and armrests”, Innerscene library. The listing identifies the textured, real-scale GLB as CC0/public domain. Source: https://www.innerscene.com/tools/library/3d-parts/office-task-chair-with-mesh-back-and-armrests-73dc5abe
- `office-art-01.jpg` — Canvas color texture from Poly Haven’s “Fancy Picture Frame 01”, CC0. Source: https://polyhaven.com/a/fancy_picture_frame_01
- `office-art-02.jpg` — Canvas color texture from Poly Haven’s “Fancy Picture Frame 02”, CC0. Source: https://polyhaven.com/a/fancy_picture_frame_02
- `marble-021-color.jpg`, `marble-021-normal-gl.jpg`, and `marble-021-roughness.jpg` — 1K color, OpenGL normal, and roughness maps from ambientCG “Marble 021”. The official listing identifies the material as CC0. Source: https://ambientcg.com/view?id=Marble021
- `carpet-012-color.webp`, `carpet-012-normalgl.webp`, and `carpet-012-roughness.webp` — color, OpenGL normal, and roughness maps extracted from `Carpet012_1K-JPG.zip`; encoded as WebP with Sharp quality 95 / effort 6. The color map was converted to grayscale to match the reference office. The official listing identifies the photogrammetry material as CC0. Sources: https://ambientcg.com/view?id=Carpet012 and https://ambientcg.com/get?file=Carpet012_1K-JPG.zip
- `robot.glb` — supplied by the project owner from their local Downloads folder. The file has no animation clips; the fly-in and hover are driven by ClearHire's scene code. The upstream creator and license are not included in the file metadata available to this project, so no redistribution license is claimed for this model.
- `robot_playground.glb` — the earlier project-owner-supplied robot asset is retained in the folder but is no longer loaded by the scene. Its upstream creator and license are unknown.
- Poly Haven license: https://polyhaven.com/license

The office room is a procedural 3D reconstruction based on the owner's reference screenshot; the screenshot itself is not used as a background texture. The resume sheet and scanner light are made in the scene code for this fictional demonstration. They contain no real candidate data and are not connected to an employer system.

- `optimized/steel-office-desk.webp.glb` and `optimized/desktop-monitor.webp.glb` — delivery variants generated from the adjacent original CC0 assets with glTF Transform 4.5.1; only base-colour textures use WebP (quality 90, effort 6). Original GLBs remain unchanged, and normal/metallic texture data is retained. The Three.js GLTFLoader bundled with this project supports `EXT_texture_webp`.
- `optimized/mobile/*.mobile-1k.webp.glb` — low-memory delivery variants generated from the original desk and monitor GLBs with glTF Transform 4.5.1. All embedded textures are resized to a 1024 px maximum with Lanczos3; base-colour textures are then encoded as WebP (quality 90, effort 6). Original 2K and source files remain unchanged.

## SHA-256 delivery manifest

Optimized variants were generated with glTF Transform 4.5.1 using WebP quality 90 / effort 6 for `baseColorTexture` only. Original source files are retained.

| File | Bytes | SHA-256 |
|---|---:|---|
| `steel-office-desk.glb` | 5,239,512 | `E65D26E0F4499545751674FEF59EAAA5DB7B8DC94093C538D2344661CE01363F` |
| `optimized/steel-office-desk.webp.glb` | 3,741,256 | `561D641CD6FB22E37DC5177F2474CBD74FC1AFCE4802A1B76D773D30132CF2EB` |
| `desktop-monitor.glb` | 4,964,548 | `E385213FD3F2FE8C0A9C2DD2238C674426BAA1396110A4475C90F38009E4AA11` |
| `optimized/desktop-monitor.webp.glb` | 792,712 | `3641FF8E8FD01D5A13C686C81C99643483BC8635A61431155BFDD7EE88B52885` |
| `optimized/mobile/steel-office-desk.mobile-1k.webp.glb` | 627,340 | `3E6B0F25CE540D251BAD2095FCBDFD0F9977B1ED03F660F7E30D79436A00747F` |
| `optimized/mobile/desktop-monitor.mobile-1k.webp.glb` | 338,748 | `45A8E8676FF8DD915E84FC27D54BFFA92AF48DE596F43EA59212CA0A931F9009` |
| `office-task-chair.glb` | 565,744 | `F2B784DC49637022D0000BFB82C622CBCCF3294EE96ED6F8D3EEAB0240F64DAF` |
| `office-copier.glb` | 392,352 | `470263BA7BDE037125C8F0BCF9A34C15E795D014D0B66C6B295551D1921A4C5F` |
| `filled-bookshelf.glb` | 1,528,144 | `497B0D7BD1CD5D5AC2FA16418C10AF0CF5438AE8A64321A3EC2B2C485639335F` |
| `robot.glb` | 608,876 | `D4557C0215E956ABFC324BBD6687BE7CE81412FE808D883826EC541654A85AD9` |
| `robot_playground.glb` | 8,691,428 | `83E190FD94316F66B788D8943C4A6B445CBE530104761F89034B6BEFD9627E0C` |
| `marble-021-color.jpg` | 1,067,026 | `3D3F3B3DD4730B22AEB72CC10BA34A658FB58282FC64E9E867BD67382C98A777` |
| `marble-021-normal-gl.jpg` | 339,360 | `4E5FB0ADB06F81707C4CB3AEBF67BDE399E0C2098EE2E03D0F2745A24AF3B728` |
| `marble-021-roughness.jpg` | 348,218 | `5A20D923F9F048FA88FFB445038CCA0C7973CBE0A88BFD8822E7D10348F1E1FB` |
| `carpet-012-color.webp` | 598,884 | `9DDB9151E8C9005CE56CCBB4A386B19458986D53D73066EC8F7935B2A9FE2E3A` |
| `carpet-012-normalgl.webp` | 804,350 | `6F7A2C10F5FEC92DA501683ACF232614252FA77A4548F3A0644622CF21E1FED7` |
| `carpet-012-roughness.webp` | 305,812 | `D6D54B26E8EDB75827567BEBE8B3541395049D705C3D3907F6412AE2E100E041` |
