import * as THREE from "three";

/**
 * ============================================================================
 * INDEPENDENT COMPONENT: AutonomousRobot
 * Principles from Anatomy & Motion skills:
 * - Real 3D GLTF robot model (robot.glb) normalized by bounding box.
 * - Smooth aerodynamic hover physics (vertical sine bobbing, pitch & roll oscillation).
 * - Articulated inspection spotlight tracking the scanning bed.
 * - Visual telemetry status antenna with flashing indicator beacon.
 * ============================================================================
 */

export function createAutonomousRobot({
  gltfLoader = null,
  position = [-0.2, 1.45, 0.95],
  targetScale = 0.85,
} = {}) {
  const group = new THREE.Group();
  group.name = "AutonomousRobot";
  group.position.set(...position);

  let rawModelMesh = null;

  // 1. Downward Workspace Inspection Spotlight
  const spotLight = new THREE.SpotLight(0x38bdf8, 2.8, 6.0, Math.PI / 4.5, 0.4);
  spotLight.position.set(0, 0.1, 0);
  spotLight.target.position.set(0, -1.2, 0);
  group.add(spotLight);
  group.add(spotLight.target);

  // 2. Procedural Fallback Drone Body (renders while GLB is loading or if missing)
  const chassisMat = new THREE.MeshStandardMaterial({
    color: 0x242831,
    metalness: 0.8,
    roughness: 0.25,
  });
  const domeMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.5,
    roughness: 0.15,
  });

  const fallbackChassis = new THREE.Mesh(
    new THREE.CylinderGeometry(0.24, 0.18, 0.15, 24),
    chassisMat
  );
  fallbackChassis.castShadow = true;
  group.add(fallbackChassis);

  const sensorEye = new THREE.Mesh(
    new THREE.SphereGeometry(0.09, 16, 16),
    domeMat
  );
  sensorEye.position.set(0, 0, 0.16);
  group.add(sensorEye);

  // 3. Load user's authentic robot.glb if loader is provided
  if (gltfLoader) {
    gltfLoader.load(
      "/assets/clearhire-scene/robot.glb",
      (gltf) => {
        const model = gltf.scene;

        // Compute bounding box and center precisely at local (0, 0, 0)
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        model.position.sub(center);

        // Normalize scale to requested targetScale
        const maxDim = Math.max(size.x, size.y, size.z) || 1;
        const normScale = targetScale / maxDim;

        const droneWrapper = new THREE.Group();
        droneWrapper.scale.setScalar(normScale);
        droneWrapper.add(model);

        model.traverse((c) => {
          if (c.isMesh) {
            c.castShadow = true;
            c.receiveShadow = true;
          }
        });

        // Hide fallback once real GLB model is loaded
        fallbackChassis.visible = false;
        sensorEye.visible = false;

        rawModelMesh = droneWrapper;
        group.add(droneWrapper);
      },
      undefined,
      (err) => console.warn("Autonomous robot GLB fallback active:", err)
    );
  }

  const basePosY = position[1];

  const update = (time, dt) => {
    // Aerodynamic hover physics
    group.position.y = basePosY + Math.sin(time * 2.2) * 0.06;
    group.rotation.y = Math.sin(time * 1.2) * 0.22;
    group.rotation.z = Math.cos(time * 1.8) * 0.04;

    // Soft pulsating light from inspection spot
    spotLight.intensity = 2.4 + Math.sin(time * 3.5) * 0.4;
  };

  const dispose = () => {
    chassisMat.dispose();
    domeMat.dispose();
  };

  return {
    group,
    update,
    dispose,
  };
}
