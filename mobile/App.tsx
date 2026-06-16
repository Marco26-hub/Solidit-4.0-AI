import { useEffect, useState } from "react";
import { Pressable, SafeAreaView, StyleSheet, Text, View } from "react-native";
import { StatusBar } from "expo-status-bar";

import type { CaptureSessionInput } from "@/api/capture";
import { logout, restoreSession } from "@/api/auth";
import { CameraCaptureScreen } from "@/camera/CameraCaptureScreen";
import { JobSelectScreen } from "@/screens/JobSelectScreen";
import { LoginScreen } from "@/screens/LoginScreen";
import { flush } from "@/state/queue";

type Screen = "home" | "jobselect" | "capture";

export default function App() {
  const [authed, setAuthed] = useState<boolean | null>(null); // null = checking
  const [screen, setScreen] = useState<Screen>("home");
  const [config, setConfig] = useState<CaptureSessionInput | null>(null);

  useEffect(() => {
    restoreSession().then((ok) => {
      setAuthed(ok);
      if (ok) flush().catch((e) => console.warn("flush offline retry failed", e));
    });
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

  if (screen === "jobselect") {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar style="dark" />
        <Header title="Nuova prova" onBack={() => setScreen("home")} dark={false} />
        <JobSelectScreen
          onStart={(cfg) => {
            setConfig(cfg);
            setScreen("capture");
          }}
        />
      </SafeAreaView>
    );
  }

  if (screen === "capture" && config) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar style="light" />
        <Header title="Acquisizione" onBack={() => setScreen("home")} />
        <CameraCaptureScreen config={config} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="dark" />
      <View style={styles.body}>
        <Text style={styles.title}>Solidità 4.0</Text>
        <Text style={styles.sub}>Acquisizione striscia multifibra (modalità controllata).</Text>

        <Pressable style={styles.primary} onPress={() => setScreen("jobselect")}>
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

function Header({ title, onBack, dark = true }: { title: string; onBack: () => void; dark?: boolean }) {
  const bg = dark ? "#0f172a" : "#fff";
  const fg = dark ? "#fff" : "#0f172a";
  return (
    <View style={[styles.header, { backgroundColor: bg }]}>
      <Pressable onPress={onBack}>
        <Text style={[styles.back, { color: fg }]}>‹ Indietro</Text>
      </Pressable>
      <Text style={[styles.headerTitle, { color: fg }]}>{title}</Text>
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
