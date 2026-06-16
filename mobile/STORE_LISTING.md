# App Store — Solidità 4.0 (capture)

Submission metadata + checklist. Original content. The iOS app is the controlled
**capture** companion to the Solidità 4.0 web platform; accounts and billing live
on the web (no in-app purchase), so Apple IAP is not required.

## App identity

- Name: **Solidità 4.0**
- Subtitle: *Acquisizione solidità colore* (≤30 chars)
- Bundle ID: `com.solidita.app`
- Category: Business (secondary: Productivity)
- Age rating: 4+

## Description (draft)

Solidità 4.0 è il companion di acquisizione del sistema di imaging digitale per la
**pre-valutazione assistita della solidità colore** dei tessuti e del cuoio.
L'operatore fotografa la striscia multifibra in modalità controllata
(esposizione, bilanciamento del bianco e fuoco bloccati) dentro la light box, con
scala grigia di riferimento; l'app guida lo scatto, blocca le catture non idonee
e invia l'immagine alla piattaforma per l'analisi ΔE / grado scala grigia.

Funziona con un account Solidità 4.0 esistente. Richiede il kit (dima, light box,
scala grigia/piastrina certificate). Non è uno spettrofotometro e non sostituisce
un laboratorio accreditato: è uno strumento di imaging digitale validabile.

## Keywords

solidità colore, tessile, cuoio, controllo qualità, ISO 105, AATCC, multifibra,
laboratorio, delta E, colour fastness

## Privacy (nutrition label)

- **Dati raccolti**: foto della prova (funzionalità app), identificativo utente
  (account). Nessun tracciamento, nessuna pubblicità, nessun data broker.
- Privacy manifest in `app.json` (`ios.privacyManifests`).
- Privacy Policy URL: `<https://…>` (pubblicare la policy GDPR da `docs/legal/`).
- Account deletion: supportato lato piattaforma (endpoint GDPR delete) — linkare
  nelle note.

## Pagamenti / IAP

Nessun acquisto in-app. Gli abbonamenti (Trace / Vision Pro) sono gestiti via
contratto B2B sul portale web; l'app non vende né sblocca contenuti a pagamento,
quindi NON usa StoreKit/IAP. (Evita il requisito IAP e i relativi rigetti.)

## Note per la review Apple (App Review Information)

- L'app richiede login: fornire un **account demo** funzionante (email + password)
  + un backend di test raggiungibile (`EXPO_PUBLIC_API_BASE`).
- La fotocamera è necessaria per la funzione principale (acquisizione striscia);
  in simulatore la camera non è disponibile → testare su device reale.
- Spiegare che è uno strumento B2B per laboratori tessili (kit hardware), non
  rivolto al consumatore generico.

## Asset richiesti

- Icona 1024×1024 (`assets/icon.png` — placeholder da sostituire con il logo).
- Screenshot per i formati iPhone richiesti (6.7" e 6.5"): Login, Selezione prova,
  Acquisizione guidata, Esito.

## Checklist submission

- [ ] Apple Developer Program attivo (99 USD/anno).
- [ ] Bundle ID + certificati + provisioning (gestiti da `expo run:ios` / EAS).
- [ ] Icona 1024 + screenshot caricati.
- [ ] Privacy Policy URL pubblico + nutrition label compilata.
- [ ] Account demo + backend di test per la review.
- [ ] Build caricata (Xcode/Transporter o EAS Submit) → TestFlight → review.
- [ ] Posizionamento conforme (no "spettrofotometro"/"certifica ISO").
