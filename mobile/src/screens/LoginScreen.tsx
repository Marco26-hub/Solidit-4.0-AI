import { Text, View } from "react-native";

export function LoginScreen() {
  return (
    <View>
      <Text style={{ fontSize: 18, fontWeight: "600" }}>Login operatore</Text>
      <Text style={{ color: "#475569", marginTop: 8 }}>
        Email · password · tenant selector. Token in secure storage (Sprint 6).
      </Text>
    </View>
  );
}
