import { useEffect, useState } from "react";
import { Pressable, SafeAreaView, StyleSheet, Text, View } from "react-native";
import { StatusBar } from "expo-status-bar";

import { logout, restoreSession } from "@/api/auth";
import { CameraCaptureScreen } from "@/camera/CameraCaptureScreen";
import { LoginScreen } from "@/screens/LoginScreen";

type Screen = "home" | "capture";

export default function App() {
  const [authed, setAuthed] = useState<boolean | null>(null); // null = checking
  const [screen, setScreen] = useState<Screen>("home");

  useEffect(() => {
    restoreSession().then(setAuthed);
  }, []);

  if (authed === null) {
    return (
      <SafeAreaView style={styles.root}>
        <Text style={styles.checking}>…</Text>
      </SafeAreaView>
    );
  }

  if (!authed) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar style="dark" />
        <View style={styles.body}>
          <LoginScreen onLoggedIn={() => setAuthed(true)} />
        </View>
      </SafeAreaView>
    );
  }

  if (screen === "capture") {
    // NOTE: config (test job / batch / method / references / grey-scale + strict)
    // is wired from the selected workflow; this scaffold opens the camera with a
    // placeholder so the capture pipeline can be exercised on device.
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar style="light" />
        <Header title="Acquisizione" onBack={() => setScreen("home")} />
        <CameraCaptureScreen
          config={{ test_job_id: "", capture_type: "multifiber_after", strict_quality: true }}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="dark" />
      <View style={styles.body}>
        <Text style={styles.title}>Solidità 4.0</Text>
        <Text style={styles.sub}>Acquisizione striscia multifibra (modalità controllata).</Text>

        <Pressable style={styles.primary} onPress={() => setScreen("capture")}>
          <Text style={styles.primaryText}>📷 Nuova acquisizione</Text>
        </Pressable>

        <Pressable
          style={styles.ghost}
          onPress={async () => {
            await logout();
            setAuthed(false);
          }}
        >
          <Text style={styles.ghostText}>Esci</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

function Header({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <View style={styles.header}>
      <Pressable onPress={onBack}>
        <Text style={styles.back}>‹ Indietro</Text>
      </Pressable>
      <Text style={styles.headerTitle}>{title}</Text>
      <View style={{ width: 60 }} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#f8fafc" },
  checking: { textAlign: "center", marginTop: 80, fontSize: 24, color: "#94a3b8" },
  body: { flex: 1, padding: 20, gap: 14 },
  title: { fontSize: 24, fontWeight: "700", color: "#0f172a" },
  sub: { color: "#475569" },
  primary: {
    backgroundColor: "#2563eb",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 8,
  },
  primaryText: { color: "#fff", fontWeight: "600", fontSize: 16 },
  ghost: { paddingVertical: 12, alignItems: "center" },
  ghostText: { color: "#64748b" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: "#0f172a",
  },
  back: { color: "#fff", width: 60 },
  headerTitle: { color: "#fff", fontWeight: "600" },
});
