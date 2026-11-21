import * as THREE from "three";

/**
 * ============================================================================
 * CINEMATIC CAMERA ENGINE (Lusion & Awwwards Gold Standard)
 * - Rock-solid stable horizon: camera.up strictly (0, 1, 0).
 * - Zero roll tilt, zero shaking, zero vibration, zero jitter.
 * - Constant, calibrated focal length (FOV 42° - architectural perspective).
 * - Critically damped exponential decay interpolation: 1.0 - exp(-dampingSpeed * dt).
 * - Sub-pixel smooth micro-parallax (clamped to ±0.03m).
 * - Zero heap allocations per frame in RAF loop.
 * ============================================================================
 */

export class SpringCameraEngine {
  constructor(camera, { baseFov = 42.0, dampingSpeed = 5.0 } = {}) {
    this.camera = camera;
    this.baseFov = baseFov;
    this.camera.fov = baseFov;
    this.camera.up.set(0, 1, 0);
    this.camera.updateProjectionMatrix();
    this.dampingSpeed = dampingSpeed;

    this.currentEye = camera.position.clone();
    this.currentLook = new THREE.Vector3(0, 0, 0);

    this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    this._parallaxOffset = new THREE.Vector3();
    this._targetWithParallax = camera.position.clone();
    this._targetLook = new THREE.Vector3(0, 0, 0);
  }

  setMouseTarget(normX, normY) {
    this.mouse.targetX = normX;
    this.mouse.targetY = normY;
  }

  update(dt, targetEye, targetLook) {
    const safeDt = Math.min(0.1, Math.max(0.001, dt));

    // 1. Smooth micro-parallax (subtle ±0.03m displacement)
    const pDecay = 1.0 - Math.exp(-3.5 * safeDt);
    this.mouse.x += (this.mouse.targetX - this.mouse.x) * pDecay;
    this.mouse.y += (this.mouse.targetY - this.mouse.y) * pDecay;

    this._parallaxOffset.set(this.mouse.x * 0.03, this.mouse.y * 0.02, 0);
    this._targetWithParallax.copy(targetEye).add(this._parallaxOffset);
    if (targetLook) {
      this._targetLook.copy(targetLook);
    }

    // 2. Exponential decay damping for camera eye (Smooth, zero overshoot, zero jitter)
    const decay = 1.0 - Math.exp(-this.dampingSpeed * safeDt);
    this.currentEye.lerp(this._targetWithParallax, decay);
    this.camera.position.copy(this.currentEye);

    // 3. Exponential decay damping for camera lookAt
    this.currentLook.lerp(this._targetLook, decay);

    // 4. Strictly lock horizon to (0, 1, 0) - Zero roll wobble
    this.camera.up.set(0, 1, 0);
    this.camera.lookAt(this.currentLook);
  }

  isSettled(threshold = 0.001) {
    return (
      this.currentEye.distanceToSquared(this._targetWithParallax) < threshold &&
      this.currentLook.distanceToSquared(this._targetLook) < threshold &&
      Math.abs(this.mouse.targetX - this.mouse.x) < 0.01 &&
      Math.abs(this.mouse.targetY - this.mouse.y) < 0.01
    );
  }
}
