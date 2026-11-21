import * as THREE from "three";

/**
 * ============================================================================
 * INDEPENDENT COMPONENT: ExecutiveDesk
 * Principles from Anatomy & Motion skills:
 * - Real physical furniture joinery (travertine slab, bronze trestle frame).
 * - Calibrated materials (roughness 0.55 travertine, brushed bronze, emerald leather).
 * - Physical 3D 48-Hour SLA Chronometer with active second hand tick.
 * - Knurled brass cable pass-through grommet.
 * - Open executive candidate interview portfolio folder.
 * ============================================================================
 */

function generateChronometerCanvas() {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  ctx.fillStyle = "#fcfbfa";
  ctx.beginPath();
  ctx.arc(128, 128, 126, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = "#d4af37";
  ctx.lineWidth = 6;
  ctx.stroke();

  // Hour tick marks
  for (let i = 0; i < 12; i += 1) {
    const angle = (i / 12) * Math.PI * 2 - Math.PI / 2;
    const isMajor = i % 3 === 0;
    const r1 = isMajor ? 92 : 106;
    const r2 = 118;
    ctx.strokeStyle = isMajor ? "#166534" : "#475569";
    ctx.lineWidth = isMajor ? 4 : 2;
    ctx.beginPath();
    ctx.moveTo(128 + Math.cos(angle) * r1, 128 + Math.sin(angle) * r1);
    ctx.lineTo(128 + Math.cos(angle) * r2, 128 + Math.sin(angle) * r2);
    ctx.stroke();
  }

  // Numbers 48h, 12h, 24h, 36h
  ctx.fillStyle = "#1e293b";
  ctx.font = "bold 20px Georgia, serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("48h", 128, 54);
  ctx.fillText("12h", 202, 128);
  ctx.fillText("24h", 128, 202);
  ctx.fillText("36h", 54, 128);

  ctx.fillStyle = "#15803d";
  ctx.font = "bold 11px monospace";
  ctx.fillText("CLEARHIRE SLA", 128, 152);
  ctx.font = "9px monospace";
  ctx.fillStyle = "#64748b";
  ctx.fillText("PRECISION CHRONO", 128, 166);

  return canvas;
}

export function createExecutiveDesk({
  gltfLoader = null,
  position = [1.0, -0.22, -4.4],
} = {}) {
  const group = new THREE.Group();
  group.name = "ExecutiveDesk";
  group.position.set(...position);

  // Materials
  const travertineMat = new THREE.MeshStandardMaterial({
    color: 0xede8df,
    roughness: 0.55,
    metalness: 0.05,
  });
  const bronzeMat = new THREE.MeshStandardMaterial({
    color: 0x1c1a17,
    metalness: 0.65,
    roughness: 0.35,
  });
  const brassMat = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    metalness: 0.85,
    roughness: 0.22,
  });
  const emeraldLeatherMat = new THREE.MeshStandardMaterial({
    color: 0x064e3b,
    roughness: 0.4,
    metalness: 0.15,
  });

  // 1. Italian Travertine Slab Desktop (2.4m x 1.4m x 0.1m)
  const deskSlab = new THREE.Mesh(
    new THREE.BoxGeometry(2.4, 0.1, 1.4),
    travertineMat
  );
  deskSlab.position.y = 0;
  deskSlab.castShadow = true;
  deskSlab.receiveShadow = true;
  group.add(deskSlab);

  // 2. Dark Bronze Trestle Desk Legs
  const leg1 = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.85, 1.2), bronzeMat);
  leg1.position.set(-0.95, -0.42, 0);
  leg1.castShadow = true;
  group.add(leg1);

  const leg2 = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.85, 1.2), bronzeMat);
  leg2.position.set(0.95, -0.42, 0);
  leg2.castShadow = true;
  group.add(leg2);

  // Horizontal Trestle Stretcher Bar
  const stretcher = new THREE.Mesh(
    new THREE.BoxGeometry(1.82, 0.05, 0.05),
    bronzeMat
  );
  stretcher.position.set(0, -0.65, 0);
  stretcher.castShadow = true;
  group.add(stretcher);

  // 3. Knurled Brass Cable Pass-Through Grommet
  const grommet = new THREE.Mesh(
    new THREE.CylinderGeometry(0.045, 0.045, 0.11, 24),
    brassMat
  );
  grommet.position.set(0.95, 0.01, -0.45);
  group.add(grommet);

  // 4. Open Emerald Green Leather Executive Interview Portfolio
  const portfolioFolder = new THREE.Mesh(
    new THREE.BoxGeometry(0.85, 0.02, 1.15),
    emeraldLeatherMat
  );
  portfolioFolder.position.set(-0.25, 0.06, 0.05);
  portfolioFolder.receiveShadow = true;
  group.add(portfolioFolder);

  // 5. Physical 3D 48-Hour SLA Chronometer
  const chronoCanvas = generateChronometerCanvas();
  const chronoTex = chronoCanvas ? new THREE.CanvasTexture(chronoCanvas) : null;

  const chronoGroup = new THREE.Group();
  chronoGroup.position.set(0.85, 0.32, -0.2);

  const chronoRing = new THREE.Mesh(
    new THREE.TorusGeometry(0.28, 0.035, 16, 48),
    brassMat
  );
  chronoGroup.add(chronoRing);

  const chronoFaceMat = chronoTex
    ? new THREE.MeshBasicMaterial({ map: chronoTex })
    : new THREE.MeshStandardMaterial({ color: 0xfcfbfa });
  const chronoFace = new THREE.Mesh(
    new THREE.CylinderGeometry(0.26, 0.26, 0.02, 32),
    chronoFaceMat
  );
  chronoFace.rotation.x = Math.PI / 2;
  chronoGroup.add(chronoFace);

  const chronoHand = new THREE.Mesh(
    new THREE.BoxGeometry(0.015, 0.18, 0.01),
    new THREE.MeshBasicMaterial({ color: 0x059669 })
  );
  chronoHand.position.set(0, 0.04, 0.02);
  chronoGroup.add(chronoHand);

  // Brass pedestal stand for the chronometer
  const chronoStem = new THREE.Mesh(
    new THREE.CylinderGeometry(0.025, 0.035, 0.26, 16),
    brassMat
  );
  chronoStem.position.set(0, -0.19, 0);
  chronoGroup.add(chronoStem);

  group.add(chronoGroup);

  // 6. Optional GLTF Task Chair behind desk
  if (gltfLoader) {
    gltfLoader.load(
      "/assets/clearhire-scene/office-task-chair.glb",
      (gltf) => {
        const chair = gltf.scene;
        chair.position.set(0, -0.43, -0.95);
        chair.rotation.y = 0;
        chair.scale.set(1.0, 1.0, 1.0);
        chair.traverse((c) => {
          if (c.isMesh) {
            c.castShadow = true;
            c.receiveShadow = true;
          }
        });
        group.add(chair);
      },
      undefined,
      (err) => console.warn("Office chair fallback:", err)
    );
  }

  const update = (time, dt) => {
    // Ticking emerald second hand
    chronoHand.rotation.z = -time * 1.5;
  };

  const dispose = () => {
    travertineMat.dispose();
    bronzeMat.dispose();
    brassMat.dispose();
    emeraldLeatherMat.dispose();
    if (chronoTex) chronoTex.dispose();
  };

  return {
    group,
    chronometer: chronoGroup,
    portfolio: portfolioFolder,
    update,
    dispose,
  };
}
