import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from "react-native";

import type { CaptureSessionInput } from "@/api/capture";
import {
  listBatches,
  listCalibrationRefs,
  listTestJobs,
  listTestMethods,
  type Batch,
  type CalibrationRef,
  type TestJob,
  type TestMethod,
} from "@/api/quality";

/** Build a real CaptureSession config (job + batch + method + references +
 * grey-scale/strict) before opening the camera. */
export function JobSelectScreen({ onStart }: { onStart: (config: CaptureSessionInput) => void }) {
  const [jobs, setJobs] = useState<TestJob[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [methods, setMethods] = useState<TestMethod[]>([]);
  const [refs, setRefs] = useState<CalibrationRef[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const [jobId, setJobId] = useState<string>("");
  const [batchId, setBatchId] = useState<string>("");
  const [method, setMethod] = useState<string>("");
  const [greyRef, setGreyRef] = useState<string>("");
  const [inframeGrey, setInframeGrey] = useState(true);
  const [strict, setStrict] = useState(true);

  useEffect(() => {
    Promise.all([listTestJobs(), listBatches(), listTestMethods(), listCalibrationRefs()])
      .then(([j, b, m, r]) => {
        setJobs(j);
        setBatches(b);
        setMethods(m);
        setRefs(r.filter((x) => x.kind === "grey_scale" && x.validity !== "retired"));
      })
      .catch((e) => setErr(String(e)));
  }, []);

  const ready = jobId && batchId && method;

  const start = () =>
    onStart({
      test_job_id: jobId,
      batch_id: batchId,
      test_method_code: method,
      capture_type: "multifiber_after",
      grey_scale_ref_id: greyRef || null,
      has_inframe_grey_scale: inframeGrey,
      strict_quality: strict,
    });

  return (
    <ScrollView contentContainerStyle={styles.body}>
      <Text style={styles.h}>Prova</Text>
      {err && <Text style={styles.err}>{err}</Text>}
      {jobs.map((j) => (
        <Row key={j.id} label={`${j.article_code ?? "—"} · ${j.lot_code ?? "—"} (${j.status})`} on={jobId === j.id} onPress={() => setJobId(j.id)} />
      ))}

      <Text style={styles.h}>Lotto multifibra</Text>
      {batches.map((b) => (
        <Row key={b.id} label={`${b.batch_code} ${b.strip_profile_code ? `(${b.strip_profile_code})` : ""}`} on={batchId === b.id} onPress={() => setBatchId(b.id)} />
      ))}

      <Text style={styles.h}>Metodo (solidità)</Text>
      {methods.map((m) => (
        <Row key={m.id} label={`${m.code} — ${m.name}`} on={method === m.code} onPress={() => setMethod(m.code)} />
      ))}

      <Text style={styles.h}>Scala grigia (riferimento)</Text>
      <Row label="— nessuno —" on={!greyRef} onPress={() => setGreyRef("")} />
      {refs.map((r) => (
        <Row key={r.id} label={`${r.code} (${r.validity})`} on={greyRef === r.id} onPress={() => setGreyRef(r.id)} />
      ))}

      <View style={styles.toggle}>
        <Text style={styles.tlabel}>Scala grigia in-frame (correzione colore)</Text>
        <Switch value={inframeGrey} onValueChange={setInframeGrey} />
      </View>
      <View style={styles.toggle}>
        <Text style={styles.tlabel}>Modalità accreditamento (rifiuto qualità)</Text>
        <Switch value={strict} onValueChange={setStrict} />
      </View>

      <Pressable style={[styles.start, !ready && styles.startOff]} disabled={!ready} onPress={start}>
        <Text style={styles.startText}>📷 Apri fotocamera</Text>
      </Pressable>
    </ScrollView>
  );
}

function Row({ label, on, onPress }: { label: string; on: boolean; onPress: () => void }) {
  return (
    <Pressable style={[styles.row, on && styles.rowOn]} onPress={onPress}>
      <Text style={[styles.rowText, on && styles.rowTextOn]} numberOfLines={1}>
        {on ? "✓ " : ""}
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  body: { padding: 16, gap: 6, paddingBottom: 40 },
  h: { fontSize: 13, fontWeight: "700", color: "#0f172a", marginTop: 14 },
  err: { color: "#b91c1c" },
  row: { paddingVertical: 10, paddingHorizontal: 12, borderRadius: 8, backgroundColor: "#fff", borderWidth: 1, borderColor: "#e2e8f0" },
  rowOn: { borderColor: "#2563eb", backgroundColor: "#eff6ff" },
  rowText: { color: "#334155" },
  rowTextOn: { color: "#1d4ed8", fontWeight: "600" },
  toggle: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 12 },
  tlabel: { flex: 1, color: "#334155", paddingRight: 10 },
  start: { backgroundColor: "#2563eb", borderRadius: 12, paddingVertical: 16, alignItems: "center", marginTop: 18 },
  startOff: { opacity: 0.4 },
  startText: { color: "#fff", fontWeight: "600", fontSize: 16 },
});
