import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { login } from "@/api/auth";

export function LoginScreen({ onLoggedIn }: { onLoggedIn: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      const res = await login(email.trim(), password);
      // single-company operator: re-issue token scoped to the only company
      if (!res.company_id && res.companies.length === 1) {
        await login(email.trim(), password, res.companies[0].id);
      }
      onLoggedIn();
    } catch (e) {
      console.error("LoginScreen: login failed", e);
      setError(e instanceof Error ? e.message : "Login fallito");
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.wrap}>
      <Text style={styles.title}>Login operatore</Text>
      <TextInput
        style={styles.input}
        placeholder="Email"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />
      <Pressable
        style={[styles.btn, (!email || !password || busy) && styles.btnOff]}
        disabled={!email || !password || busy}
        onPress={submit}
      >
        {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Accedi</Text>}
      </Pressable>
      {error && <Text style={styles.err}>{error}</Text>}
      <Text style={styles.note}>
        Piattaforma di imaging digitale per pre-valutazione. Non sostituisce un laboratorio
        accreditato.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 12 },
  title: { fontSize: 20, fontWeight: "700", color: "#0f172a" },
  input: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 16,
    backgroundColor: "#fff",
  },
  btn: {
    backgroundColor: "#2563eb",
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
  },
  btnOff: { opacity: 0.5 },
  btnText: { color: "#fff", fontWeight: "600", fontSize: 16 },
  err: { color: "#dc2626" },
  note: { color: "#94a3b8", fontSize: 12, marginTop: 8 },
});
