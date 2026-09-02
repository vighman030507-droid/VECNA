import { Suspense, useRef, useEffect, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { EffectComposer, Bloom, ChromaticAberration, Vignette } from "@react-three/postprocessing";
import * as THREE from "three";
import { EmberField } from "./EmberField";
import { AudioLevelProvider, Status } from "./useAudioLevel";

type VecnaSceneProps = {
  status: Status;
  level: number;
  fearLevel?: 1 | 2 | 3;
  curseActive?: boolean;
};

function SceneContent({
  fearLevel = 1,
  curseActive = false,
}: {
  fearLevel?: 1 | 2 | 3;
  curseActive?: boolean;
}) {
  const { camera } = useThree();
  const redLightRef = useRef<THREE.PointLight>(null);
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      mouseRef.current.targetX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseRef.current.targetY = -(e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener("mousemove", onMouseMove, { passive: true });
    return () => window.removeEventListener("mousemove", onMouseMove);
  }, []);

  useFrame((state) => {
    const time = state.clock.elapsedTime;

    // Smooth mouse parallax lerp
    mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.05;
    mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.05;

    camera.position.x = mouseRef.current.x * 0.35;
    camera.position.y = mouseRef.current.y * 0.22;
    camera.lookAt(0, 0, -2);

    // Flickering dying red bulb pulsating stronger with fearLevel
    if (redLightRef.current) {
      const flickerSpeed = 1.8 + fearLevel * 0.8;
      const flicker = Math.sin(time * flickerSpeed) * (0.4 * fearLevel) + (Math.random() > 0.93 ? 1.0 : 0);
      redLightRef.current.intensity = (2.4 + flicker) * (1 + (fearLevel - 1) * 0.35);
    }
  });

  const chromaticOffset = useMemo(() => {
    const val = 0.0012 + (fearLevel - 1) * 0.0018 + (curseActive ? 0.002 : 0);
    return new THREE.Vector2(val, val);
  }, [fearLevel, curseActive]);

  const emberCount = useMemo(() => {
    return Math.min(600, 250 + fearLevel * 100);
  }, [fearLevel]);

  return (
    <>
      {/* Exponential Fog in Void Black (#050506) */}
      <fogExp2 attach="fog" args={["#050506", 0.14 + (curseActive ? 0.06 : 0)]} />

      {/* Dim Bluish Ambient Light */}
      <ambientLight color="#0b0c0d" intensity={0.4} />

      {/* Strong Red Spotlight Behind Model (#d61f26) */}
      <pointLight
        ref={redLightRef}
        color="#d61f26"
        intensity={2.6 * fearLevel}
        distance={16 + fearLevel * 2}
        position={[0, 4.2, -3.2]}
      />

      {/* Brass Rim Light for Silhouette Edge (#c99a4d) */}
      <pointLight
        color="#c99a4d"
        intensity={1.2}
        distance={12}
        position={[4.0, 1.2, -1.5]}
      />
      <pointLight
        color="#c99a4d"
        intensity={1.2}
        distance={12}
        position={[-4.0, 1.2, -1.5]}
      />

      {/* 3D Ember/Spore Particle System */}
      <EmberField count={emberCount} />

      {/* Postprocessing Stack */}
      <EffectComposer enableNormalPass={false} multisampling={0}>
        <Bloom
          luminanceThreshold={0.4}
          luminanceSmoothing={0.3}
          intensity={1.4 + fearLevel * 0.4}
          mipmapBlur
        />
        <ChromaticAberration
          offset={chromaticOffset}
          radialModulation={false}
          modulationOffset={0}
        />
        <Vignette eskil={false} offset={0.25} darkness={curseActive ? 0.95 : 0.8} />
      </EffectComposer>
    </>
  );
}

export function VecnaScene({
  status,
  level,
  fearLevel = 1,
  curseActive = false,
}: VecnaSceneProps) {
  return (
    <AudioLevelProvider level={level} status={status}>
      <div className={`three-scene-wrapper ${curseActive ? "curse-active-scene" : ""}`} aria-hidden="true">
        <Canvas
          dpr={[1, 1.5]}
          camera={{ position: [0, 0, 4.2], fov: 45, near: 0.1, far: 50 }}
          gl={{
            powerPreference: "high-performance",
            antialias: true,
            alpha: true,
            toneMapping: THREE.ACESFilmicToneMapping,
            toneMappingExposure: 1.1,
          }}
        >
          <Suspense fallback={null}>
            <SceneContent fearLevel={fearLevel} curseActive={curseActive} />
          </Suspense>
        </Canvas>
      </div>
    </AudioLevelProvider>
  );
}
