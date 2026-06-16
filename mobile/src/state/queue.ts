// Offline capture queue. When an upload fails (no connectivity), the photo is
// persisted to the app's document directory with its capture config; flush()
// retries the full createSession -> upload -> analyze chain and drops entries on
// success. Survives app restarts (manifest is a JSON file on disk).
import * as FileSystem from "expo-file-system";

import {
  analyzeCaptureSession,
  createCaptureSession,
  uploadCaptureImage,
  type CaptureSessionInput,
} from "@/api/capture";
import { getAccessToken } from "@/api/client";

const DIR = `${FileSystem.documentDirectory}capture_queue/`;
const MANIFEST = `${DIR}manifest.json`;

export interface QueueItem {
  id: string;
  config: CaptureSessionInput;
  file: string; // local file:// path inside DIR
  assetType: string;
  createdAt: string;
}

async function ensureDir(): Promise<void> {
  const info = await FileSystem.getInfoAsync(DIR);
  if (!info.exists) await FileSystem.makeDirectoryAsync(DIR, { intermediates: true });
}

async function readManifest(): Promise<QueueItem[]> {
  try {
    const txt = await FileSystem.readAsStringAsync(MANIFEST);
    return JSON.parse(txt) as QueueItem[];
  } catch {
    return [];
  }
}

async function writeManifest(items: QueueItem[]): Promise<void> {
  await ensureDir();
  await FileSystem.writeAsStringAsync(MANIFEST, JSON.stringify(items));
}

export async function enqueue(
  config: CaptureSessionInput,
  photoPath: string,
  assetType: string,
  createdAt: string
): Promise<void> {
  await ensureDir();
  const id = `${createdAt.replace(/[^0-9]/g, "")}-${Math.round(Number(createdAt) % 1e6) || 0}`;
  const dest = `${DIR}${id}.jpg`;
  const src = photoPath.startsWith("file://") ? photoPath : `file://${photoPath}`;
  await FileSystem.copyAsync({ from: src, to: dest });
  const items = await readManifest();
  items.push({ id, config, file: dest, assetType, createdAt });
  await writeManifest(items);
}

export async function pendingCount(): Promise<number> {
  return (await readManifest()).length;
}

/** Retry every queued capture. Returns how many were uploaded. Needs a token. */
export async function flush(): Promise<number> {
  if (!getAccessToken()) return 0;
  const items = await readManifest();
  if (items.length === 0) return 0;
  const remaining: QueueItem[] = [];
  let done = 0;
  for (const it of items) {
    try {
      const session = await createCaptureSession(it.config);
      await uploadCaptureImage(session.id, it.file, it.assetType, getAccessToken());
      await analyzeCaptureSession(session.id);
      await FileSystem.deleteAsync(it.file, { idempotent: true });
      done += 1;
    } catch {
      remaining.push(it); // keep for the next attempt
    }
  }
  await writeManifest(remaining);
  return done;
}
