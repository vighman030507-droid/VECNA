import { createContext, useContext, ReactNode } from "react";

export type Status = "idle" | "listening" | "thinking" | "speaking" | "error";

type AudioLevelContextType = {
  level: number;
  status: Status;
};

const AudioLevelContext = createContext<AudioLevelContextType>({
  level: 0,
  status: "idle",
});

export function AudioLevelProvider({
  children,
  level,
  status,
}: {
  children: ReactNode;
  level: number;
  status: Status;
}) {
  return (
    <AudioLevelContext.Provider value={{ level, status }}>
      {children}
    </AudioLevelContext.Provider>
  );
}

export function useAudioLevel() {
  return useContext(AudioLevelContext);
}
