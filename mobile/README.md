# Solidità 4.0 — Mobile (iOS capture)

Expo + React Native + TypeScript, iOS-first. The portal (web) does management; the
**native app is the metrology-grade CAPTURE module** for iPhone 16 Pro: it locks
exposure / white-balance / focus and disables HDR so every shot is acquired under
identical, repeatable conditions — controls Safari/getUserMedia cannot give.

## Why native (not just the web app)

A browser cannot lock AE/AWB/AF, select RAW/full-resolution formats, or read the
torch/sensors. For repeatable colour-fastness imaging that matters: the same
strip must read the same way every time. The web app is fine for management and
demo/pre-evaluation; accreditable acquisition needs this native path.

## What's wired (scaffold)

- `react-native-vision-camera` v4 — manual exposure/focus lock, `photoHdr: false`,
  `qualityPrioritization: "quality"`, max photo resolution (`app.json` has the
  camera permission + config plugin).
- `src/camera/CameraCaptureScreen.tsx` — guided overlay, capture gates (real tilt
  from `expo-sensors` DeviceMotion; blur/exposure are frame-processor stubs), and
  the full flow: createCaptureSession → upload photo → analyze (backend).
- `src/api/capture.ts` — capture-session / upload (multipart) / analyze, matching
  `/api/v1/capture-sessions`. Passes `has_inframe_grey_scale` + `strict_quality`.
- Capture-gate logic stays pure in `src/state/captureStore.ts`.

## Run (needs a dev build — vision-camera is native, not Expo Go)

```bash
cd mobile
npm install
npm run prebuild        # expo prebuild -p ios (generates the iOS project)
npm run ios             # expo run:ios — Xcode + a device/simulator
# set the API base:
EXPO_PUBLIC_API_BASE=https://<backend-url> npm run ios
npm run typecheck       # after npm install (vision-camera types come from node_modules)
```

> `npm run typecheck` only resolves the camera/sensor types after `npm install`
> (the deps are declared in package.json but not vendored).

## Done

- **Login + session**: `src/api/auth.ts` (login → token in `expo-secure-store`,
  `restoreSession` on launch, logout) + real `LoginScreen`.
- **Job-selection flow**: `src/screens/JobSelectScreen.tsx` fetches jobs / batches /
  methods / grey-scale references and builds the real `CaptureSessionInput` config
  (job, batch, method, reference, in-frame grey-scale + strict toggles), passed to
  `CameraCaptureScreen`. Flow: Login → Home → Selezione prova → Acquisizione → Esito.
- **Offline queue**: `src/state/queue.ts` — failed uploads persist to the document
  dir (`expo-file-system`) with their config; `flush()` retries on app launch.
  Capture screen shows "Salvato in coda offline" when offline.
- **App Store readiness**: `app.json` privacy manifest + camera usage + bundle id;
  `STORE_LISTING.md` (metadata, privacy nutrition, no-IAP rationale, review notes,
  submission checklist).

## TODO before field use

- Frame processor (worklet) for real blur/exposure scoring → feed the gates
  (today tilt is real; blur/exposure are stubbed high).
- ArUco/marker detection for geometry coherence (pairs with backend homography).
- App icon 1024 + screenshots; Apple Developer account → TestFlight → submit.

Hardware: iPhone 16 Pro+ recommended; 15 Pro/Pro Max with calibration. Non-Pro
devices: consultation/barcode only, NOT Vision acquisition. Physical dima +
lightbox + ISO grey scale required for accreditable capture.
