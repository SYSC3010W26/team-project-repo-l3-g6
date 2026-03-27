import { Canvas } from '@react-three/fiber';
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

interface StickerProps {
  position: [number, number, number];
  rotation: [number, number, number];
  color: string;
}

function Sticker({ position, rotation, color }: StickerProps) {
  return (
    <mesh position={position} rotation={rotation}>
      {/* Slightly smaller than 1 unit to leave thin black gap between stickers */}
      <planeGeometry args={[0.88, 0.88]} />
      <meshStandardMaterial color={color} side={THREE.FrontSide} />
    </mesh>
  );
}

interface FaceProps {
  /** 9-char face string, e.g. "UUUUUUUUU" */
  faceChars: string;
  /** Offset from cube center along the face's normal axis (+0.51 so stickers sit on surface) */
  normalOffset: number;
  /** Euler rotation to orient this face outward */
  rotation: [number, number, number];
  /** Base position (center of face) before per-sticker offset */
  basePosition: [number, number, number];
}

function Face({ faceChars, rotation, basePosition }: FaceProps) {
  const stickers: React.ReactElement[] = [];
  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 3; col++) {
      const idx = row * 3 + col;
      const char = faceChars[idx] ?? 'U';
      const color = COLOR_MAP[char] ?? '#888888';
      // Place sticker at col offset (-1, 0, 1) and row offset (-1, 0, 1) in face-local space
      // The basePosition already encodes the face's outward shift; sticker offsets are perpendicular
      const [bx, by, bz] = basePosition;
      // We'll compute position relative to face orientation using the rotation angles
      // Since faces are axis-aligned, we can determine the two tangent axes from the rotation:
      const colOffset = col - 1; // -1, 0, +1
      const rowOffset = 1 - row; // +1, 0, -1 (flip so row 0 = top)
      let px = bx;
      let py = by;
      let pz = bz;

      // Determine tangent axes based on face rotation
      const [rx] = rotation;
      if (Math.abs(rx) < 0.1) {
        // Front (z+) or Back (z-): tangents are X and Y
        px += colOffset;
        py += rowOffset;
      } else if (Math.abs(rx - Math.PI / 2) < 0.1 || Math.abs(rx + Math.PI / 2) < 0.1) {
        // Top (rx = -π/2) or Bottom (rx = π/2): tangents are X and Z
        px += colOffset;
        pz += (rx < 0 ? rowOffset : -rowOffset);
      } else {
        // Left or Right (ry = ±π/2): tangents are Z and Y
        const [, ry] = rotation;
        pz += (ry > 0 ? -colOffset : colOffset);
        py += rowOffset;
      }

      stickers.push(
        <Sticker
          key={idx}
          position={[px, py, pz]}
          rotation={rotation}
          color={color}
        />
      );
    }
  }
  return <>{stickers}</>;
}

// Black cube body (so gaps between stickers show as black)
function CubeBody() {
  return (
    <mesh>
      <boxGeometry args={[3.05, 3.05, 3.05]} />
      <meshStandardMaterial color="#111111" />
    </mesh>
  );
}

interface CubeSceneProps {
  stateStr: string;
}

function CubeScene({ stateStr }: CubeSceneProps) {
  const s = stateStr.length === 54 ? stateStr : SOLVED_STATE;

  // Face slices: U=0-8, R=9-17, F=18-26, D=27-35, L=36-44, B=45-53
  const U = s.slice(0, 9);
  const R = s.slice(9, 18);
  const F = s.slice(18, 27);
  const D = s.slice(27, 36);
  const L = s.slice(36, 45);
  const B = s.slice(45, 54);

  const OFFSET = 1.51; // face sits just outside the 3-unit cube (±1.5 half-extent + 0.01)

  return (
    <>
      <ambientLight intensity={0.8} />
      <directionalLight position={[5, 5, 5]} intensity={0.6} />
      <CubeBody />
      {/* Front face: +Z, no rotation */}
      <Face faceChars={F} normalOffset={OFFSET} rotation={[0, 0, 0]} basePosition={[0, 0, OFFSET]} />
      {/* Back face: -Z, rotate 180° around Y */}
      <Face faceChars={B} normalOffset={OFFSET} rotation={[0, Math.PI, 0]} basePosition={[0, 0, -OFFSET]} />
      {/* Up face: +Y, rotate -90° around X */}
      <Face faceChars={U} normalOffset={OFFSET} rotation={[-Math.PI / 2, 0, 0]} basePosition={[0, OFFSET, 0]} />
      {/* Down face: -Y, rotate +90° around X */}
      <Face faceChars={D} normalOffset={OFFSET} rotation={[Math.PI / 2, 0, 0]} basePosition={[0, -OFFSET, 0]} />
      {/* Right face: +X, rotate 90° around Y */}
      <Face faceChars={R} normalOffset={OFFSET} rotation={[0, Math.PI / 2, 0]} basePosition={[OFFSET, 0, 0]} />
      {/* Left face: -X, rotate -90° around Y */}
      <Face faceChars={L} normalOffset={OFFSET} rotation={[0, -Math.PI / 2, 0]} basePosition={[-OFFSET, 0, 0]} />
    </>
  );
}

interface CubeViewer3DProps {
  stateString?: string;
}

export default function CubeViewer3D({ stateString }: CubeViewer3DProps) {
  const stateStr = stateString ?? SOLVED_STATE;

  return (
    <div className="bg-slate-900 rounded-lg" style={{ height: 300 }}>
      <Canvas camera={{ position: [5, 5, 5], fov: 45 }}>
        <OrbitControls enablePan={false} />
        <CubeScene stateStr={stateStr} />
      </Canvas>
    </div>
  );
}
