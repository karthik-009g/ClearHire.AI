import { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

/**
 * ============================================================================
 * CINEMATIC LENS POST-PROCESSING SHADER
 * 35mm Film Grain dither, Anamorphic Vignette, Peripheral Chromatic Aberration
 * Eliminates 8-bit banding and gives Lusion's signature filmic richness.
 * ============================================================================
 */
const CinematicLensShader = {
  name: "CinematicLensShader",
  uniforms: {
    tDiffuse: { value: null },
    uTime: { value: 0 },
    uGrainAmount: { value: 0.007 },
    uVignetteDarkness: { value: 0.35 },
    uChromaticOffset: { value: 0.0008 },
  },
  vertexShader: `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    uniform sampler2D tDiffuse;
    uniform float uTime;
    uniform float uGrainAmount;
    uniform float uVignetteDarkness;
    uniform float uChromaticOffset;
    varying vec2 vUv;

    void main() {
      vec2 dir = vUv - 0.5;
      float dist = length(dir);

      // Micro Chromatic Aberration toward periphery
      float offset = dist * uChromaticOffset;
      float r = texture2D(tDiffuse, vUv + dir * offset).r;
      float g = texture2D(tDiffuse, vUv).g;
      float b = texture2D(tDiffuse, vUv - dir * offset).b;
      vec3 color = vec3(r, g, b);

      // Procedural 35mm Film Grain dither
      float noise = fract(sin(dot(vUv + fract(uTime * 1.5), vec2(12.9898, 78.233))) * 43758.5453);
      color += (noise - 0.5) * uGrainAmount;

      // Anamorphic Vignette falloff
      float vignette = smoothstep(1.75, 0.65, dist * 2.0);
      color *= mix(1.0 - uVignetteDarkness, 1.0, vignette);

      gl_FragColor = vec4(color, 1.0);
    }
  `,
};

/**
 * ============================================================================
 * SECOND-ORDER DYNAMICS PHYSICS ENGINE
 * Natural Frequency f=1.35, Damping Ratio z=0.75, Response r=1.5
 * ============================================================================
 */
class SecondOrderDynamics3D {
  constructor(f = 1.35, z = 0.75, r = 1.5, x0 = 0, y0 = 0, z0 = 0) {
    this.f = f;
    this.z = z;
    this.r = r;
    this.computeConstants();

    this.x = x0; this.y = y0; this.z = z0;
    this.xp = x0; this.yp = y0; this.zp = z0;
    this.xd = 0; this.yd = 0; this.zd = 0;
  }

  computeConstants() {
    const f = Math.max(0.001, this.f);
    const z = Math.max(0, this.z);
    const PI = Math.PI;
    this.k1 = z / (PI * f);
    this.k2 = 1 / ((2 * PI * f) * (2 * PI * f));
    this.k3 = (this.r * z) / (2 * PI * f);
  }

  update(dt, tx, ty, tz) {
    if (dt <= 0) return { x: this.x, y: this.y, z: this.z };
    const k2Stable = Math.max(this.k2, 1.1 * ((dt * dt) / 4 + (dt * this.k1) / 2), dt * this.k1);

    const vx = (tx - this.xp) / dt;
    this.xp = tx;
    this.x += dt * this.xd;
    this.xd += (dt * (tx + this.k3 * vx - this.x - this.k1 * this.xd)) / k2Stable;

    const vy = (ty - this.yp) / dt;
    this.yp = ty;
    this.y += dt * this.yd;
    this.yd += (dt * (ty + this.k3 * vy - this.y - this.k1 * this.yd)) / k2Stable;

    const vz = (tz - this.zp) / dt;
    this.zp = tz;
    this.z += dt * this.zd;
    this.zd += (dt * (tz + this.k3 * vz - this.z - this.k1 * this.zd)) / k2Stable;

    return { x: this.x, y: this.y, z: this.z };
  }
}

// 10 Verified Corporate Talent Nodes
const TALENT_NODES = [
  { id: 1, company: "Razorpay", title: "Staff Backend Engineer", ats: "Greenhouse", color: 0x5369d9, angle: 0 },
  { id: 2, company: "Postman", title: "Lead Systems Architect", ats: "Ashby", color: 0xbd7652, angle: 0.63 },
  { id: 3, company: "CRED", title: "Principal Platform Lead", ats: "Lever", color: 0x5b7f6a, angle: 1.26 },
  { id: 4, company: "Swiggy", title: "Senior AI Infra Engineer", ats: "Workday", color: 0xd6ad69, angle: 1.88 },
  { id: 5, company: "Zepto", title: "Distributed Systems Lead", ats: "Greenhouse", color: 0x5369d9, angle: 2.51 },
  { id: 6, company: "InMobi", title: "AdTech Real-Time Architect", ats: "Ashby", color: 0xbd7652, angle: 3.14 },
  { id: 7, company: "BrowserStack", title: "Cloud Grid Engineer", ats: "Lever", color: 0x5b7f6a, angle: 3.77 },
  { id: 8, company: "Zerodha", title: "High-Frequency Core Dev", ats: "Greenhouse", color: 0x5369d9, angle: 4.40 },
  { id: 9, company: "Groww", title: "Trading Engine Architect", ats: "Ashby", color: 0xbd7652, angle: 5.03 },
  { id: 10, company: "PhonePe", title: "Payment Orchestration Lead", ats: "Workday", color: 0xd6ad69, angle: 5.65 },
];

function createBadgeTexture(company, ats) {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 112;
  const ctx = canvas.getContext("2d");

  // Sleek cyber frosted card
  ctx.fillStyle = "#0c1322";
  ctx.fillRect(0, 0, 256, 112);

  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 3;
  ctx.strokeRect(3, 3, 250, 106);

  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 26px sans-serif";
  ctx.fillText(company, 16, 46);

  ctx.fillStyle = "#38bdf8";
  ctx.font = "bold 15px monospace";
  ctx.fillText("● " + ats + " Direct", 16, 84);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

export default function ClearHireLusionScene({
  progress = 0,
  continuousChapter = 0,
  activeChapter = 0,
  scrollVelocity = 0,
  motionRef = null,
  onSelectNode = () => {},
}) {
  const mountRef = useRef(null);
  const onSelectNodeRef = useRef(onSelectNode);
  const motionRefRef = useRef(motionRef);

  useEffect(() => { onSelectNodeRef.current = onSelectNode; }, [onSelectNode]);
  useEffect(() => { motionRefRef.current = motionRef; }, [motionRef]);

  const progressRef = useRef(progress);
  useEffect(() => { progressRef.current = progress; }, [progress]);

  const velocityRef = useRef(scrollVelocity);
  useEffect(() => { velocityRef.current = scrollVelocity; }, [scrollVelocity]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // 1. SCENE & DEEP SPACE ATMOSPHERE
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020409);
    scene.fog = new THREE.FogExp2(0x020409, 0.016);

    // 2. CAMERA CHOREOGRAPHY: Wide 50° cinematic FOV
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);

    // 9 Camera Waypoints gliding down the architectural corridor
    const cameraPoints = [
      new THREE.Vector3(0, 2.2, 22),         // Ch 01: Sourcing Radar
      new THREE.Vector3(-1.4, 1.8, 17.5),    // Ch 02: Screener (Look right to crystal)
      new THREE.Vector3(1.4, 1.6, 13.5),     // Ch 03: Anti-Ghosting (Look left to glass)
      new THREE.Vector3(-1.2, 1.4, 9.5),     // Ch 04: 1-Page ATS (Look right to resume)
      new THREE.Vector3(1.2, 1.3, 5.5),      // Ch 05: JD Intelligence (Look left to gems)
      new THREE.Vector3(-1.0, 1.1, 1.5),     // Ch 06: Pipeline CRM (Look right to stairs)
      new THREE.Vector3(1.0, 1.2, -2.5),     // Ch 07: Interview Lab (Look left to emerald)
      new THREE.Vector3(-0.8, 1.4, -6.5),    // Ch 08: Daily Briefing (Look right to radar)
      new THREE.Vector3(0, 1.6, -10.5),      // Ch 09: Enterprise Security Gate Finale
    ];
    const cameraSpline = new THREE.CatmullRomCurve3(cameraPoints);

    // LookAt Spline targeting visual anchors
    const lookAtPoints = [
      new THREE.Vector3(1.8, 0.6, 16),       // Ch 01
      new THREE.Vector3(2.4, 0.8, 13),       // Ch 02 (Crystal Prism)
      new THREE.Vector3(-2.2, 0.8, 9),       // Ch 03 (Broken Glass)
      new THREE.Vector3(2.2, 0.8, 5.5),      // Ch 04 (ATS Resume)
      new THREE.Vector3(-2.2, 0.8, 1.5),     // Ch 05 (Gem Cluster)
      new THREE.Vector3(1.8, -0.2, -2.5),    // Ch 06 (Stairs)
      new THREE.Vector3(-2.0, 0.8, -6.5),    // Ch 07 (Emerald)
      new THREE.Vector3(2.0, 0.8, -10.5),    // Ch 08 (Briefing)
      new THREE.Vector3(0, 0.6, -16.0),      // Ch 09 (Security Gate)
    ];
    const lookAtSpline = new THREE.CatmullRomCurve3(lookAtPoints);

    // Second-Order Dynamics Controller for Camera Inertia
    const cameraDynamics = new SecondOrderDynamics3D(1.35, 0.75, 1.5, 0, 2.2, 22);
    const lookAtDynamics = new SecondOrderDynamics3D(1.35, 0.75, 1.5, 1.8, 0.6, 16);

    // 3. RENDERER WITH ACES FILMIC TONE MAPPING
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setClearColor(0x020409, 1.0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.innerWidth < 760 ? 1.5 : 1.75));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.3;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    container.appendChild(renderer.domElement);

    // 4. POST-PROCESSING COMPOSER PIPELINE (UnrealBloom + CinematicLensShader)
    const composer = new EffectComposer(renderer);
    const renderPass = new RenderPass(scene, camera);
    composer.addPass(renderPass);

    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(width, height),
      0.45, // strength
      0.35, // radius
      0.22  // threshold
    );
    composer.addPass(bloomPass);

    const lensPass = new ShaderPass(CinematicLensShader);
    lensPass.uniforms.uGrainAmount.value = 0.007;
    lensPass.uniforms.uVignetteDarkness.value = 0.35;
    lensPass.uniforms.uChromaticOffset.value = 0.0008;
    composer.addPass(lensPass);

    const outputPass = new OutputPass();
    composer.addPass(outputPass);

    // 5. STUDIO LIGHTING RIG & HDR ENVIRONMENT
    const ambientLight = new THREE.AmbientLight(0x0f172a, 2.8);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 4.0);
    keyLight.position.set(-8, 16, 18);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    scene.add(keyLight);

    const facilityRimLight = new THREE.PointLight(0x5369d9, 4.8, 50);
    facilityRimLight.position.set(0, 4, 12);
    scene.add(facilityRimLight);

    const laserBlueLight = new THREE.PointLight(0x38bdf8, 4.0, 40);
    laserBlueLight.position.set(2, 2, -15);
    scene.add(laserBlueLight);

    // Load High-Resolution Studio HDR for Photorealistic PBR Reflections
    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    pmremGenerator.compileEquirectangularShader();
    new RGBELoader().load(
      "/assets/studio_small_09_2k.hdr",
      (hdrTexture) => {
        const envMap = pmremGenerator.fromEquirectangular(hdrTexture).texture;
        scene.environment = envMap;
        hdrTexture.dispose();
        pmremGenerator.dispose();
      },
      undefined,
      () => {}
    );

    // 6. ATMOSPHERIC BOKEH DUST PARTICLES (Soft cyan, lavender, starlight motes)
    const particleCount = 1200;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleColors = new Float32Array(particleCount * 3);
    const motePalette = [
      new THREE.Color(0x38bdf8), // Cyan
      new THREE.Color(0xa855f7), // Lavender
      new THREE.Color(0xf8fafc), // Crisp Starlight
    ];

    for (let i = 0; i < particleCount; i++) {
      const radius = 6.0 + Math.random() * 22;
      const angle = Math.random() * Math.PI * 2;
      particlePositions[i * 3 + 0] = Math.cos(angle) * radius;
      particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 16;
      particlePositions[i * 3 + 2] = -Math.random() * 70 + 25;

      const c = motePalette[Math.floor(Math.random() * motePalette.length)];
      particleColors[i * 3 + 0] = c.r;
      particleColors[i * 3 + 1] = c.g;
      particleColors[i * 3 + 2] = c.b;
    }
    particleGeo.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
    particleGeo.setAttribute("color", new THREE.BufferAttribute(particleColors, 3));

    const particleMat = new THREE.PointsMaterial({
      size: 0.12,
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending,
    });
    const particleSystem = new THREE.Points(particleGeo, particleMat);
    scene.add(particleSystem);

    // 7. EXTENDED ARCHITECTURAL RUNWAY FLOOR WITH 4K PBR TEXTURES
    const floorTexLoader = new THREE.TextureLoader();
    const floorBaseColor = floorTexLoader.load("/assets/pbr/BlueMetalPlate_BaseColor_4K.jpg");
    floorBaseColor.wrapS = THREE.RepeatWrapping;
    floorBaseColor.wrapT = THREE.RepeatWrapping;
    floorBaseColor.repeat.set(2, 24);

    const floorNormal = floorTexLoader.load("/assets/pbr/BlueMetalPlate_NormalGL_4K.jpg");
    floorNormal.wrapS = THREE.RepeatWrapping;
    floorNormal.wrapT = THREE.RepeatWrapping;
    floorNormal.repeat.set(2, 24);

    const runwayFloorGeo = new THREE.PlaneGeometry(16, 90);
    const runwayFloorMat = new THREE.MeshStandardMaterial({
      map: floorBaseColor,
      normalMap: floorNormal,
      normalScale: new THREE.Vector2(0.8, 0.8),
      roughness: 0.35,
      metalness: 0.85,
    });
    const runwayFloor = new THREE.Mesh(runwayFloorGeo, runwayFloorMat);
    runwayFloor.rotation.x = -Math.PI / 2;
    runwayFloor.position.set(0, -2.85, 0);
    runwayFloor.receiveShadow = true;
    scene.add(runwayFloor);

    // 8. ASYNCHRONOUS GLTF 3D MODEL LOADER
    const gltfLoader = new GLTFLoader();
    const facilityGroup = new THREE.Group();
    scene.add(facilityGroup);

    // Track loaded model references for animation
    const animatedModels = {
      crystals: [],
      brokenGlass: null,
      emeraldGem: null,
      gemCluster: null,
      gatewayLasers: null,
      gateDoor: null,
    };

    // Load Modular Corridors along Z runway from Z=+20 to Z=-30
    [20, 10, 0, -10, -20].forEach((zPos) => {
      gltfLoader.load(
        "/assets/corridor-wide.glb",
        (gltf) => {
          const corridor = gltf.scene;
          corridor.scale.set(1.8, 1.8, 1.8);
          corridor.position.set(0, -2.8, zPos);
          corridor.traverse((child) => {
            if (child.isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;
              child.material = new THREE.MeshStandardMaterial({
                color: 0x141b2b,
                metalness: 0.88,
                roughness: 0.22,
                envMapIntensity: 1.2,
              });
            }
          });
          facilityGroup.add(corridor);
        },
        undefined,
        () => {}
      );
    });

    // Overhead Industrial Cables along Z runway
    [20, 10, 0, -10, -20].forEach((zPos) => {
      gltfLoader.load(
        "/assets/cables.glb",
        (gltf) => {
          const cables = gltf.scene;
          cables.scale.set(1.6, 1.6, 1.6);
          cables.position.set(0, 4.2, zPos);
          cables.traverse((child) => {
            if (child.isMesh) {
              child.material = new THREE.MeshStandardMaterial({
                color: 0x0a101b,
                metalness: 0.9,
                roughness: 0.3,
              });
            }
          });
          facilityGroup.add(cables);
        },
        undefined,
        () => {}
      );
    });

    // --- CHAPTER 01: SOURCING RADAR & 10 TALENT NODES ---
    const nodesGroup = new THREE.Group();
    nodesGroup.position.set(2.4, 0.6, 16);
    const nodeMeshes = [];

    const radarRingGeo = new THREE.RingGeometry(2.4, 2.5, 64);
    const radarRingMat = new THREE.MeshBasicMaterial({
      color: 0x5369d9,
      transparent: true,
      opacity: 0.75,
      side: THREE.DoubleSide,
    });
    const radarRing = new THREE.Mesh(radarRingGeo, radarRingMat);
    radarRing.rotation.x = Math.PI / 2;
    radarRing.position.set(0, -0.6, 0);
    nodesGroup.add(radarRing);

    const radarInnerRingGeo = new THREE.RingGeometry(1.3, 1.38, 48);
    const radarInnerRing = new THREE.Mesh(radarInnerRingGeo, radarRingMat);
    radarInnerRing.rotation.x = Math.PI / 2;
    radarInnerRing.position.set(0, -0.58, 0);
    nodesGroup.add(radarInnerRing);

    // Create 10 High-Resolution Corporate Talent Badges
    TALENT_NODES.forEach((item) => {
      const tileTex = createBadgeTexture(item.company, item.ats);
      const tileGeo = new THREE.PlaneGeometry(1.4, 0.62);
      const tileMat = new THREE.MeshStandardMaterial({
        map: tileTex,
        roughness: 0.15,
        metalness: 0.5,
        transparent: true,
        opacity: 0.96,
        side: THREE.DoubleSide,
      });
      const tile = new THREE.Mesh(tileGeo, tileMat);

      const r = 1.9 + (item.id % 3) * 0.4;
      tile.position.set(
        Math.cos(item.angle) * r,
        (item.id % 4) * 0.32 - 0.35,
        Math.sin(item.angle) * r
      );
      tile.userData = item;
      nodesGroup.add(tile);
      nodeMeshes.push(tile);
    });
    scene.add(nodesGroup);

    // --- CHAPTER 02: Realistic Crystal Model (Crystal_iPoly3D_CC0.glb) ---
    const screenerGroup = new THREE.Group();
    screenerGroup.position.set(2.4, 0.8, 13);
    gltfLoader.load(
      "/assets/Crystal_iPoly3D_CC0.glb",
      (gltf) => {
        const crystal = gltf.scene;
        crystal.scale.set(1.2, 1.2, 1.2);
        crystal.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshPhysicalMaterial({
              color: 0x38bdf8,
              emissive: 0x0284c7,
              emissiveIntensity: 0.45,
              roughness: 0.04,
              metalness: 0.1,
              transmission: 0.92,
              ior: 1.54,
              thickness: 1.8,
              transparent: true,
              opacity: 0.94,
              envMapIntensity: 2.2,
            });
          }
        });
        screenerGroup.add(crystal);
        animatedModels.crystals.push(crystal);
      },
      undefined,
      () => {}
    );

    const screenerScanGeo = new THREE.CylinderGeometry(0.04, 0.04, 4.0);
    const screenerScanMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      blending: THREE.AdditiveBlending,
    });
    const screenerScan = new THREE.Mesh(screenerScanGeo, screenerScanMat);
    screenerGroup.add(screenerScan);
    scene.add(screenerGroup);

    // --- CHAPTER 03: Realistic Broken Glass Window (Khronos_Glass_Broken_Window.glb) ---
    const antiGhostGroup = new THREE.Group();
    antiGhostGroup.position.set(-2.2, 0.8, 9);
    gltfLoader.load(
      "/assets/Khronos_Glass_Broken_Window.glb",
      (gltf) => {
        const glass = gltf.scene;
        glass.scale.set(1.6, 1.6, 1.6);
        glass.rotation.y = -0.3;
        glass.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshPhysicalMaterial({
              color: 0xe2e8f0,
              roughness: 0.04,
              metalness: 0.05,
              transmission: 0.88,
              ior: 1.52,
              thickness: 1.2,
              transparent: true,
              opacity: 0.88,
              envMapIntensity: 2.0,
            });
          }
        });
        antiGhostGroup.add(glass);
        animatedModels.brokenGlass = glass;
      },
      undefined,
      () => {}
    );

    // Emerald Green Direct Requisition Bypass Laser
    const bypassRailGeo = new THREE.CylinderGeometry(0.05, 0.05, 6.5);
    const bypassRailMat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      blending: THREE.AdditiveBlending,
    });
    const bypassRail = new THREE.Mesh(bypassRailGeo, bypassRailMat);
    bypassRail.rotation.z = Math.PI / 2;
    bypassRail.position.set(0, 0, 0.2);
    antiGhostGroup.add(bypassRail);
    scene.add(antiGhostGroup);

    // --- CHAPTER 04: 1-Page ATS Resume Holographic Slab ---
    const resumeGroup = new THREE.Group();
    resumeGroup.position.set(2.2, 0.8, 5.5);
    const resumeSheetGeo = new THREE.PlaneGeometry(3.0, 4.4);
    const resumeSheetMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      emissive: 0x5369d9,
      emissiveIntensity: 0.28,
      roughness: 0.2,
      metalness: 0.85,
      transparent: true,
      opacity: 0.92,
      side: THREE.DoubleSide,
    });
    const resumeSheet = new THREE.Mesh(resumeSheetGeo, resumeSheetMat);
    resumeSheet.rotation.y = -0.28;
    resumeGroup.add(resumeSheet);

    const scanLineGeo = new THREE.PlaneGeometry(3.0, 0.09);
    const scanLineMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.95,
    });
    const scanLine = new THREE.Mesh(scanLineGeo, scanLineMat);
    scanLine.position.z = 0.04;
    resumeGroup.add(scanLine);
    scene.add(resumeGroup);

    // --- CHAPTER 05: Realistic Gem Stones Cluster (Gem_Stones_Natalia_Wojtkowska_CC_BY_4.0.glb) ---
    const jdGroup = new THREE.Group();
    jdGroup.position.set(-2.2, 0.8, 1.5);
    gltfLoader.load(
      "/assets/Gem_Stones_Natalia_Wojtkowska_CC_BY_4.0.glb",
      (gltf) => {
        const gem = gltf.scene;
        gem.scale.set(0.9, 0.9, 0.9);
        gem.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshStandardMaterial({
              color: 0x5369d9,
              emissive: 0x1e1b4b,
              emissiveIntensity: 0.35,
              roughness: 0.1,
              metalness: 0.4,
              envMapIntensity: 2.2,
            });
          }
        });
        jdGroup.add(gem);
        animatedModels.gemCluster = gem;
      },
      undefined,
      () => {}
    );

    const jdReticleOuterGeo = new THREE.RingGeometry(1.8, 1.94, 48);
    const jdReticleMat = new THREE.MeshBasicMaterial({
      color: 0x5369d9,
      transparent: true,
      opacity: 0.75,
      side: THREE.DoubleSide,
    });
    const jdReticleOuter = new THREE.Mesh(jdReticleOuterGeo, jdReticleMat);
    jdGroup.add(jdReticleOuter);
    scene.add(jdGroup);

    // --- CHAPTER 06: Architectural Stairs (stairs-wide.glb) & Pipeline CRM ---
    const pipelineGroup = new THREE.Group();
    pipelineGroup.position.set(1.8, -1.2, -2.5);
    gltfLoader.load(
      "/assets/stairs-wide.glb",
      (gltf) => {
        const stairs = gltf.scene;
        stairs.scale.set(1.5, 1.5, 1.5);
        stairs.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshStandardMaterial({
              color: 0x141b2b,
              metalness: 0.88,
              roughness: 0.22,
              envMapIntensity: 1.2,
            });
          }
        });
        pipelineGroup.add(stairs);
      },
      undefined,
      () => {}
    );

    // 7 Kanban glowing pads ascending the steps
    const kanbanColors = [0x5369d9, 0x5369d9, 0x38bdf8, 0x10b981, 0x5b7f6a, 0xd6ad69, 0x706e68];
    for (let k = 0; k < 7; k++) {
      const padGeo = new THREE.BoxGeometry(2.0, 0.12, 0.75);
      const padMat = new THREE.MeshStandardMaterial({
        color: kanbanColors[k],
        emissive: kanbanColors[k],
        emissiveIntensity: 0.45,
        roughness: 0.25,
        metalness: 0.7,
        transparent: true,
        opacity: 0.92,
      });
      const pad = new THREE.Mesh(padGeo, padMat);
      pad.position.set((k - 3) * 0.75, 0.65 + (k - 3) * 0.3, -k * 0.75);
      pipelineGroup.add(pad);
    }
    scene.add(pipelineGroup);

    // --- CHAPTER 07: Realistic Green Gem (Quaternius_Gem_Green.glb) ---
    const interviewGroup = new THREE.Group();
    interviewGroup.position.set(-2.0, 0.8, -6.5);
    gltfLoader.load(
      "/assets/Quaternius_Gem_Green.glb",
      (gltf) => {
        const gem = gltf.scene;
        gem.scale.set(0.9, 0.9, 0.9);
        gem.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshPhysicalMaterial({
              color: 0x10b981,
              emissive: 0x059669,
              emissiveIntensity: 0.4,
              roughness: 0.05,
              metalness: 0.15,
              transmission: 0.9,
              ior: 1.55,
              thickness: 1.6,
              transparent: true,
              opacity: 0.94,
              envMapIntensity: 2.2,
            });
          }
        });
        interviewGroup.add(gem);
        animatedModels.emeraldGem = gem;
      },
      undefined,
      () => {}
    );

    const octaGeo = new THREE.OctahedronGeometry(1.6, 0);
    const octaMat = new THREE.MeshStandardMaterial({
      color: 0xbd7652,
      wireframe: true,
      transparent: true,
      opacity: 0.85,
    });
    const octaMesh = new THREE.Mesh(octaGeo, octaMat);
    interviewGroup.add(octaMesh);
    scene.add(interviewGroup);

    // --- CHAPTER 08: Multi-Channel Morning Briefing Radar Waves ---
    const briefingGroup = new THREE.Group();
    briefingGroup.position.set(2.0, 0.8, -10.5);
    const pulseRings = [];
    [2.0, 3.8, 5.6, 7.4].forEach((radius, i) => {
      const ringGeo = new THREE.RingGeometry(radius - 0.08, radius, 48);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x5369d9,
        transparent: true,
        opacity: 0.6,
        side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 2;
      briefingGroup.add(ring);
      pulseRings.push({ mesh: ring, baseRadius: radius, phase: i * 0.45 });
    });
    scene.add(briefingGroup);

    // --- CHAPTER 09: Monumental Security Gate, Lasers, Door & Portal Lighting ---
    const portalGroup = new THREE.Group();
    portalGroup.position.set(0, -1.8, -16.0);

    gltfLoader.load(
      "/assets/gate.glb",
      (gltf) => {
        const gate = gltf.scene;
        gate.scale.set(2.4, 2.4, 2.4);
        gate.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.material = new THREE.MeshStandardMaterial({
              color: 0x141b2b,
              metalness: 0.9,
              roughness: 0.18,
              envMapIntensity: 1.3,
            });
          }
        });
        portalGroup.add(gate);
      },
      undefined,
      () => {}
    );

    gltfLoader.load(
      "/assets/gate-lasers.glb",
      (gltf) => {
        const gateLasers = gltf.scene;
        gateLasers.scale.set(2.4, 2.4, 2.4);
        gateLasers.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshBasicMaterial({
              color: 0x38bdf8,
              transparent: true,
              opacity: 0.95,
            });
          }
        });
        portalGroup.add(gateLasers);
        animatedModels.gatewayLasers = gateLasers;
      },
      undefined,
      () => {}
    );

    gltfLoader.load(
      "/assets/gate-door.glb",
      (gltf) => {
        const gateDoor = gltf.scene;
        gateDoor.scale.set(2.4, 2.4, 2.4);
        gateDoor.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshStandardMaterial({
              color: 0x0f172a,
              metalness: 0.92,
              roughness: 0.2,
            });
          }
        });
        portalGroup.add(gateDoor);
        animatedModels.gateDoor = gateDoor;
      },
      undefined,
      () => {}
    );

    const portalDoorLight = new THREE.PointLight(0x5369d9, 5.0, 24);
    portalDoorLight.position.set(0, 3, 1);
    portalGroup.add(portalDoorLight);
    scene.add(portalGroup);

    // Story Visual Groups collection for chapter focal fading
    const storyVisualGroups = [
      { group: nodesGroup, chapter: 0 },
      { group: screenerGroup, chapter: 1 },
      { group: antiGhostGroup, chapter: 2 },
      { group: resumeGroup, chapter: 3 },
      { group: jdGroup, chapter: 4 },
      { group: pipelineGroup, chapter: 5 },
      { group: interviewGroup, chapter: 6 },
      { group: briefingGroup, chapter: 7 },
      { group: portalGroup, chapter: 8 },
    ];

    // 9. MOUSE TRACKING & RAYCASTING FOR INTERACTIVE CORPORATE NODES
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    const raycaster = new THREE.Raycaster();
    const mouseVector = new THREE.Vector2();

    const onPointerMove = (e) => {
      mouse.targetX = (e.clientX / width - 0.5) * 2;
      mouse.targetY = -(e.clientY / height - 0.5) * 2;
    };
    window.addEventListener("pointermove", onPointerMove);

    const onClick = (e) => {
      const rect = container.getBoundingClientRect();
      mouseVector.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseVector.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouseVector, camera);

      const intersects = raycaster.intersectObjects(nodeMeshes, false);
      if (intersects.length > 0) {
        const clickedNode = intersects[0].object.userData;
        onSelectNodeRef.current(clickedNode);
      }
    };
    container.addEventListener("click", onClick);

    // 10. MASTER 120 FPS RAF TICK LOOP WITH HIGH-PRECISION TIMER
    let animId;
    let lastTime = performance.now();
    let elapsedTime = 0;

    const render = (now) => {
      animId = requestAnimationFrame(render);
      const dt = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;
      elapsedTime += dt;
      const time = elapsedTime;

      // Mouse Parallax Lerp
      mouse.x += (mouse.targetX - mouse.x) * 0.08;
      mouse.y += (mouse.targetY - mouse.y) * 0.08;

      const motion = motionRefRef.current?.current;
      const p = Math.max(0, Math.min(1, motion?.progress ?? progressRef.current));
      const vel = motion?.velocity ?? velocityRef.current;

      // Catmull-Rom Target Camera Position & LookAt
      const splinePos = cameraSpline.getPointAt(p);
      const splineLookAt = lookAtSpline.getPointAt(p);

      const targetCamX = splinePos.x + mouse.x * 0.65;
      const targetCamY = splinePos.y + mouse.y * 0.45;
      const targetCamZ = splinePos.z - Math.min(Math.abs(vel) * 3.0, 2.5);

      const smoothedCam = cameraDynamics.update(dt, targetCamX, targetCamY, targetCamZ);
      const smoothedLook = lookAtDynamics.update(dt, splineLookAt.x, splineLookAt.y, splineLookAt.z);

      camera.position.set(smoothedCam.x, smoothedCam.y, smoothedCam.z);
      camera.lookAt(smoothedLook.x, smoothedLook.y, smoothedLook.z);
      camera.rotation.z = -vel * 0.015;

      // Update Cinematic Shader Pass Uniforms
      lensPass.uniforms.uTime.value = time;

      // Animate Particles
      particleSystem.rotation.y = time * 0.02;

      // Animate Realistic GLB 3D Models
      // A. Talent Nodes in Chapter 01
      radarRing.rotation.z = time * 0.5;
      radarInnerRing.rotation.z = -time * 0.8;
      nodeMeshes.forEach((mesh, idx) => {
        mesh.quaternion.copy(camera.quaternion);
        mesh.position.y = (idx % 4) * 0.32 - 0.35 + Math.sin(time * 1.8 + idx) * 0.08;
      });

      // B. Crystals in Chapter 02
      animatedModels.crystals.forEach((cr, idx) => {
        cr.rotation.x = time * 0.6 + idx;
        cr.rotation.y = time * 0.8;
        cr.position.y = Math.sin(time * 1.5 + idx) * 0.15;
      });
      screenerScan.position.y = Math.sin(time * 2.2) * 1.4;

      // C. Broken Glass in Chapter 03
      if (animatedModels.brokenGlass) {
        animatedModels.brokenGlass.position.y = Math.sin(time * 1.2) * 0.08;
      }

      // D. Resume Scanline in Chapter 04
      scanLine.position.y = Math.sin(time * 2.4) * 1.8;

      // E. Gem Stones Cluster in Chapter 05
      if (animatedModels.gemCluster) {
        animatedModels.gemCluster.rotation.y = time * 0.75;
      }
      jdReticleOuter.rotation.z = time * 0.45;

      // F. Emerald Gem & STAR Octahedron in Chapter 07
      if (animatedModels.emeraldGem) {
        animatedModels.emeraldGem.rotation.y = time * 0.9;
        animatedModels.emeraldGem.rotation.x = time * 0.4;
      }
      octaMesh.rotation.x = time * 0.5;
      octaMesh.rotation.y = time * 0.7;

      // G. Acoustic Briefing Waves in Chapter 08
      pulseRings.forEach((r) => {
        const pulse = (time * 0.8 + r.phase) % 1;
        const scale = 1 + pulse * 0.85;
        r.mesh.scale.set(scale, scale, 1);
        r.mesh.material.opacity = Math.max(0, 0.6 * (1 - pulse));
      });

      // H. Gateway Lasers & Sliding Door in Chapter 09
      if (animatedModels.gateDoor) {
        const doorOpen = Math.min(1.0, Math.max(0, (p - 0.88) / 0.12));
        animatedModels.gateDoor.position.x = doorOpen * 2.4;
      }

      // Chapter Focal Visibility
      const chFloat = p * 8.0;
      storyVisualGroups.forEach(({ group, chapter }) => {
        const dist = Math.abs(chFloat - chapter);
        group.visible = dist < 1.4;
      });

      // Render via Post-Processing Composer (UnrealBloom + Film Grain + Vignette)
      composer.render();
    };

    animId = requestAnimationFrame(render);

    // Resize Handler
    const handleResize = () => {
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      composer.setSize(w, h);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.innerWidth < 760 ? 1.5 : 1.75));
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("resize", handleResize);
      container.removeEventListener("click", onClick);
      if (renderer.domElement && renderer.domElement.parentElement) {
        renderer.domElement.parentElement.removeChild(renderer.domElement);
      }
      renderer.dispose();
      composer.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className="fixed inset-0 w-full h-full pointer-events-auto z-10"
      style={{ overflow: "hidden" }}
    />
  );
}
