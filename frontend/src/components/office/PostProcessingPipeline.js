import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";

/**
 * ============================================================================
 * OPTICAL LENS & FILM GRAIN SHADER (Awwwards / Lusion Standard)
 * - 35mm fine dither grain to eliminate 8-bit banding on warm studio floors
 * - Soft architectural radial vignette
 * - Micro chromatic dispersion toward viewport corners
 * ============================================================================
 */
const OpticalLensShader = {
  uniforms: {
    tDiffuse: { value: null },
    uTime: { value: 0 },
    uGrainIntensity: { value: 0.016 },
    uAberrationOffset: { value: 0.0008 },
  },
  vertexShader: `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    uniform sampler2D tDiffuse;
    uniform float uTime;
    uniform float uGrainIntensity;
    uniform float uAberrationOffset;
    varying vec2 vUv;

    void main() {
      vec2 distFromCenter = vUv - vec2(0.5);
      float dist = length(distFromCenter);

      // Subtle lens dispersion / chromatic aberration at corners
      vec2 redUv = vUv - distFromCenter * uAberrationOffset * dist;
      vec2 blueUv = vUv + distFromCenter * uAberrationOffset * dist;

      float r = texture2D(tDiffuse, redUv).r;
      float g = texture2D(tDiffuse, vUv).g;
      float b = texture2D(tDiffuse, blueUv).b;
      vec3 color = vec3(r, g, b);

      // High-frequency procedural film grain (breaks 8-bit banding)
      float noise = (fract(sin(dot(vUv, vec2(12.9898, 78.233) + uTime * 0.05)) * 43758.5453) - 0.5) * uGrainIntensity;
      color += noise;

      gl_FragColor = vec4(color, 1.0);
    }
  `,
};

export function createPostProcessingPipeline(arg1, scene, camera, opts = {}) {
  let renderer, finalScene, finalCamera, width, height;
  if (arg1 && arg1.renderer) {
    renderer = arg1.renderer;
    finalScene = arg1.scene;
    finalCamera = arg1.camera;
    width = arg1.width || 800;
    height = arg1.height || 600;
  } else {
    renderer = arg1;
    finalScene = scene;
    finalCamera = camera;
    width = opts.width || 800;
    height = opts.height || 600;
  }

  if (!renderer || typeof document === "undefined") return null;

  // 60 FPS Guardrail: Detect mobile / low-power GPUs to conserve memory bandwidth and fill rate
  const isMobile =
    typeof window !== "undefined" &&
    (/Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) ||
      window.innerWidth < 768 ||
      (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4));

  // Use HalfFloatType for true HDR tone mapping & bloom dynamics (MSAA 2x on desktop, 0 on mobile)
  const renderTarget = new THREE.WebGLRenderTarget(width, height, {
    type: THREE.HalfFloatType,
    samples: isMobile ? 0 : 2,
  });

  const composer = new EffectComposer(renderer, renderTarget);

  // Pass 1: Base scene render
  const renderPass = new RenderPass(finalScene, finalCamera);
  composer.addPass(renderPass);

  // Pass 2: Selective High-Threshold UnrealBloomPass at Half-Resolution
  // Luminance threshold 1.02 ensures only emissive elements (>1.02) bloom,
  // preventing floor and wall surfaces from washing out. Half-res blit saves 75% fill rate.
  const bloomWidth = Math.max(128, Math.floor(width * 0.5));
  const bloomHeight = Math.max(128, Math.floor(height * 0.5));
  const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(bloomWidth, bloomHeight),
    0.24, // Bloom strength
    0.3,  // Radius
    1.02  // Luminance threshold (only true emissive lights bloom)
  );
  bloomPass.enabled = !isMobile;
  composer.addPass(bloomPass);

  // Pass 3: Optical Lens & 35mm Film Grain ShaderPass
  const lensPass = new ShaderPass(OpticalLensShader);
  composer.addPass(lensPass);

  // Pass 4: Official Three.js OutputPass (Applies ACESFilmic tone mapping and sRGB encoding)
  const outputPass = new OutputPass();
  composer.addPass(outputPass);

  const setSize = (w, h) => {
    composer.setSize(w, h);
    bloomPass.resolution.set(
      Math.max(128, Math.floor(w * 0.5)),
      Math.max(128, Math.floor(h * 0.5))
    );
  };

  const setAberration = (val) => {
    if (lensPass?.uniforms?.uAberrationOffset) {
      lensPass.uniforms.uAberrationOffset.value = val;
    }
  };

  const render = (time) => {
    lensPass.uniforms.uTime.value = time;
    composer.render();
  };

  const dispose = () => {
    composer.dispose();
    renderTarget.dispose();
    bloomPass.dispose();
  };

  return {
    composer,
    bloomPass,
    lensPass,
    setSize,
    setAberration,
    render,
    dispose,
  };
}

export function PostProcessingPipeline(arg1, scene, camera, opts) {
  return createPostProcessingPipeline(arg1, scene, camera, opts);
}
