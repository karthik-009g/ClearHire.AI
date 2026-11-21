import * as THREE from "three";

/**
 * ============================================================================
 * INDEPENDENT COMPONENT: WorkstationComputer
 * Principles from Anatomy (desk-computer) & Motion skills:
 * - Precision chassis case with bevelled corners and ventilation louvers.
 * - Recessed CRT / OLED display bezel with rubber gasket.
 * - Dynamic phosphor scanline canvas (live terminal AST output & blinking cursor).
 * - Mechanical keyboard with individual keycap rows.
 * - Coiled cable harness.
 * - Power rocker switch & soft pulsating power indicator LED.
 * ============================================================================
 */

function generateScreenCanvas(statusText = "CLEARHIRE AST PARSER v4.2", time = 0) {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 320;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  // Deep phosphor CRT background
  ctx.fillStyle = "#0c1017";
  ctx.fillRect(0, 0, 512, 320);

  // Scanlines
  ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
  for (let y = 0; y < 320; y += 4) {
    ctx.fillRect(0, y, 512, 2);
  }

  // Cyan phosphor glow header
  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 2;
  ctx.strokeRect(8, 8, 496, 304);

  // Header status bar
  ctx.fillStyle = "#0284c7";
  ctx.fillRect(10, 10, 492, 28);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 13px monospace";
  ctx.textAlign = "left";
  ctx.fillText("CLEARHIRE KERNEL // HIGH-THROUGHPUT ATS NODE", 20, 28);

  // Terminal readout lines
  ctx.fillStyle = "#38bdf8";
  ctx.font = "12px monospace";
  let ty = 64;
  ctx.fillText("> INTAKE BUFFER: Sarah_Chen_Staff_Engineer.pdf", 24, ty);
  ty += 22;
  ctx.fillText("> 1200 DPI OCR ENGINE: COMPLETE [0.014s]", 24, ty);
  ty += 22;
  ctx.fillText("> QUANTUM TOKENIZER: 1,842 TOKENS EXTRACTED", 24, ty);
  ty += 22;
  ctx.fillStyle = "#10b981";
  ctx.fillText("> AST GUARANTEE: 99.4% DETERMINISTIC COMPLIANCE", 24, ty);
  ty += 22;
  ctx.fillText("> ZERO HALLUCINATIONS VERIFIED", 24, ty);
  ty += 22;
  ctx.fillStyle = "#94a3b8";
  ctx.fillText("> ROUTING VELOCITY: PNEUMATIC 48 KM/H CONDUIT", 24, ty);

  // Blinking cursor
  if (Math.sin(time * 6) > 0) {
    ty += 24;
    ctx.fillStyle = "#10b981";
    ctx.fillRect(24, ty - 12, 10, 14);
  }

  return canvas;
}

export function createWorkstationComputer({
  gltfLoader = null,
  position = [2.0, 0.38, -4.3],
} = {}) {
  const group = new THREE.Group();
  group.name = "WorkstationComputer";
  group.position.set(...position);

  // Materials
  const caseMat = new THREE.MeshStandardMaterial({
    color: 0x22262e,
    roughness: 0.35,
    metalness: 0.65,
  });
  const bezelMat = new THREE.MeshStandardMaterial({
    color: 0x0f1115,
    roughness: 0.85,
  });
  const brassMat = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    roughness: 0.25,
    metalness: 0.85,
  });

  // Dynamic CRT Phosphor Screen Texture
  let screenCanvas = generateScreenCanvas();
  let screenTex = screenCanvas ? new THREE.CanvasTexture(screenCanvas) : null;
  if (screenTex) screenTex.minFilter = THREE.LinearFilter;

  // 1. Display Monitor Case & Screen
  const monitorGroup = new THREE.Group();

  const caseBody = new THREE.Mesh(
    new THREE.BoxGeometry(0.85, 0.55, 0.14),
    caseMat
  );
  caseBody.castShadow = true;
  caseBody.receiveShadow = true;
  monitorGroup.add(caseBody);

  const bezelMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(0.81, 0.51),
    bezelMat
  );
  bezelMesh.position.z = 0.071;
  monitorGroup.add(bezelMesh);

  const screenMat = screenTex
    ? new THREE.MeshBasicMaterial({ map: screenTex })
    : new THREE.MeshBasicMaterial({ color: 0x0c1017 });
  const screenMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(0.76, 0.46),
    screenMat
  );
  screenMesh.position.z = 0.073;
  monitorGroup.add(screenMesh);

  // Articulated Monitor Stand
  const standStem = new THREE.Mesh(
    new THREE.CylinderGeometry(0.025, 0.03, 0.42, 16),
    caseMat
  );
  standStem.position.set(0, -0.32, -0.05);
  monitorGroup.add(standStem);

  const standBase = new THREE.Mesh(
    new THREE.CylinderGeometry(0.18, 0.2, 0.03, 32),
    caseMat
  );
  standBase.position.set(0, -0.52, -0.05);
  standBase.castShadow = true;
  monitorGroup.add(standBase);

  group.add(monitorGroup);

  // 2. Mechanical Keyboard (Anatomy Style Extruded Keys)
  const kbGroup = new THREE.Group();
  kbGroup.position.set(0, -0.5, 0.45);
  kbGroup.rotation.x = -0.12;

  const kbCase = new THREE.Mesh(
    new THREE.BoxGeometry(0.58, 0.025, 0.22),
    caseMat
  );
  kbCase.castShadow = true;
  kbGroup.add(kbCase);

  // Keycap bed
  const keyMat = new THREE.MeshStandardMaterial({
    color: 0x334155,
    roughness: 0.45,
  });
  const accentKeyMat = new THREE.MeshStandardMaterial({
    color: 0x059669,
    roughness: 0.35,
  });

  const keyGeo = new THREE.BoxGeometry(0.028, 0.015, 0.028);
  for (let r = 0; r < 5; r += 1) {
    for (let c = 0; c < 14; c += 1) {
      const isAccent = (r === 2 && c === 13) || (r === 4 && c === 6);
      const key = new THREE.Mesh(keyGeo, isAccent ? accentKeyMat : keyMat);
      key.position.set(
        -0.24 + c * 0.037,
        0.018,
        -0.075 + r * 0.038
      );
      kbGroup.add(key);
    }
  }
  group.add(kbGroup);

  // 3. Coiled Cable Harness
  const cableCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, -0.5, 0.34),
    new THREE.Vector3(0.1, -0.52, 0.22),
    new THREE.Vector3(0.05, -0.52, 0.08),
    new THREE.Vector3(0.08, -0.48, -0.05),
  ]);
  const cableMesh = new THREE.Mesh(
    new THREE.TubeGeometry(cableCurve, 24, 0.008, 8, false),
    new THREE.MeshStandardMaterial({ color: 0x111317, roughness: 0.8 })
  );
  group.add(cableMesh);

  // 4. Pulsing Power LED
  const ledMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.8,
  });
  const powerLed = new THREE.Mesh(
    new THREE.SphereGeometry(0.008, 12, 12),
    ledMat
  );
  powerLed.position.set(0.38, -0.24, 0.074);
  monitorGroup.add(powerLed);

  const update = (time, dt) => {
    // Softly pulsating power LED
    ledMat.emissiveIntensity = 0.5 + Math.sin(time * 3) * 0.4;

    // Refresh dynamic screen canvas cursor every 250ms
    if (screenTex && Math.floor(time * 4) !== Math.floor((time - dt) * 4)) {
      screenCanvas = generateScreenCanvas("CLEARHIRE AST PARSER v4.2", time);
      if (screenCanvas) {
        screenTex.image = screenCanvas;
        screenTex.needsUpdate = true;
      }
    }
  };

  const dispose = () => {
    caseMat.dispose();
    bezelMat.dispose();
    brassMat.dispose();
    keyMat.dispose();
    accentKeyMat.dispose();
    if (screenTex) screenTex.dispose();
  };

  return {
    group,
    update,
    dispose,
  };
}
