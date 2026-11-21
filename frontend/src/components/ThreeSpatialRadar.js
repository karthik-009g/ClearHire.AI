import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import * as THREE from "three";

/**
 * ============================================================================
 * SECOND-ORDER DYNAMICS PHYSICS ENGINE
 * Reverse-engineered procedural animation model (f = 1.5, z = 0.8, r = 2.0)
 * Reference: t3ssel8r / Keijiro dynamic spring-damper state integration.
 * ============================================================================
 */
export class SecondOrderDynamics {
  constructor(f = 1.5, z = 0.8, r = 2.0, x0 = 0) {
    this.f = f;
    this.z = z;
    this.r = r;
    this._computeConstants();

    this.xp = x0; // previous input
    this.y = x0;  // current output
    this.yd = 0;  // current velocity
  }

  setParams(f, z, r) {
    this.f = f;
    this.z = z;
    this.r = r;
    this._computeConstants();
  }

  _computeConstants() {
    const f = Math.max(0.001, this.f);
    const z = Math.max(0, this.z);
    const r = this.r;
    const PI = Math.PI;

    this.k1 = z / (PI * f);
    this.k2 = 1 / ((2 * PI * f) * (2 * PI * f));
    this.k3 = (r * z) / (2 * PI * f);
  }

  reset(x0 = 0) {
    this.xp = x0;
    this.y = x0;
    this.yd = 0;
  }

  update(dt, x, xd = null) {
    if (dt <= 0) return this.y;
    // Calculate input velocity if not explicitly provided
    if (xd === null) {
      xd = (x - this.xp) / dt;
      this.xp = x;
    }

    // Numerical stability clamp for variable delta times
    const k2Stable = Math.max(
      this.k2,
      1.1 * ((dt * dt) / 4 + (dt * this.k1) / 2),
      dt * this.k1
    );

    // Semi-implicit Euler integration with second-order acceleration
    this.y = this.y + dt * this.yd;
    this.yd = this.yd + (dt * (x + this.k3 * xd - this.y - this.k1 * this.yd)) / k2Stable;

    return this.y;
  }
}

/**
 * Multi-Axis Second-Order Dynamics for 3D Vector & Spherical systems
 */
export class SecondOrderDynamics3D {
  constructor(f = 1.5, z = 0.8, r = 2.0, x0 = 0, y0 = 0, z0 = 0) {
    this.x = new SecondOrderDynamics(f, z, r, x0);
    this.y = new SecondOrderDynamics(f, z, r, y0);
    this.z = new SecondOrderDynamics(f, z, r, z0);
    this.value = { x: x0, y: y0, z: z0 };
  }

  reset(x = 0, y = 0, z = 0) {
    this.x.reset(x);
    this.y.reset(y);
    this.z.reset(z);
    this.value.x = x;
    this.value.y = y;
    this.value.z = z;
  }

  update(dt, targetX, targetY, targetZ) {
    this.value.x = this.x.update(dt, targetX);
    this.value.y = this.y.update(dt, targetY);
    this.value.z = this.z.update(dt, targetZ);
    return this.value;
  }
}

/**
 * ============================================================================
 * SYNTHESIZED SPATIAL AUDIO MICRO-INTERACTIONS (Disabled)
 * Sound has been completely removed from the entire application.
 * ============================================================================
 */
class SpatialAudioEngine {
  constructor() {
    this.ctx = null;
    this.muted = true;
  }
  ensureContext() {}
  toggleMute() { return true; }
  playRadarPing() {}
  playHover() {}
  playSelect() {}
}

const audio = new SpatialAudioEngine();

// Fallback high-authenticity talent nodes if empty list provided
const FALLBACK_JOBS = [
  {
    id: 101,
    title: "Senior Backend Systems Engineer",
    company: "Razorpay",
    score: 97,
    ghosting_risk: "low",
    ats_provider: "greenhouse",
    location: "Bengaluru, India",
    ctc_range: "₹30 - 45 LPA",
    notice: "≤ 30 Days",
    skills: ["Go", "Distributed Systems", "PostgreSQL", "Kafka"],
  },
  {
    id: 102,
    title: "Staff Distributed Platform Architect",
    company: "Postman",
    score: 94,
    ghosting_risk: "low",
    ats_provider: "lever",
    location: "Bengaluru (Hybrid)",
    ctc_range: "₹45 - 65 LPA",
    notice: "≤ 60 Days",
    skills: ["Node.js", "Kubernetes", "Redis", "Microservices"],
  },
  {
    id: 103,
    title: "High-Throughput Python Engineer",
    company: "Zepto",
    score: 92,
    ghosting_risk: "low",
    ats_provider: "ashby",
    location: "Mumbai / Bengaluru",
    ctc_range: "₹28 - 40 LPA",
    notice: "Immediate",
    skills: ["FastAPI", "AsyncIO", "Celery", "PostgreSQL"],
  },
  {
    id: 104,
    title: "Core Infrastructure & AI SDE III",
    company: "CRED",
    score: 89,
    ghosting_risk: "low",
    ats_provider: "greenhouse",
    location: "Bengaluru, India",
    ctc_range: "₹40 - 55 LPA",
    notice: "≤ 30 Days",
    skills: ["Golang", "AWS", "gRPC", "Vector DBs"],
  },
  {
    id: 105,
    title: "Cloud & Data Streaming Architect",
    company: "InMobi",
    score: 86,
    ghosting_risk: "low",
    ats_provider: "lever",
    location: "Bengaluru, India",
    ctc_range: "₹35 - 50 LPA",
    notice: "≤ 45 Days",
    skills: ["Spark", "Flink", "Kafka", "Java"],
  },
  {
    id: 106,
    title: "Full-Stack Reliability Engineer",
    company: "BrowserStack",
    score: 82,
    ghosting_risk: "medium",
    ats_provider: "workday",
    location: "Mumbai, India",
    ctc_range: "₹25 - 38 LPA",
    notice: "≤ 60 Days",
    skills: ["Ruby", "React", "Docker", "SRE"],
  },
  {
    id: 107,
    title: "Distributed Edge Services SDE",
    company: "Swiggy",
    score: 80,
    ghosting_risk: "medium",
    ats_provider: "greenhouse",
    location: "Bengaluru, India",
    ctc_range: "₹26 - 36 LPA",
    notice: "≤ 30 Days",
    skills: ["Java", "Spring Boot", "Kafka", "DynamoDB"],
  },
  {
    id: 108,
    title: "Platform DevOps & Infra Engineer",
    company: "Zomato",
    score: 75,
    ghosting_risk: "medium",
    ats_provider: "direct_portal",
    location: "Gurugram, India",
    ctc_range: "₹22 - 32 LPA",
    notice: "≤ 30 Days",
    skills: ["Terraform", "Kubernetes", "Prometheus", "CI/CD"],
  },
];

// Module-level scratch objects to eliminate RAF heap allocations
const _scratchSpherical = new THREE.Spherical();
const _scratchLookOffset = new THREE.Vector3();
const _scratchWorldPos = new THREE.Vector3();
const _scratchIntersects = [];

/**
 * ============================================================================
 * THREE.JS ORBITAL SOURCING RADAR & TALENT CONSTELLATION COMPONENT
 * With Second-Order Dynamics Physics (f=1.5, z=0.8, r=2.0)
 * ============================================================================
 */
export default function ThreeSpatialRadar({
  jobs = [],
  selectedJobId = null,
  onSelectJob = () => {},
  onHoverJob = () => {},
}) {
  const mountRef = useRef(null);
  const capsuleRef = useRef(null);

  // Stable callback references to prevent WebGL teardown/recreation
  const onSelectJobRef = useRef(onSelectJob);
  onSelectJobRef.current = onSelectJob;

  const onHoverJobRef = useRef(onHoverJob);
  onHoverJobRef.current = onHoverJob;

  // Active / Selected Node State
  const [activeNode, setActiveNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [cameraZoomRadius, setCameraZoomRadius] = useState(20);
  const [viewPreset, setViewPreset] = useState("cinematic"); // "cinematic" | "topdown" | "focus"
  const [filterMode, setFilterMode] = useState("all"); // "all" | "low_risk" | "top_matches"

  // Stable references for Three.js interactions
  const triggerFocusRef = useRef(null);
  const triggerZoomRef = useRef(null);
  const triggerPresetRef = useRef(null);

  // Normalise jobs input (memoized to prevent WebGL context recreation when jobs reference is stable)
  const displayJobs = useMemo(() => {
    return jobs && jobs.length > 0 ? jobs.slice(0, 24) : FALLBACK_JOBS;
  }, [jobs]);

  // Synchronize external selectedJobId with radar camera focus without WebGL context destruction
  useEffect(() => {
    if (selectedJobId && triggerFocusRef.current && displayJobs) {
      const match = displayJobs.find((j) => j.id === selectedJobId);
      if (match) {
        triggerFocusRef.current(match);
      }
    }
  }, [selectedJobId, displayJobs]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 900;
    const height = container.clientHeight || 560;

    // ------------------------------------------------------------------------
    // 1. SCENE & DEEP HORIZON ATMOSPHERE (Warm Studio Stone Palette)
    // ------------------------------------------------------------------------
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf6f4ee);
    scene.fog = new THREE.FogExp2(0xf6f4ee, 0.015);

    // ------------------------------------------------------------------------
    // 2. CAMERA & SECOND-ORDER DYNAMICS CONTROLLERS (f=1.5, z=0.8, r=2.0)
    // ------------------------------------------------------------------------
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);

    // Initial Spherical Coordinates
    const initialRadius = 22;
    const initialTheta = Math.PI / 4.2;
    const initialPhi = Math.PI / 3.1;

    // Current animated spherical values
    let currentSpherical = {
      radius: initialRadius,
      theta: initialTheta,
      phi: initialPhi,
    };

    // Target spherical coordinates set by user interaction
    let targetSpherical = {
      radius: initialRadius,
      theta: initialTheta,
      phi: initialPhi,
    };

    // Target LookAt focus point (supports focusing on specific talent nodes)
    let targetLookAt = new THREE.Vector3(0, 0, 0);
    let currentLookAt = new THREE.Vector3(0, 0, 0);

    // Instantiating Second-Order Dynamics physics instances (f=1.5, z=0.8, r=2.0)
    const cameraSphericalDynamics = new SecondOrderDynamics3D(
      1.5,
      0.8,
      2.0,
      initialRadius,
      initialTheta,
      initialPhi
    );
    const cameraLookAtDynamics = new SecondOrderDynamics3D(
      1.5,
      0.8,
      2.0,
      0,
      0,
      0
    );

    camera.position.setFromSpherical(
      new THREE.Spherical(initialRadius, initialPhi, initialTheta)
    );
    camera.lookAt(0, 0, 0);

    // ------------------------------------------------------------------------
    // 3. RENDERER WITH 60 FPS PERFORMANCE CAP (DPR <= 1.5) & HARDWARE OPTIMIZATION
    // ------------------------------------------------------------------------
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.95;
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // ------------------------------------------------------------------------
    // 4. LIGHTING SYSTEM (Warm Travertine & Studio Lighting)
    // ------------------------------------------------------------------------
    const ambientLight = new THREE.AmbientLight(0xf5efe6, 1.9);
    scene.add(ambientLight);

    const primaryLight = new THREE.DirectionalLight(0xfff6eb, 2.2);
    primaryLight.position.set(18, 30, 22);
    scene.add(primaryLight);

    const rimLight = new THREE.DirectionalLight(0xd4ccbd, 1.4);
    rimLight.position.set(-25, -15, -20);
    scene.add(rimLight);

    const coreLight = new THREE.PointLight(0xd97706, 2.8, 32);
    coreLight.position.set(0, 0, 0);
    scene.add(coreLight);

    // ------------------------------------------------------------------------
    // 5. DISTANT STELLAR DUST (Warm Travertine Stone Motes & Bronze Specks)
    // ------------------------------------------------------------------------
    const dustCount = 550;
    const dustGeo = new THREE.BufferGeometry();
    const dustPositions = new Float32Array(dustCount * 3);
    const dustColors = new Float32Array(dustCount * 3);

    for (let i = 0; i < dustCount; i++) {
      dustPositions[i * 3] = (Math.random() - 0.5) * 160;
      dustPositions[i * 3 + 1] = (Math.random() - 0.5) * 80;
      dustPositions[i * 3 + 2] = (Math.random() - 0.5) * 160;

      const isAmber = Math.random() > 0.45;
      dustColors[i * 3] = isAmber ? 0.85 : 0.72;
      dustColors[i * 3 + 1] = isAmber ? 0.65 : 0.62;
      dustColors[i * 3 + 2] = isAmber ? 0.35 : 0.50;
    }

    dustGeo.setAttribute("position", new THREE.BufferAttribute(dustPositions, 3));
    dustGeo.setAttribute("color", new THREE.BufferAttribute(dustColors, 3));

    const dustMat = new THREE.PointsMaterial({
      size: 0.18,
      vertexColors: true,
      transparent: true,
      opacity: 0.40,
      blending: THREE.NormalBlending,
    });
    const dustSystem = new THREE.Points(dustGeo, dustMat);
    scene.add(dustSystem);

    // ------------------------------------------------------------------------
    // 6. ORBITAL SOURCING RADAR GROUND MATRIX & CONCENTRIC RANGE RINGS
    // ------------------------------------------------------------------------
    const radarGroup = new THREE.Group();
    radarGroup.position.y = -3.8;
    scene.add(radarGroup);

    // Precision Cartesian Coordinates Floor Grid (Warm Bronze / Stone)
    const gridHelper = new THREE.GridHelper(64, 48, 0xd4ccbd, 0xe8e2d5);
    gridHelper.position.y = 0;
    radarGroup.add(gridHelper);

    // Concentric Radar Range Rings (Match Score Tiers - Emerald, Amber, Bronze)
    const rangeRingsData = [
      { radius: 7.5, label: "95%+ MATCH TIER", color: 0x059669, opacity: 0.40 },
      { radius: 13.0, label: "85%+ DIRECT ATS", color: 0xd97706, opacity: 0.35 },
      { radius: 18.5, label: "70%+ SOURCING PERIPHERY", color: 0x8c7851, opacity: 0.25 },
    ];

    rangeRingsData.forEach((tier) => {
      const ringGeo = new THREE.RingGeometry(tier.radius - 0.06, tier.radius + 0.06, 96);
      const ringMat = new THREE.MeshBasicMaterial({
        color: tier.color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: tier.opacity,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = -Math.PI / 2;
      radarGroup.add(ringMesh);

      // Subtle dashed border ring
      const circlePts = [];
      const segs = 64;
      for (let s = 0; s <= segs; s++) {
        const theta = (s / segs) * Math.PI * 2;
        circlePts.push(new THREE.Vector3(Math.cos(theta) * tier.radius, 0.02, Math.sin(theta) * tier.radius));
      }
      const circleGeo = new THREE.BufferGeometry().setFromPoints(circlePts);
      const circleLine = new THREE.Line(
        circleGeo,
        new THREE.LineDashedMaterial({
          color: tier.color,
          dashSize: 0.5,
          gapSize: 0.3,
          transparent: true,
          opacity: tier.opacity * 1.5,
        })
      );
      circleLine.computeLineDistances();
      radarGroup.add(circleLine);
    });

    // Dynamic Expanding Radar Sonar Ripple Wave
    const pulseRingGeo = new THREE.RingGeometry(0.5, 1.2, 64);
    const pulseRingMat = new THREE.MeshBasicMaterial({
      color: 0xd97706,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.45,
    });
    const pulseRingMesh = new THREE.Mesh(pulseRingGeo, pulseRingMat);
    pulseRingMesh.rotation.x = -Math.PI / 2;
    radarGroup.add(pulseRingMesh);
    let pulseProgress = 0;

    // Active Rotating Sonar Radar Sweep Beam (clearhire.ai Radar Signature)
    const sweepGroup = new THREE.Group();
    radarGroup.add(sweepGroup);

    // Sweep fan plane (35-degree scanning arc)
    const sweepFanGeo = new THREE.CircleGeometry(20, 32, 0, Math.PI / 5);
    const sweepFanMat = new THREE.MeshBasicMaterial({
      color: 0xd97706,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.05,
    });
    const sweepFanMesh = new THREE.Mesh(sweepFanGeo, sweepFanMat);
    sweepFanMesh.rotation.x = -Math.PI / 2;
    sweepFanMesh.rotation.z = 0;
    sweepGroup.add(sweepFanMesh);

    // Leading High-Intensity Laser Line of the radar sweep
    const sweepLineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0.05, 0),
      new THREE.Vector3(Math.cos(Math.PI / 5) * 20, 0.05, Math.sin(Math.PI / 5) * 20),
    ]);
    const sweepLineMat = new THREE.LineBasicMaterial({
      color: 0x8c7851,
      transparent: true,
      opacity: 0.45,
    });
    const sweepLine = new THREE.Line(sweepLineGeo, sweepLineMat);
    sweepGroup.add(sweepLine);

    // ------------------------------------------------------------------------
    // 7. CRYSTALLINE RESUME & TALENT ORIGIN CORE (The Candidate Anchor)
    // ------------------------------------------------------------------------
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Inner Pulsing Icosahedron Core
    const innerCoreGeo = new THREE.IcosahedronGeometry(1.65, 2);
    const innerCoreMat = new THREE.MeshStandardMaterial({
      color: 0x24231f,
      emissive: 0xd97706,
      emissiveIntensity: 0.65,
      roughness: 0.25,
      metalness: 0.75,
    });
    const innerCoreMesh = new THREE.Mesh(innerCoreGeo, innerCoreMat);
    coreGroup.add(innerCoreMesh);

    // Outer Faceted Geometric Cage (Counter-rotating wireframe)
    const cageGeo = new THREE.IcosahedronGeometry(2.35, 1);
    const cageMat = new THREE.MeshBasicMaterial({
      color: 0x8c7851,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
    });
    const cageMesh = new THREE.Mesh(cageGeo, cageMat);
    coreGroup.add(cageMesh);

    // Vertical Quantum Data Pillar Beam (Piercing upward from ground)
    const pillarGeo = new THREE.CylinderGeometry(0.08, 0.08, 22, 16);
    const pillarMat = new THREE.MeshBasicMaterial({
      color: 0xd4ccbd,
      transparent: true,
      opacity: 0.35,
    });
    const pillarMesh = new THREE.Mesh(pillarGeo, pillarMat);
    pillarMesh.position.y = 4;
    coreGroup.add(pillarMesh);

    // Core Particle Halo Swarm Ring
    const haloParticleCount = 90;
    const haloParticleGeo = new THREE.BufferGeometry();
    const haloPositions = new Float32Array(haloParticleCount * 3);
    for (let i = 0; i < haloParticleCount; i++) {
      const angle = (i / haloParticleCount) * Math.PI * 2;
      const r = 3.6 + (Math.random() - 0.5) * 0.8;
      haloPositions[i * 3] = Math.cos(angle) * r;
      haloPositions[i * 3 + 1] = (Math.random() - 0.5) * 1.2;
      haloPositions[i * 3 + 2] = Math.sin(angle) * r;
    }
    haloParticleGeo.setAttribute("position", new THREE.BufferAttribute(haloPositions, 3));
    const haloParticleMat = new THREE.PointsMaterial({
      color: 0xd97706,
      size: 0.18,
      transparent: true,
      opacity: 0.8,
      blending: THREE.NormalBlending,
    });
    const haloParticleSystem = new THREE.Points(haloParticleGeo, haloParticleMat);
    coreGroup.add(haloParticleSystem);

    // ------------------------------------------------------------------------
    // 8. STELLAR TALENT NODES & CONSTELLATION GRAPH
    // ------------------------------------------------------------------------
    const nodesGroup = new THREE.Group();
    scene.add(nodesGroup);

    const interactiveHitMeshes = [];
    const nodeStateEntries = [];
    const nodePositionsVectorList = [];

    displayJobs.forEach((job, index) => {
      const nodeSubGroup = new THREE.Group();

      // Orbital distance inversely proportional to match score (top score closer to candidate core)
      const score = Number(job.score) || 90 - index * 2;
      const normalizedDist = Math.max(0, Math.min(100, score));
      // Distance ranges from 6.0 (100% score) to 18.5 (50% score)
      const orbitalRadius = 6.0 + (100 - normalizedDist) * 0.25;

      // Angular distribution in orbital plane with natural altitude variation
      const theta = (index / displayJobs.length) * Math.PI * 2 + (index % 2 === 0 ? 0.2 : -0.2);
      const elevationY = Math.sin(index * 1.7) * 2.2 + 0.3;

      const posX = Math.cos(theta) * orbitalRadius;
      const posY = elevationY;
      const posZ = Math.sin(theta) * orbitalRadius;

      nodeSubGroup.position.set(posX, posY, posZ);
      nodePositionsVectorList.push(new THREE.Vector3(posX, posY, posZ));

      // Color coding based on Anti-Ghosting Risk Signal (Emerald, Amber, Terracotta)
      const isLowRisk = job.ghosting_risk === "low";
      const isMediumRisk = job.ghosting_risk === "medium";
      const themeColor = isLowRisk ? 0x059669 : isMediumRisk ? 0xd97706 : 0xc2410c;

      // 1. Stellar Diamond/Octahedron Nucleus (Warm Walnut & Emissive Gem)
      const crystalGeo = new THREE.OctahedronGeometry(0.85, 0);
      const crystalMat = new THREE.MeshStandardMaterial({
        color: 0x24231f,
        emissive: themeColor,
        emissiveIntensity: 0.50,
        roughness: 0.20,
        metalness: 0.65,
        transparent: true,
        opacity: 0.95,
      });
      const crystalMesh = new THREE.Mesh(crystalGeo, crystalMat);
      nodeSubGroup.add(crystalMesh);

      // 2. Holographic Gimbal Ring Halo
      const haloTorusGeo = new THREE.TorusGeometry(1.3, 0.025, 8, 36);
      const haloTorusMat = new THREE.MeshBasicMaterial({
        color: themeColor,
        transparent: true,
        opacity: 0.55,
      });
      const haloTorusMesh = new THREE.Mesh(haloTorusGeo, haloTorusMat);
      haloTorusMesh.rotation.x = Math.PI / 3;
      nodeSubGroup.add(haloTorusMesh);

      // 3. Invisible enlarged Raycast Hit-Sphere for smooth pointer picking
      const hitSphereGeo = new THREE.SphereGeometry(1.5, 12, 12);
      const hitSphereMat = new THREE.MeshBasicMaterial({
        visible: false,
      });
      const hitSphereMesh = new THREE.Mesh(hitSphereGeo, hitSphereMat);
      nodeSubGroup.add(hitSphereMesh);

      // 4. Ground Drop-Line Beacon connecting node down to the radar grid
      const groundDropPts = [
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, -3.8 - posY, 0),
      ];
      const groundDropGeo = new THREE.BufferGeometry().setFromPoints(groundDropPts);
      const groundDropMat = new THREE.LineBasicMaterial({
        color: themeColor,
        transparent: true,
        opacity: 0.30,
      });
      const groundDropLine = new THREE.Line(groundDropGeo, groundDropMat);
      nodeSubGroup.add(groundDropLine);

      // 5. Gravitational Tether Ray to Candidate Origin Core (Turned Bronze)
      const coreTetherPts = [
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(-posX, -posY, -posZ),
      ];
      const coreTetherGeo = new THREE.BufferGeometry().setFromPoints(coreTetherPts);
      const coreTetherMat = new THREE.LineBasicMaterial({
        color: 0xd4ccbd,
        transparent: true,
        opacity: 0.20,
      });
      const coreTetherLine = new THREE.Line(coreTetherGeo, coreTetherMat);
      nodeSubGroup.add(coreTetherLine);

      // Per-node Second-Order Dynamics for hover scale and spring physics
      const scaleDynamics = new SecondOrderDynamics(1.5, 0.8, 2.0, 1.0);

      // Attach metadata for raycasting and loop animation
      hitSphereMesh.userData = {
        job,
        index,
        parentGroup: nodeSubGroup,
        crystalMesh,
        haloTorusMesh,
        themeColor,
        basePos: new THREE.Vector3(posX, posY, posZ),
        scaleDynamics,
        targetScale: 1.0,
      };

      interactiveHitMeshes.push(hitSphereMesh);
      nodeStateEntries.push(hitSphereMesh.userData);
      nodesGroup.add(nodeSubGroup);
    });

    // ------------------------------------------------------------------------
    // 9. TALENT CONSTELLATION LINKAGES (Inter-node Neural Web)
    // ------------------------------------------------------------------------
    const constellationLines = [];
    const constellationLineMat = new THREE.LineBasicMaterial({
      color: 0xd4ccbd,
      transparent: true,
      opacity: 0.30,
      blending: THREE.NormalBlending,
    });

    for (let i = 0; i < nodePositionsVectorList.length; i++) {
      for (let j = i + 1; j < nodePositionsVectorList.length; j++) {
        const dist = nodePositionsVectorList[i].distanceTo(nodePositionsVectorList[j]);
        // Connect nearby nodes within proximity radius to form constellation geometry
        if (dist < 8.2) {
          const lineGeo = new THREE.BufferGeometry().setFromPoints([
            nodePositionsVectorList[i],
            nodePositionsVectorList[j],
          ]);
          const line = new THREE.Line(lineGeo, constellationLineMat);
          scene.add(line);
          constellationLines.push(line);
        }
      }
    }

    // ------------------------------------------------------------------------
    // 10. POINTER, ORBIT & CAMERA EVENT HANDLERS
    // ------------------------------------------------------------------------
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2(-1000, -1000);
    let isDragging = false;
    let prevPointerPos = { x: 0, y: 0 };
    let activeHoveredNodeData = null;
    let isAutoOrbiting = true;
    let lastUserInteractionTime = Date.now();

    const onPointerMove = (e) => {
      const rect = container.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      if (isDragging) {
        lastUserInteractionTime = Date.now();
        isAutoOrbiting = false;
        const deltaX = e.clientX - prevPointerPos.x;
        const deltaY = e.clientY - prevPointerPos.y;
        prevPointerPos = { x: e.clientX, y: e.clientY };

        targetSpherical.theta -= deltaX * 0.007;
        // Clamp phi to prevent flipping over poles
        targetSpherical.phi = Math.max(
          0.08,
          Math.min(Math.PI / 2.05, targetSpherical.phi - deltaY * 0.007)
        );
      }
    };

    const onPointerDown = (e) => {
      // Ignore if clicking on floating HTML overlay controls
      if (e.target !== renderer.domElement) return;
      isDragging = true;
      lastUserInteractionTime = Date.now();
      prevPointerPos = { x: e.clientX, y: e.clientY };
    };

    const onPointerUp = () => {
      isDragging = false;
    };

    // Smooth second-order damped zoom wheel
    const onWheel = (e) => {
      e.preventDefault();
      lastUserInteractionTime = Date.now();
      isAutoOrbiting = false;

      const zoomDelta = e.deltaY * 0.02;
      targetSpherical.radius = Math.max(8.5, Math.min(38.0, targetSpherical.radius + zoomDelta));
      setCameraZoomRadius(Math.round(targetSpherical.radius));
    };

    // Click selection
    const onClick = (e) => {
      if (e.target !== renderer.domElement) return;
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(interactiveHitMeshes);

      if (intersects.length > 0) {
        const nodeData = intersects[0].object.userData;
        setActiveNode(nodeData.job);
        if (onSelectJobRef.current) {
          onSelectJobRef.current(nodeData.job);
        }

        // Focus camera onto selected node
        const targetPos = nodeData.basePos;
        targetLookAt.copy(targetPos);
        targetSpherical.radius = 14;
      }
    };

    // Double click to reset focus to scene origin
    const onDoubleClick = (e) => {
      if (e.target !== renderer.domElement) return;
      targetLookAt.set(0, 0, 0);
      targetSpherical.radius = initialRadius;
      targetSpherical.theta = initialTheta;
      targetSpherical.phi = initialPhi;
      setActiveNode(null);
      if (onSelectJobRef.current) {
        onSelectJobRef.current(null);
      }
    };

    container.addEventListener("pointermove", onPointerMove);
    container.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointerup", onPointerUp);
    container.addEventListener("wheel", onWheel, { passive: false });
    container.addEventListener("click", onClick);
    container.addEventListener("dblclick", onDoubleClick);

    // Responsive Canvas Resize
    const onResize = () => {
      const w = container.clientWidth || 900;
      const h = container.clientHeight || 560;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    // ------------------------------------------------------------------------
    // 11. EXTERNAL COMMAND BRIDGES (Camera Presets & Controls)
    // ------------------------------------------------------------------------
    triggerFocusRef.current = (job) => {
      const found = nodeStateEntries.find((entry) => entry.job.id === job.id);
      if (found) {
        setActiveNode(found.job);
        targetLookAt.copy(found.basePos);
        targetSpherical.radius = 12.5;
        setViewPreset("focus");
      }
    };

    triggerZoomRef.current = (direction) => {
      lastUserInteractionTime = Date.now();
      const delta = direction === "in" ? -4 : 4;
      targetSpherical.radius = Math.max(8.5, Math.min(38.0, targetSpherical.radius + delta));
      setCameraZoomRadius(Math.round(targetSpherical.radius));
    };

    triggerPresetRef.current = (preset) => {
      lastUserInteractionTime = Date.now();
      setViewPreset(preset);
      if (preset === "topdown") {
        targetLookAt.set(0, 0, 0);
        targetSpherical.phi = 0.12;
        targetSpherical.radius = 28;
      } else if (preset === "cinematic") {
        targetLookAt.set(0, 0, 0);
        targetSpherical.phi = Math.PI / 3.1;
        targetSpherical.theta = Math.PI / 4.2;
        targetSpherical.radius = 22;
      } else if (preset === "horizon") {
        targetLookAt.set(0, 0, 0);
        targetSpherical.phi = Math.PI / 2.15;
        targetSpherical.radius = 18;
      }
    };

    // ------------------------------------------------------------------------
    // 12. PHYSICS INTEGRATION & ANIMATION LOOP
    // ------------------------------------------------------------------------
    let animationFrameId = null;
    const clock = new THREE.Clock();

    // Tab visibility handling: pause RAF when backgrounded, resume when foregrounded
    let isTabVisible = !document.hidden;

    const onVisibilityChange = () => {
      isTabVisible = !document.hidden;
      if (isTabVisible) {
        if (!animationFrameId) {
          clock.getDelta(); // reset delta accumulator
          animationFrameId = requestAnimationFrame(animate);
        }
      } else {
        if (animationFrameId) {
          cancelAnimationFrame(animationFrameId);
          animationFrameId = null;
        }
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);

    const animate = () => {
      if (!isTabVisible || document.hidden) {
        animationFrameId = null;
        return;
      }

      const dt = Math.min(clock.getDelta(), 0.1);
      const elapsedTime = clock.getElapsedTime();

      // 1. Subtle auto-orbit when user is idle for more than 4 seconds
      if (Date.now() - lastUserInteractionTime > 4000) {
        targetSpherical.theta += 0.0015;
      }

      // 2. Second-Order Dynamics Integration for Camera Spherical Coordinates
      // Parameters: f=1.5, z=0.8, r=2.0
      const currentCameraSpherical = cameraSphericalDynamics.update(
        dt,
        targetSpherical.radius,
        targetSpherical.theta,
        targetSpherical.phi
      );

      // 3. Second-Order Dynamics Integration for Camera LookAt Target
      const currentLookAtPos = cameraLookAtDynamics.update(
        dt,
        targetLookAt.x,
        targetLookAt.y,
        targetLookAt.z
      );

      // Update camera position via spherical projection (zero heap allocation)
      _scratchSpherical.set(
        currentCameraSpherical.x, // radius
        currentCameraSpherical.z, // phi
        currentCameraSpherical.y  // theta
      );
      camera.position.setFromSpherical(_scratchSpherical);
      // Offset camera by dynamic lookAt
      _scratchLookOffset.set(currentLookAtPos.x, currentLookAtPos.y, currentLookAtPos.z);
      camera.position.add(_scratchLookOffset);
      camera.lookAt(_scratchLookOffset);

      // 4. Rotate Candidate Origin Core and Particles
      innerCoreMesh.rotation.y += 0.006;
      innerCoreMesh.rotation.x = Math.sin(elapsedTime * 0.8) * 0.15;
      cageMesh.rotation.y -= 0.009;
      cageMesh.rotation.z += 0.004;
      haloParticleSystem.rotation.y += 0.004;
      dustSystem.rotation.y += 0.0003;

      // 5. Active Rotating Radar Sonar Sweep Beam
      sweepGroup.rotation.y += 0.016;

      // Dynamic Expanding Ground Sonar Wave
      pulseProgress += dt * 0.45;
      if (pulseProgress > 1.0) {
        pulseProgress = 0;
      }
      pulseRingMesh.scale.setScalar(1.0 + pulseProgress * 22);
      pulseRingMat.opacity = Math.max(0, 0.45 * (1.0 - pulseProgress));

      // 6. Raycast Hover Detection for Stellar Nodes (Pre-allocated scratch array)
      if (!isDragging) {
        raycaster.setFromCamera(mouse, camera);
        _scratchIntersects.length = 0;
        raycaster.intersectObjects(interactiveHitMeshes, false, _scratchIntersects);

        if (_scratchIntersects.length > 0) {
          const hitData = _scratchIntersects[0].object.userData;
          if (activeHoveredNodeData !== hitData) {
            // Restore previous node target scale
            if (activeHoveredNodeData) {
              activeHoveredNodeData.targetScale = 1.0;
            }
            activeHoveredNodeData = hitData;
            hitData.targetScale = 1.6;
            setHoveredNode(hitData.job);
            if (onHoverJobRef.current) {
              onHoverJobRef.current(hitData.job);
            }
          }
        } else if (activeHoveredNodeData) {
          activeHoveredNodeData.targetScale = 1.0;
          activeHoveredNodeData = null;
          setHoveredNode(null);
          if (onHoverJobRef.current) {
            onHoverJobRef.current(null);
          }
        }
      }

      // 7. Update Stellar Nodes & Holographic Halos via Second-Order Dynamics (zero closure loop)
      for (let i = 0, len = nodeStateEntries.length; i < len; i++) {
        const entry = nodeStateEntries[i];
        const crystalMesh = entry.crystalMesh;
        const haloTorusMesh = entry.haloTorusMesh;
        const scaleDynamics = entry.scaleDynamics;
        const targetScale = entry.targetScale;
        const basePos = entry.basePos;
        const parentGroup = entry.parentGroup;

        // Dynamic scale computed through Second-Order Dynamics
        const currentScale = scaleDynamics.update(dt, targetScale);
        crystalMesh.scale.setScalar(currentScale);
        haloTorusMesh.scale.setScalar(currentScale * 1.15);

        // Continuous organic hovering motion
        crystalMesh.rotation.x += 0.012;
        crystalMesh.rotation.y += 0.018;
        haloTorusMesh.rotation.z -= 0.022;

        // Gentle vertical levitation oscillation
        parentGroup.position.y = basePos.y + Math.sin(elapsedTime * 2.2 + entry.index) * 0.18;
      }

      // 8. Compute 2D Screen-space Projection for Holographic Data Capsule (zero heap allocation & direct DOM updates)
      let targetInspectNode = activeHoveredNodeData;
      if (!targetInspectNode && activeNode) {
        for (let i = 0, len = nodeStateEntries.length; i < len; i++) {
          if (nodeStateEntries[i].job.id === activeNode.id) {
            targetInspectNode = nodeStateEntries[i];
            break;
          }
        }
      }

      if (targetInspectNode) {
        targetInspectNode.parentGroup.getWorldPosition(_scratchWorldPos);
        _scratchWorldPos.y += 1.8; // Offset slightly above node
        _scratchWorldPos.project(camera);

        // Check if node is in front of camera frustum
        if (_scratchWorldPos.z < 1) {
          const screenX = ((_scratchWorldPos.x + 1) * width) / 2;
          const screenY = ((-_scratchWorldPos.y + 1) * height) / 2;
          const posX = Math.min(Math.max(20, screenX - 140), width - 300);
          const posY = Math.max(50, Math.min(screenY - 120, height - 220));

          if (capsuleRef.current) {
            capsuleRef.current.style.display = "block";
            capsuleRef.current.style.opacity = "1";
            capsuleRef.current.style.transform = "translate3d(" + posX + "px," + posY + "px, 0)";
          }
        } else {
          if (capsuleRef.current) {
            capsuleRef.current.style.display = "none";
            capsuleRef.current.style.opacity = "0";
          }
        }
      } else {
        if (capsuleRef.current) {
          capsuleRef.current.style.display = "none";
          capsuleRef.current.style.opacity = "0";
        }
      }

      renderer.render(scene, camera);
      animationFrameId = requestAnimationFrame(animate);
    };

    animationFrameId = requestAnimationFrame(animate);

    // ------------------------------------------------------------------------
    // CLEANUP ON UNMOUNT
    // ------------------------------------------------------------------------
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
      }
      document.removeEventListener("visibilitychange", onVisibilityChange);
      container.removeEventListener("pointermove", onPointerMove);
      container.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointerup", onPointerUp);
      container.removeEventListener("wheel", onWheel);
      container.removeEventListener("click", onClick);
      container.removeEventListener("dblclick", onDoubleClick);
      window.removeEventListener("resize", onResize);

      scene.traverse((obj) => {
        if (obj.geometry) {
          obj.geometry.dispose();
        }
        if (obj.material) {
          if (Array.isArray(obj.material)) {
            obj.material.forEach((mat) => mat.dispose());
          } else {
            obj.material.dispose();
          }
        }
      });

      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [displayJobs]);

  // Handle preset buttons
  const handlePreset = (preset) => {
    if (triggerPresetRef.current) {
      triggerPresetRef.current(preset);
    }
  };

  // Handle zoom buttons
  const handleZoom = (dir) => {
    if (triggerZoomRef.current) {
      triggerZoomRef.current(dir);
    }
  };

  // Inspecting Job Capsule (either hovered or active node)
  const currentCapsuleJob = hoveredNode || activeNode;

  return (
    <div className="three-spatial-viewport relative w-full h-[580px] rounded-2xl overflow-hidden border border-[#24231f]/12 bg-[#faf7f0]/85 backdrop-blur-xl shadow-sm select-none touch-pan-y">
      {/* Three.js Canvas Container */}
      <div
        ref={mountRef}
        className="w-full h-full cursor-grab active:cursor-grabbing outline-none"
      />

      {/* TOP LEFT: REAL-TIME RADAR TELEMETRY HUD OVERLAY (Warm Editorial Style) */}
      <div className="absolute top-4 left-4 pointer-events-none flex flex-col gap-2 z-20">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] tracking-widest text-[#24231f] bg-[#faf7f0]/90 border border-[#24231f]/12 px-3.5 py-1.5 rounded-full flex items-center gap-2 backdrop-blur-xl shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-600 animate-ping" />
            3D ORBITAL TALENT RADAR
          </span>
          <span className="font-mono text-[10px] text-[#706e68] bg-[#faf7f0]/80 px-3 py-1.5 rounded-full border border-[#24231f]/10 backdrop-blur-md">
            NODES: {displayJobs.length}
          </span>
        </div>

        {/* Dynamic Physics Badge */}
        <div className="flex items-center gap-2">
          <span className="font-mono text-[9px] text-[#706e68] bg-[#faf7f0]/75 px-2.5 py-1 rounded-md border border-[#24231f]/10 backdrop-blur-md">
            PHYSICS: 2ND-ORDER (f=1.5, z=0.8, r=2.0)
          </span>
          <span className="font-mono text-[9px] text-[#8c7851] bg-[#faf7f0]/75 px-2.5 py-1 rounded-md border border-[#8c7851]/20 backdrop-blur-md">
            RANGE: 20 AU
          </span>
        </div>
      </div>

      {/* TOP RIGHT: CAMERA PRESET CONTROLS & ZOOM BUTTONS (Editorial Glass HUD) */}
      <div className="absolute top-4 right-4 flex items-center gap-2 z-20">
        {/* Preset View Buttons */}
        <div className="flex items-center bg-[#faf7f0]/90 border border-[#24231f]/12 rounded-xl p-1 backdrop-blur-xl shadow-sm">
          <button
            type="button"
            onClick={() => handlePreset("cinematic")}
            className={`font-mono text-[10px] px-2.5 py-1 rounded-lg transition-all ${
              viewPreset === "cinematic"
                ? "bg-[#24231f] text-[#faf7f0] font-bold shadow-xs"
                : "text-[#706e68] hover:text-[#24231f]"
            }`}
            title="Cinematic Perspective View"
          >
            🌌 Orbit 45°
          </button>
          <button
            type="button"
            onClick={() => handlePreset("topdown")}
            className={`font-mono text-[10px] px-2.5 py-1 rounded-lg transition-all ${
              viewPreset === "topdown"
                ? "bg-[#24231f] text-[#faf7f0] font-bold shadow-xs"
                : "text-[#706e68] hover:text-[#24231f]"
            }`}
            title="Top-Down Sonar Radar View"
          >
            📡 Sonar Grid
          </button>
          <button
            type="button"
            onClick={() => handlePreset("horizon")}
            className={`font-mono text-[10px] px-2.5 py-1 rounded-lg transition-all ${
              viewPreset === "horizon"
                ? "bg-[#24231f] text-[#faf7f0] font-bold shadow-xs"
                : "text-[#706e68] hover:text-[#24231f]"
            }`}
            title="Ground Horizon View"
          >
            🪐 Horizon
          </button>
        </div>

        {/* Zoom In / Out Buttons */}
        <div className="flex items-center bg-[#faf7f0]/90 border border-[#24231f]/12 rounded-xl p-0.5 backdrop-blur-xl shadow-sm">
          <button
            type="button"
            onClick={() => handleZoom("in")}
            className="w-7 h-7 text-[#706e68] hover:text-[#24231f] hover:bg-black/5 rounded-lg flex items-center justify-center font-bold text-xs"
            title="Zoom In"
          >
            +
          </button>
          <button
            type="button"
            onClick={() => handleZoom("out")}
            className="w-7 h-7 text-[#706e68] hover:text-[#24231f] hover:bg-black/5 rounded-lg flex items-center justify-center font-bold text-xs"
            title="Zoom Out"
          >
            -
          </button>
        </div>
      </div>

      {/* BOTTOM LEFT: INTERACTION GUIDE PILL */}
      <div className="absolute bottom-4 left-4 pointer-events-none flex items-center gap-2 z-20">
        <div className="font-mono text-[10px] text-[#706e68] bg-[#faf7f0]/90 px-3.5 py-1.5 rounded-xl border border-[#24231f]/12 backdrop-blur-xl shadow-sm flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="text-[#24231f] font-semibold">🖱️ Drag</span> Orbit
          </span>
          <span className="text-[#24231f]/20">•</span>
          <span className="flex items-center gap-1">
            <span className="text-[#24231f] font-semibold">📜 Scroll</span> Zoom ({cameraZoomRadius} AU)
          </span>
          <span className="text-[#24231f]/20">•</span>
          <span className="flex items-center gap-1">
            <span className="text-[#24231f] font-semibold">🎯 Click Node</span> Focus Capsule
          </span>
          <span className="text-[#24231f]/20">•</span>
          <span className="flex items-center gap-1">
            <span className="text-[#24231f] font-semibold">⚡ 2x Click</span> Recenter
          </span>
        </div>
      </div>

      {/* BOTTOM RIGHT: RADAR LEGEND PILL */}
      <div className="absolute bottom-4 right-4 pointer-events-none flex items-center gap-2 z-20">
        <div className="font-mono text-[10px] bg-[#faf7f0]/90 px-3 py-1.5 rounded-xl border border-[#24231f]/12 backdrop-blur-xl flex items-center gap-3 shadow-sm text-[#706e68]">
          <span className="flex items-center gap-1.5 text-emerald-800 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-600" /> Low Ghosting (Direct ATS)
          </span>
          <span className="flex items-center gap-1.5 text-amber-800 font-medium">
            <span className="w-2 h-2 rounded-full bg-amber-600" /> Moderate
          </span>
        </div>
      </div>

      {/* =========================================================================
          HOLOGRAPHIC DATA CAPSULE (PINNED 3D PROJECTION + EDITORIAL GLASS)
          Direct DOM-manipulated ref to eliminate 60 FPS React re-renders
          ========================================================================= */}
      {currentCapsuleJob && (
        <div
          ref={capsuleRef}
          className="absolute pointer-events-auto z-30 transition-all duration-75 ease-out"
          style={{
            display: "none",
            opacity: 0,
            left: 0,
            top: 0,
            transform: "translate3d(0px, 0px, 0)",
          }}
        >
          {/* Editorial Glass Capsule Card */}
          <div className="w-[300px] bg-[#faf7f0]/95 border border-[#24231f]/15 rounded-2xl p-4 shadow-xl backdrop-blur-2xl text-left animate-fade-in relative font-sans text-[#24231f]">
            {/* Header: Company & Ghosting Authenticity Badge */}
            <div className="flex items-center justify-between gap-2 mb-2 relative z-10">
              <span className="font-mono text-[11px] uppercase tracking-wider text-[#24231f] font-bold truncate">
                {currentCapsuleJob.company}
              </span>
              <span
                className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold border ${
                  currentCapsuleJob.ghosting_risk === "low"
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                    : "bg-amber-50 text-amber-800 border-amber-200"
                }`}
              >
                {currentCapsuleJob.ghosting_risk === "low" ? "🟢 Direct ATS" : "🟡 Review"}
              </span>
            </div>

            {/* Job Title */}
            <h4 className="font-serif text-sm font-semibold text-[#24231f] leading-snug line-clamp-2 mb-2.5">
              {currentCapsuleJob.title}
            </h4>

            {/* Quick Metrics Bar: Match Score & Location */}
            <div className="grid grid-cols-2 gap-2 py-2 px-2.5 rounded-xl bg-white/70 border border-[#24231f]/10 font-mono text-[10px] mb-3">
              <div>
                <span className="text-[#706e68] block text-[8px] uppercase">Match Score</span>
                <span className="text-emerald-700 font-bold text-xs">
                  {Math.round(currentCapsuleJob.score || 94)}% Fit
                </span>
              </div>
              <div>
                <span className="text-[#706e68] block text-[8px] uppercase">Portal Type</span>
                <span className="text-[#24231f] font-semibold capitalize truncate block">
                  {currentCapsuleJob.ats_provider || "Greenhouse"}
                </span>
              </div>
            </div>

            {/* Target CTC & Notice Period Details (if present) */}
            {(currentCapsuleJob.ctc_range || currentCapsuleJob.notice) && (
              <div className="flex items-center justify-between font-mono text-[9px] text-[#706e68] mb-3 px-1">
                <span>💰 {currentCapsuleJob.ctc_range || "₹25 - 40 LPA"}</span>
                <span>⏱️ {currentCapsuleJob.notice || "≤ 30 Days"}</span>
              </div>
            )}

            {/* CTA Button: Direct Apply / Inspect */}
            <button
              type="button"
              onClick={() => {
                if (onSelectJobRef.current) {
                  onSelectJobRef.current(currentCapsuleJob);
                }
              }}
              className="w-full font-mono text-xs py-2 rounded-xl font-medium bg-[#24231f] text-[#faf7f0] hover:bg-[#3d3a33] active:scale-95 transition-all shadow-sm flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <span>Inspect Requisition Details</span>
              <span>→</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
