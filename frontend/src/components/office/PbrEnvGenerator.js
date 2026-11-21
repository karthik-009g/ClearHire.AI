import * as THREE from "three";

/**
 * ============================================================================
 * PROCEDURAL STUDIO HDR ENVIRONMENT (PMREM) GENERATOR
 * Generates an architectural high-dynamic-range radiance probe without
 * requiring heavy external 15MB .hdr downloads.
 * Calibrated for PBR metals (brass, steel, bronze) and stone (travertine).
 * ============================================================================
 */

export function createStudioEnvironment(renderer) {
  if (!renderer || typeof document === "undefined") return null;

  const pmremGenerator = new THREE.PMREMGenerator(renderer);
  pmremGenerator.compileEquirectangularShader();

  const envScene = new THREE.Scene();

  // Warm studio overhead softbox light plane
  const softboxGeo = new THREE.PlaneGeometry(16, 12);
  const softboxMat = new THREE.MeshBasicMaterial({
    color: 0xfff6eb,
    side: THREE.DoubleSide,
  });
  const softbox = new THREE.Mesh(softboxGeo, softboxMat);
  softbox.position.set(0, 10, 0);
  softbox.rotation.x = Math.PI / 2;
  envScene.add(softbox);

  // Cool lateral rim bounce emitter (adds crisp metallic edge glints)
  const coolBounceGeo = new THREE.PlaneGeometry(12, 8);
  const coolBounceMat = new THREE.MeshBasicMaterial({
    color: 0xd4e4ff,
    side: THREE.DoubleSide,
  });
  const coolBounce = new THREE.Mesh(coolBounceGeo, coolBounceMat);
  coolBounce.position.set(-8, 5, -6);
  coolBounce.rotation.y = Math.PI / 3;
  envScene.add(coolBounce);

  // Warm key kicker plane
  const warmKickerGeo = new THREE.PlaneGeometry(10, 6);
  const warmKickerMat = new THREE.MeshBasicMaterial({
    color: 0xffeed4,
    side: THREE.DoubleSide,
  });
  const warmKicker = new THREE.Mesh(warmKickerGeo, warmKickerMat);
  warmKicker.position.set(8, 6, 6);
  warmKicker.rotation.y = -Math.PI / 4;
  envScene.add(warmKicker);

  // Warm floor reflection horizon plane
  const floorGeo = new THREE.PlaneGeometry(30, 30);
  const floorMat = new THREE.MeshBasicMaterial({
    color: 0xeeece2,
    side: THREE.DoubleSide,
  });
  const floorPlane = new THREE.Mesh(floorGeo, floorMat);
  floorPlane.position.set(0, -6, 0);
  floorPlane.rotation.x = -Math.PI / 2;
  envScene.add(floorPlane);

  const envTexture = pmremGenerator.fromScene(envScene, 0.04).texture;

  // Cleanup temporary resources
  pmremGenerator.dispose();
  softboxGeo.dispose();
  softboxMat.dispose();
  coolBounceGeo.dispose();
  coolBounceMat.dispose();
  warmKickerGeo.dispose();
  warmKickerMat.dispose();
  floorGeo.dispose();
  floorMat.dispose();

  return envTexture;
}

/**
 * ============================================================================
 * PROCEDURAL CONTACT SHADOW & AMBIENT OCCLUSION GENERATOR
 * Generates soft inverse-square radial contact shadow textures to physically
 * ground machine plinths, robot leveling feet, and desk legs to the floor.
 * ============================================================================
 */
export function createContactShadowTexture() {
  if (typeof document === "undefined") return null;
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, "rgba(18, 17, 15, 0.76)");
  grad.addColorStop(0.3, "rgba(18, 17, 15, 0.46)");
  grad.addColorStop(0.65, "rgba(18, 17, 15, 0.16)");
  grad.addColorStop(1, "rgba(18, 17, 15, 0.0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 128, 128);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/**
 * ============================================================================
 * PROCEDURAL NORMAL & ROUGHNESS MAP GENERATORS (512x512 HD PBR)
 * High-frequency surface perturbation & coupled roughness for tactile realism.
 * ============================================================================
 */

export function generateTravertinePbrTextures() {
  if (typeof document === "undefined") return { normalMap: null, roughnessMap: null };
  const size = 512;
  const normCanvas = document.createElement("canvas");
  normCanvas.width = size;
  normCanvas.height = size;
  const normCtx = normCanvas.getContext("2d");

  const roughCanvas = document.createElement("canvas");
  roughCanvas.width = size;
  roughCanvas.height = size;
  const roughCtx = roughCanvas.getContext("2d");

  if (!normCtx || !roughCtx) return { normalMap: null, roughnessMap: null };

  const normImg = normCtx.createImageData(size, size);
  const roughImg = roughCtx.createImageData(size, size);
  const nData = normImg.data;
  const rData = roughImg.data;

  // Generate porous horizontal mineral striation normal & roughness maps
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const idx = (y * size + x) * 4;

      // Multi-frequency mineral vein oscillation
      const s1 = Math.sin(y * 0.12 + Math.cos(x * 0.04) * 2.5);
      const s2 = Math.sin(y * 0.35 + Math.sin(x * 0.06) * 3.5);
      const isCavity = Math.sin(x * 0.2 + y * 0.15) > 0.85 && Math.random() > 0.6;
      const cavityDepth = isCavity ? -0.45 : 0;

      const dx = Math.cos(x * 0.08) * 0.05;
      const dy = (s1 * 0.15 + s2 * 0.1 + cavityDepth) * 0.55;
      const len = Math.hypot(-dx, -dy, 1.0) || 1.0;

      nData[idx] = Math.floor(((-dx / len) * 0.5 + 0.5) * 255);
      nData[idx + 1] = Math.floor(((-dy / len) * 0.5 + 0.5) * 255);
      nData[idx + 2] = Math.floor(((1.0 / len) * 0.5 + 0.5) * 255);
      nData[idx + 3] = 255;

      // Coupled roughness: polished crystalline veins (~0.28) vs porous pits (~0.85)
      const roughVal = isCavity ? 0.88 : 0.32 + Math.abs(s1) * 0.38;
      const rByte = Math.floor(roughVal * 255);
      rData[idx] = rByte;
      rData[idx + 1] = rByte;
      rData[idx + 2] = rByte;
      rData[idx + 3] = 255;
    }
  }

  normCtx.putImageData(normImg, 0, 0);
  roughCtx.putImageData(roughImg, 0, 0);

  const normalMap = new THREE.CanvasTexture(normCanvas);
  normalMap.wrapS = THREE.RepeatWrapping;
  normalMap.wrapT = THREE.RepeatWrapping;
  normalMap.repeat.set(4, 3);

  const roughnessMap = new THREE.CanvasTexture(roughCanvas);
  roughnessMap.wrapS = THREE.RepeatWrapping;
  roughnessMap.wrapT = THREE.RepeatWrapping;
  roughnessMap.repeat.set(4, 3);

  return { normalMap, roughnessMap };
}

export function generateTravertineNormalTexture() {
  return generateTravertinePbrTextures().normalMap;
}

export function generatePaperNormalTexture() {
  if (typeof document === "undefined") return null;
  const size = 512;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  const imgData = ctx.createImageData(size, size);
  const data = imgData.data;

  // Interwoven curvilinear cotton rag fiber weave
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const idx = (y * size + x) * 4;

      const fiber1 = Math.sin(x * 0.45 + Math.sin(y * 0.15) * 2.0);
      const fiber2 = Math.cos(y * 0.45 + Math.cos(x * 0.15) * 2.0);
      const noise = (Math.random() - 0.5) * 0.05;

      const dx = (fiber1 * 0.06 + noise) * 0.6;
      const dy = (fiber2 * 0.06 + noise) * 0.6;
      const len = Math.hypot(-dx, -dy, 1.0) || 1.0;

      data[idx] = Math.floor(((-dx / len) * 0.5 + 0.5) * 255);
      data[idx + 1] = Math.floor(((-dy / len) * 0.5 + 0.5) * 255);
      data[idx + 2] = Math.floor(((1.0 / len) * 0.5 + 0.5) * 255);
      data[idx + 3] = 255;
    }
  }

  ctx.putImageData(imgData, 0, 0);
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(4, 5);
  return tex;
}

export function generateBrushedMetalNormalTexture() {
  if (typeof document === "undefined") return null;
  const size = 512;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  const imgData = ctx.createImageData(size, size);
  const data = imgData.data;

  // Anisotropic lathe brush lines (horizontal micro-grooves)
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const idx = (y * size + x) * 4;

      const grooveY = Math.sin(y * 1.6) * 0.08 + (Math.random() - 0.5) * 0.025;
      const grooveX = (Math.random() - 0.5) * 0.012;
      const len = Math.hypot(-grooveX, -grooveY, 1.0) || 1.0;

      data[idx] = Math.floor(((-grooveX / len) * 0.5 + 0.5) * 255);
      data[idx + 1] = Math.floor(((-grooveY / len) * 0.5 + 0.5) * 255);
      data[idx + 2] = Math.floor(((1.0 / len) * 0.5 + 0.5) * 255);
      data[idx + 3] = 255;
    }
  }

  ctx.putImageData(imgData, 0, 0);
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(6, 2);
  return tex;
}
