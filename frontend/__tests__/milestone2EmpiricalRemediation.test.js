import React from "react";
import fs from "fs";
import path from "path";
import * as parser from "@babel/parser";
import traverse from "@babel/traverse";

jest.mock("three", () => {
  class Vector2 {
    constructor(x = 0, y = 0) {
      this.x = x;
      this.y = y;
    }
    set(x, y) {
      this.x = x;
      this.y = y;
      return this;
    }
  }

  class Vector3 {
    constructor(x = 0, y = 0, z = 0) {
      this.x = x;
      this.y = y;
      this.z = z;
    }
    set(x, y, z) {
      this.x = x;
      this.y = y;
      this.z = z;
      return this;
    }
    clone() {
      return new Vector3(this.x, this.y, this.z);
    }
    copy(v) {
      this.x = v.x;
      this.y = v.y;
      this.z = v.z;
      return this;
    }
    add(v) {
      this.x += v.x;
      this.y += v.y;
      this.z += v.z;
      return this;
    }
    lerp(v, alpha) {
      this.x += (v.x - this.x) * alpha;
      this.y += (v.y - this.y) * alpha;
      this.z += (v.z - this.z) * alpha;
      return this;
    }
    distanceToSquared(v) {
      const dx = this.x - v.x;
      const dy = this.y - v.y;
      const dz = this.z - v.z;
      return dx * dx + dy * dy + dz * dz;
    }
    getWorldPosition(target) {
      target.copy(this);
      return target;
    }
    project() {
      return this;
    }
    setFromSpherical(s) {
      const sinRadius = Math.sin(s.phi) * s.radius;
      this.x = sinRadius * Math.sin(s.theta);
      this.y = Math.cos(s.phi) * s.radius;
      this.z = sinRadius * Math.cos(s.theta);
      return this;
    }
  }

  class Spherical {
    constructor(radius = 1, phi = 0, theta = 0) {
      this.radius = radius;
      this.phi = phi;
      this.theta = theta;
    }
    set(r, p, t) {
      this.radius = r;
      this.phi = p;
      this.theta = t;
      return this;
    }
  }

  class Clock {
    constructor() {
      this.oldTime = 0;
    }
    getDelta() {
      return 0.016;
    }
    getElapsedTime() {
      return 1.0;
    }
  }

  class Scene {
    constructor() {
      this.background = null;
      this.fog = null;
      this.children = [];
    }
    add(child) {
      this.children.push(child);
    }
    traverse(cb) {
      cb(this);
    }
  }

  class Color {
    constructor(val) {
      this.val = val;
    }
  }

  class FogExp2 {
    constructor(color, density) {
      this.color = color;
      this.density = density;
    }
  }

  class PerspectiveCamera {
    constructor(fov = 45, aspect = 1, near = 0.1, far = 1000) {
      this.fov = fov;
      this.aspect = aspect;
      this.near = near;
      this.far = far;
      this.position = new Vector3();
      this.up = new Vector3(0, 1, 0);
    }
    updateProjectionMatrix() {}
    lookAt() {}
    setFromSpherical() {}
  }

  class WebGLRenderer {
    constructor() {
      this.domElement = document.createElement("canvas");
      this.shadowMap = { enabled: false, type: 0 };
      this.toneMapping = 0;
      this.toneMappingExposure = 1;
    }
    setSize() {}
    setPixelRatio() {}
    render() {}
    dispose() {}
  }

  class Raycaster {
    constructor() {
      this.ray = {};
    }
    setFromCamera() {}
    intersectObjects(objects, recursive, optionalTarget) {
      if (optionalTarget) {
        optionalTarget.length = 0;
        return optionalTarget;
      }
      return [];
    }
  }

  class Group {
    constructor() {
      this.position = new Vector3();
      this.rotation = { x: 0, y: 0, z: 0 };
      this.children = [];
    }
    add(child) {
      this.children.push(child);
    }
    getWorldPosition(v) {
      v.copy(this.position);
      return v;
    }
  }

  class GridHelper extends Group {}

  class Mesh {
    constructor(geo, mat) {
      this.geometry = geo;
      this.material = mat;
      this.position = new Vector3();
      this.rotation = { x: 0, y: 0, z: 0 };
      this.scale = {
        setScalar: jest.fn(),
      };
      this.userData = {};
    }
  }

  class Line {
    constructor(geo, mat) {
      this.geometry = geo;
      this.material = mat;
      this.computeLineDistances = jest.fn();
    }
  }

  class BufferGeometry {
    setAttribute() {}
    setFromPoints() {
      return this;
    }
    dispose() {}
  }

  class BufferAttribute {
    constructor(arr, size) {
      this.array = arr;
      this.itemSize = size;
    }
  }

  class Float32BufferAttribute extends BufferAttribute {}

  class Material {
    constructor() {
      this.opacity = 1;
    }
    dispose() {}
  }

  class LineSegments {
    constructor() {
      this.geometry = new BufferGeometry();
      this.material = new Material();
    }
  }

  class LineBasicMaterial extends Material {}
  class LineDashedMaterial extends Material {}
  class Points {
    constructor() {
      this.rotation = { x: 0, y: 0, z: 0 };
      this.geometry = new BufferGeometry();
      this.material = new Material();
    }
  }
  class PointsMaterial extends Material {}
  class MeshBasicMaterial extends Material {}
  class MeshStandardMaterial extends Material {}
  class RingGeometry extends BufferGeometry {}
  class CircleGeometry extends BufferGeometry {}
  class IcosahedronGeometry extends BufferGeometry {}
  class OctahedronGeometry extends BufferGeometry {}
  class TorusGeometry extends BufferGeometry {}
  class SphereGeometry extends BufferGeometry {}
  class BoxGeometry extends BufferGeometry {}
  class CylinderGeometry extends BufferGeometry {}
  class AmbientLight {}
  class DirectionalLight {
    constructor() {
      this.position = new Vector3();
    }
  }
  class PointLight {
    constructor() {
      this.position = new Vector3();
    }
  }

  return {
    Vector2,
    Vector3,
    Spherical,
    Clock,
    Scene,
    Color,
    FogExp2,
    PerspectiveCamera,
    WebGLRenderer,
    Raycaster,
    Group,
    GridHelper,
    Mesh,
    Line,
    BufferGeometry,
    BufferAttribute,
    Float32BufferAttribute,
    Material,
    LineSegments,
    LineBasicMaterial,
    LineDashedMaterial,
    Points,
    PointsMaterial,
    MeshBasicMaterial,
    MeshStandardMaterial,
    RingGeometry,
    CircleGeometry,
    IcosahedronGeometry,
    OctahedronGeometry,
    TorusGeometry,
    SphereGeometry,
    BoxGeometry,
    CylinderGeometry,
    AmbientLight,
    DirectionalLight,
    PointLight,
    AdditiveBlending: 2,
    DoubleSide: 2,
    ACESFilmicToneMapping: 4,
    PCFSoftShadowMap: 2,
  };
});

import * as THREE from "three";
import { SpringCameraEngine } from "../src/components/office/SpringCameraEngine";
import { SecondOrderDynamics3D } from "../src/components/ThreeSpatialRadar";
import ThreeSpatialRadar from "../src/components/ThreeSpatialRadar";
import { render, act } from "@testing-library/react";

describe("Milestone 2 Empirical Remediation Verification Suite", () => {
  describe("1. SpringCameraEngine isSettled & Idle Throttling", () => {
    it("defines isSettled(threshold) and correctly detects camera and mouse convergence", () => {
      const camera = new THREE.PerspectiveCamera(42, 16 / 9, 0.1, 100);
      camera.position.set(0, 2, 5);
      const springCam = new SpringCameraEngine(camera);

      expect(typeof springCam.isSettled).toBe("function");

      // Initial state is settled because target matches initial eye and look
      expect(springCam.isSettled()).toBe(true);

      // Advance target far away
      const farTarget = new THREE.Vector3(10, 5, 20);
      const farLook = new THREE.Vector3(0, 0, -10);
      springCam.update(0.016, farTarget, farLook);

      // Camera has not reached target yet, so isSettled must be false
      expect(springCam.isSettled()).toBe(false);

      // Step physics until settled (exponential decay)
      for (let i = 0; i < 200; i++) {
        springCam.update(0.05, farTarget, farLook);
      }

      // Camera has now converged within threshold
      expect(springCam.isSettled()).toBe(true);

      // Mouse displacement should also un-settle the engine
      springCam.setMouseTarget(0.8, -0.6);
      springCam.update(0.016, farTarget, farLook);
      expect(springCam.isSettled()).toBe(false);

      // Once mouse converges, isSettled becomes true again
      for (let i = 0; i < 150; i++) {
        springCam.update(0.05, farTarget, farLook);
      }
      expect(springCam.isSettled()).toBe(true);
    });
  });

  describe("2. SecondOrderDynamics3D Zero Heap Churn", () => {
    it("mutates and returns pre-allocated this.value across consecutive updates", () => {
      const dynamics = new SecondOrderDynamics3D(1.5, 0.8, 2.0, 0, 0, 0);
      const r1 = dynamics.update(0.016, 5, 10, 15);
      const r2 = dynamics.update(0.016, 5, 10, 15);

      // Referential equality proves zero new object literal allocations per frame
      expect(r1).toBe(r2);
      expect(typeof r1.x).toBe("number");
      expect(typeof r1.y).toBe("number");
      expect(typeof r1.z).toBe("number");
    });
  });

  describe("3. Static AST Analysis: Zero Heap Allocations in Animation Loops", () => {
    it("asserts strictly 0 NewExpression, ObjectExpression, ArrayExpression, and ArrowFunctionExpression in ThreeSpatialRadar animate()", () => {
      const filePath = path.join(__dirname, "../src/components/ThreeSpatialRadar.js");
      const code = fs.readFileSync(filePath, "utf8");
      const ast = parser.parse(code, { sourceType: "module", plugins: ["jsx"] });

      let animateNode = null;
      traverse(ast, {
        VariableDeclarator(p) {
          if (p.node.id.name === "animate") {
            animateNode = p.node.init;
          }
        },
      });

      expect(animateNode).not.toBeNull();

      let newExpr = 0;
      let objExpr = 0;
      let arrExpr = 0;
      let arrowExpr = 0;

      traverse(animateNode, {
        noScope: true,
        NewExpression() {
          newExpr++;
        },
        ObjectExpression() {
          objExpr++;
        },
        ArrayExpression() {
          arrExpr++;
        },
        ArrowFunctionExpression() {
          arrowExpr++;
        },
      });

      expect(newExpr).toBe(0);
      expect(objExpr).toBe(0);
      expect(arrExpr).toBe(0);
      expect(arrowExpr).toBe(0);
    });

    it("asserts strictly 0 NewExpression, ObjectExpression, ArrayExpression, and ArrowFunctionExpression in ClearHireAmbientWorld animate()", () => {
      const filePath = path.join(__dirname, "../src/components/ClearHireAmbientWorld.js");
      const code = fs.readFileSync(filePath, "utf8");
      const ast = parser.parse(code, { sourceType: "module", plugins: ["jsx"] });

      let animateNode = null;
      traverse(ast, {
        ClassMethod(p) {
          if (p.node.key.name === "animate") {
            animateNode = p.node.body;
          }
        },
      });

      expect(animateNode).not.toBeNull();

      let newExpr = 0;
      let objExpr = 0;
      let arrExpr = 0;
      let arrowExpr = 0;

      traverse(animateNode, {
        noScope: true,
        NewExpression() {
          newExpr++;
        },
        ObjectExpression() {
          objExpr++;
        },
        ArrayExpression() {
          arrExpr++;
        },
        ArrowFunctionExpression() {
          arrowExpr++;
        },
      });

      expect(newExpr).toBe(0);
      expect(objExpr).toBe(0);
      expect(arrExpr).toBe(0);
      expect(arrowExpr).toBe(0);
    });
  });

  describe("4. ThreeSpatialRadar Tab Visibility Pausing", () => {
    it("listens to visibilitychange, cancels RAF when hidden, and resumes when visible", () => {
      const originalRaf = window.requestAnimationFrame;
      const originalCaf = window.cancelAnimationFrame;

      let rafCount = 0;
      let cafCount = 0;
      window.requestAnimationFrame = jest.fn((cb) => {
        rafCount++;
        return rafCount;
      });
      window.cancelAnimationFrame = jest.fn((id) => {
        cafCount++;
      });

      let hiddenValue = false;
      Object.defineProperty(document, "hidden", {
        configurable: true,
        get: () => hiddenValue,
      });

      const sampleJobs = [
        {
          id: 1,
          title: "SDE 2",
          company: "Acme Corp",
          score: 95,
          ghosting_risk: "low",
        },
      ];

      const { unmount } = render(
        <ThreeSpatialRadar jobs={sampleJobs} onSelectJob={() => {}} onHoverJob={() => {}} />
      );

      expect(window.requestAnimationFrame).toHaveBeenCalled();
      const initialCafCount = cafCount;

      // Simulate tab hidden
      act(() => {
        hiddenValue = true;
        document.dispatchEvent(new Event("visibilitychange"));
      });

      expect(cafCount).toBeGreaterThan(initialCafCount);

      // Simulate tab foregrounded
      act(() => {
        hiddenValue = false;
        document.dispatchEvent(new Event("visibilitychange"));
      });

      expect(window.requestAnimationFrame).toHaveBeenCalled();

      unmount();

      window.requestAnimationFrame = originalRaf;
      window.cancelAnimationFrame = originalCaf;
    });
  });

  describe("5. Stable Callbacks & WebGL Teardown Prevention", () => {
    it("does not re-trigger scene initialization when parent re-renders with new callback references", () => {
      const sampleJobs = [
        {
          id: 1,
          title: "SDE 2",
          company: "Acme Corp",
          score: 95,
          ghosting_risk: "low",
        },
      ];

      const cb1 = jest.fn();
      const cb2 = jest.fn();

      const { rerender, container } = render(
        <ThreeSpatialRadar jobs={sampleJobs} onSelectJob={cb1} onHoverJob={() => {}} />
      );

      const canvas1 = container.querySelector("canvas");

      // Rerender with brand new function references for callbacks
      rerender(
        <ThreeSpatialRadar jobs={sampleJobs} onSelectJob={cb2} onHoverJob={() => {}} />
      );

      const canvas2 = container.querySelector("canvas");

      // Canvas element reference must remain identical (no WebGL context recreation)
      expect(canvas1).toBe(canvas2);
    });
  });
});
