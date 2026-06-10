# Solidità 4.0 — Mobile (skeleton)

Expo + React Native + TypeScript. iOS-first. **Placeholder** (Sprint 6 builds the
real guided-capture flow with native camera/sensor modules, barcode scanning,
secure storage, offline encrypted queue).

```bash
cd mobile
npm install
npm run ios        # requires Xcode + Expo
npm run typecheck
```

Screens: Login → Department selector → Barcode scan → Workflow → Guided capture →
Upload → Result. Capture-gate logic lives in `src/state/captureStore.ts`.

Hardware: iPhone 16 Pro+ recommended; 15 Pro/Pro Max with calibration. Non-Pro
devices: consultation/barcode only, NOT Vision acquisition.
