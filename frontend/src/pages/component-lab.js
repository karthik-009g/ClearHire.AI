import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";
import {
  createOfficeRoom,
  createExecutiveDesk,
  createWorkstationComputer,
  createOfficePrinterScanner,
  createAutonomousRobot,
  createCandidateResume,
} from "../components/office";

const COMPONENT_SPECS = [
  {
    id: "office-room",
    name: "Office Room Envelope",
    category: "Environment & Architectural Rig",
    skills: ["anatomy", "explainer-default"],
    description:
      "A complete architectural office envelope featuring stone floor tiles, corner walls, skirting baseboards, overhead steel gantry lighting rigs, softbox diffusers, and 280 floating golden dust motes.",
    specs: [
      { label: "Floor Surface", value: "Italian Limestone Tile (Roughness 0.88)" },
      { label: "Wall Envelope", value: "Matte Architectural Plaster (#f5f2eb)" },
      { label: "Lighting Rig", value: "Overhead Steel Gantries + Softbox Diffusers" },
      { label: "Atmosphere", value: "280 Ambient Golden Dust Motes with Drift Physics" },
    ],
    cameraPos: [0, 4.5, 12],
    lookAt: [0, 1.5, 0],
  },
  {
    id: "executive-desk",
    name: "Executive Decision Desk",
    category: "Precision Architectural Furniture",
    skills: ["anatomy", "explainer-engaging", "sound-effects"],
    description:
      "Chamfered Italian travertine stone slab desktop supported by heavy dark bronze trestle legs with foot stretchers, open emerald green leather interview portfolio, knurled brass grommet, and an active 48-Hour SLA Chronometer with ticking emerald second hand.",
    specs: [
      { label: "Desktop Slab", value: "Travertine Stone (2.4m × 1.4m × 0.1m, Chamfered)" },
      { label: "Trestle Frame", value: "Dark Cast Bronze with Foot Stretcher Pins" },
      { label: "Covenant Chrono", value: "3D Turned Brass Dial with Ticking Emerald Hand" },
      { label: "Candidate Portfolio", value: "Open Emerald Green Saddle Leather (#064e3b)" },
    ],
    cameraPos: [0, 1.8, 3.8],
    lookAt: [0, 0, 0],
  },
  {
    id: "workstation-computer",
    name: "Workstation Terminal",
    category: "Precision Instrument (Anatomy Craft)",
    skills: ["anatomy", "explainer-default", "object-separation"],
    description:
      "Directly modeled on the anatomy desk-computer craft: precision chassis with ventilation louvers, recessed CRT bezel with dark gasket, real-time phosphor scanline display with live AST parsing telemetry, extruded mechanical keycaps, coiled cable harness, and pulsing power LED.",
    specs: [
      { label: "Display Case", value: "Dark Anodized Alloy with Ventilation Louvers" },
      { label: "Screen Tech", value: "Real-Time CRT Phosphor Scanlines + Terminal Readout" },
      { label: "Keyboard Bed", value: "Mechanical Bevelled Keycaps (70 individual solids)" },
      { label: "Cable Harness", value: "Coiled Black Rubber Harness to Chassis Port" },
    ],
    cameraPos: [0, 0.8, 2.2],
    lookAt: [0, 0.1, 0],
  },
  {
    id: "printer-scanner",
    name: "Office Printer / ATS Scanner",
    category: "Mechanisms & Optical Intake",
    skills: ["anatomy", "explainer-high-energy", "motion-broll"],
    description:
      "Heavy dark-anodized cast aluminum chassis on 4 turned brass leveling feet with knurled lock nuts. Stainless intake platen bed with engraved ruler ticks, rotating pinch feed rollers, sweeping cyan optical laser curtain, dynamic CRT face screen with state-driven expressions, and dual antenna telemetry beacons.",
    specs: [
      { label: "Leveling Feet", value: "4 Turned Solid Brass Feet with Knurled Lock Rings" },
      { label: "Intake Platen", value: "Stainless Steel with Engraved Calibration Ticks" },
      { label: "Laser Array", value: "Sweeping Optical Cyan Curtain with Emissive Glow" },
      { label: "CRT Monitor Face", value: "Dynamic States: Idle, Scanning, Reject, Covenant" },
    ],
    cameraPos: [0, 0.9, 2.6],
    lookAt: [0, 0.2, 0],
  },
  {
    id: "autonomous-robot",
    name: "Autonomous Drone Robot",
    category: "Robotics & Visual Inspection",
    skills: ["anatomy", "motion-broll", "arena"],
    description:
      "Articulated robotic inspection companion integrating the user's authentic robot.glb, normalized by bounding box to realistic scale (~0.85m tall). Hover gimbal with smooth aerodynamic sine-wave hover physics, pitch/roll banking, and a downward inspection spotlight illuminating the workspace.",
    specs: [
      { label: "3D Asset", value: "robot.glb (Normalized & Centered by Bounding Box)" },
      { label: "Hover Physics", value: "Aerodynamic Sine-Wave Vertical & Roll Oscillation" },
      { label: "Inspection Light", value: "Targeted Cyan SpotLight with Soft Conical Falloff" },
      { label: "Telemetry", value: "Autonomous Scan Telemetry Antenna & Sensor Dome" },
    ],
    cameraPos: [0, 0.6, 2.8],
    lookAt: [0, 0.1, 0],
  },
  {
    id: "candidate-resume",
    name: "Candidate Cotton Resume",
    category: "Physical Document & Material",
    skills: ["anatomy", "motion-broll", "explainer-engaging"],
    description:
      "Multi-material double-sided 100% cotton paper document (0.72m × 1.02m) with ultra-high-definition 1024×1440 procedural texture: milled borders, Sarah Chen verified credentials, quantified impact metrics, ATS compliance chips, holographic security seal, and machine-readable barcode with aerodynamic flutter physics.",
    specs: [
      { label: "Paper Stock", value: "100% Rag Cotton (#faf8f4) with Fiber Texture" },
      { label: "Resolution", value: "1024 × 1440 High-DPI Canvas Rendering" },
      { label: "Hiring Credentials", value: "Sarah Chen (Staff AI & Systems Engineer, MIT)" },
      { label: "Verification", value: "Cryptographic AST Seal + Quantified Metrics" },
    ],
    cameraPos: [0, 0.35, 1.7],
    lookAt: [0, 0, 0],
  },
];

export default function ComponentLabPage() {
  const mountRef = useRef(null);
  const [selectedCompId, setSelectedCompId] = useState("office-room");
  const [currentMood, setCurrentMood] = useState("scanning");

  const selectedSpec = COMPONENT_SPECS.find((c) => c.id === selectedCompId) || COMPONENT_SPECS[0];

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return undefined;

    // 1. Scene, Camera, WebGL Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f2eb);

    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(...selectedSpec.cameraPos);
    camera.lookAt(new THREE.Vector3(...selectedSpec.lookAt));

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setClearColor(0xf5f2eb, 1);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.appendChild(renderer.domElement);

    // 2. Studio Lighting
    const hemiLight = new THREE.HemisphereLight(0xfffaef, 0xd4cebd, 2.2);
    scene.add(hemiLight);

    const sunLight = new THREE.DirectionalLight(0xfff7e8, 3.0);
    sunLight.position.set(6, 12, 8);
    sunLight.castShadow = true;
    scene.add(sunLight);

    const fillLight = new THREE.DirectionalLight(0xd6e5ff, 1.2);
    fillLight.position.set(-8, 6, -5);
    scene.add(fillLight);

    // 3. Instantiate Selected Component
    const gltfLoader = new GLTFLoader();
    let compInstance = null;

    if (selectedSpec.id === "office-room") {
      compInstance = createOfficeRoom();
    } else if (selectedSpec.id === "executive-desk") {
      compInstance = createExecutiveDesk({ gltfLoader, position: [0, 0, 0] });
    } else if (selectedSpec.id === "workstation-computer") {
      compInstance = createWorkstationComputer({ gltfLoader, position: [0, 0, 0] });
    } else if (selectedSpec.id === "printer-scanner") {
      compInstance = createOfficePrinterScanner({ position: [0, 0, 0] });
      compInstance.setMood(currentMood);
    } else if (selectedSpec.id === "autonomous-robot") {
      compInstance = createAutonomousRobot({ gltfLoader, position: [0, 0, 0] });
    } else if (selectedSpec.id === "candidate-resume") {
      compInstance = createCandidateResume({ initialPosition: [0, 0, 0] });
    }

    if (compInstance) {
      if (compInstance.group) scene.add(compInstance.group);
      if (compInstance.mesh) scene.add(compInstance.mesh);
    }

    // 4. Mouse Orbit Dragging
    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };
    let spherical = {
      radius: camera.position.distanceTo(new THREE.Vector3(...selectedSpec.lookAt)),
      theta: Math.atan2(camera.position.x - selectedSpec.lookAt[0], camera.position.z - selectedSpec.lookAt[2]),
      phi: Math.acos((camera.position.y - selectedSpec.lookAt[1]) / camera.position.distanceTo(new THREE.Vector3(...selectedSpec.lookAt))),
    };

    const updateCameraFromSpherical = () => {
      camera.position.x = selectedSpec.lookAt[0] + spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
      camera.position.y = selectedSpec.lookAt[1] + spherical.radius * Math.cos(spherical.phi);
      camera.position.z = selectedSpec.lookAt[2] + spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);
      camera.lookAt(new THREE.Vector3(...selectedSpec.lookAt));
    };

    const onMouseDown = (e) => {
      isDragging = true;
      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e) => {
      if (!isDragging) return;
      const dx = (e.clientX - prevMouse.x) * 0.008;
      const dy = (e.clientY - prevMouse.y) * 0.008;
      prevMouse = { x: e.clientX, y: e.clientY };

      spherical.theta -= dx;
      spherical.phi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, spherical.phi - dy));
      updateCameraFromSpherical();
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e) => {
      spherical.radius = Math.max(1.0, Math.min(25.0, spherical.radius + e.deltaY * 0.004));
      updateCameraFromSpherical();
    };

    container.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    container.addEventListener("wheel", onWheel);

    const onResize = () => {
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    window.addEventListener("resize", onResize);

    // 5. Animation Loop
    let reqId = 0;
    let lastTime = performance.now();
    let startTime = performance.now();

    const animate = () => {
      reqId = requestAnimationFrame(animate);
      const now = performance.now();
      const dt = Math.min(0.1, (now - lastTime) / 1000);
      lastTime = now;
      const time = (now - startTime) / 1000;

      if (compInstance && compInstance.update) {
        compInstance.update(
          time,
          dt,
          selectedCompId === "printer-scanner" ? currentMood : null
        );
      }

      renderer.render(scene, camera);
    };
    reqId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(reqId);
      container.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      container.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", onResize);
      if (compInstance && compInstance.dispose) {
        compInstance.dispose();
      }
      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [selectedCompId, currentMood, selectedSpec]);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-[#f5f2eb] text-[#24231f] flex flex-col font-sans select-none">
      {/* Top Header */}
      <header className="h-16 px-6 border-b border-[#24231f]/10 bg-[#faf7f0]/90 backdrop-blur-md flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <Link href="/login" className="flex items-baseline gap-0.5 hover:opacity-80 transition-opacity">
            <span className="font-serif text-lg font-bold text-[#24231f]">clearhire</span>
            <span className="text-[#15803d] font-mono text-xs font-bold">.ai</span>
          </Link>
          <span className="text-[#706e68]/40">/</span>
          <span className="font-mono text-xs uppercase tracking-wider text-[#706e68] font-bold">
            INDEPENDENT 3D COMPONENT LABORATORY
          </span>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="px-4 py-1.5 rounded-full border border-[#24231f]/15 bg-white text-[#24231f] font-mono text-xs font-bold hover:bg-[#24231f] hover:text-white transition-all shadow-xs"
          >
            ← Return to Full Story Experience
          </Link>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Component Selector */}
        <aside className="w-80 border-r border-[#24231f]/10 bg-[#faf7f0]/60 backdrop-blur-xl p-5 flex flex-col gap-4 overflow-y-auto z-10">
          <div>
            <span className="font-mono text-[10px] uppercase font-bold text-[#706e68] tracking-widest">
              INDEPENDENT 3D ASSETS
            </span>
            <h2 className="font-serif text-xl font-bold tracking-tight text-[#24231f] mt-0.5">
              6 Modular Elements
            </h2>
            <p className="text-xs text-[#706e68] leading-relaxed mt-1">
              Crafted with the 8 Antigravity skills. Inspect, rotate, and audit each physical component independently.
            </p>
          </div>

          <div className="flex flex-col gap-2 pt-2">
            {COMPONENT_SPECS.map((comp) => (
              <button
                key={comp.id}
                type="button"
                onClick={() => setSelectedCompId(comp.id)}
                className={`w-full p-3.5 rounded-2xl text-left transition-all border ${
                  selectedCompId === comp.id
                    ? "bg-white border-[#15803d] shadow-md ring-1 ring-[#15803d]/30"
                    : "bg-[#faf7f0]/70 border-[#24231f]/10 hover:bg-white hover:border-[#24231f]/20"
                }`}
              >
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="font-mono text-[10px] uppercase font-semibold text-[#706e68]">
                    {comp.category}
                  </span>
                  {selectedCompId === comp.id && (
                    <span className="w-2 h-2 rounded-full bg-[#15803d] animate-pulse" />
                  )}
                </div>
                <div className="font-serif text-base font-bold text-[#24231f]">
                  {comp.name}
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {comp.skills.map((sk) => (
                    <span
                      key={sk}
                      className="px-2 py-0.5 rounded-full font-mono text-[9px] bg-[#15803d]/10 text-[#15803d] font-bold border border-[#15803d]/20"
                    >
                      {sk}
                    </span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </aside>

        {/* Center: 3D Viewport with Orbit Controls */}
        <main className="flex-1 relative overflow-hidden bg-[#f5f2eb]">
          <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

          {/* Viewport Control Pill */}
          <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-[#faf7f0]/90 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-[#24231f]/15 shadow-sm font-mono text-[11px] text-[#706e68]">
            <span className="w-2 h-2 rounded-full bg-[#34d399] animate-pulse" />
            <span>Interactive Orbit (Drag to rotate, Scroll to zoom)</span>
          </div>

          {/* Scanner Mood Switcher (Visible only when printer/scanner is selected) */}
          {selectedCompId === "printer-scanner" && (
            <div className="absolute top-4 right-4 z-10 flex items-center gap-1.5 bg-[#faf7f0]/95 backdrop-blur-md p-1.5 rounded-full border border-[#24231f]/15 shadow-md">
              <span className="font-mono text-[10px] uppercase font-bold text-[#706e68] px-2">State:</span>
              {["idle", "scanning", "rejected", "accepted"].map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setCurrentMood(m)}
                  className={`px-3 py-1 rounded-full font-mono text-xs font-bold uppercase transition-all ${
                    currentMood === m
                      ? m === "rejected"
                        ? "bg-red-600 text-white shadow-xs"
                        : m === "accepted"
                        ? "bg-[#15803d] text-white shadow-xs"
                        : m === "scanning"
                        ? "bg-[#0284c7] text-white shadow-xs"
                        : "bg-[#24231f] text-white shadow-xs"
                      : "text-[#706e68] hover:text-[#24231f]"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          )}
        </main>

        {/* Right Sidebar: Component Anatomy & Craft Specs */}
        <aside className="w-96 border-l border-[#24231f]/10 bg-[#faf7f0]/60 backdrop-blur-xl p-6 flex flex-col gap-4 overflow-y-auto z-10">
          <div>
            <span className="font-mono text-[10px] uppercase font-bold text-[#15803d] tracking-widest bg-[#15803d]/10 px-2.5 py-0.5 rounded-full border border-[#15803d]/25">
              SPECIFICATION SHEET
            </span>
            <h3 className="font-serif text-2xl font-bold tracking-tight text-[#24231f] mt-2">
              {selectedSpec.name}
            </h3>
            <p className="text-xs text-[#525048] leading-relaxed mt-2">
              {selectedSpec.description}
            </p>
          </div>

          <div className="border-t border-[#24231f]/10 pt-3">
            <span className="font-mono text-[10px] uppercase font-bold text-[#706e68] tracking-widest block mb-2.5">
              ANATOMICAL SPECIFICATIONS
            </span>
            <div className="space-y-2">
              {selectedSpec.specs.map((sp) => (
                <div
                  key={sp.label}
                  className="p-2.5 rounded-xl bg-white/80 border border-[#24231f]/8 font-mono text-xs flex flex-col gap-0.5"
                >
                  <span className="text-[10px] text-[#706e68] uppercase font-semibold">
                    {sp.label}
                  </span>
                  <span className="text-[#24231f] font-medium text-[11px]">
                    {sp.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-[#24231f]/10 pt-3">
            <span className="font-mono text-[10px] uppercase font-bold text-[#706e68] tracking-widest block mb-2">
              SKILL INTEGRATION BREAKDOWN
            </span>
            <div className="p-3 rounded-2xl bg-white/70 border border-[#24231f]/8 text-xs text-[#525048] space-y-1.5 leading-relaxed font-sans">
              <p>
                <strong>• Anatomy:</strong> Modeled with four-tone lighting, precise physical dimensions, chamfers, knurled textures, and depth-sorted solid parts.
              </p>
              <p>
                <strong>• Motion:</strong> Eased continuous physics with aerodynamic drag, rotating guide bearings, and spring-damped camera orbits.
              </p>
              <p>
                <strong>• Object-Separation:</strong> Self-contained lifecycle (`create`, `update`, `dispose`) ensuring full isolation.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
