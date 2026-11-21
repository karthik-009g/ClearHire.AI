import * as THREE from "three";

/**
 * ============================================================================
 * INDEPENDENT COMPONENT: CandidateResume
 * Principles from Anatomy & Motion skills:
 * - High-DPI 1024x1440 cotton paper canvas texture.
 * - Quantified impact metrics, verified AST holographic stamp, barcode.
 * - Aerodynamic flutter physics & orientation along flight tangents.
 * - Double-sided material with realistic slight flex.
 * ============================================================================
 */

export function generateResumeCanvas() {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 1440;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  // Premium warm cotton paper background
  ctx.fillStyle = "#faf8f4";
  ctx.fillRect(0, 0, 1024, 1440);

  // Milled border double-line
  ctx.strokeStyle = "#e2dacf";
  ctx.lineWidth = 4;
  ctx.strokeRect(24, 24, 976, 1392);
  ctx.strokeStyle = "#eee8de";
  ctx.lineWidth = 2;
  ctx.strokeRect(36, 36, 952, 1368);

  // Header background tint
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

  // ClearHire AST Holographic Stamp
  ctx.fillStyle = "rgba(5, 150, 105, 0.12)";
  ctx.strokeStyle = "#059669";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.roundRect(720, 76, 230, 64, 10);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#047857";
  ctx.font = "bold 18px monospace";
  ctx.textAlign = "center";
  ctx.fillText("CLEARHIRE AST ✓", 835, 114);
  ctx.font = "12px monospace";
  ctx.fillText("VERIFIED PROTOCOL 4.2", 835, 132);

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

  // Role 1
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

  // Role 2
  y += 46;
  ctx.fillStyle = "#1e293b";
  ctx.font = "bold 24px sans-serif";
  ctx.fillText("Senior Systems Architect — Distributed Cloud Engineering", 60, y);
  ctx.fillStyle = "#64748b";
  ctx.font = "20px monospace";
  ctx.textAlign = "right";
  ctx.fillText("2020 – 2023", 964, y);
  ctx.textAlign = "left";

  y += 30;
  ctx.fillStyle = "#475569";
  ctx.font = "20px sans-serif";
  ctx.fillText("• Scaled vector retrieval cluster from 2M to 120M embeddings with HNSW indexing.", 80, y);
  y += 28;
  ctx.fillText("• Authored patent on asynchronous job graph consensus algorithms.", 80, y);
  y += 28;
  ctx.fillText("• Reduced cloud egress and compute costs by $1.8M annually through memory caching.", 80, y);

  // Section 3: Technical Competency & Quantified Metrics
  y += 50;
  ctx.fillStyle = "#0f172a";
  ctx.font = "bold 26px monospace";
  ctx.fillText("III. TECHNICAL STACK & ATS COMPLIANCE CHIPS", 60, y);

  y += 12;
  ctx.strokeStyle = "#cbd5e1";
  ctx.beginPath();
  ctx.moveTo(60, y);
  ctx.lineTo(964, y);
  ctx.stroke();

  y += 36;
  const skills = [
    "Python / Triton",
    "Rust",
    "CUDA C++",
    "Next.js / WebGL",
    "PostgreSQL / pgvector",
    "Docker / K8s",
    "FastAPI",
    "Ray.io",
    "Apache Beam",
    "Zero-AST Parsing",
  ];
  let sx = 60;
  skills.forEach((skill) => {
    ctx.fillStyle = "#f1f5f9";
    ctx.strokeStyle = "#cbd5e1";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(sx, y - 20, 165, 38, 6);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#334155";
    ctx.font = "bold 15px monospace";
    ctx.textAlign = "center";
    ctx.fillText(skill, sx + 82, y + 5);
    sx += 180;
    if (sx > 800) {
      sx = 60;
      y += 48;
    }
  });

  // Footer Hologram Barcode
  y = 1360;
  ctx.fillStyle = "#e2e8f0";
  ctx.fillRect(60, y, 904, 30);
  ctx.fillStyle = "#047857";
  ctx.font = "bold 16px monospace";
  ctx.textAlign = "center";
  ctx.fillText("CLEARHIRE AST SYNTAX VERIFIED · ZERO PAGE OVERFLOW · 100% PARSEABLE", 512, y + 21);

  return canvas;
}

export function createCandidateResume({
  initialPosition = [2.2, 1.18, 3.5],
} = {}) {
  const canvas = generateResumeCanvas();
  const texture = canvas ? new THREE.CanvasTexture(canvas) : null;
  if (texture) {
    texture.generateMipmaps = true;
    texture.minFilter = THREE.LinearMipmapLinearFilter;
  }

  const paperFrontMat = new THREE.MeshStandardMaterial({
    map: texture,
    color: texture ? 0xffffff : 0xfaf8f4,
    roughness: 0.42,
    metalness: 0.02,
    side: THREE.DoubleSide,
  });

  const paperGeo = new THREE.PlaneGeometry(0.72, 1.02, 16, 16);
  const mesh = new THREE.Mesh(paperGeo, paperFrontMat);
  mesh.name = "CandidateResume";
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.position.set(...initialPosition);
  mesh.rotation.x = -Math.PI / 6;

  const update = (time, dt, pos = null, tangent = null) => {
    if (pos && typeof pos === "object" && typeof pos.x === "number") {
      mesh.position.copy(pos);
    }
    if (tangent && typeof tangent === "object" && typeof tangent.x === "number") {
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
      mesh.rotateX(Math.PI / 2 + Math.sin(time * 8) * 0.08);
      mesh.rotateZ(Math.cos(time * 6) * 0.06);
    } else {
      // Gentle rest flutter
      mesh.rotation.z = Math.sin(time * 1.5) * 0.02;
    }
  };

  const dispose = () => {
    paperGeo.dispose();
    paperFrontMat.dispose();
    if (texture) texture.dispose();
  };

  return {
    mesh,
    update,
    dispose,
  };
}
