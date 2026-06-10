import { Text, View } from "react-native";

const DEPARTMENTS = ["Tintoria", "Stamperia Inkjet", "Stamperia Tradizionale", "Finissaggio/Confezione"];

export function DepartmentSelectorScreen() {
  return (
    <View>
      <Text style={{ fontSize: 18, fontWeight: "600" }}>Seleziona reparto</Text>
      {DEPARTMENTS.map((d) => (
        <Text key={d} style={{ color: "#334155", marginTop: 6 }}>
          • {d}
        </Text>
      ))}
    </View>
  );
}
