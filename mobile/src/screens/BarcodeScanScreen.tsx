import { Text, View } from "react-native";

export function BarcodeScanScreen() {
  return (
    <View>
      <Text style={{ fontSize: 18, fontWeight: "600" }}>Scansiona barcode commessa</Text>
      <Text style={{ color: "#475569", marginTop: 8 }}>
        Scan codice articolo/commessa → fetch brand specs + test target (Sprint 6,
        native barcode module).
      </Text>
    </View>
  );
}
