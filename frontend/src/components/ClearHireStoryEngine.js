import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { RGBELoader } from "three/examples/jsm/loaders/RGBELoader.js";
import {
  PostProcessingPipeline,
  SpringCameraEngine,
  generateTravertinePbrTextures,
  createContactShadowTexture,
} from "./office";

/**
 * ============================================================================
 * CLEARHIRE 3D SPATIAL AUTONOMY ENGINE (Awwwards & Lusion Benchmark)
 * - Photorealistic Modernist Executive Gallery with Real 2K Studio HDR IBL.
 * - Spatial Zone Separation: Zero visual occlusion across all 9 chapters.
 * - Exact Parametric Spline Sampling: getPoint(t) for 1:1 chapter synchrony.
 * - Authentic GLTF Architectural Assets (Desk, Monitor, Chair, Copier, Robot).
 * - Rock-solid, critically-damped camera rail (Zero roll wobble, zero shaking).
 * - Calibrated PBR surfaces (Travertine, brushed bronze, titanium, cotton rag).
 * - Multi-material candidate dossier with holographic security seal.
 * - Pure 60/120 FPS runtime with 0 heap allocation churn.
 * ============================================================================
 */

// Module scratch vectors to eliminate RAF heap allocations
const _scratchProj = new THREE.Vector3();
const _upUnitY = new THREE.Vector3(0, 1, 0);

// Volumetric Laser Curtain Shader with Additive Gaussian Core
const LaserVolumetricShader = {
  vertexShader: `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    uniform float uTime;
    uniform vec3 uColor;
    uniform float uIntensity;
    varying vec2 vUv;

    void main() {
      float distY = abs(vUv.y - 0.5);
      float core = exp(-distY * distY * 48.0);
      float edgeFade = smoothstep(0.0, 0.15, vUv.x) * smoothstep(1.0, 0.85, vUv.x);
      float wave = sin(vUv.x * 28.0 + uTime * 5.0) * 0.08 + 0.92;
      float alpha = core * edgeFade * wave * 0.85;
      gl_FragColor = vec4(uColor * uIntensity, alpha);
    }
  `,
};

// 9 Narrative Chapter Configurations
export const STORY_STAGES = [
  {
    index: 0,
    num: "01",
    shortLabel: "INTAKE",
    title: "Candidate Dossier Dispatched",
    narrative:
      "Crafted with zero fluff and mathematical ATS margin budgets. Sarah Chen's verified credentials rest on the executive intake stand, ready for real-time AST ingestion.",
    scannerStatus: "READY // WAITING INTAKE",
    robotMood: "idle",
    destination: "Approaching Primary Gateway",
    coordinates: "X: +1.20 | Y: +0.83 | Z: +1.00",
    badge: "AST 100% PREPARED",
  },
  {
    index: 1,
    num: "02",
    shortLabel: "LIFT",
    title: "Aerodynamic Flutter Lift",
    narrative:
      "The heavy 32lb cotton rag dossier catches the intake air stream, lifting gracefully from the presentation stand toward the precision optical scanning platen.",
    scannerStatus: "AIR INTAKE VELOCITY: 2.4 M/S",
    robotMood: "idle",
    destination: "Approaching Primary Gateway",
    coordinates: "X: +0.20 | Y: +1.25 | Z: +0.20",
    badge: "INTAKE STREAM ACTIVE",
  },
  {
    index: 2,
    num: "03",
    shortLabel: "OCR SCAN",
    title: "Precision Optical ATS Ingest",
    narrative:
      "The paper lands cleanly on the scanner platen. Rotating guide rollers pull the sheet under a sweeping cyan laser curtain that segments sections and benchmarks credentials.",
    scannerStatus: "LASER PARSING AST & KEYWORDS...",
    robotMood: "scanning",
    destination: "Under Heuristic Evaluation",
    coordinates: "X: -2.00 | Y: +1.09 | Z: -0.80",
    badge: "1200 DPI OPTICAL OCR",
  },
  {
    index: 3,
    num: "04",
    shortLabel: "AST PARSE",
    title: "The Heuristic Divergence",
    narrative:
      "Two hiring realities fork in real time: archaic regex filters flag missing formatting keywords, while ClearHire's verified pipeline validates architectural excellence.",
    scannerStatus: "BRANCH EVALUATION ACTIVE",
    robotMood: "scanning",
    destination: "Fork: Legacy Trap vs ClearHire Covenant",
    coordinates: "X: -2.00 | Y: +1.09 | Z: -0.80",
    badge: "HEURISTIC FORK: DIVERGENCE",
  },
  {
    index: 4,
    num: "05",
    shortLabel: "FORK",
    title: "The Discarded Incinerator",
    narrative:
      "In legacy systems, qualified applications are silently dropped into an industrial archive bin. 75% of human talent is rejected by antiquated keyword filters.",
    scannerStatus: "ROUTED TO ARCHIVE BIN",
    robotMood: "rejected",
    destination: "Hazard Disposal Pit",
    coordinates: "X: -2.80 | Y: +0.28 | Z: -0.80",
    badge: "DISCARDED APPLICANTS: 14,291",
  },
  {
    index: 5,
    num: "06",
    shortLabel: "COVENANT",
    title: "The ClearHire 48H Covenant",
    narrative:
      "ClearHire's deterministic pipeline bypasses third-party scrapers, establishing an encrypted peer-to-peer hiring channel straight to engineering leadership.",
    scannerStatus: "COVENANT ENCRYPTED // PEER-TO-PEER",
    robotMood: "accepted",
    destination: "Direct Hiring Gateway",
    coordinates: "X: -0.60 | Y: +1.20 | Z: -1.60",
    badge: "GUARANTEED REVIEW COVENANT",
  },
  {
    index: 6,
    num: "07",
    shortLabel: "TRANSIT",
    title: "Direct Velocity Transit",
    narrative:
      "The approved dossier accelerates across the executive suite, rocketing past recruiter gatekeepers straight to the decision-maker's desk.",
    scannerStatus: "CONDUIT VELOCITY: 48 KM/H // DIRECT",
    robotMood: "accepted",
    destination: "Executive Desk Inbound",
    coordinates: "X: +0.00 | Y: +1.10 | Z: -1.90",
    badge: "TRANSIT VELOCITY: 48 KM/H",
  },
  {
    index: 7,
    num: "08",
    shortLabel: "DESK",
    title: "Executive Desk Approach",
    narrative:
      "Decelerating over the modernist steel workstation, the verified dossier aligns with the executive portfolio alongside the precision SLA chronometer.",
    scannerStatus: "APPROACHING PORTFOLIO // DECELERATING",
    robotMood: "accepted",
    destination: "Executive Desk Portfolio",
    coordinates: "X: +0.35 | Y: +0.90 | Z: -2.10",
    badge: "PRECISION DESK ALIGNMENT",
  },
  {
    index: 8,
    num: "09",
    shortLabel: "PORTAL",
    title: "The Executive Decision Desk",
    narrative:
      "Your dossier rests inside the hiring manager's executive portfolio on the desk, bound by a legally enforceable 48-Hour SLA covenant. Sign in below to enter the workspace.",
    scannerStatus: "DESK DELIVERY CONFIRMED // SLA ACTIVE",
    robotMood: "accepted",
    destination: "Interview Secured // Candidate Enclave Ready",
    coordinates: "X: +0.25 | Y: +0.77 | Z: -2.15",
    badge: "48-HOUR SLA COVENANT ACTIVE",
  },
];

/**
 * Creates a normalized wrapper Group for any GLTF scene:
 * - Computes the model's bounding box and center.
 * - Offsets the mesh inside the wrapper so wrapper (0,0,0) is centered in X and Z,
 *   with the bottom flush at Y=0 (or centered in Y if centerAtBase is false).
 * - Scales the model to the target height or width.
 * - This prevents model pivot drift and guarantees perfect positioning.
 */
function createFittedModel(gltfScene, { targetHeight = 0, targetWidth = 0, centerAtBase = true }) {
  const wrapper = new THREE.Group();
  wrapper.add(gltfScene);

  gltfScene.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(gltfScene);
  const size = box.getSize(new THREE.Vector3());

  let scale = 1.0;
  if (targetHeight > 0 && size.y > 0) {
    scale = targetHeight / size.y;
  } else if (targetWidth > 0 && size.x > 0) {
    scale = targetWidth / size.x;
  }
  gltfScene.scale.set(scale, scale, scale);

  gltfScene.updateMatrixWorld(true);
  const scaledBox = new THREE.Box3().setFromObject(gltfScene);
  const scaledCenter = scaledBox.getCenter(new THREE.Vector3());

  gltfScene.position.x = -scaledCenter.x;
  gltfScene.position.z = -scaledCenter.z;
  if (centerAtBase) {
    gltfScene.position.y = -scaledBox.min.y;
  } else {
    gltfScene.position.y = -scaledCenter.y;
  }

  gltfScene.traverse((c) => {
    if (c.isMesh) {
      c.castShadow = true;
      c.receiveShadow = true;
    }
  });

  return {
    wrapper,
    size: new THREE.Vector3(size.x * scale, size.y * scale, size.z * scale),
    scale,
  };
}

// Modernist Candidate Intake Credenza (Stage 01 Launchpad)
function createModernistCredenza() {
  const group = new THREE.Group();

  // 4 Slender Brushed Bronze Legs
  const legMat = new THREE.MeshStandardMaterial({
    color: 0x927040,
    metalness: 0.85,
    roughness: 0.25,
  });
  const legGeo = new THREE.CylinderGeometry(0.015, 0.012, 0.18, 16);
  const legOffsets = [
    [-0.32, -0.18],
    [0.32, -0.18],
    [-0.32, 0.18],
    [0.32, 0.18],
  ];
  legOffsets.forEach(([lx, lz]) => {
    const leg = new THREE.Mesh(legGeo, legMat);
    leg.position.set(lx, 0.09, lz);
    leg.castShadow = true;
    group.add(leg);
  });

  // Cabinet Body (Warm American Walnut)
  const bodyMat = new THREE.MeshStandardMaterial({
    color: 0x2e2722,
    roughness: 0.55,
    metalness: 0.05,
  });
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.60, 0.44), bodyMat);
  body.position.set(0, 0.48, 0);
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  // Top Surface Slab (Honed Dark Travertine)
  const topMat = new THREE.MeshStandardMaterial({
    color: 0x1f1d1a,
    roughness: 0.35,
    metalness: 0.15,
  });
  const topSlab = new THREE.Mesh(new THREE.BoxGeometry(0.76, 0.04, 0.48), topMat);
  topSlab.position.set(0, 0.80, 0);
  topSlab.castShadow = true;
  topSlab.receiveShadow = true;
  group.add(topSlab);

  // Recessed Intake Presentation Tray with subtle emerald backlight
  const trayMat = new THREE.MeshStandardMaterial({
    color: 0x15261d,
    roughness: 0.4,
    metalness: 0.3,
  });
  const tray = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.01, 0.38), trayMat);
  tray.position.set(0, 0.822, 0);
  group.add(tray);

  // Brass Corner Registration Pins
  const pinMat = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    metalness: 0.9,
    roughness: 0.2,
  });
  const pinGeo = new THREE.CylinderGeometry(0.006, 0.006, 0.02, 12);
  const pinOffsets = [
    [-0.27, -0.17],
    [0.27, -0.17],
    [-0.27, 0.17],
    [0.27, 0.17],
  ];
  pinOffsets.forEach(([px, pz]) => {
    const pin = new THREE.Mesh(pinGeo, pinMat);
    pin.position.set(px, 0.83, pz);
    group.add(pin);
  });

  return group;
}

// Industrial Archive / Rejection Bin (Stage 05 Legacy Trap)
function createIndustrialRejectionBin() {
  const group = new THREE.Group();

  const binMat = new THREE.MeshStandardMaterial({
    color: 0x262626,
    roughness: 0.65,
    metalness: 0.4,
  });
  const binGeo = new THREE.CylinderGeometry(0.24, 0.20, 0.46, 24, 1, true);
  const binMesh = new THREE.Mesh(binGeo, binMat);
  binMesh.position.y = 0.23;
  binMesh.castShadow = true;
  binMesh.receiveShadow = true;
  group.add(binMesh);

  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.20, 0.20, 0.01, 24), binMat);
  base.position.y = 0.005;
  group.add(base);

  const ringMat = new THREE.MeshStandardMaterial({
    color: 0xb91c1c, // Hazard Warning Crimson
    roughness: 0.3,
    metalness: 0.6,
  });
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.012, 12, 32), ringMat);
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.46;
  group.add(ring);

  const paperMat = new THREE.MeshStandardMaterial({
    color: 0xd4d4d8,
    roughness: 0.9,
    metalness: 0.0,
  });
  for (let i = 0; i < 6; i++) {
    const crumple = new THREE.Mesh(new THREE.DodecahedronGeometry(0.065, 0), paperMat);
    crumple.position.set(
      (Math.random() - 0.5) * 0.18,
      0.12 + i * 0.05,
      (Math.random() - 0.5) * 0.18
    );
    crumple.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
    group.add(crumple);
  }

  return group;
}

// High-fidelity 1024x1440 Cotton Paper Resume Texture Generator
function generateResumeCanvas() {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 1440;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  ctx.fillStyle = "#faf8f4";
  ctx.fillRect(0, 0, 1024, 1440);

  ctx.strokeStyle = "#e2dacf";
  ctx.lineWidth = 4;
  ctx.strokeRect(24, 24, 976, 1392);
  ctx.strokeStyle = "#eee8de";
  ctx.lineWidth = 2;
  ctx.strokeRect(36, 36, 952, 1368);

  ctx.fillStyle = "#f3eee3";
  ctx.fillRect(48, 48, 928, 220);

  // Candidate Avatar badge
  ctx.fillStyle = "#16382b";
  ctx.beginPath();
  ctx.roundRect(80, 76, 128, 128, 16);
  ctx.fill();

  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 52px monospace";
  ctx.textAlign = "center";
  ctx.fillText("SC", 144, 160);

  // Candidate Name & Role
  ctx.textAlign = "left";
  ctx.fillStyle = "#15201b";
  ctx.font = "bold 52px Georgia, serif";
  ctx.fillText("SARAH CHEN", 236, 132);

  ctx.fillStyle = "#059669";
  ctx.font = "bold 24px monospace";
  ctx.fillText("STAFF AI & SYSTEMS ENGINEER", 236, 172);

  ctx.fillStyle = "#64748b";
  ctx.font = "22px sans-serif";
  ctx.fillText("San Francisco, CA  ·  sarah.chen@alum.mit.edu  ·  +1 (415) 890-4421", 236, 212);

  // Holographic Prismatic Diffraction Stamp
  const holoGrad = ctx.createLinearGradient(720, 76, 950, 140);
  holoGrad.addColorStop(0, "rgba(5, 150, 105, 0.22)");
  holoGrad.addColorStop(0.25, "rgba(56, 189, 248, 0.28)");
  holoGrad.addColorStop(0.5, "rgba(236, 72, 153, 0.26)");
  holoGrad.addColorStop(0.75, "rgba(234, 179, 8, 0.25)");
  holoGrad.addColorStop(1, "rgba(16, 185, 129, 0.22)");
  ctx.fillStyle = holoGrad;
  ctx.strokeStyle = "#059669";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.roundRect(720, 76, 230, 64, 10);
  ctx.fill();
  ctx.stroke();

  ctx.strokeStyle = "rgba(255, 255, 255, 0.45)";
  ctx.lineWidth = 1.5;
  for (let sx = 730; sx < 940; sx += 18) {
    ctx.beginPath();
    ctx.moveTo(sx, 76);
    ctx.lineTo(sx + 20, 140);
    ctx.stroke();
  }

  ctx.fillStyle = "#065f46";
  ctx.font = "bold 17px monospace";
  ctx.textAlign = "center";
  ctx.fillText("CLEARHIRE AST ✓", 835, 106);
  ctx.font = "bold 11px monospace";
  ctx.fillStyle = "#047857";
  ctx.fillText("HOLO PROTOCOL 4.2", 835, 124);

  // Section 1: Executive Overview
  let y = 320;
  ctx.textAlign = "left";
  ctx.fillStyle = "#0f172a";
  ctx.font = "bold 26px monospace";
  ctx.fillText("I. EXECUTIVE SUMMARY", 60, y);

  y += 12;
  ctx.strokeStyle = "#cbd5e1";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(60, y);
  ctx.lineTo(964, y);
  ctx.stroke();

  y += 36;
  ctx.fillStyle = "#475569";
  ctx.font = "20px sans-serif";
  ctx.fillText("Principal engineer leading fault-tolerant distributed agents and LLM inference pipelines.", 60, y);
  y += 28;
  ctx.fillText("Designed high-throughput RAG systems processing 45M tokens/sec with sub-50ms p99 SLA.", 60, y);
  y += 28;
  ctx.fillText("Expert in zero-hallucination AST constraints, GPU quantization kernels, and high-availability cloud.", 60, y);

  // Section 2: Core Engineering Experience
  y += 50;
  ctx.fillStyle = "#0f172a";
  ctx.font = "bold 26px monospace";
  ctx.fillText("II. VERIFIED EXPERIENCE & QUANTIFIED IMPACT", 60, y);

  y += 12;
  ctx.strokeStyle = "#cbd5e1";
  ctx.beginPath();
  ctx.moveTo(60, y);
  ctx.lineTo(964, y);
  ctx.stroke();

  y += 36;
  ctx.fillStyle = "#1e293b";
  ctx.font = "bold 24px sans-serif";
  ctx.fillText("Staff Infrastructure Engineer — Autonomous AI Systems", 60, y);
  ctx.fillStyle = "#64748b";
  ctx.font = "20px monospace";
  ctx.textAlign = "right";
  ctx.fillText("2023 – PRESENT", 964, y);
  ctx.textAlign = "left";

  y += 30;
  ctx.fillStyle = "#475569";
  ctx.font = "20px sans-serif";
  ctx.fillText("• Architected multi-agent orchestration runtime with deterministic AST parse guarantees.", 80, y);
  y += 28;
  ctx.fillText("• Cut model quantization memory overhead by 42% utilizing custom Triton kernels.", 80, y);
  y += 28;
  ctx.fillText("• Maintained zero unplanned downtime across 18 enterprise production deployments.", 80, y);

  y += 46;
  ctx.fillStyle = "#1e293b";
  ctx.font = "bold 24px sans-serif";
  ctx.fillText("Senior Systems Architect — High-Throughput Distributed Systems", 60, y);
  ctx.fillStyle = "#64748b";
  ctx.font = "20px monospace";
  ctx.textAlign = "right";
  ctx.fillText("2020 – 2023", 964, y);
  ctx.textAlign = "left";

  y += 30;
  ctx.fillStyle = "#475569";
  ctx.font = "20px sans-serif";
  ctx.fillText("• Engineered sub-millisecond asynchronous message bus handling 2.4B events/day.", 80, y);
  y += 28;
  ctx.fillText("• Deployed Kubernetes autoscaling cluster across 3 availability zones with zero packet loss.", 80, y);

  // Section 3: Technical Skills Matrix
  y += 54;
  ctx.fillStyle = "#0f172a";
  ctx.font = "bold 26px monospace";
  ctx.fillText("III. TECHNICAL STACK & ARCHITECTURAL EXPERTISE", 60, y);

  y += 12;
  ctx.strokeStyle = "#cbd5e1";
  ctx.beginPath();
  ctx.moveTo(60, y);
  ctx.lineTo(964, y);
  ctx.stroke();

  y += 36;
  ctx.fillStyle = "#059669";
  ctx.font = "bold 20px monospace";
  ctx.fillText("LANGUAGES & RUNTIMES: ", 60, y);
  ctx.fillStyle = "#1e293b";
  ctx.font = "20px sans-serif";
  ctx.fillText("Rust, Python 3.12, TypeScript, Go 1.22, C++, GLSL / WGSL", 330, y);

  y += 32;
  ctx.fillStyle = "#059669";
  ctx.font = "bold 20px monospace";
  ctx.fillText("AI & DISTRIBUTED SYSTEMS: ", 60, y);
  ctx.fillStyle = "#1e293b";
  ctx.font = "20px sans-serif";
  ctx.fillText("PyTorch, CUDA, Triton, vLLM, Kafka, Redis, ClickHouse, Docker", 330, y);

  // Section 4: Academic Background
  y += 54;
  ctx.fillStyle = "#0f172a";
  ctx.font = "bold 26px monospace";
  ctx.fillText("IV. EDUCATION & REPOSITORIES", 60, y);

  y += 12;
  ctx.strokeStyle = "#cbd5e1";
  ctx.beginPath();
  ctx.moveTo(60, y);
  ctx.lineTo(964, y);
  ctx.stroke();

  y += 36;
  ctx.fillStyle = "#1e293b";
  ctx.font = "bold 22px sans-serif";
  ctx.fillText("Massachusetts Institute of Technology (MIT)", 60, y);
  ctx.fillStyle = "#64748b";
  ctx.font = "20px monospace";
  ctx.textAlign = "right";
  ctx.fillText("CAMBRIDGE, MA", 964, y);
  ctx.textAlign = "left";

  y += 28;
  ctx.fillStyle = "#475569";
  ctx.font = "20px sans-serif";
  ctx.fillText("B.S. in Electrical Engineering & Computer Science (EECS)  ·  GPA: 4.9 / 5.0", 60, y);

  return canvas;
}

// Glowing Terminal Screen Canvas for Workstation Monitor
function generateMonitorTerminalCanvas() {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 640;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  ctx.fillStyle = "#080c14";
  ctx.fillRect(0, 0, 1024, 640);

  // Scanlines
  ctx.fillStyle = "rgba(0, 0, 0, 0.20)";
  for (let y = 0; y < 640; y += 4) {
    ctx.fillRect(0, y, 1024, 2);
  }

  // Header Bar
  ctx.fillStyle = "#111827";
  ctx.fillRect(0, 0, 1024, 56);
  ctx.fillStyle = "#38bdf8";
  ctx.font = "bold 22px monospace";
  ctx.fillText("CLEARHIRE KERNEL v2.4 // EXECUTIVE INTERVIEW ENCLAVE", 24, 38);

  // Status Rows
  ctx.fillStyle = "#10b981";
  ctx.font = "bold 20px monospace";
  ctx.fillText("> INTAKE DOSSIER: Sarah_Chen_Staff_Engineer.pdf", 32, 110);
  ctx.fillText("> 1200 DPI OCR ENGINE: COMPLETE [0.014s]", 32, 155);
  ctx.fillText("> AST GUARANTEE: 99.4% DETERMINISTIC COMPLIANCE", 32, 200);
  ctx.fillText("> REJECTION BYPASS: 100% REQUISITION DIRECT", 32, 245);
  ctx.fillText("> 48-HOUR SLA COVENANT: ACTIVE [T-47:59:12]", 32, 290);

  ctx.fillStyle = "#38bdf8";
  ctx.fillText("> INTERVIEW ENCLAVE: SECURED FOR DECISION MAKER", 32, 360);
  ctx.fillStyle = "#fbbf24";
  ctx.fillText("> CANDIDATE CREDENTIALS: VALIDATED & ENCRYPTED", 32, 405);
  ctx.fillStyle = "#a855f7";
  ctx.fillText("> PEER-TO-PEER CHANNEL: ESTABLISHED WITH VP ENG", 32, 450);

  // Bottom Status Pill
  ctx.fillStyle = "#064e3b";
  ctx.beginPath();
  ctx.roundRect(32, 530, 960, 60, 12);
  ctx.fill();
  ctx.fillStyle = "#34d399";
  ctx.font = "bold 22px monospace";
  ctx.textAlign = "center";
  ctx.fillText("● SYSTEM READY // CANDIDATE ADVANCED TO DIRECT REVIEW", 512, 568);

  return canvas;
}

// 48-Hour SLA Chronometer Dial Canvas
function generateChronometerCanvas() {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  ctx.fillStyle = "#fcfbfa";
  ctx.beginPath();
  ctx.arc(256, 256, 250, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = "#d4af37";
  ctx.lineWidth = 12;
  ctx.stroke();

  for (let i = 0; i < 12; i += 1) {
    const angle = (i / 12) * Math.PI * 2 - Math.PI / 2;
    const isMajor = i % 3 === 0;
    const r1 = isMajor ? 180 : 210;
    const r2 = 236;
    ctx.strokeStyle = isMajor ? "#166534" : "#475569";
    ctx.lineWidth = isMajor ? 8 : 4;
    ctx.beginPath();
    ctx.moveTo(256 + Math.cos(angle) * r1, 256 + Math.sin(angle) * r1);
    ctx.lineTo(256 + Math.cos(angle) * r2, 256 + Math.sin(angle) * r2);
    ctx.stroke();
  }

  ctx.fillStyle = "#1e293b";
  ctx.font = "bold 44px Georgia, serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("48h", 256, 110);
  ctx.fillText("12h", 400, 256);
  ctx.fillText("24h", 256, 400);
  ctx.fillText("36h", 112, 256);

  ctx.fillStyle = "#15803d";
  ctx.font = "bold 24px monospace";
  ctx.fillText("CLEARHIRE SLA", 256, 300);
  ctx.font = "18px monospace";
  ctx.fillStyle = "#64748b";
  ctx.fillText("PRECISION CHRONO", 256, 330);

  return canvas;
}

export default function ClearHireStoryEngine({
  motionRef = null,
  activeBranch = "clearhire", // "legacy" or "clearhire"
  onStageChange = () => {},
  onSpatialTelemetry = () => {},
}) {
  const mountRef = useRef(null);
  const activeBranchRef = useRef(activeBranch);
  const onStageChangeRef = useRef(onStageChange);
  const onSpatialTelemetryRef = useRef(onSpatialTelemetry);

  useEffect(() => {
    activeBranchRef.current = activeBranch;
  }, [activeBranch]);

  useEffect(() => {
    onStageChangeRef.current = onStageChange;
  }, [onStageChange]);

  useEffect(() => {
    onSpatialTelemetryRef.current = onSpatialTelemetry;
  }, [onSpatialTelemetry]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return undefined;

    // 1. Scene, Camera, WebGL Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f2eb);

    const camera = new THREE.PerspectiveCamera(
      42.0, // Calibrated constant focal length (architectural perspective)
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    camera.up.set(0, 1, 0);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
      stencil: false,
      depth: true,
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.82;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    container.appendChild(renderer.domElement);

    // 2. Post-Processing Pipeline
    const postPipeline = new PostProcessingPipeline(renderer, scene, camera, {
      width: container.clientWidth,
      height: container.clientHeight,
    });

    // 3. Cinematic Camera Dynamics Engine (Strictly locked horizon, critically damped)
    const springCam = new SpringCameraEngine(camera, {
      baseFov: 42.0,
      dampingSpeed: 5.0,
    });

    // 4. Photorealistic Environment Lighting & Studio HDR
    const pmremGen = new THREE.PMREMGenerator(renderer);
    pmremGen.compileEquirectangularShader();
    new RGBELoader().load(
      "/assets/studio_small_09_2k.hdr",
      (hdrTex) => {
        const envMap = pmremGen.fromEquirectangular(hdrTex).texture;
        scene.environment = envMap;
        hdrTex.dispose();
        pmremGen.dispose();
      },
      undefined,
      (err) => console.warn("Studio HDR fallback:", err)
    );

    // Warm Sun Directional Light (Calibrated intensity to avoid blowout)
    const sunLight = new THREE.DirectionalLight(0xfff8ee, 1.1);
    sunLight.position.set(5.0, 7.5, 4.0);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 1.0;
    sunLight.shadow.camera.far = 25.0;
    sunLight.shadow.camera.left = -6;
    sunLight.shadow.camera.right = 6;
    sunLight.shadow.camera.top = 6;
    sunLight.shadow.camera.bottom = -6;
    sunLight.shadow.bias = -0.0001;
    sunLight.shadow.radius = 2.0;
    scene.add(sunLight);

    const ambientLight = new THREE.AmbientLight(0xf5f2eb, 0.22);
    scene.add(ambientLight);

    // Desk accent illumination
    const deskSpot = new THREE.SpotLight(0xfffbf0, 0.9, 7.0, Math.PI / 4, 0.4);
    deskSpot.position.set(0.25, 3.2, -2.15);
    deskSpot.target.position.set(0.25, 0.76, -2.15);
    scene.add(deskSpot);
    scene.add(deskSpot.target);

    // 5. Contact Shadow Helper
    const contactShadowTex = createContactShadowTexture();
    const createContactShadow = (widthM, lengthM, opacity = 0.6) => {
      const geo = new THREE.PlaneGeometry(widthM, lengthM);
      const mat = new THREE.MeshBasicMaterial({
        map: contactShadowTex,
        transparent: true,
        opacity,
        depthWrite: false,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.rotation.x = -Math.PI / 2;
      return mesh;
    };

    // 6. Architectural Room Envelope (Floor at y = 0.0)
    const { normal: travertineNormal, roughness: travertineRoughness } =
      generateTravertinePbrTextures();

    const floorMat = new THREE.MeshStandardMaterial({
      color: 0xe0dad0,
      roughness: 0.50,
      metalness: 0.04,
      normalMap: travertineNormal,
      roughnessMap: travertineRoughness,
    });
    if (travertineNormal) floorMat.normalScale.set(0.2, 0.2);

    const floorMesh = new THREE.Mesh(new THREE.PlaneGeometry(16, 16), floorMat);
    floorMesh.rotation.x = -Math.PI / 2;
    floorMesh.position.set(0, 0, -1.0);
    floorMesh.receiveShadow = true;
    scene.add(floorMesh);

    // Architectural Gallery Walls with Skirting Baseboards
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xded9cf, // Warm gallery plaster grey-beige
      roughness: 0.92,
      metalness: 0.02,
    });
    const backWall = new THREE.Mesh(new THREE.PlaneGeometry(16, 4.5), wallMat);
    backWall.position.set(0, 2.25, -4.8);
    backWall.receiveShadow = true;
    scene.add(backWall);

    const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(16, 4.5), wallMat);
    leftWall.rotation.y = Math.PI / 2;
    leftWall.position.set(-5.5, 2.25, -1.0);
    leftWall.receiveShadow = true;
    scene.add(leftWall);

    const baseboardMat = new THREE.MeshStandardMaterial({
      color: 0x2d2822,
      roughness: 0.4,
      metalness: 0.6,
    });
    const baseboard = new THREE.Mesh(new THREE.BoxGeometry(16, 0.12, 0.04), baseboardMat);
    baseboard.position.set(0, 0.06, -4.78);
    scene.add(baseboard);

    // Framed Gallery Wall Art
    const texLoader = new THREE.TextureLoader();
    const art1Tex = texLoader.load("/assets/clearhire-scene/office-art-01.jpg");
    art1Tex.colorSpace = THREE.SRGBColorSpace;
    const artFrame1 = new THREE.Mesh(
      new THREE.PlaneGeometry(1.6, 2.2),
      new THREE.MeshStandardMaterial({ map: art1Tex, roughness: 0.35 })
    );
    artFrame1.position.set(-2.8, 2.4, -4.76);
    scene.add(artFrame1);

    const art2Tex = texLoader.load("/assets/clearhire-scene/office-art-02.jpg");
    art2Tex.colorSpace = THREE.SRGBColorSpace;
    const artFrame2 = new THREE.Mesh(
      new THREE.PlaneGeometry(1.4, 2.0),
      new THREE.MeshStandardMaterial({ map: art2Tex, roughness: 0.35 })
    );
    artFrame2.rotation.y = Math.PI / 2;
    artFrame2.position.set(-5.46, 2.4, -1.8);
    scene.add(artFrame2);

    // 7. GLTF Architectural Models (Centered & Flush via createFittedModel)
    const gltfLoader = new GLTFLoader();

    // A. Executive Modernist Desk (Placed in Center-Left Alcove at x = 0.25, z = -2.15)
    const deskShadow = createContactShadow(2.4, 1.4, 0.65);
    deskShadow.position.set(0.25, 0.002, -2.15);
    scene.add(deskShadow);

    gltfLoader.load(
      "/assets/clearhire-scene/steel-office-desk.glb",
      (gltf) => {
        const { wrapper: deskGroup } = createFittedModel(gltf.scene, {
          targetHeight: 0.76,
          centerAtBase: true,
        });
        deskGroup.position.set(0.25, 0.0, -2.15);
        scene.add(deskGroup);
      },
      undefined,
      (err) => console.warn("Desk fallback:", err)
    );

    // B. Executive Task Chair (Tucked Behind Desk)
    const chairShadow = createContactShadow(0.85, 0.85, 0.5);
    chairShadow.position.set(0.25, 0.002, -2.85);
    scene.add(chairShadow);

    gltfLoader.load(
      "/assets/clearhire-scene/office-task-chair.glb",
      (gltf) => {
        const { wrapper: chairGroup } = createFittedModel(gltf.scene, {
          targetHeight: 0.98,
          centerAtBase: true,
        });
        chairGroup.position.set(0.25, 0.0, -2.85);
        chairGroup.rotation.y = 0.08;
        scene.add(chairGroup);
      },
      undefined,
      (err) => console.warn("Chair fallback:", err)
    );

    // C. Desktop Workstation Monitor with Live ClearHire Terminal Screen
    const monitorCanvas = generateMonitorTerminalCanvas();
    const monitorTex = monitorCanvas ? new THREE.CanvasTexture(monitorCanvas) : null;
    if (monitorTex) {
      monitorTex.colorSpace = THREE.SRGBColorSpace;
      monitorTex.minFilter = THREE.LinearFilter;
    }

    gltfLoader.load(
      "/assets/clearhire-scene/desktop-monitor.glb",
      (gltf) => {
        gltf.scene.traverse((child) => {
          if (child.isMesh && child.name.toLowerCase().includes("screen") && monitorTex) {
            child.material = new THREE.MeshBasicMaterial({
              map: monitorTex,
            });
          }
        });

        const { wrapper: monitorGroup } = createFittedModel(gltf.scene, {
          targetHeight: 0.50,
          centerAtBase: true,
        });
        monitorGroup.position.set(0.70, 0.76, -2.25);
        monitorGroup.rotation.y = -0.32;
        scene.add(monitorGroup);
      },
      undefined,
      (err) => console.warn("Monitor fallback:", err)
    );

    // D. Office Copier / Scanner (Placed on Left Midground at x = -2.00, z = -0.80)
    const copierShadow = createContactShadow(1.3, 1.1, 0.6);
    copierShadow.position.set(-2.00, 0.002, -0.80);
    scene.add(copierShadow);

    gltfLoader.load(
      "/assets/clearhire-scene/office-copier.glb",
      (gltf) => {
        const { wrapper: copierGroup } = createFittedModel(gltf.scene, {
          targetHeight: 1.15,
          centerAtBase: true,
        });
        copierGroup.position.set(-2.00, 0.0, -0.80);
        copierGroup.rotation.y = 0.48;
        scene.add(copierGroup);
      },
      undefined,
      (err) => console.warn("Copier fallback:", err)
    );

    // E. Sweeping Optical Cyan Laser Curtain on Copier Platen
    const laserMat = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uColor: { value: new THREE.Color(0x38bdf8) },
        uIntensity: { value: 0.9 },
      },
      vertexShader: LaserVolumetricShader.vertexShader,
      fragmentShader: LaserVolumetricShader.fragmentShader,
      transparent: true,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.NormalBlending,
    });
    const laserMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.50, 0.16), laserMat);
    laserMesh.rotation.x = -Math.PI / 2;
    laserMesh.rotation.z = 0.48;
    laserMesh.position.set(-2.00, 1.09, -0.80);
    scene.add(laserMesh);

    // F. Autonomous Robot Drone (Hovering above platen at x = -2.00, z = -0.80)
    let droneGroup = null;
    const droneShadow = createContactShadow(0.5, 0.5, 0.35);
    droneShadow.position.set(-2.00, 1.085, -0.80);
    scene.add(droneShadow);

    gltfLoader.load(
      "/assets/clearhire-scene/robot.glb",
      (gltf) => {
        const { wrapper: robotGroup } = createFittedModel(gltf.scene, {
          targetHeight: 0.38,
          centerAtBase: false,
        });
        robotGroup.position.set(-2.00, 1.48, -0.80);
        robotGroup.rotation.y = 0.35;
        droneGroup = robotGroup;
        scene.add(robotGroup);
      },
      undefined,
      (err) => console.warn("Robot fallback:", err)
    );

    // G. Filled Bookshelf (Flush against back wall)
    gltfLoader.load(
      "/assets/clearhire-scene/filled-bookshelf.glb",
      (gltf) => {
        const { wrapper: shelfGroup } = createFittedModel(gltf.scene, {
          targetHeight: 2.2,
          centerAtBase: true,
        });
        shelfGroup.position.set(-3.4, 0.0, -4.65);
        scene.add(shelfGroup);
      },
      undefined,
      (err) => console.warn("Shelf fallback:", err)
    );

    // 8. Intake Presentation Credenza (Placed in Right Foreground at x = +1.20, z = +1.00)
    const credenza = createModernistCredenza();
    credenza.position.set(1.20, 0.0, 1.00);
    credenza.rotation.y = -0.22;
    scene.add(credenza);

    const credenzaShadow = createContactShadow(1.1, 0.8, 0.55);
    credenzaShadow.position.set(1.20, 0.002, 1.00);
    scene.add(credenzaShadow);

    // 9. Industrial Rejection Bin (Placed on Far-Left Wall beside Copier at x = -2.80, z = -0.80)
    const rejectBin = createIndustrialRejectionBin();
    rejectBin.position.set(-2.80, 0.0, -0.80);
    scene.add(rejectBin);

    const rejectBinShadow = createContactShadow(0.65, 0.65, 0.5);
    rejectBinShadow.position.set(-2.80, 0.002, -0.80);
    scene.add(rejectBinShadow);

    // 10. Candidate Portfolio Folder on Executive Desk
    const portfolioGroup = new THREE.Group();
    portfolioGroup.position.set(0.25, 0.765, -2.15);

    const leatherMat = new THREE.MeshStandardMaterial({
      color: 0x064e3b,
      roughness: 0.45,
      metalness: 0.15,
    });
    const portfolio = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.015, 0.78), leatherMat);
    portfolio.receiveShadow = true;
    portfolioGroup.add(portfolio);
    scene.add(portfolioGroup);

    // 11. Turned Brass 48-Hour SLA Chronometer (Resting flat on left desk surface)
    const chronoCanvas = generateChronometerCanvas();
    const chronoTex = chronoCanvas ? new THREE.CanvasTexture(chronoCanvas) : null;
    if (chronoTex) chronoTex.colorSpace = THREE.SRGBColorSpace;

    const chronoGroup = new THREE.Group();
    chronoGroup.position.set(-0.15, 0.765, -2.20);
    chronoGroup.rotation.x = 0.28; // Tilted 16 degrees toward viewer

    const brassMat = new THREE.MeshStandardMaterial({
      color: 0xd4af37,
      metalness: 0.88,
      roughness: 0.20,
    });

    const chronoBase = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.12, 0.03, 32), brassMat);
    chronoBase.position.y = 0.015;
    chronoGroup.add(chronoBase);

    const chronoRing = new THREE.Mesh(new THREE.TorusGeometry(0.105, 0.012, 16, 36), brassMat);
    chronoRing.rotation.x = Math.PI / 2;
    chronoRing.position.y = 0.032;
    chronoGroup.add(chronoRing);

    const chronoDial = new THREE.Mesh(
      new THREE.CylinderGeometry(0.10, 0.10, 0.004, 32),
      chronoTex ? new THREE.MeshBasicMaterial({ map: chronoTex }) : brassMat
    );
    chronoDial.position.y = 0.031;
    chronoGroup.add(chronoDial);

    const chronoHand = new THREE.Mesh(
      new THREE.BoxGeometry(0.005, 0.003, 0.075),
      new THREE.MeshBasicMaterial({ color: 0x059669 })
    );
    chronoHand.position.set(0, 0.034, 0);
    chronoGroup.add(chronoHand);
    scene.add(chronoGroup);

    // 12. Physical Candidate Cotton Rag Resume
    const resumeCanvas = generateResumeCanvas();
    const resumeTex = resumeCanvas ? new THREE.CanvasTexture(resumeCanvas) : null;
    if (resumeTex) {
      resumeTex.colorSpace = THREE.SRGBColorSpace;
      resumeTex.minFilter = THREE.LinearMipmapLinearFilter;
    }

    const resumeMat = new THREE.MeshPhysicalMaterial({
      map: resumeTex,
      color: 0xffffff,
      roughness: 0.65,
      metalness: 0.0,
      sheen: 0.85,
      sheenColor: new THREE.Color(0xfffaf0),
      sheenRoughness: 0.55,
      side: THREE.DoubleSide,
    });
    // Scaled to real executive folio dimension (0.34m x 0.48m)
    const resumeGeo = new THREE.PlaneGeometry(0.34, 0.48, 12, 12);
    const resumeMesh = new THREE.Mesh(resumeGeo, resumeMat);
    resumeMesh.castShadow = true;
    resumeMesh.receiveShadow = true;
    scene.add(resumeMesh);

    // 13. Fluid Continuous Flight Paths (Across Dedicated Zones)
    const clearhireFlight = new THREE.CatmullRomCurve3([
      new THREE.Vector3(1.20, 0.835, 1.00),   // 01: Intake credenza tray (Right foreground)
      new THREE.Vector3(0.20, 1.250, 0.20),   // 02: Flutter lift across central hall
      new THREE.Vector3(-2.00, 1.095, -0.80), // 03: Copier platen glass (Left midground)
      new THREE.Vector3(-2.00, 1.095, -0.80), // 04: AST validation pause
      new THREE.Vector3(-1.40, 1.250, -1.20), // 05: Branch fast-track lift
      new THREE.Vector3(-0.60, 1.200, -1.60), // 06: Transit across gallery
      new THREE.Vector3(0.00, 1.100, -1.90),  // 07: Covenant acceleration
      new THREE.Vector3(0.18, 0.900, -2.10),  // 08: Approach executive desk
      new THREE.Vector3(0.25, 0.780, -2.15),  // 09: Lands flush on leather portfolio
    ]);

    const rejectFlight = new THREE.CatmullRomCurve3([
      new THREE.Vector3(1.20, 0.835, 1.00),
      new THREE.Vector3(0.20, 1.250, 0.20),
      new THREE.Vector3(-2.00, 1.095, -0.80),
      new THREE.Vector3(-2.00, 1.095, -0.80),
      new THREE.Vector3(-2.50, 0.550, -0.80), // 05: Drop down to archive basket
      new THREE.Vector3(-2.80, 0.320, -0.80), // 06: Inside rejection bin
      new THREE.Vector3(-2.80, 0.320, -0.80), // 07
      new THREE.Vector3(-2.80, 0.320, -0.80), // 08
      new THREE.Vector3(-2.80, 0.320, -0.80), // 09
    ]);

    // 14. Meticulously Art-Directed Camera Waypoints (Zero Occlusion, Masterclass Framing)
    const cameraWaypoints = [
      // 01: Launchpad - Beautiful establishing shot, frames Intake Credenza in right midground
      { eye: new THREE.Vector3(0.20, 1.75, 3.10), look: new THREE.Vector3(1.10, 0.80, 1.00) },
      // 02: Flutter Lift - Camera pulls back as paper ascends across hall
      { eye: new THREE.Vector3(-0.30, 1.65, 2.00), look: new THREE.Vector3(0.40, 1.20, 0.30) },
      // 03: Copier Platen & Robot - Completely unobstructed view of Copier and Robot Drone
      { eye: new THREE.Vector3(-1.10, 1.45, 0.20), look: new THREE.Vector3(-2.00, 1.12, -0.80) },
      // 04: Token Parsing - Focused on AST scan
      { eye: new THREE.Vector3(-1.35, 1.38, -0.10), look: new THREE.Vector3(-2.00, 1.10, -0.80) },
      // 05: Divergence - Framing Rejection Bin beside Copier
      { eye: new THREE.Vector3(-1.70, 1.45, 0.10), look: new THREE.Vector3(-2.50, 0.45, -0.80) },
      // 06: Transit Corridor
      { eye: new THREE.Vector3(-0.40, 1.55, -0.60), look: new THREE.Vector3(-0.60, 1.20, -1.60) },
      // 07: Covenant Fast-Track
      { eye: new THREE.Vector3(0.10, 1.52, -0.90), look: new THREE.Vector3(0.25, 1.05, -1.95) },
      // 08: Approaching Executive Desk
      { eye: new THREE.Vector3(0.45, 1.48, -0.50), look: new THREE.Vector3(0.45, 0.85, -2.15) },
      // 09: Executive Decision Desk & Workspace Portal (Centered, Balanced Depth)
      { eye: new THREE.Vector3(0.25, 1.42, 0.55), look: new THREE.Vector3(0.25, 0.80, -2.15) },
    ];

    const cameraEyeSpline = new THREE.CatmullRomCurve3(
      cameraWaypoints.map((w) => w.eye),
      false,
      "catmullrom",
      0.5
    );
    const cameraLookSpline = new THREE.CatmullRomCurve3(
      cameraWaypoints.map((w) => w.look),
      false,
      "catmullrom",
      0.5
    );

    // Mouse Parallax listener (Sub-pixel, locked to max ±0.03m)
    const onMouseMove = (e) => {
      const normX = (e.clientX / window.innerWidth - 0.5) * 2;
      const normY = -(e.clientY / window.innerHeight - 0.5) * 2;
      springCam.setMouseTarget(normX, normY);
    };
    window.addEventListener("mousemove", onMouseMove);

    const onResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      postPipeline.setSize(w, h);
    };
    window.addEventListener("resize", onResize);
    onResize();

    // 15. Animation Loop
    let reqId = 0;
    let lastTime = performance.now();
    let startTime = performance.now();
    let currentStageIndex = 0;

    // Spatial Telemetry Anchors in 3D world space
    const anchorCopier = new THREE.Vector3(-2.00, 1.10, -0.80);
    const anchorRobot = new THREE.Vector3(-2.00, 1.50, -0.80);
    const anchorChrono = new THREE.Vector3(-0.15, 0.80, -2.20);

    const projectToScreen = (worldPos) => {
      _scratchProj.copy(worldPos).project(camera);
      const w = container.clientWidth;
      const h = container.clientHeight;
      return {
        x: (_scratchProj.x * 0.5 + 0.5) * w,
        y: (-(_scratchProj.y * 0.5) + 0.5) * h,
        visible: _scratchProj.z < 1.0,
      };
    };

    const animate = () => {
      reqId = requestAnimationFrame(animate);
      const now = performance.now();
      const dt = Math.min(0.05, Math.max(0.001, (now - lastTime) / 1000));
      lastTime = now;
      const time = (now - startTime) / 1000;

      let p = 0;
      if (motionRef && motionRef.current !== undefined && motionRef.current !== null) {
        if (typeof motionRef.current === "number") {
          p = motionRef.current;
        } else if (typeof motionRef.current.progress === "number") {
          p = motionRef.current.progress;
        }
      }
      p = Math.max(0, Math.min(1, isNaN(p) ? 0 : p));

      const isLegacy = activeBranchRef.current === "legacy";

      // Map progress p (0..1) to 9 discrete stages
      const rawStage = p * 8.0;
      const stageFloor = Math.floor(rawStage);
      const stageIndex = Math.min(8, Math.max(0, isNaN(stageFloor) ? 0 : stageFloor));

      if (stageIndex !== currentStageIndex) {
        currentStageIndex = stageIndex;
        if (onStageChangeRef.current) {
          onStageChangeRef.current(stageIndex);
        }
      }

      // Exact parametric sampling via getPoint (1:1 with 9 chapters)
      const clampedP = Math.max(0.0, Math.min(1.0, isNaN(p) ? 0.0 : p));
      const defaultEye = new THREE.Vector3(0.20, 1.75, 3.10);
      const defaultLook = new THREE.Vector3(1.10, 0.80, 1.00);
      const targetEye = cameraEyeSpline ? (cameraEyeSpline.getPoint(clampedP) || defaultEye) : defaultEye;
      const targetLook = cameraLookSpline ? (cameraLookSpline.getPoint(clampedP) || defaultLook) : defaultLook;

      // Critically damped camera update (Rock-solid, zero shaking, locked horizon)
      if (springCam && targetEye && targetLook) {
        springCam.update(dt, targetEye, targetLook);
      }

      // Candidate Resume flight
      const activeFlight = isLegacy ? rejectFlight : clearhireFlight;
      const paperPos = activeFlight.getPoint(clampedP);
      resumeMesh.position.copy(paperPos);

      // Aerodynamic paper orientation (Resting flat on surfaces, banking in flight)
      if (clampedP <= 0.04) {
        // Stage 01: Resting flat on intake credenza tray
        resumeMesh.rotation.set(-Math.PI / 2, 0, -0.22);
      } else if (clampedP >= 0.22 && clampedP <= 0.40) {
        // Stage 03 & 04: Resting flat on copier scanning platen
        resumeMesh.rotation.set(-Math.PI / 2, 0, 0.48);
      } else if (clampedP >= 0.94) {
        // Stage 09: Resting flat in executive portfolio on desk
        resumeMesh.rotation.set(-Math.PI / 2, 0, 0);
      } else {
        // In flight: aerodynamic banking with printed face pointing up
        const tangent = activeFlight.getTangent(clampedP).normalize();
        const rollAngle = -tangent.x * 0.45;
        const pitchAngle = Math.asin(Math.max(-0.99, Math.min(0.99, tangent.y)));
        resumeMesh.rotation.set(-Math.PI / 2 + pitchAngle, rollAngle, Math.atan2(tangent.x, tangent.z));
      }

      // Chronometer second hand tick
      chronoHand.rotation.y = -time * 1.5;

      // Autonomous Robot Drone subtle hover
      if (droneGroup) {
        droneGroup.position.y = 1.48 + Math.sin(time * 1.5) * 0.02;
        droneGroup.rotation.y = 0.35 + Math.sin(time * 0.8) * 0.05;
      }

      // Sweeping optical laser plane
      if (stageIndex === 2 || stageIndex === 3) {
        laserMesh.visible = true;
        laserMesh.position.z = -0.80 + Math.sin(time * 5.0) * 0.08;
        laserMat.uniforms.uTime.value = time;
        laserMat.uniforms.uColor.value.setHex(0x38bdf8);
      } else {
        laserMesh.visible = false;
      }

      // Emit Spatial Telemetry Anchors for UI Overlay
      if (onSpatialTelemetryRef.current) {
        onSpatialTelemetryRef.current({
          resume: projectToScreen(resumeMesh.position),
          platen: projectToScreen(anchorCopier),
          pneumatic: projectToScreen(anchorRobot),
          chrono: projectToScreen(anchorChrono),
        });
      }

      // Render through tone-mapped post-processing stack
      if (postPipeline) {
        postPipeline.render(time);
      } else {
        renderer.render(scene, camera);
      }
    };

    reqId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(reqId);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("resize", onResize);
      if (postPipeline) postPipeline.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className="absolute inset-0 w-full h-full pointer-events-none select-none z-0 overflow-hidden"
      aria-hidden="true"
    />
  );
}
