import { useState } from "react";
import { SafeAreaView, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { StatusBar } from "expo-status-bar";

import { LoginScreen } from "@/screens/LoginScreen";
import { DepartmentSelectorScreen } from "@/screens/DepartmentSelectorScreen";
import { BarcodeScanScreen } from "@/screens/BarcodeScanScreen";
import { GuidedCaptureScreen } from "@/screens/GuidedCaptureScreen";

// Minimal screen switcher placeholder. Sprint 6 replaces this with
// react-navigation + native camera/sensor modules.
const SCREENS = {
  Login: LoginScreen,
  Department: DepartmentSelectorScreen,
  Barcode: BarcodeScanScreen,
  Capture: GuidedCaptureScreen,
} as const;

type ScreenKey = keyof typeof SCREENS;

export default function App() {
  const [screen, setScreen] = useState<ScreenKey>("Login");
  const Current = SCREENS[screen];

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="dark" />
      <Text style={styles.title}>Solidità 4.0 — Mobile (skeleton)</Text>
      <ScrollView horizontal style={styles.nav} showsHorizontalScrollIndicator={false}>
        {(Object.keys(SCREENS) as ScreenKey[]).map((key) => (
          <TouchableOpacity
            key={key}
            onPress={() => setScreen(key)}
            style={[styles.tab, screen === key && styles.tabActive]}
          >
            <Text style={screen === key ? styles.tabTextActive : styles.tabText}>{key}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      <View style={styles.body}>
        <Current />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#f8fafc" },
  title: { fontSize: 16, fontWeight: "600", padding: 12, color: "#0f172a" },
  nav: { flexGrow: 0, paddingHorizontal: 8 },
  tab: { paddingVertical: 8, paddingHorizontal: 14, marginRight: 8, borderRadius: 8, backgroundColor: "#e2e8f0" },
  tabActive: { backgroundColor: "#0f172a" },
  tabText: { color: "#334155" },
  tabTextActive: { color: "#ffffff" },
  body: { flex: 1, padding: 16 },
});
