# Beatjie — MekoTools-Auslieferung

Eine kleine Schlagzeug-Maschine im Browser: vier Klangsätze mit je acht Stimmen,
sechzehn Schritte, Tempo, Effekte je Klang und ein Muster, das sich als Link
weitergeben lässt. Kein Konto, keine Anmeldung, kein Ton verlässt das Gerät.

* **Läuft hier:** https://beatjie.mekotools.de
* **Original:** https://github.com/dindles/beatjie (Autor: Dindles), CC BY-NC-SA 4.0
* **Fester Stand:** `3e7aea257bf6ecc378067f195a959b3dbbf74035` (12. Juni 2026)

## Was diese Fassung ändert

Die Auslieferung entsteht im Bau aus dem festgeschriebenen Archiv-Abzug des
Originals. `scripts/klange-setzen.py` prüft dabei jeden Eingriff gegen den
Quelltext und bricht ab, wenn etwas nicht mehr passt — lieber kein Abbild als
ein stillschweigend verändertes.

1. **Alle 32 Klänge ersetzt.** Das Original nennt für keine einzige Datei eine
   Herkunft; Klänge ohne belegbare Herkunft geben wir nicht weiter. An ihre
   Stelle treten freie Aufnahmen unter CC0 1.0:

   - **Stargate Sample Pack** (Stargate DAW) — 6 Klänge
   - **Versilian Community Sample Library (VCSL)** — 6 Klänge
   - **VSCO 2 Community Edition** — 4 Klänge
   - **Freesound**, Aufnahmen einzelner Urheber — 16 Klänge (Stimmen, Geräusche,
     Natur)

   Jeder Klang ist einzeln belegt: `klang/manifest.json` nennt Ziel, Rolle,
   Quelle, Adresse und Urheber; im Werkzeug selbst trägt jede Datei ihre Herkunft
   in den ID3-Feldern (Urheber, Werk, Lizenz, Ursprungsdatei).
   Format: MP3, 44,1 kHz, mono, 192 kbit/s, Spitze rund −1,5 dBFS,
   0,13–1,23 s je Klang.

2. **Besuchsstatistik entfernt.** Das Original lädt ein Zählskript von
   `goatcounter.com`. Es ist gestrichen; das Werkzeug ruft zur Laufzeit keine
   fremde Adresse auf (im Betrieb nachgeprüft: alle Anfragen an die eigene
   Adresse, 0 fremde Wirte).

3. **Adressangaben** in `src/app.html` zeigen auf `beatjie.mekotools.de`.

4. **Hinweis im Startbild**, dass es sich um eine angepasste Fassung für
   MekoTools handelt. Der Urheberverweis des Originals bleibt erhalten.

Näheres zu Rechten und Herkunft: [NOTICE](NOTICE). Für den Einsatz im Unterricht:
[docs/anleitung.md](docs/anleitung.md), [docs/didaktik.md](docs/didaktik.md),
[docs/unterrichtsentwurf.md](docs/unterrichtsentwurf.md).

## Bauen

Gebaut wird ausschließlich in der CI (GitHub Actions, `.github/workflows/abbild-bauen.yml`),
auf dem Zielrechner wird nichts gebaut. Der Bauablauf

* holt den Quelltext-Abzug des festgeschriebenen Stands,
* setzt die Klänge aus `klang/` mit `scripts/klange-setzen.py`,
* entfernt die Zählung und setzt die Adressen,
* baut die Seite mit pnpm und legt sie hinter nginx (schlankes `nginx:alpine-slim`),
* kontrolliert sich selbst: Startseite vorhanden, **genau 32** Klangdateien,
  keine Spur von `goatcounter`, `nginx -t` muss durchgehen.

Ergebnis: `ghcr.io/mekotools/beatjie:latest`.

## Bedienung in Kurzform

* **1–4** wählt den Klangsatz, **Q W E R / A S D F** wählen und spielen die acht
  Klänge des Satzes, **P** schaltet die Vorschau um.
* **Z** stumm, **X** Tonhöhe (C2, E2, F2, C1), **C** Echo, **V** Hall — jeweils
  für den ausgewählten Klang; **B** Hochpass, **N** Verzerrung für den ganzen Satz.
* **Leertaste** startet und stoppt, **Pfeil auf/ab** ändert das Tempo (60–200).
* Der Schalter **demo** zeigt das Beispielvideo des Autors.
* Das Muster steckt im Link: wer den Link öffnet, hört dasselbe Muster. Es wird
  nichts gespeichert und nichts gesendet.
