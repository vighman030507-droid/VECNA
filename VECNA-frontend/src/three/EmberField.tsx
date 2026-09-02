import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { useAudioLevel } from "./useAudioLevel";

export function EmberField({ count = 350 }: { count?: number }) {
  const pointsRef = useRef<THREE.Points>(null);
  const { level, status } = useAudioLevel();

  const [positions, velocities, colors] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const idx = i * 3;
      pos[idx] = (Math.random() - 0.5) * 14;
      pos[idx + 1] = (Math.random() - 0.5) * 10;
      pos[idx + 2] = -1 - Math.random() * 6;

      vel[idx] = (Math.random() - 0.5) * 0.006;
      vel[idx + 1] = 0.005 + Math.random() * 0.012; // Floating upward
      vel[idx + 2] = (Math.random() - 0.5) * 0.005;

      const isEmber = Math.random() > 0.65;
      if (isEmber) {
        // Blood red ember (#d61f26)
        col[idx] = 0.84;
        col[idx + 1] = 0.12;
        col[idx + 2] = 0.15;
      } else {
        // Soft ivory spore (rgba(233,227,208,0.18))
        col[idx] = 0.91;
        col[idx + 1] = 0.89;
        col[idx + 2] = 0.81;
      }
    }
    return [pos, vel, col];
  }, [count]);

  useFrame((state, delta) => {
    if (!pointsRef.current) return;
    const posAttr = pointsRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const array = posAttr.array as Float32Array;

    const speedBoost = 1.0 + level * 2.2 + (status === "speaking" ? 0.8 : 0);

    for (let i = 0; i < count; i++) {
      const idx = i * 3;
      array[idx] += (velocities[idx] + Math.sin(state.clock.elapsedTime + i) * 0.002) * speedBoost;
      array[idx + 1] += velocities[idx + 1] * speedBoost;
      array[idx + 2] += velocities[idx + 2] * speedBoost;

      // Wrap boundaries
      if (array[idx + 1] > 5) array[idx + 1] = -5;
      if (array[idx] > 7) array[idx] = -7;
      if (array[idx] < -7) array[idx] = 7;
    }

    posAttr.needsUpdate = true;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.12}
        vertexColors
        transparent
        opacity={0.65}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
}
