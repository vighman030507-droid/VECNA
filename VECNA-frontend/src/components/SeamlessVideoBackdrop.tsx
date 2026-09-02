import { useEffect, useRef, useState } from "react";

type SeamlessVideoBackdropProps = {
  src: string;
  fallbackSrc?: string;
  className?: string;
  active?: boolean;
  crossfadeDuration?: number;
};

export function SeamlessVideoBackdrop({
  src,
  fallbackSrc,
  className = "background-video",
  active = false,
  crossfadeDuration = 0.75,
}: SeamlessVideoBackdropProps) {
  const videoRefA = useRef<HTMLVideoElement>(null);
  const videoRefB = useRef<HTMLVideoElement>(null);
  const [activeVideo, setActiveVideo] = useState<"A" | "B">("A");

  useEffect(() => {
    const vidA = videoRefA.current;
    const vidB = videoRefB.current;
    if (!vidA || !vidB) return;

    // Start video A immediately
    vidA.play().catch(() => {});

    let triggeredFromA = false;
    let triggeredFromB = false;

    const onTimeUpdateA = () => {
      if (!vidA.duration || Number.isNaN(vidA.duration)) return;
      const timeLeft = vidA.duration - vidA.currentTime;

      if (timeLeft <= crossfadeDuration && !triggeredFromA) {
        triggeredFromA = true;
        triggeredFromB = false;
        vidB.currentTime = 0;
        vidB
          .play()
          .then(() => {
            setActiveVideo("B");
          })
          .catch(() => {});
      }
    };

    const onTimeUpdateB = () => {
      if (!vidB.duration || Number.isNaN(vidB.duration)) return;
      const timeLeft = vidB.duration - vidB.currentTime;

      if (timeLeft <= crossfadeDuration && !triggeredFromB) {
        triggeredFromB = true;
        triggeredFromA = false;
        vidA.currentTime = 0;
        vidA
          .play()
          .then(() => {
            setActiveVideo("A");
          })
          .catch(() => {});
      }
    };

    vidA.addEventListener("timeupdate", onTimeUpdateA);
    vidB.addEventListener("timeupdate", onTimeUpdateB);

    return () => {
      vidA.removeEventListener("timeupdate", onTimeUpdateA);
      vidB.removeEventListener("timeupdate", onTimeUpdateB);
    };
  }, [crossfadeDuration]);

  return (
    <div className={`background-video-container ${active ? "is-active" : ""}`} aria-hidden="true">
      {/* Primary Video Node (Buffer A) */}
      <video
        ref={videoRefA}
        className={`${className} ${activeVideo === "A" ? "video-visible" : "video-hidden"}`}
        muted
        playsInline
        preload="auto"
        style={{
          transition: `opacity ${crossfadeDuration}s ease-in-out`,
        }}
      >
        <source src={src} type="video/mp4" />
        {fallbackSrc && <source src={fallbackSrc} type="video/mp4" />}
      </video>

      {/* Secondary Video Node (Buffer B for gapless crossfade loop) */}
      <video
        ref={videoRefB}
        className={`${className} ${activeVideo === "B" ? "video-visible" : "video-hidden"}`}
        muted
        playsInline
        preload="auto"
        style={{
          transition: `opacity ${crossfadeDuration}s ease-in-out`,
        }}
      >
        <source src={src} type="video/mp4" />
        {fallbackSrc && <source src={fallbackSrc} type="video/mp4" />}
      </video>
    </div>
  );
}
