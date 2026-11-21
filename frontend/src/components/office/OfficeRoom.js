import * as THREE from "three";

/**
 * ============================================================================
 * INDEPENDENT COMPONENT: OfficeRoom
 * Principles from Anatomy & Motion skills:
 * - Real architectural room envelope (walls, skirting boards, stone tile floor).
 * - Calibrated studio lighting (key sun, cool sky fill, floor bounce).
 * - Overhead softbox lighting rig structure.
 * - Floating golden ambient dust motes.
 * - Contact shadow plane for grounded realism.
 * ============================================================================
 */
export function createOfficeRoom({
  floorColor = 0xeeece2,
  wallColor = 0xf5f2eb,
  gridColor = 0xd4ccbd,
  dustCount = 280,
} = {}) {
  const group = new THREE.Group();
  group.name = "OfficeRoom";

  // 1. Stone Tile Floor with subtle PBR roughness
  const floorGeo = new THREE.PlaneGeometry(90, 90);
  const floorMat = new THREE.MeshStandardMaterial({
    color: floorColor,
    roughness: 0.88,
    metalness: 0.05,
  });
  const floorMesh = new THREE.Mesh(floorGeo, floorMat);
  floorMesh.rotation.x = -Math.PI / 2;
  floorMesh.position.y = -0.65;
  floorMesh.receiveShadow = true;
  group.add(floorMesh);

  // Architectural Grid Markings
  const gridHelper = new THREE.GridHelper(36, 36, gridColor, 0xe4ded4);
  gridHelper.position.y = -0.64;
  group.add(gridHelper);

  // 2. Studio Walls (Back & Side Corner)
  const wallMat = new THREE.MeshStandardMaterial({
    color: wallColor,
    roughness: 0.95,
    metalness: 0.02,
  });

  // Back Wall
  const backWall = new THREE.Mesh(new THREE.PlaneGeometry(50, 16), wallMat);
  backWall.position.set(0, 7.35, -9.5);
  backWall.receiveShadow = true;
  group.add(backWall);

  // Side Left Wall
  const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(30, 16), wallMat);
  leftWall.rotation.y = Math.PI / 2;
  leftWall.position.set(-15, 7.35, 2.5);
  leftWall.receiveShadow = true;
  group.add(leftWall);

  // 3. Architectural Skirting / Baseboards along walls
  const baseboardMat = new THREE.MeshStandardMaterial({
    color: 0xd8d2c4,
    roughness: 0.7,
    metalness: 0.1,
  });
  const backBaseboard = new THREE.Mesh(
    new THREE.BoxGeometry(50, 0.18, 0.04),
    baseboardMat
  );
  backBaseboard.position.set(0, -0.56, -9.46);
  group.add(backBaseboard);

  const leftBaseboard = new THREE.Mesh(
    new THREE.BoxGeometry(0.04, 0.18, 30),
    baseboardMat
  );
  leftBaseboard.position.set(-14.96, -0.56, 2.5);
  group.add(leftBaseboard);

  // 4. Overhead Studio Lighting Rig Structure (Industrial Steel Gantries)
  const gantryMat = new THREE.MeshStandardMaterial({
    color: 0x2b303a,
    metalness: 0.8,
    roughness: 0.35,
  });
  const gantryBeam1 = new THREE.Mesh(
    new THREE.BoxGeometry(24, 0.08, 0.08),
    gantryMat
  );
  gantryBeam1.position.set(0, 6.2, 0);
  group.add(gantryBeam1);

  const gantryBeam2 = new THREE.Mesh(
    new THREE.BoxGeometry(24, 0.08, 0.08),
    gantryMat
  );
  gantryBeam2.position.set(0, 6.2, -4.0);
  group.add(gantryBeam2);

  // Overhead Softbox Diffuser Panels
  const softboxMat = new THREE.MeshBasicMaterial({
    color: 0xfffaee,
    transparent: true,
    opacity: 0.85,
  });
  const softboxPanel1 = new THREE.Mesh(
    new THREE.PlaneGeometry(6, 3),
    softboxMat
  );
  softboxPanel1.rotation.x = Math.PI / 2;
  softboxPanel1.position.set(0, 6.15, 0);
  group.add(softboxPanel1);

  // 5. Ambient Floating Golden Dust Motes
  const motePos = new Float32Array(dustCount * 3);
  const moteVel = new Float32Array(dustCount);
  for (let i = 0; i < dustCount; i += 1) {
    motePos[i * 3] = (Math.random() - 0.5) * 24;
    motePos[i * 3 + 1] = Math.random() * 7 - 0.5;
    motePos[i * 3 + 2] = Math.random() * 24 - 12;
    moteVel[i] = 0.2 + Math.random() * 0.5;
  }
  const moteGeo = new THREE.BufferGeometry();
  moteGeo.setAttribute("position", new THREE.BufferAttribute(motePos, 3));
  const moteMat = new THREE.PointsMaterial({
    color: 0xd4af37,
    size: 0.045,
    transparent: true,
    opacity: 0.55,
  });
  const dustMotes = new THREE.Points(moteGeo, moteMat);
  group.add(dustMotes);

  // Per-frame update method
  const update = (time, dt) => {
    const posAttr = moteGeo.attributes.position;
    const arr = posAttr.array;
    for (let i = 0; i < dustCount; i += 1) {
      arr[i * 3 + 1] += Math.sin(time * moteVel[i] + i) * 0.0015;
      arr[i * 3] += Math.cos(time * 0.3 + i) * 0.0008;
    }
    posAttr.needsUpdate = true;
  };

  const dispose = () => {
    floorGeo.dispose();
    floorMat.dispose();
    moteGeo.dispose();
    moteMat.dispose();
  };

  return {
    group,
    update,
    dispose,
  };
}
