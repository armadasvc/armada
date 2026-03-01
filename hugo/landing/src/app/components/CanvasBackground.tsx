import { useEffect, useRef } from "react";

const CELL_SIZE = 36;
const ACCENT = { r: 60, g: 70, b: 85 };
const MAX_WAKES = 300;
const MOUSE_REPULSION_RADIUS = 120;
const MOUSE_GLOW_RADIUS = 180;
const BOAT_WRAP_MARGIN = 60;

const BOAT_TYPES = [
  { name: "carrier", len: 5, w: 0.6 },
  { name: "battleship", len: 4, w: 0.55 },
  { name: "cruiser", len: 3, w: 0.5 },
  { name: "sub", len: 3, w: 0.35 },
  { name: "destroyer", len: 2, w: 0.45 },
];

function rgba(color: typeof ACCENT, alpha: number) {
  return `rgba(${color.r}, ${color.g}, ${color.b}, ${alpha})`;
}

function dist(ax: number, ay: number, bx: number, by: number) {
  const dx = ax - bx;
  const dy = ay - by;
  return Math.sqrt(dx * dx + dy * dy);
}

interface GridPoint {
  x: number;
  y: number;
}
interface Boat {
  x: number;
  y: number;
  angle: number;
  speed: number;
  drift: number;
  len: number;
  w: number;
  type: string;
  opacity: number;
  flickerPhase: number;
}
interface Wake {
  x: number;
  y: number;
  life: number;
  decay: number;
  size: number;
}

export function CanvasBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let W = 0;
    let H = 0;
    let grid: GridPoint[] = [];
    let boats: Boat[] = [];
    let wakes: Wake[] = [];
    const mouse = { x: -1000, y: -1000 };
    let time = 0;
    let raf: number;

    function createGrid() {
      grid = [];
      const cols = Math.ceil(W / CELL_SIZE) + 1;
      const rows = Math.ceil(H / CELL_SIZE) + 1;
      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          grid.push({ x: i * CELL_SIZE, y: j * CELL_SIZE });
        }
      }
    }

    function drawGrid() {
      const cols = Math.ceil(W / CELL_SIZE) + 1;
      const rows = Math.ceil(H / CELL_SIZE) + 1;

      ctx!.strokeStyle = rgba(ACCENT, 0.04);
      ctx!.lineWidth = 0.5;
      for (let i = 0; i <= cols; i++) {
        ctx!.beginPath();
        ctx!.moveTo(i * CELL_SIZE, 0);
        ctx!.lineTo(i * CELL_SIZE, H);
        ctx!.stroke();
      }
      for (let j = 0; j <= rows; j++) {
        ctx!.beginPath();
        ctx!.moveTo(0, j * CELL_SIZE);
        ctx!.lineTo(W, j * CELL_SIZE);
        ctx!.stroke();
      }

      for (const g of grid) {
        const d = dist(g.x, g.y, mouse.x, mouse.y);
        const glow =
          d < MOUSE_GLOW_RADIUS ? (1 - d / MOUSE_GLOW_RADIUS) * 0.6 : 0;
        ctx!.beginPath();
        ctx!.arc(g.x, g.y, 1 + glow * 2, 0, Math.PI * 2);
        ctx!.fillStyle = rgba(ACCENT, 0.25 + glow);
        ctx!.fill();
      }
    }

    function createBoats() {
      boats = [];
      const count = 15 + Math.floor((W * H) / 120000);
      for (let i = 0; i < count; i++) {
        const type = BOAT_TYPES[Math.floor(Math.random() * BOAT_TYPES.length)];
        const scale = 0.9 + Math.random() * 1.0;
        boats.push({
          x: Math.random() * W,
          y: Math.random() * H,
          angle: Math.random() * Math.PI * 2,
          speed: 0.15 + Math.random() * 0.35,
          drift: (Math.random() - 0.5) * 0.002,
          len: type.len * CELL_SIZE * 0.35 * scale,
          w: type.w * CELL_SIZE * 0.35 * scale,
          type: type.name,
          opacity: 0.12 + Math.random() * 0.25,
          flickerPhase: Math.random() * Math.PI * 2,
        });
      }
    }

    function updateBoats() {
      for (const b of boats) {
        b.x += Math.cos(b.angle) * b.speed;
        b.y += Math.sin(b.angle) * b.speed;
        b.angle += b.drift;

        if (b.x > W + BOAT_WRAP_MARGIN) b.x = -BOAT_WRAP_MARGIN;
        if (b.x < -BOAT_WRAP_MARGIN) b.x = W + BOAT_WRAP_MARGIN;
        if (b.y > H + BOAT_WRAP_MARGIN) b.y = -BOAT_WRAP_MARGIN;
        if (b.y < -BOAT_WRAP_MARGIN) b.y = H + BOAT_WRAP_MARGIN;

        const d = dist(b.x, b.y, mouse.x, mouse.y);
        if (d < MOUSE_REPULSION_RADIUS) {
          const force = (1 - d / MOUSE_REPULSION_RADIUS) * 0.8;
          b.x += ((b.x - mouse.x) / d) * force;
          b.y += ((b.y - mouse.y) / d) * force;
        }
      }
    }

    function drawBoat(b: Boat) {
      const { x, y, angle, len, w: bw, opacity, flickerPhase } = b;
      const flicker = 0.85 + Math.sin(time * 0.5 + flickerPhase) * 0.15;
      const alpha = opacity * flicker;

      ctx!.save();
      ctx!.translate(x, y);
      ctx!.rotate(angle);

      ctx!.beginPath();
      ctx!.moveTo(len * 0.5, 0);
      ctx!.lineTo(len * 0.2, -bw);
      ctx!.lineTo(-len * 0.4, -bw);
      ctx!.lineTo(-len * 0.5, -bw * 0.5);
      ctx!.lineTo(-len * 0.5, bw * 0.5);
      ctx!.lineTo(-len * 0.4, bw);
      ctx!.lineTo(len * 0.2, bw);
      ctx!.closePath();
      ctx!.fillStyle = rgba(ACCENT, alpha * 0.15);
      ctx!.fill();
      ctx!.strokeStyle = rgba(ACCENT, alpha);
      ctx!.lineWidth = 0.8;
      ctx!.stroke();

      ctx!.beginPath();
      ctx!.moveTo(-len * 0.3, 0);
      ctx!.lineTo(len * 0.3, 0);
      ctx!.strokeStyle = rgba(ACCENT, alpha * 0.5);
      ctx!.lineWidth = 0.5;
      ctx!.stroke();

      if (b.type === "carrier" || b.type === "battleship") {
        ctx!.fillStyle = rgba(ACCENT, alpha * 0.3);
        ctx!.fillRect(-len * 0.1, -bw * 0.5, len * 0.15, bw);
      }

      if (b.type === "battleship" || b.type === "cruiser") {
        ctx!.beginPath();
        ctx!.arc(len * 0.25, 0, bw * 0.35, 0, Math.PI * 2);
        ctx!.fillStyle = rgba(ACCENT, alpha * 0.4);
        ctx!.fill();
        ctx!.beginPath();
        ctx!.moveTo(len * 0.25, 0);
        ctx!.lineTo(len * 0.45, 0);
        ctx!.strokeStyle = rgba(ACCENT, alpha * 0.6);
        ctx!.lineWidth = 0.6;
        ctx!.stroke();
      }

      if (b.type === "sub") {
        ctx!.beginPath();
        ctx!.arc(len * 0.1, 0, bw * 0.6, 0, Math.PI * 2);
        ctx!.strokeStyle = rgba(ACCENT, alpha * 0.4);
        ctx!.lineWidth = 0.5;
        ctx!.stroke();
      }

      ctx!.restore();
    }

    function updateWakes() {
      for (let i = 0; i < boats.length; i += 3) {
        const b = boats[i];
        if (Math.random() > 0.3) continue;
        wakes.push({
          x: b.x - Math.cos(b.angle) * b.len * 0.5,
          y: b.y - Math.sin(b.angle) * b.len * 0.5,
          life: 1,
          decay: 0.008 + Math.random() * 0.008,
          size: 1 + Math.random() * 1.5,
        });
      }

      for (let i = wakes.length - 1; i >= 0; i--) {
        const wk = wakes[i];
        wk.life -= wk.decay;
        if (wk.life <= 0) {
          wakes.splice(i, 1);
          continue;
        }
        ctx!.beginPath();
        ctx!.arc(wk.x, wk.y, wk.size * wk.life, 0, Math.PI * 2);
        ctx!.fillStyle = rgba(ACCENT, wk.life * 0.12);
        ctx!.fill();
      }

      if (wakes.length > MAX_WAKES) wakes.splice(0, wakes.length - MAX_WAKES);
    }

    function animate() {
      time += 0.016;
      ctx!.clearRect(0, 0, W, H);
      drawGrid();
      updateWakes();
      updateBoats();
      for (const b of boats) drawBoat(b);
      raf = requestAnimationFrame(animate);
    }

    function resize() {
      W = canvas!.width = window.innerWidth;
      H = canvas!.height = window.innerHeight;
      createGrid();
      createBoats();
    }

    const onMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    const onMouseLeave = () => {
      mouse.x = -1000;
      mouse.y = -1000;
    };

    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseleave", onMouseLeave);

    resize();
    animate();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseleave", onMouseLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed top-0 left-0 w-full h-full pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}
