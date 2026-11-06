import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface Heart3DCanvasProps {
  bpm?: number;
  interactive?: boolean;
}

export const Heart3DCanvas: React.FC<Heart3DCanvasProps> = ({
  bpm = 72,
  interactive = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const isVisibleRef = useRef(true);

  const autoRotate = true;
  const thermalGlow = true;

  const autoRotateRef = useRef(autoRotate);
  autoRotateRef.current = autoRotate;
  const thermalGlowRef = useRef(thermalGlow);
  thermalGlowRef.current = thermalGlow;
  const bpmRef = useRef(bpm);
  bpmRef.current = bpm;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 520;
    const height = container.clientHeight || 520;

    // 1. Scene, Camera, High-Precision WebGL Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
    camera.position.set(0, 0, 7.8);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    container.appendChild(renderer.domElement);

    // 2. High-Fidelity Biological Lighting
    const ambientLight = new THREE.AmbientLight(0x280710, 2.2);
    scene.add(ambientLight);

    // Main Surgical Key Light (Highlights glossy vascular surface)
    const keyLight = new THREE.DirectionalLight(0xfff6ee, 3.8);
    keyLight.position.set(4, 5, 6);
    scene.add(keyLight);

    // Deep Myocardial Crimson Rim Light
    const crimsonRim = new THREE.DirectionalLight(0xff2d55, 3.2);
    crimsonRim.position.set(-5, -2, 4);
    scene.add(crimsonRim);

    // Telemetry Cyan Backlight
    const cyanRim = new THREE.DirectionalLight(0x007aff, 2.4);
    cyanRim.position.set(0, 4, -5);
    scene.add(cyanRim);

    // Thermal "Heating" Point Lights (surges with cardiac systole)
    const thermalCoreLight = new THREE.PointLight(0xff3b30, 5.0, 14);
    thermalCoreLight.position.set(0, -0.2, 0.6);
    scene.add(thermalCoreLight);

    const apexHeatLight = new THREE.PointLight(0xff9500, 3.2, 8);
    apexHeatLight.position.set(-0.2, -1.8, 0.8);
    scene.add(apexHeatLight);

    // 3. Texture Loading (User's Exact Anatomical Heart Model Image)
    const textureLoader = new THREE.TextureLoader();

    const realHeartTexture = textureLoader.load("/real_heart_model.png");
    realHeartTexture.generateMipmaps = true;
    realHeartTexture.minFilter = THREE.LinearMipmapLinearFilter;
    realHeartTexture.magFilter = THREE.LinearFilter;

    const normalTexture = textureLoader.load("/real_heart_normal.png");
    normalTexture.generateMipmaps = true;

    const depthTexture = textureLoader.load("/real_heart_depth.png");
    depthTexture.generateMipmaps = true;

    const emissiveTexture = textureLoader.load("/real_heart_emissive.png");
    emissiveTexture.generateMipmaps = true;

    // 4. Volumetric 3D Anatomical Heart Geometry
    const heartRoot = new THREE.Group();
    scene.add(heartRoot);

    // 444x691 aspect ratio (W/H = 0.6425 -> 2.95 x 4.60)
    const geoW = 2.98;
    const geoH = 4.64;
    const segs = 128; // High-density tessellation for smooth 3D displacement

    // A. Front Anatomical Volumetric Surface
    const frontGeo = new THREE.PlaneGeometry(geoW, geoH, segs, segs);
    const fPos = frontGeo.attributes.position;
    const fV = new THREE.Vector3();

    // Sculpt macroscopic anatomical 3D curvature into vertices
    for (let i = 0; i < fPos.count; i++) {
      fV.fromBufferAttribute(fPos, i);
      const nx = fV.x / (geoW * 0.5);
      const ny = fV.y / (geoH * 0.5);
      const distSq = nx * nx + ny * ny;

      if (distSq < 1.0) {
        // Dome elevation forward in +Z
        const domeZ = Math.cos(Math.sqrt(distSq) * Math.PI * 0.5) * 0.48;
        fV.z = domeZ;
      }
      fPos.setXYZ(i, fV.x, fV.y, fV.z);
    }
    frontGeo.computeVertexNormals();

    const frontMat = new THREE.MeshPhysicalMaterial({
      map: realHeartTexture,
      normalMap: normalTexture,
      normalScale: new THREE.Vector2(0.85, 0.85),
      displacementMap: depthTexture,
      displacementScale: 0.32,
      displacementBias: 0.0,
      emissiveMap: emissiveTexture,
      emissive: 0xff3b30,
      emissiveIntensity: 0.45,
      transparent: true,
      roughness: 0.22,
      metalness: 0.06,
      clearcoat: 0.95, // Glistening biological moisture
      clearcoatRoughness: 0.1,
      side: THREE.FrontSide,
    });

    const frontMesh = new THREE.Mesh(frontGeo, frontMat);
    heartRoot.add(frontMesh);

    // B. Back Anatomical Volumetric Surface (Mirrored for seamless 360° rotation)
    const backGeo = new THREE.PlaneGeometry(geoW, geoH, segs, segs);
    const bPos = backGeo.attributes.position;
    for (let i = 0; i < bPos.count; i++) {
      fV.fromBufferAttribute(bPos, i);
      const nx = fV.x / (geoW * 0.5);
      const ny = fV.y / (geoH * 0.5);
      const distSq = nx * nx + ny * ny;
      if (distSq < 1.0) {
        fV.z = -Math.cos(Math.sqrt(distSq) * Math.PI * 0.5) * 0.45;
      }
      bPos.setXYZ(i, fV.x, fV.y, fV.z);
    }
    backGeo.computeVertexNormals();

    const backMat = new THREE.MeshPhysicalMaterial({
      map: realHeartTexture,
      normalMap: normalTexture,
      normalScale: new THREE.Vector2(-0.85, 0.85),
      displacementMap: depthTexture,
      displacementScale: -0.28,
      displacementBias: 0.0,
      emissiveMap: emissiveTexture,
      emissive: 0xaa1828,
      emissiveIntensity: 0.35,
      transparent: true,
      roughness: 0.28,
      metalness: 0.06,
      clearcoat: 0.9,
      clearcoatRoughness: 0.12,
      side: THREE.BackSide,
    });
    const backMesh = new THREE.Mesh(backGeo, backMat);
    heartRoot.add(backMesh);

    // C. Internal Thermal Radiant Halo
    const haloCanvas = document.createElement("canvas");
    haloCanvas.width = 256;
    haloCanvas.height = 256;
    const hCtx = haloCanvas.getContext("2d")!;
    const hGrad = hCtx.createRadialGradient(128, 128, 10, 128, 128, 128);
    hGrad.addColorStop(0, "rgba(255, 69, 0, 0.95)");   // Radiant orange heat
    hGrad.addColorStop(0.35, "rgba(255, 45, 85, 0.75)"); // Thermal crimson
    hGrad.addColorStop(0.7, "rgba(139, 0, 0, 0.3)");
    hGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
    hCtx.fillStyle = hGrad;
    hCtx.fillRect(0, 0, 256, 256);

    const haloTexture = new THREE.CanvasTexture(haloCanvas);
    const haloMat = new THREE.MeshBasicMaterial({
      map: haloTexture,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const haloMesh = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 5.2), haloMat);
    haloMesh.position.set(0, -0.1, -0.05);
    heartRoot.add(haloMesh);

    // 5. Orbiting Bio-Electrical Conduction Rings
    const ringGroup = new THREE.Group();
    scene.add(ringGroup);

    const ringMat1 = new THREE.MeshBasicMaterial({
      color: 0x5856d6, // Royal Purple
      transparent: true,
      opacity: 0.45,
      wireframe: true,
    });
    const ring1 = new THREE.Mesh(new THREE.TorusGeometry(2.8, 0.02, 8, 80), ringMat1);
    ring1.rotation.x = Math.PI / 3;
    ring1.rotation.y = Math.PI / 6;
    ringGroup.add(ring1);

    const ringMat2 = new THREE.MeshBasicMaterial({
      color: 0x007aff, // Azure Blue
      transparent: true,
      opacity: 0.4,
      wireframe: true,
    });
    const ring2 = new THREE.Mesh(new THREE.TorusGeometry(3.1, 0.016, 8, 80), ringMat2);
    ring2.rotation.x = -Math.PI / 4;
    ring2.rotation.z = Math.PI / 5;
    ringGroup.add(ring2);

    // 6. Bio-Electrical Ionic Particles
    const particleCount = 350;
    const particleGeo = new THREE.BufferGeometry();
    const particlePos = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      const radius = 2.2 + Math.random() * 2.2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      particlePos[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      particlePos[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      particlePos[i * 3 + 2] = radius * Math.cos(phi);
    }
    particleGeo.setAttribute("position", new THREE.BufferAttribute(particlePos, 3));

    const pCanvas = document.createElement("canvas");
    pCanvas.width = 32;
    pCanvas.height = 32;
    const pCtx = pCanvas.getContext("2d")!;
    const pGrad = pCtx.createRadialGradient(16, 16, 0, 16, 16, 16);
    pGrad.addColorStop(0, "rgba(255, 255, 255, 1)");
    pGrad.addColorStop(0.3, "rgba(255, 60, 90, 0.85)");
    pGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
    pCtx.fillStyle = pGrad;
    pCtx.fillRect(0, 0, 32, 32);
    const pTex = new THREE.CanvasTexture(pCanvas);

    const particleMat = new THREE.PointsMaterial({
      size: 0.16,
      map: pTex,
      transparent: true,
      opacity: 0.82,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 7. Interactive Drag & Mouse Tracking
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let manualRotY = 0;
    let manualRotX = 0;
    let mouseNormX = 0;
    let mouseNormY = 0;

    const handlePointerDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const handlePointerMove = (e: MouseEvent) => {
      if (!container) return;
      const rect = container.getBoundingClientRect();
      mouseNormX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseNormY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);

      if (isDragging) {
        const deltaX = e.clientX - prevMouseX;
        const deltaY = e.clientY - prevMouseY;
        manualRotY += deltaX * 0.012;
        manualRotX += deltaY * 0.012;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      }
    };

    const handlePointerUp = () => {
      isDragging = false;
    };

    container.addEventListener("mousedown", handlePointerDown);
    window.addEventListener("mousemove", handlePointerMove);
    window.addEventListener("mouseup", handlePointerUp);

    // Visibility Observer
    const observer = new IntersectionObserver(([entry]) => {
      isVisibleRef.current = entry.isIntersecting;
    }, { threshold: 0.1 });
    observer.observe(container);

    // 8. Physiological Beating, Heating & 3D Rotating Animation Loop
    const clock = new THREE.Clock();
    let animId: number;

    const render = () => {
      animId = requestAnimationFrame(render);
      if (!isVisibleRef.current) return;

      const elapsed = clock.getElapsedTime();

      // Cardiac Cycle Calculation (Lub-Dub rhythm at current BPM)
      const currentRate = bpmRef.current;
      const beatFreq = currentRate / 60.0;
      const phase = (elapsed * beatFreq) % 1.0;

      let systole = 0;
      let diastole = 0;

      // First beat (Ventricular Systole) - Strong contraction & apex twist
      if (phase >= 0.08 && phase < 0.24) {
        const p = (phase - 0.08) / 0.16;
        systole = Math.sin(p * Math.PI);
      }
      // Second beat (Diastolic reload)
      else if (phase >= 0.28 && phase < 0.42) {
        const p = (phase - 0.28) / 0.14;
        diastole = Math.sin(p * Math.PI) * 0.55;
      }

      const netPulse = systole + diastole;

      // Realistic cardiac deformation (expansion and contraction)
      const scaleX = 1.0 + netPulse * 0.12;
      const scaleY = 1.0 - netPulse * 0.07;
      const scaleZ = 1.0 + netPulse * 0.1;
      heartRoot.scale.set(scaleX, scaleY, scaleZ);

      // Systolic apex torsion twist
      heartRoot.rotation.z = systole * 0.06;

      // Thermal "Heating" Effect
      const isHeating = thermalGlowRef.current;
      const heatIntensity = isHeating ? (3.5 + netPulse * 10.0) : 2.0;
      thermalCoreLight.intensity = heatIntensity;
      apexHeatLight.intensity = isHeating ? (2.2 + netPulse * 5.5) : 1.2;

      frontMat.emissiveIntensity = isHeating ? (0.45 + netPulse * 1.3) : 0.2;
      backMat.emissiveIntensity = isHeating ? (0.35 + netPulse * 1.0) : 0.15;
      haloMat.opacity = isHeating ? (0.55 + netPulse * 0.45) : 0.2;
      haloMesh.scale.set(1.0 + netPulse * 0.18, 1.0 + netPulse * 0.18, 1.0);

      // 3D Continuous Rotation & Manual Drag / Parallax
      if (autoRotateRef.current) {
        manualRotY += 0.008;
      }

      const targetRotY = manualRotY + (interactive ? mouseNormX * 0.45 : 0);
      const targetRotX = manualRotX + (interactive ? Math.sin(elapsed * 0.2) * 0.06 + mouseNormY * 0.3 : 0);

      heartRoot.rotation.y += (targetRotY - heartRoot.rotation.y) * 0.08;
      heartRoot.rotation.x += (targetRotX - heartRoot.rotation.x) * 0.08;

      // Orbiting conduction rings
      ring1.rotation.z += 0.01;
      ring2.rotation.z -= 0.008;
      ringGroup.rotation.y += 0.005;

      // Particle aura drift
      particles.rotation.y = elapsed * 0.06;
      particles.rotation.x = Math.sin(elapsed * 0.15) * 0.04;

      renderer.render(scene, camera);
    };

    render();

    // Resize handling
    const handleResize = () => {
      if (!container) return;
      const newW = container.clientWidth;
      const newH = container.clientHeight;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    };
    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener("mousedown", handlePointerDown);
      window.removeEventListener("mousemove", handlePointerMove);
      window.removeEventListener("mouseup", handlePointerUp);
      window.removeEventListener("resize", handleResize);
      observer.disconnect();

      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
      frontGeo.dispose();
      backGeo.dispose();
      frontMat.dispose();
      backMat.dispose();
      haloMat.dispose();
      ringMat1.dispose();
      ringMat2.dispose();
      particleGeo.dispose();
      particleMat.dispose();

      realHeartTexture.dispose();
      normalTexture.dispose();
      depthTexture.dispose();
      emissiveTexture.dispose();
      haloTexture.dispose();
      pTex.dispose();
      renderer.dispose();
    };
  }, [interactive]);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        minHeight: "480px",
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* 3D WebGL Canvas Container */}
      <div
        ref={containerRef}
        style={{
          width: "100%",
          height: "100%",
          minHeight: "440px",
          cursor: "grab",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
        title="Click and drag to rotate the 3D heart model"
      />
    </div>
  );
};

export default Heart3DCanvas;
