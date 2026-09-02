import {
  CSSProperties,
  MouseEvent,
  PointerEvent,
  ReactNode,
  useEffect,
  useRef,
  useState,
} from "react";

type Point = { x: number; y: number };

type MovablePanelProps = {
  children: ReactNode;
  className: string;
  defaultPosition: Point;
  id: string;
  label: string;
};

const storagePrefix = "vecna.panel-layout.v7.";
const LONG_PRESS_MS = 500; // ms held before drag activates

function clamp(point: Point) {
  const maxX = typeof window !== "undefined" ? Math.max(8, window.innerWidth - 60) : 1920;
  const maxY = typeof window !== "undefined" ? Math.max(8, window.innerHeight - 60) : 1080;
  return {
    x: Math.max(8, Math.min(point.x, maxX)),
    y: Math.max(8, Math.min(point.y, maxY)),
  };
}

function loadPosition(id: string, fallback: Point) {
  try {
    const saved = window.localStorage.getItem(`${storagePrefix}${id}`);
    if (!saved) return fallback;
    const position = JSON.parse(saved) as Point;
    return Number.isFinite(position.x) && Number.isFinite(position.y) ? clamp(position) : fallback;
  } catch {
    return fallback;
  }
}

function savePosition(id: string, pos: Point) {
  try {
    window.localStorage.setItem(`${storagePrefix}${id}`, JSON.stringify(pos));
  } catch {
    // Ignore
  }
}

export function MovablePanel({ children, className, defaultPosition, id, label }: MovablePanelProps) {
  const panelRef = useRef<HTMLDivElement | null>(null);
  const longPressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dragOrigin = useRef<Point | null>(null);
  const pointerIdRef = useRef<number | null>(null);
  const pendingPointerRef = useRef<{ clientX: number; clientY: number } | null>(null);
  const [position, setPosition] = useState(() => loadPosition(id, defaultPosition));
  const [isDragReady, setIsDragReady] = useState(false);   // long-press primed
  const [isUnlocked, setIsUnlocked] = useState(false);     // double-click toggle
  const [isDragging, setIsDragging] = useState(false);
  const [menu, setMenu] = useState<Point | null>(null);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(`${storagePrefix}${id}`);
      if (!saved) setPosition(clamp(defaultPosition));
    } catch { /* ignore */ }
  }, [defaultPosition, id]);

  useEffect(() => {
    const onResize = () => setPosition((current) => clamp(current));
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    if (!menu) return;
    const dismiss = () => setMenu(null);
    window.addEventListener("pointerdown", dismiss, { once: true });
    return () => window.removeEventListener("pointerdown", dismiss);
  }, [menu]);

  function cancelLongPress() {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  }

  function isInteractiveTarget(target: EventTarget | null): boolean {
    const el = target as HTMLElement | null;
    return !!(
      el &&
      (el.closest("button") ||
        el.closest("input") ||
        el.closest("textarea") ||
        el.closest("select") ||
        el.closest("a") ||
        el.closest(".messages") ||
        el.closest(".panel-context-menu"))
    );
  }

  function handleDoubleClick(event: MouseEvent<HTMLDivElement>) {
    if (isInteractiveTarget(event.target)) return;
    setIsUnlocked((prev) => !prev);
    setIsDragReady((prev) => !prev);
  }

  function handlePointerDown(event: PointerEvent<HTMLDivElement>) {
    if (event.button !== 0) return;
    if (isInteractiveTarget(event.target)) return;

    if (isUnlocked) {
      // Immediate drag if unlocked via double click
      dragOrigin.current = { x: event.clientX - position.x, y: event.clientY - position.y };
      pointerIdRef.current = event.pointerId;
      try {
        panelRef.current?.setPointerCapture(event.pointerId);
      } catch { /* Ignore */ }
      setIsDragging(true);
      return;
    }

    pendingPointerRef.current = { clientX: event.clientX, clientY: event.clientY };

    // Start long-press timer — drag only activates after 500ms hold
    longPressTimerRef.current = setTimeout(() => {
      longPressTimerRef.current = null;
      setIsDragReady(true);
      setMenu(null);

      // Activate drag immediately once long-press fires
      if (pendingPointerRef.current && panelRef.current) {
        const { clientX, clientY } = pendingPointerRef.current;
        dragOrigin.current = { x: clientX - position.x, y: clientY - position.y };
        pointerIdRef.current = event.pointerId;
        try {
          panelRef.current.setPointerCapture(event.pointerId);
        } catch { /* Ignore */ }
        setIsDragging(true);
      }
    }, LONG_PRESS_MS);
  }

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    // Cancel long press if pointer moves more than 8px (not a hold)
    if (longPressTimerRef.current && pendingPointerRef.current) {
      const dx = event.clientX - pendingPointerRef.current.clientX;
      const dy = event.clientY - pendingPointerRef.current.clientY;
      if (Math.sqrt(dx * dx + dy * dy) > 8) {
        cancelLongPress();
        setIsDragReady(false);
      }
    }

    if (!isDragging || !dragOrigin.current) return;
    if (pointerIdRef.current !== null && event.pointerId !== pointerIdRef.current) return;

    const nextPos = clamp({
      x: event.clientX - dragOrigin.current.x,
      y: event.clientY - dragOrigin.current.y,
    });
    setPosition(nextPos);
  }

  function handlePointerUp(event: PointerEvent<HTMLDivElement>) {
    cancelLongPress();
    pendingPointerRef.current = null;

    if (isDragging) {
      setIsDragging(false);
      setIsDragReady(false);
      dragOrigin.current = null;
      pointerIdRef.current = null;
      savePosition(id, position);
      try {
        panelRef.current?.releasePointerCapture(event.pointerId);
      } catch { /* Ignore */ }
    } else {
      setIsDragReady(false);
    }
  }

  function openMenu(event: MouseEvent<HTMLDivElement>) {
    event.preventDefault();
    setMenu({ x: event.clientX, y: event.clientY });
  }

  function resetPosition() {
    try {
      window.localStorage.removeItem(`${storagePrefix}${id}`);
    } catch { /* ignore */ }
    setPosition(clamp(defaultPosition));
    setMenu(null);
  }

  return (
    <div
      ref={panelRef}
      className={`movable-panel ${className} ${isDragReady || isUnlocked ? "drag-ready" : ""} ${isDragging ? "is-dragging" : ""} ${isUnlocked ? "is-unlocked" : ""}`}
      style={{ "--panel-x": `${position.x}px`, "--panel-y": `${position.y}px` } as CSSProperties}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      onDoubleClick={handleDoubleClick}
      onContextMenu={openMenu}
      aria-label={`${label} (double-click or hold 0.5s to drag)`}
    >
      {(isDragReady || isUnlocked) && !isDragging && (
        <div className="drag-hint" aria-hidden="true">
          {isUnlocked ? "🔓 UNLOCKED — DRAG FREELY (2x CLICK TO LOCK)" : "HOLD TO DRAG…"}
        </div>
      )}
      {children}
      {menu && (
        <div
          className="panel-context-menu"
          role="menu"
          aria-label={`${label} panel options`}
          style={{ left: menu.x, top: menu.y }}
          onPointerDown={(event) => event.stopPropagation()}
        >
          <button type="button" role="menuitem" onClick={resetPosition}>
            Reset position
          </button>
        </div>
      )}
    </div>
  );
}
