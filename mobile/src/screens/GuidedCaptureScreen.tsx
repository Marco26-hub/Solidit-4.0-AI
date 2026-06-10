import { Text, View } from "react-native";

import { evaluateCaptureGates, initialCaptureState } from "@/state/captureStore";

export function GuidedCaptureScreen() {
  // Mock telemetry to illustrate the capture gate logic.
  const mock = { ...initialCaptureState.telemetry, tiltDeg: 1, blurScore: 0.9, exposureScore: 0.9, motionScore: 0.1 };
  const { ready, errors } = evaluateCaptureGates(mock);

  return (
    <View>
      <Text style={{ fontSize: 18, fontWeight: "600" }}>Acquisizione guidata</Text>
      <Text style={{ color: "#475569", marginTop: 8 }}>
        Overlay: multifibra · tile/reference · marker · distanza · tilt · blur · exposure.
      </Text>
      <Text style={{ marginTop: 12, fontWeight: "600", color: ready ? "#15803d" : "#b91c1c" }}>
        {ready ? "Capture READY (auto-shot)" : `Blocked: ${errors.join(", ")}`}
      </Text>
      <Text style={{ color: "#94a3b8", marginTop: 8, fontSize: 12 }}>
        In metrological mode manual capture is blocked until all gates pass. Distance
        is guaranteed by the physical dima; LiDAR/ToF is a coherence check only.
      </Text>
    </View>
  );
}
