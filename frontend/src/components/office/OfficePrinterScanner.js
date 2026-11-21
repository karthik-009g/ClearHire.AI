import * as THREE from "three";

/**
 * ============================================================================
 * INDEPENDENT COMPONENT: OfficePrinterScanner (Square Robot ATS Gateway)
 * Principles from Anatomy & Motion skills:
 * - Real physical mechanisms (4 turned brass leveling feet, platen guide bed,
 *   rotating pinch feed rollers, laser curtain, CRT display screen).
 * - Dual antenna telemetry stalks with state-driven color shifting beacons.
 * - Knurled micrometer adjustment knobs.
 * - Dynamic mood state machine: idle, scanning, rejected, accepted.
 * ============================================================================
 */

function updatePrinterScreen(canvas, mood = "idle", time = 0, statusText = "") {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = canvas.width;
  const h = canvas.height;

  // Background gradient based on state
  let bgGrad = ctx.createLinearGradient(0, 0, 0, h);
  if (mood === "rejected") {
    bgGrad.addColorStop(0, "#2a0a0d");
    bgGrad.addColorStop(1, "#150204");
  } else if (mood === "accepted") {
    bgGrad.addColorStop(0, "#062217");
    bgGrad.addColorStop(1, "#020f0a");
  } else if (mood === "scanning") {
    bgGrad.addColorStop(0, "#08202d");
    bgGrad.addColorStop(1, "#030c12");
  } else {
    bgGrad.addColorStop(0, "#14171d");
    bgGrad.addColorStop(1, "#090a0d");
  }
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, w, h);

  // CRT scanline overlay
  ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
  for (let y = 0; y < h; y += 4) {
    ctx.fillRect(0, y, w, 2);
  }

  // Bezel border
  ctx.strokeStyle =
    mood === "rejected"
      ? "#ef4444"
      : mood === "accepted"
      ? "#10b981"
      : mood === "scanning"
      ? "#38bdf8"
      : "#94a3b8";
  ctx.lineWidth = 4;
  ctx.strokeRect(6, 6, w - 12, h - 12);

  // Digital eyes / Scanner state glyphs
  ctx.textAlign = "center";
  if (mood === "rejected") {
    ctx.fillStyle = "#ef4444";
    ctx.font = "bold 52px monospace";
    ctx.fillText("✕", w * 0.35, h * 0.44);
    ctx.fillText("✕", w * 0.65, h * 0.44);

    ctx.fillStyle = "#f87171";
    ctx.font = "bold 15px monospace";
    ctx.fillText("[ HEURISTIC REJECT ]", w * 0.5, h * 0.68);
    ctx.font = "12px monospace";
    ctx.fillText("DISCARD TO INCINERATOR", w * 0.5, h * 0.84);
  } else if (mood === "accepted") {
    ctx.fillStyle = "#10b981";
    ctx.font = "bold 52px monospace";
    ctx.fillText("✓", w * 0.35, h * 0.44);
    ctx.fillText("✓", w * 0.65, h * 0.44);

    ctx.fillStyle = "#34d399";
    ctx.font = "bold 15px monospace";
    ctx.fillText("[ AST VERIFIED: 99.4% ]", w * 0.5, h * 0.68);
    ctx.font = "12px monospace";
    ctx.fillText("PNEUMATIC DIRECT CONDUIT", w * 0.5, h * 0.84);
  } else if (mood === "scanning") {
    const eyeOsc = Math.sin(time * 6) * 14;
    ctx.fillStyle = "#38bdf8";
    ctx.fillRect(w * 0.28, h * 0.32 + eyeOsc * 0.3, 40, 22);
    ctx.fillRect(w * 0.60, h * 0.32 - eyeOsc * 0.3, 40, 22);

    ctx.fillStyle = "#7dd3fc";
    ctx.font = "bold 14px monospace";
    ctx.fillText("PARSING AST DATA...", w * 0.5, h * 0.68);

    const barW = Math.abs(Math.sin(time * 8)) * 140 + 40;
    ctx.fillStyle = "#0284c7";
    ctx.fillRect((w - barW) / 2, h * 0.78, barW, 8);
  } else {
    ctx.fillStyle = "#94a3b8";
    ctx.fillRect(w * 0.30, h * 0.36, 36, 18);
    ctx.fillRect(w * 0.58, h * 0.36, 36, 18);

    ctx.fillStyle = "#cbd5e1";
    ctx.font = "bold 14px monospace";
    ctx.fillText("CLEARHIRE ATS v2.4", w * 0.5, h * 0.68);
    ctx.font = "11px monospace";
    ctx.fillText("READY FOR INTAKE", w * 0.5, h * 0.82);
  }
}

export function createOfficePrinterScanner({
  position = [-0.2, 0.65, 0.95],
} = {}) {
  const group = new THREE.Group();
  group.name = "OfficePrinterScanner";
  group.position.set(...position);

  // Materials
  const darkAnodizedMat = new THREE.MeshStandardMaterial({
    color: 0x1e2229,
    metalness: 0.75,
    roughness: 0.28,
  });
  const brassMat = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    metalness: 0.85,
    roughness: 0.22,
  });
  const stainlessPlatenMat = new THREE.MeshStandardMaterial({
    color: 0x94a3b8,
    metalness: 0.82,
    roughness: 0.25,
  });

  // 1. Heavy Anodized Base Plinth on 4 Turned Brass Feet
  const basePlate = new THREE.Mesh(
    new THREE.BoxGeometry(1.44, 0.1, 1.15),
    darkAnodizedMat
  );
  basePlate.position.set(0, -0.52, 0);
  basePlate.castShadow = true;
  basePlate.receiveShadow = true;
  group.add(basePlate);

  const footGeo = new THREE.CylinderGeometry(0.065, 0.08, 0.12, 16);
  const footOffsets = [
    [-0.6, -0.6, -0.45],
    [0.6, -0.6, -0.45],
    [-0.6, -0.6, 0.45],
    [0.6, -0.6, 0.45],
  ];
  footOffsets.forEach(([fx, fy, fz]) => {
    const foot = new THREE.Mesh(footGeo, brassMat);
    foot.position.set(fx, fy, fz);
    foot.castShadow = true;
    group.add(foot);
  });

  // 2. Main Scanner Chassis Block
  const bodyMesh = new THREE.Mesh(
    new THREE.BoxGeometry(1.32, 1.05, 0.96),
    darkAnodizedMat
  );
  bodyMesh.castShadow = true;
  bodyMesh.receiveShadow = true;
  group.add(bodyMesh);

  // 3. Stainless Guide Platen Intake Mouth & Rollers
  const platenBed = new THREE.Mesh(
    new THREE.BoxGeometry(0.9, 0.04, 0.4),
    stainlessPlatenMat
  );
  platenBed.position.set(0, -0.22, 0.42);
  platenBed.receiveShadow = true;
  group.add(platenBed);

  const rollerGeo = new THREE.CylinderGeometry(0.038, 0.038, 0.86, 16);
  rollerGeo.rotateZ(Math.PI / 2);
  const topRoller = new THREE.Mesh(rollerGeo, brassMat);
  topRoller.position.set(0, -0.16, 0.38);
  group.add(topRoller);

  const bottomRoller = new THREE.Mesh(rollerGeo, brassMat);
  bottomRoller.position.set(0, -0.26, 0.38);
  group.add(bottomRoller);

  // 4. Knurled Brass Tuning Knobs on chassis sides
  const knobGeo = new THREE.CylinderGeometry(0.09, 0.09, 0.08, 24);
  knobGeo.rotateZ(Math.PI / 2);
  const leftKnob = new THREE.Mesh(knobGeo, brassMat);
  leftKnob.position.set(-0.7, 0.08, 0.1);
  group.add(leftKnob);

  const rightKnob = new THREE.Mesh(knobGeo, brassMat);
  rightKnob.position.set(0.7, 0.08, 0.1);
  group.add(rightKnob);

  // 5. Dual Antenna Telemetry Masts with Glowing Beacon Spheres
  const antStemGeo = new THREE.CylinderGeometry(0.016, 0.016, 0.38, 12);
  const leftAnt = new THREE.Mesh(antStemGeo, brassMat);
  leftAnt.position.set(-0.42, 0.72, 0);
  group.add(leftAnt);

  const rightAnt = new THREE.Mesh(antStemGeo, brassMat);
  rightAnt.position.set(0.42, 0.72, 0);
  group.add(rightAnt);

  const beaconGeo = new THREE.SphereGeometry(0.07, 16, 16);
  const leftBeaconMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.6,
    roughness: 0.2,
  });
  const leftBeacon = new THREE.Mesh(beaconGeo, leftBeaconMat);
  leftBeacon.position.set(-0.42, 0.91, 0);
  group.add(leftBeacon);

  const rightBeaconMat = leftBeaconMat.clone();
  const rightBeacon = new THREE.Mesh(beaconGeo, rightBeaconMat);
  rightBeacon.position.set(0.42, 0.91, 0);
  group.add(rightBeacon);

  // 6. Dynamic CRT Phosphor Scanline Screen
  const screenCanvas =
    typeof document !== "undefined" ? document.createElement("canvas") : null;
  if (screenCanvas) {
    screenCanvas.width = 280;
    screenCanvas.height = 160;
  }
  const screenTex = screenCanvas ? new THREE.CanvasTexture(screenCanvas) : null;
  if (screenTex) screenTex.minFilter = THREE.LinearFilter;

  const screenBezel = new THREE.Mesh(
    new THREE.PlaneGeometry(0.96, 0.56),
    new THREE.MeshStandardMaterial({ color: 0x0b0d11, roughness: 0.9 })
  );
  screenBezel.position.set(0, 0.18, 0.485);
  group.add(screenBezel);

  const faceMat = screenTex
    ? new THREE.MeshBasicMaterial({ map: screenTex })
    : new THREE.MeshBasicMaterial({ color: 0x14171d });
  const faceScreen = new THREE.Mesh(
    new THREE.PlaneGeometry(0.92, 0.52),
    faceMat
  );
  faceScreen.position.set(0, 0.18, 0.49);
  group.add(faceScreen);

  // 7. Sweeping Optical Cyan Laser Curtain
  const laserMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(0.88, 0.04),
    new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.85,
      side: THREE.DoubleSide,
    })
  );
  laserMesh.rotation.x = Math.PI / 2;
  laserMesh.position.set(0, -0.21, 0.42);
  group.add(laserMesh);

  let currentMood = "idle";

  const setMood = (mood) => {
    currentMood = mood;
    if (mood === "scanning") {
      laserMesh.visible = true;
      laserMesh.material.color.setHex(0x38bdf8);
      leftBeaconMat.emissive.setHex(0x0284c7);
      rightBeaconMat.emissive.setHex(0x0284c7);
    } else if (mood === "rejected") {
      laserMesh.visible = true;
      laserMesh.material.color.setHex(0xef4444);
      leftBeaconMat.emissive.setHex(0xef4444);
      rightBeaconMat.emissive.setHex(0xef4444);
    } else if (mood === "accepted") {
      laserMesh.visible = true;
      laserMesh.material.color.setHex(0x10b981);
      leftBeaconMat.emissive.setHex(0x10b981);
      rightBeaconMat.emissive.setHex(0x10b981);
    } else {
      laserMesh.visible = false;
      leftBeaconMat.emissive.setHex(0x475569);
      rightBeaconMat.emissive.setHex(0x475569);
    }
  };

  const update = (time, dt, mood = currentMood) => {
    if (mood !== currentMood) {
      setMood(mood);
    }

    // Rotating guide rollers
    topRoller.rotation.x += dt * 3.5;
    bottomRoller.rotation.x -= dt * 3.5;

    // Sweeping laser curtain
    if (laserMesh.visible) {
      laserMesh.position.z = 0.42 + Math.sin(time * 7) * 0.08;
    }

    // Update screen canvas
    if (screenCanvas && screenTex) {
      updatePrinterScreen(screenCanvas, currentMood, time, "");
      screenTex.needsUpdate = true;
    }
  };

  const dispose = () => {
    darkAnodizedMat.dispose();
    brassMat.dispose();
    stainlessPlatenMat.dispose();
    if (screenTex) screenTex.dispose();
  };

  return {
    group,
    setMood,
    update,
    dispose,
  };
}
