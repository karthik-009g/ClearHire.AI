import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import {
  PostProcessingPipeline,
  SpringCameraEngine,
  generateTravertinePbrTextures,
} from "./office";

// Reusable scratch vectors to eliminate RAF heap allocations
const _scratchVec3 = new THREE.Vector3();
const _scratchLook = new THREE.Vector3();
const _scratchProj = new THREE.Vector3();

// 6 Key Station Camera Configurations
export const STATION_CONFIGS = {
  "/": {
    name: "Executive Decision Desk & Portfolio",
    eye: new THREE.Vector3(0.25, 1.42, 0.55),
    look: new THREE.Vector3(0.25, 0.80, -2.15),
    focalAsset: "desk",
    laserActive: false,
  },
  "/resmat-ai": {
    name: "Candidate Intake Credenza & Cotton Dossier",
    eye: new THREE.Vector3(0.35, 1.55, 2.70),
    look: new THREE.Vector3(1.20, 0.835, 1.00),
    focalAsset: "credenza",
    laserActive: false,
  },
  "/jd-analyzer": {
    name: "Copier Scanner Platen & Laser Curtain",
    eye: new THREE.Vector3(-1.15, 1.42, 0.15),
    look: new THREE.Vector3(-2.00, 1.10, -0.80),
    focalAsset: "copier",
    laserActive: true,
  },
  "/job-hunter": {
    name: "Transit Rail & Radar Constellation",
    eye: new THREE.Vector3(-0.15, 1.58, -0.65),
    look: new THREE.Vector3(0.10, 1.08, -2.00),
    focalAsset: "transit",
    laserActive: false,
  },
  "/applications": {
    name: "48H SLA Chronometer & Enclave",
    eye: new THREE.Vector3(-0.10, 1.12, -1.65),
    look: new THREE.Vector3(-0.15, 0.78, -2.20),
    focalAsset: "chronometer",
    laserActive: false,
  },
  "/student-lab": {
    name: "Autonomous Drone Inspector Hub",
    eye: new THREE.Vector3(-1.40, 1.62, -0.15),
    look: new THREE.Vector3(-2.00, 1.48, -0.80),
    focalAsset: "robot",
    laserActive: false,
  },
};

// Fallback configuration for any other authenticated route (e.g., /funnel-analytics)
const DEFAULT_STATION = {
  name: "Executive Suite Panorama",
  eye: new THREE.Vector3(0.20, 1.70, 1.20),
  look: new THREE.Vector3(0.00, 0.90, -1.80),
  focalAsset: "panoramic",
  laserActive: false,
};

/**
 * Normalizes a GLTF model into a centered wrapper group
 */
function fitModel(gltfScene, { targetHeight = 0, centerAtBase = true }) {
  const wrapper = new THREE.Group();
  wrapper.add(gltfScene);

  gltfScene.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(gltfScene);
  const size = box.getSize(new THREE.Vector3());

  let scale = 1.0;
  if (targetHeight > 0 && size.y > 0) {
    scale = targetHeight / size.y;
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

  return wrapper;
}

/**
 * Singleton Engine Managing Persistent Three.js Scene, WebGL Context, and RAF
 */
class AmbientWorldEngine {
  constructor() {
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.postPipeline = null;
    this.springCam = null;
    this.container = null;
    this.rafId = null;
    this.isInitialized = false;
    this.isAttached = false;
    this.detachTimeout = null;

    this.activeRoute = "/";
    this.targetEye = new THREE.Vector3(0.25, 1.42, 0.55);
    this.targetLook = new THREE.Vector3(0.25, 0.80, -2.15);

    // Animated objects references
    this.droneGroup = null;
    this.laserMesh = null;
    this.laserMat = null;
    this.chronoHand = null;

    this.lastTime = 0;
    this.startTime = 0;
    this.isTabVisible = true;
    this.lastInteractionTime = 0;
    this.lastRenderTime = 0;

    // Bind event handlers
    this.onWindowResize = this.onWindowResize.bind(this);
    this.onMouseMove = this.onMouseMove.bind(this);
    this.onVisibilityChange = this.onVisibilityChange.bind(this);
    this.onUserActive = this.onUserActive.bind(this);
    this.animate = this.animate.bind(this);
  }

  init() {
    if (this.isInitialized || typeof window === "undefined") return;

    // 1. Scene setup with studio warm stone background
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xf6f4ee);

    // 2. Camera setup with architectural perspective (42.0°)
    const w = window.innerWidth || 1200;
    const h = window.innerHeight || 800;
    const aspect = w / h;
    const initialFov = aspect < 1.0 ? 42.0 / Math.min(1.0, aspect * 1.35) : 42.0;
    this.camera = new THREE.PerspectiveCamera(initialFov, aspect, 0.1, 100);
    this.camera.up.set(0, 1, 0);

    // 3. WebGL Renderer with strict 60 FPS performance caps
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
      stencil: false,
      depth: true,
      alpha: false,
    });
    this.renderer.setSize(w, h);
    // Strict 60 FPS Guardrail: Cap pixel ratio at 1.5
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 0.85;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.renderer.domElement.style.pointerEvents = "none";

    // 4. Post-Processing Pipeline (runs half-res bloom and mobile bypass)
    this.postPipeline = new PostProcessingPipeline(
      this.renderer,
      this.scene,
      this.camera,
      { width: w, height: h }
    );

    // 5. Spring Camera Dynamics Engine
    this.springCam = new SpringCameraEngine(this.camera, {
      baseFov: 42.0,
      dampingSpeed: 3.8, // Calibrated critically damped transition speed
    });

    // 6. Studio Lighting & Environment
    this._buildLighting();

    // 7. Architectural Room Envelope & PBR Surfaces
    this._buildRoomEnvelope();

    // 8. Modular Office Stations (Desk, Credenza, Copier, Robot, Chrono)
    this._buildSceneAssets();

    // 9. Attach global listeners
    window.addEventListener("resize", this.onWindowResize);
    window.addEventListener("mousemove", this.onMouseMove, { passive: true });
    window.addEventListener("pointermove", this.onUserActive, { passive: true });
    window.addEventListener("scroll", this.onUserActive, { passive: true });
    window.addEventListener("touchstart", this.onUserActive, { passive: true });
    document.addEventListener("visibilitychange", this.onVisibilityChange);

    this.startTime = performance.now();
    this.lastTime = performance.now();
    this.lastInteractionTime = performance.now();
    this.lastRenderTime = performance.now();
    this.isInitialized = true;
  }

  attach(newContainer, route) {
    if (this.detachTimeout) {
      clearTimeout(this.detachTimeout);
      this.detachTimeout = null;
    }

    this.init();

    if (this.container !== newContainer) {
      this.container = newContainer;
      if (this.renderer && !newContainer.contains(this.renderer.domElement)) {
        newContainer.appendChild(this.renderer.domElement);
      }
    }

    this.isAttached = true;
    this.setActiveRoute(route);
    this.onWindowResize();

    if (!this.rafId) {
      this.lastTime = performance.now();
      this.lastInteractionTime = performance.now();
      this.rafId = requestAnimationFrame(this.animate);
    }
  }

  detach(container) {
    // Grace period before pausing RAF (prevents frame drops during fast route clicks)
    this.detachTimeout = setTimeout(() => {
      this.isAttached = false;
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
        this.rafId = null;
      }
    }, 400);
  }

  setActiveRoute(route) {
    this.activeRoute = route;
    const config = STATION_CONFIGS[route] || DEFAULT_STATION;
    this.targetEye.copy(config.eye);
    this.targetLook.copy(config.look);

    if (this.laserMesh) {
      this.laserMesh.visible = config.laserActive;
    }
    this.onUserActive();
  }

  onUserActive() {
    this.lastInteractionTime = performance.now();
  }

  onWindowResize() {
    if (!this.renderer || !this.camera || typeof window === "undefined") return;
    const w = window.innerWidth;
    const h = window.innerHeight;
    const aspect = w / h;

    // Mobile adaptive FOV: dynamically widen in portrait mode (<1.0) to prevent lateral cutoff
    if (aspect < 1.0) {
      this.camera.fov = 42.0 / Math.min(1.0, aspect * 1.35);
    } else {
      this.camera.fov = 42.0;
    }

    this.camera.aspect = aspect;
    this.camera.updateProjectionMatrix();

    this.renderer.setSize(w, h);
    if (this.postPipeline) {
      this.postPipeline.setSize(w, h);
    }
    this.onUserActive();
  }

  onMouseMove(e) {
    if (!this.springCam) return;
    const normX = (e.clientX / window.innerWidth - 0.5) * 2;
    const normY = -(e.clientY / window.innerHeight - 0.5) * 2;
    this.springCam.setMouseTarget(normX, normY);
    this.onUserActive();
  }

  onVisibilityChange() {
    this.isTabVisible = !document.hidden;
    if (this.isTabVisible && this.isAttached && !this.rafId) {
      this.lastTime = performance.now();
      this.lastInteractionTime = performance.now();
      this.rafId = requestAnimationFrame(this.animate);
    }
  }

  animate() {
    if (!this.isAttached || !this.isTabVisible) {
      this.rafId = null;
      return;
    }

    this.rafId = requestAnimationFrame(this.animate);

    const now = performance.now();
    const idleDuration = now - this.lastInteractionTime;

    // Idle throttling: if user is idle > 3.5s and spring camera is settled, cap render rate at 20 FPS
    const isCameraSettled =
      this.springCam &&
      typeof this.springCam.isSettled === "function" &&
      this.springCam.isSettled();
    if (idleDuration > 3500 && isCameraSettled) {
      if (now - this.lastRenderTime < 50) return;
    }

    this.lastRenderTime = now;
    const dt = Math.min(0.05, Math.max(0.001, (now - this.lastTime) / 1000));
    this.lastTime = now;
    const time = (now - this.startTime) / 1000;

    // 1. Update Camera Position and LookAt via Spring Engine
    if (this.springCam) {
      this.springCam.update(dt, this.targetEye, this.targetLook);
    }

    // 2. Animate Chronometer Ticking Emerald Second Hand
    if (this.chronoHand) {
      this.chronoHand.rotation.z = -time * 1.5;
    }

    // 3. Animate Autonomous Robot Drone Hover Physics
    if (this.droneGroup) {
      this.droneGroup.position.y = 1.48 + Math.sin(time * 1.8) * 0.025;
      this.droneGroup.rotation.y = 0.35 + Math.sin(time * 0.8) * 0.05;
    }

    // 4. Animate Copier Laser Curtain
    if (this.laserMesh && this.laserMesh.visible) {
      this.laserMesh.position.z = -0.80 + Math.sin(time * 5.0) * 0.08;
      if (this.laserMat?.uniforms?.uTime) {
        this.laserMat.uniforms.uTime.value = time;
      }
    }

    // 5. Render Scene via Post-Processing Pipeline
    if (this.postPipeline) {
      this.postPipeline.render(time);
    } else {
      this.renderer.render(this.scene, this.camera);
    }
  }

  _buildLighting() {
    // Directional Sun Light
    const sunLight = new THREE.DirectionalLight(0xfff8ee, 1.15);
    sunLight.position.set(5.0, 7.5, 4.0);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 1024;
    sunLight.shadow.mapSize.height = 1024;
    sunLight.shadow.bias = -0.0001;
    this.scene.add(sunLight);

    // Warm Ambient Studio Fill
    const ambientLight = new THREE.AmbientLight(0xf5efe6, 0.35);
    this.scene.add(ambientLight);

    // Desk Spot Accent
    const deskSpot = new THREE.SpotLight(0xfffbf0, 0.9, 7.0, Math.PI / 4, 0.4);
    deskSpot.position.set(0.25, 3.2, -2.15);
    deskSpot.target.position.set(0.25, 0.76, -2.15);
    this.scene.add(deskSpot);
    this.scene.add(deskSpot.target);
  }

  _buildRoomEnvelope() {
    const { normal: travertineNormal, roughness: travertineRoughness } =
      generateTravertinePbrTextures();

    // 16m x 16m Italian Limestone Floor
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0xe0dad0,
      roughness: 0.50,
      metalness: 0.04,
      normalMap: travertineNormal,
      roughnessMap: travertineRoughness,
    });
    if (travertineNormal) floorMat.normalScale.set(0.2, 0.2);

    const floor = new THREE.Mesh(new THREE.PlaneGeometry(16, 16), floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(0, 0, -1.0);
    floor.receiveShadow = true;
    this.scene.add(floor);

    // Gallery Plaster Walls
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xded9cf,
      roughness: 0.92,
      metalness: 0.02,
    });
    const backWall = new THREE.Mesh(new THREE.PlaneGeometry(16, 4.5), wallMat);
    backWall.position.set(0, 2.25, -4.8);
    backWall.receiveShadow = true;
    this.scene.add(backWall);

    const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(16, 4.5), wallMat);
    leftWall.rotation.y = Math.PI / 2;
    leftWall.position.set(-5.5, 2.25, -1.0);
    leftWall.receiveShadow = true;
    this.scene.add(leftWall);

    // Fine gallery baseboard
    const baseboardMat = new THREE.MeshStandardMaterial({
      color: 0x2d2822,
      roughness: 0.4,
      metalness: 0.6,
    });
    const baseboard = new THREE.Mesh(new THREE.BoxGeometry(16, 0.12, 0.04), baseboardMat);
    baseboard.position.set(0, 0.06, -4.78);
    this.scene.add(baseboard);
  }

  _buildSceneAssets() {
    const gltfLoader = new GLTFLoader();

    // 1. Executive Modernist Desk
    gltfLoader.load(
      "/assets/clearhire-scene/steel-office-desk.glb",
      (gltf) => {
        const desk = fitModel(gltf.scene, { targetHeight: 0.76, centerAtBase: true });
        desk.position.set(0.25, 0.0, -2.15);
        this.scene.add(desk);
      },
      undefined,
      (err) => console.warn("AmbientWorld desk fallback:", err)
    );

    // 2. Executive Task Chair
    gltfLoader.load(
      "/assets/clearhire-scene/office-task-chair.glb",
      (gltf) => {
        const chair = fitModel(gltf.scene, { targetHeight: 0.98, centerAtBase: true });
        chair.position.set(0.25, 0.0, -2.85);
        chair.rotation.y = 0.08;
        this.scene.add(chair);
      },
      undefined,
      (err) => console.warn("AmbientWorld chair fallback:", err)
    );

    // 3. Office Copier / Scanner
    gltfLoader.load(
      "/assets/clearhire-scene/office-copier.glb",
      (gltf) => {
        const copier = fitModel(gltf.scene, { targetHeight: 1.15, centerAtBase: true });
        copier.position.set(-2.00, 0.0, -0.80);
        copier.rotation.y = 0.48;
        this.scene.add(copier);
      },
      undefined,
      (err) => console.warn("AmbientWorld copier fallback:", err)
    );

    // 4. Sweeping Optical Cyan Laser on Copier
    const laserGeo = new THREE.PlaneGeometry(0.50, 0.16);
    this.laserMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.75,
      side: THREE.DoubleSide,
    });
    this.laserMesh = new THREE.Mesh(laserGeo, this.laserMat);
    this.laserMesh.rotation.x = -Math.PI / 2;
    this.laserMesh.rotation.z = 0.48;
    this.laserMesh.position.set(-2.00, 1.09, -0.80);
    this.laserMesh.visible = false;
    this.scene.add(this.laserMesh);

    // 5. Autonomous Robot Drone
    gltfLoader.load(
      "/assets/clearhire-scene/robot.glb",
      (gltf) => {
        const robot = fitModel(gltf.scene, { targetHeight: 0.38, centerAtBase: false });
        robot.position.set(-2.00, 1.48, -0.80);
        robot.rotation.y = 0.35;
        this.droneGroup = robot;
        this.scene.add(robot);
      },
      undefined,
      (err) => console.warn("AmbientWorld robot fallback:", err)
    );

    // 6. Chronometer Second Hand Reference (Desk Chronometer at -0.15, 0.765, -2.20)
    const chronoGroup = new THREE.Group();
    chronoGroup.position.set(-0.15, 0.765, -2.20);
    chronoGroup.rotation.x = 0.28;

    // Dial body
    const dialBody = new THREE.Mesh(
      new THREE.CylinderGeometry(0.08, 0.085, 0.02, 32),
      new THREE.MeshStandardMaterial({ color: 0xd4af37, metalness: 0.85, roughness: 0.25 })
    );
    dialBody.rotation.x = Math.PI / 2;
    chronoGroup.add(dialBody);

    // Face
    const dialFace = new THREE.Mesh(
      new THREE.CircleGeometry(0.075, 32),
      new THREE.MeshStandardMaterial({ color: 0xfcfbfa, roughness: 0.4 })
    );
    dialFace.position.z = 0.011;
    chronoGroup.add(dialFace);

    // Emerald Second Hand
    this.chronoHand = new THREE.Mesh(
      new THREE.BoxGeometry(0.003, 0.06, 0.002),
      new THREE.MeshBasicMaterial({ color: 0x059669 })
    );
    this.chronoHand.position.set(0, 0.02, 0.012);
    chronoGroup.add(this.chronoHand);
    this.scene.add(chronoGroup);
  }

  dispose() {
    if (this.rafId) cancelAnimationFrame(this.rafId);
    if (typeof window !== "undefined") {
      window.removeEventListener("resize", this.onWindowResize);
      window.removeEventListener("mousemove", this.onMouseMove);
      window.removeEventListener("pointermove", this.onUserActive);
      window.removeEventListener("scroll", this.onUserActive);
      window.removeEventListener("touchstart", this.onUserActive);
      document.removeEventListener("visibilitychange", this.onVisibilityChange);
    }
    if (this.postPipeline) this.postPipeline.dispose();
    if (this.renderer) this.renderer.dispose();
    this.isInitialized = false;
    this.isAttached = false;
  }
}

// Module-level persistent singleton
let globalAmbientEngine = null;

function getAmbientWorldEngine() {
  if (typeof window === "undefined") return null;
  if (!globalAmbientEngine) {
    globalAmbientEngine = new AmbientWorldEngine();
  }
  return globalAmbientEngine;
}

/**
 * ClearHireAmbientWorld React Wrapper Component
 */
export default function ClearHireAmbientWorld({ activeRoute = "/" }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return undefined;

    const engine = getAmbientWorldEngine();
    if (engine) {
      engine.attach(container, activeRoute);
    }

    return () => {
      if (engine) {
        engine.detach(container);
      }
    };
  }, []);

  useEffect(() => {
    const engine = getAmbientWorldEngine();
    if (engine) {
      engine.setActiveRoute(activeRoute);
    }
  }, [activeRoute]);

  return (
    <div
      ref={mountRef}
      id="clearhire-ambient-canvas-container"
      className="fixed inset-0 w-full h-full pointer-events-none select-none z-0 overflow-hidden"
      aria-hidden="true"
    />
  );
}
