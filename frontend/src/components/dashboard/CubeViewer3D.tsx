import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

// Default solved state string (54 chars, WCA face order: U R F D L B)
const SOLVED_STATE = 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB';

// Sticker color map
const COLOR_MAP: Record<string, string> = {
  U: '#ffffff', // white
  R: '#ff2200', // red
  F: '#00aa44', // green
  D: '#ffdd00', // yellow
  L: '#ff8800', // orange
  B: '#0055ff', // blue
};

type FaceKey = 'U' | 'D' | 'L' | 'R' | 'F' | 'B';

const MOVE_CONFIG: Record<string, { axis: THREE.Vector3; condition: (pos: THREE.Vector3) => boolean; angle: number }> = {
  U: { axis: new THREE.Vector3(0, 1, 0), condition: (p) => p.y > 0.5, angle: -Math.PI / 2 },
  D: { axis: new THREE.Vector3(0, 1, 0), condition: (p) => p.y < -0.5, angle: Math.PI / 2 },
  L: { axis: new THREE.Vector3(1, 0, 0), condition: (p) => p.x < -0.5, angle: Math.PI / 2 },
  R: { axis: new THREE.Vector3(1, 0, 0), condition: (p) => p.x > 0.5, angle: -Math.PI / 2 },
  F: { axis: new THREE.Vector3(0, 0, 1), condition: (p) => p.z > 0.5, angle: -Math.PI / 2 },
  B: { axis: new THREE.Vector3(0, 0, 1), condition: (p) => p.z < -0.5, angle: Math.PI / 2 },
};

interface CubeletStickerProps {
  face: FaceKey;
  color: string;
}

function CubeletSticker({ face, color }: CubeletStickerProps) {
  let position: [number, number, number] = [0, 0, 0];
  let rotation: [number, number, number] = [0, 0, 0];
  const offset = 0.501;

  switch (face) {
    case 'U': position = [0, offset, 0]; rotation = [-Math.PI / 2, 0, 0]; break;
    case 'D': position = [0, -offset, 0]; rotation = [Math.PI / 2, 0, 0]; break;
    case 'L': position = [-offset, 0, 0]; rotation = [0, -Math.PI / 2, 0]; break;
    case 'R': position = [offset, 0, 0]; rotation = [0, Math.PI / 2, 0]; break;
    case 'F': position = [0, 0, offset]; rotation = [0, 0, 0]; break;
    case 'B': position = [0, 0, -offset]; rotation = [0, Math.PI, 0]; break;
  }

  return (
    <mesh position={position} rotation={rotation}>
      {/* Slightly smaller than 1 unit to leave thin black gap between stickers */}
      <planeGeometry args={[0.88, 0.88]} />
      <meshStandardMaterial color={color} side={THREE.FrontSide} />
    </mesh>
  );
}

interface CubeletData {
  position: [number, number, number];
  stickers: {
    face: FaceKey;
    color: string;
  }[];
}

function Cubelet({ position, stickers, index, cubeletRefs }: CubeletData & { index: number; cubeletRefs: React.MutableRefObject<(THREE.Group | null)[]> }) {
  const groupRef = useRef<THREE.Group>(null);
  
  // Register this cubelet's rotation group ref
  useEffect(() => {
    // eslint-disable-next-line react-hooks/immutability
    cubeletRefs.current[index] = groupRef.current;
  }, [index, cubeletRefs]);

  return (
    <group ref={groupRef}>
      <group position={position}>
        {/* Black cube body for this cubelet */}
        <mesh>
          <boxGeometry args={[0.98, 0.98, 0.98]} />
          <meshStandardMaterial color="#111111" />
        </mesh>
        {stickers.map((s, i) => (
          <CubeletSticker key={i} face={s.face} color={s.color} />
        ))}
      </group>
    </group>
  );
}

function getCubeletsFromState(stateStr: string): CubeletData[] {
  const s = stateStr.length === 54 ? stateStr : SOLVED_STATE;
  const cubelets: CubeletData[] = [];

  for (let x = -1; x <= 1; x++) {
    for (let y = -1; y <= 1; y++) {
      for (let z = -1; z <= 1; z++) {
        if (x === 0 && y === 0 && z === 0) continue;

        const stickers: { face: FaceKey; color: string }[] = [];

        // Up face (y=1): WCA indices 0-8
        if (y === 1) {
          const idx = 3 * (z + 1) + (x + 1);
          stickers.push({ face: 'U', color: COLOR_MAP[s[idx]] || '#888888' });
        }
        // Down face (y=-1): WCA indices 27-35
        if (y === -1) {
          const idx = 27 + 3 * (1 - z) + (x + 1);
          stickers.push({ face: 'D', color: COLOR_MAP[s[idx]] || '#888888' });
        }
        // Front face (z=1): WCA indices 18-26
        if (z === 1) {
          const idx = 18 + 3 * (1 - y) + (x + 1);
          stickers.push({ face: 'F', color: COLOR_MAP[s[idx]] || '#888888' });
        }
        // Back face (z=-1): WCA indices 45-53
        if (z === -1) {
          const idx = 45 + 3 * (1 - y) + (1 - x);
          stickers.push({ face: 'B', color: COLOR_MAP[s[idx]] || '#888888' });
        }
        // Right face (x=1): WCA indices 9-17
        if (x === 1) {
          const idx = 9 + 3 * (1 - y) + (1 - z);
          stickers.push({ face: 'R', color: COLOR_MAP[s[idx]] || '#888888' });
        }
        // Left face (x=-1): WCA indices 36-44
        if (x === -1) {
          const idx = 36 + 3 * (1 - y) + (z + 1);
          stickers.push({ face: 'L', color: COLOR_MAP[s[idx]] || '#888888' });
        }

        cubelets.push({
          position: [x, y, z],
          stickers
        });
      }
    }
  }
  return cubelets;
}

interface CubeSceneProps {
  stateStr: string;
  animatingMove?: string;
  onAnimationComplete: () => void;
}

function CubeScene({ stateStr, animatingMove, onAnimationComplete }: CubeSceneProps) {
  const cubelets = useMemo(() => getCubeletsFromState(stateStr), [stateStr]);
  const cubeletRefs = useRef<(THREE.Group | null)[]>([]);
  const animProgress = useRef(0);
  const activeMove = useRef<string | null>(null);
  const ANIM_DURATION = 0.25; // 250ms

  // Synchronize the animation ref with the prop
  useEffect(() => {
    if (animatingMove) {
      activeMove.current = animatingMove;
      animProgress.current = 0;
    } else {
      activeMove.current = null;
      // Reset rotations when not animating
      cubeletRefs.current.forEach(ref => {
        if (ref) ref.rotation.set(0, 0, 0);
      });
    }
  }, [animatingMove]);

  useFrame((_, delta) => {
    if (!activeMove.current) return;

    animProgress.current += delta / ANIM_DURATION;
    const progress = Math.min(animProgress.current, 1);
    const move = activeMove.current;

    const face = move[0];
    const modifier = move[1] || '';
    const config = MOVE_CONFIG[face];
    if (!config) return;

    let totalAngle = config.angle;
    if (modifier === "'") totalAngle *= -1;
    if (modifier === '2') totalAngle *= 2;

    const currentAngle = totalAngle * progress;

    cubeletRefs.current.forEach((ref, i) => {
      if (!ref || !cubelets[i]) return;
      const pos = cubelets[i].position;
      const vecPos = new THREE.Vector3(...pos);
      if (config.condition(vecPos)) {
        if (config.axis.x !== 0) ref.rotation.x = currentAngle;
        if (config.axis.y !== 0) ref.rotation.y = currentAngle;
        if (config.axis.z !== 0) ref.rotation.z = currentAngle;
      }
    });

    if (progress >= 1) {
      // Instantly clear the move ref so we don't double-call completion
      activeMove.current = null;
      onAnimationComplete();
    }
  });

  return (
    <>
      <ambientLight intensity={0.8} />
      <directionalLight position={[5, 5, 5]} intensity={0.6} />
      {cubelets.map((c, i) => (
        <Cubelet 
          key={i} 
          position={c.position} 
          stickers={c.stickers} 
          index={i} 
          cubeletRefs={cubeletRefs} 
        />
      ))}
    </>
  );
}

interface CubeViewer3DProps {
  stateString?: string;
  animatingMove?: string;
}

export default function CubeViewer3D({ stateString, animatingMove }: CubeViewer3DProps) {
  const [displayedState, setDisplayedState] = useState(stateString ?? SOLVED_STATE);
  const [currentAnimMove, setCurrentAnimMove] = useState<string | undefined>(undefined);

  const [prevProps, setPrevProps] = useState({ stateString, animatingMove });

  // Sync state with props during render to avoid cascading renders
  if (stateString !== prevProps.stateString || animatingMove !== prevProps.animatingMove) {
    setPrevProps({ stateString, animatingMove });
    const target = stateString ?? SOLVED_STATE;
    if (target !== displayedState) {
      if (animatingMove) {
        if (currentAnimMove !== animatingMove) {
          setCurrentAnimMove(animatingMove);
        }
      } else {
        setDisplayedState(target);
        setCurrentAnimMove(undefined);
      }
    }
  }

  useEffect(() => {
    // This effect is now just for potential side-effects or logging
  }, [stateString, animatingMove]);

  const handleAnimationComplete = () => {
    setDisplayedState(stateString ?? SOLVED_STATE);
    setCurrentAnimMove(undefined);
  };

  return (
    <div className="bg-slate-900 rounded-lg shadow-inner overflow-hidden" style={{ height: 300 }}>
      <Canvas camera={{ position: [5, 5, 5], fov: 45 }}>
        <OrbitControls enablePan={false} />
        <CubeScene 
          stateStr={displayedState} 
          animatingMove={currentAnimMove}
          onAnimationComplete={handleAnimationComplete}
        />
      </Canvas>
    </div>
  );
}
