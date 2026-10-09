#!/usr/bin/env python3
"""Setzt die freien Klänge in den festgeschriebenen Quelltext-Abzug von beatjie ein und
entfernt die Fremdaufrufe.  Jede Abweichung bricht ab — lieber kein Abbild als ein falsches.

Aufruf: klange-setzen.py <quelle> <klangverzeichnis>
"""
import json
import re
import sys
from pathlib import Path

NOTIZ = ("Angepasste Fassung für MekoTools: alle 32 Klänge wurden durch freie Aufnahmen "
         "(CC0) ersetzt, die Zählung im Netz entfernt. Kein Ton verlässt das Gerät.")
NOTIZ_KURZ = ("Angepasste Fassung für MekoTools: Klänge durch freie Aufnahmen (CC0) ersetzt, "
              "keine fremden Aufrufe.")

ANZ = 32


def anker(bedingung, text):
    if not bedingung:
        sys.exit(f"ANKER: {text}")


def wellenformat(datei):
    """MP3-Kopfdaten ohne Fremdwerkzeug lesen: Abtastrate, Kanäle, ID3 vorhanden"""
    d = datei.read_bytes()
    id3 = d[:3] == b"ID3"
    i = 0
    if id3 and len(d) > 10:
        # ID3v2-Kopf ist "synchronisationssicher": je Byte nur 7 Bit.
        groesse = ((d[6] & 0x7F) << 21) | ((d[7] & 0x7F) << 14) | ((d[8] & 0x7F) << 7) | (d[9] & 0x7F)
        i = 10 + groesse
    while i < len(d) - 4:
        if d[i] == 0xFF and (d[i + 1] & 0xE0) == 0xE0:
            b1, b2, b3 = d[i + 1], d[i + 2], d[i + 3]
            version = (b1 >> 3) & 0x03          # 3 = MPEG1
            schicht = (b1 >> 1) & 0x03          # 1 = Layer III
            bitraten = [(0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320),
                        (0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384),
                        (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320),
                        (0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384)][1]
            raten = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}
            sr = raten.get(version, [0])[(b2 >> 2) & 0x03]
            kanaele = 1 if ((b3 >> 6) & 0x03) == 3 else 2
            kbit = bitraten[(b2 >> 4) & 0x0F]
            return {"id3": id3, "mpeg": version, "layer": schicht, "rate": sr,
                    "kanaele": kanaele, "kbit": kbit}
        i += 1
    return {"id3": id3, "mpeg": 0, "layer": 0, "rate": 0, "kanaele": 0, "kbit": 0}


def main():
    quelle, klang = Path(sys.argv[1]), Path(sys.argv[2])

    # 1. Gestalt des Abzugs
    paket = quelle / "package.json"
    anker(paket.is_file(), "package.json fehlt")
    pj = json.loads(paket.read_text())
    anker("build" in pj.get("scripts", {}), "Bauschritt build fehlt in package.json")
    daten = quelle / "src/lib/data/audio-packs.ts"
    anker(daten.is_file(), "audio-packs.ts fehlt")
    text = daten.read_text()
    anker(text.count("url:") == ANZ, f"audio-packs.ts nennt {text.count('url:')} statt {ANZ} Klänge")
    app = quelle / "src/app.html"
    anker(app.is_file(), "src/app.html fehlt")
    intro = quelle / "src/lib/components/intro-audio-context-prompt.svelte"
    anker(intro.is_file(), "Intro-Baustein fehlt")

    # 2. Plan und Zieldateien
    plan = json.loads((klang / "manifest.json").read_text())
    anker(len(plan) == ANZ, f"Manifest hat {len(plan)} statt {ANZ} Einträge")
    for e in plan:
        ziel = quelle / "static/audio" / e["ziel"]
        anker(ziel.is_file(), f"Zieldatei fehlt: {ziel.relative_to(quelle)}")
    for e in plan:
        quelle_datei = klang / e["ziel"]
        anker(quelle_datei.is_file(), f"neuer Klang fehlt: {e['ziel']}")
        (quelle / "static/audio" / e["ziel"]).write_bytes(quelle_datei.read_bytes())

    # 3. genau ANZ Klangdateien, Namen wie im Plan
    dateien = sorted(p.relative_to(quelle / "static/audio").as_posix()
                     for p in (quelle / "static/audio").rglob("*.mp3"))
    anker(len(dateien) == ANZ, f"{len(dateien)} Klangdateien statt {ANZ}")
    anker(dateien == sorted(e["ziel"] for e in plan), "Dateiliste weicht vom Plan ab")

    # 4. Format der neuen Dateien
    for e in plan:
        f = wellenformat(quelle / "static/audio" / e["ziel"])
        anker(f["id3"], f"{e['ziel']}: keine ID3-Kennung (Herkunft fehlt)")
        anker(f["mpeg"] == 3 and f["layer"] == 1, f"{e['ziel']}: kein MPEG-1 Layer III")
        anker(f["rate"] == 44100, f"{e['ziel']}: {f['rate']} Hz statt 44100")
        anker(f["kanaele"] == 1, f"{e['ziel']}: {f['kanaele']} Kanäle statt 1")
    print(f"Formprüfung: {ANZ} Dateien, 44,1 kHz, mono, ID3 vorhanden")

    # 5. Zählung im Netz entfernen (Fremdaufruf)
    a = app.read_text()
    block = re.search(r"\n\s*<script\s+data-goatcounter[\s\S]*?</script>", a)
    if block is not None:
        a = a[:block.start()] + "\n" + a[block.end():]
        print("src/app.html: Zählung entfernt")
    elif "goatcounter" in a:
        sys.exit("ANKER: Zähl-Baustein in unerwarteter Form")
    else:
        print("src/app.html: Zählung war schon entfernt (zweiter Lauf)")
    anker("goatcounter" not in a, "goatcounter noch vorhanden")

    # 6. Adressangaben auf unsere Auslieferung und ehrliche Beschreibung
    a = a.replace("https://dindles.net/beatjie", "https://beatjie.mekotools.de")
    a = a.replace("https://dindles.net/beatjie/og-image.png",
                  "https://beatjie.mekotools.de/og-image.png")
    a = a.replace("Create and share drum beats in your browser.",
                  "Kleine Schlagzeug-Maschine im Browser (angepasste Fassung für MekoTools).")
    anker("dindles.net" not in a, "fremde Adresse noch in app.html")
    app.write_text(a)
    print("src/app.html: Zählung entfernt, Adressen auf beatjie.mekotools.de gesetzt")

    # 7. Kennzeichnung der Änderung sichtbar in der Oberfläche
    i = intro.read_text()
    anker("dindles-link" in i, "Ankerstelle (Urheberverweis) im Intro nicht gefunden")
    if NOTIZ not in i:
        stelle = i.index("dindles-link")
        zeilenanfang = i.rindex("\n", 0, stelle)
        einrueckung = " " * (len(i[:zeilenanfang].split("\n")[-1]) + 2)
        i = (i[:zeilenanfang] + "\n" + einrueckung +
             '<p class="text-small mt-hinweis">' + NOTIZ + "</p>" + i[zeilenanfang:])
        intro.write_text(i)
        print("Intro: MekoTools-Hinweis ergänzt")
    else:
        print("Intro: MekoTools-Hinweis war schon vorhanden")

    # 7b. Derselbe Hinweis dauerhaft in der Einstellungsleiste: der Startbild-
    # schirm verschwindet nach der Ton-Bestätigung, die Kennzeichnung als
    # geänderte Fassung muss aber auffindbar bleiben.
    einst = quelle / "src/lib/components/app-settings.svelte"
    anker(einst.is_file(), "app-settings.svelte fehlt")
    e = einst.read_text()
    if NOTIZ_KURZ not in e:
        stelle = "</div>\n\n<style>"
        anker(stelle in e, "Ankerstelle in app-settings.svelte nicht gefunden")
        e = e.replace(stelle,
                      '</div>\n\n<p class="mt-hinweis">' + NOTIZ_KURZ + "</p>\n\n<style>", 1)
        regel = "  .mt-hinweis {\n    text-align: center;\n    font-size: 0.65rem;\n" \
                "    opacity: 0.75;\n    margin: 0.15rem 0 0;\n  }\n"
        anker("</style>" in e, "kein Stilblock in app-settings.svelte")
        e = e.replace("</style>", regel + "</style>", 1)
        einst.write_text(e)
        print("Einstellungen: dauerhafter MekoTools-Hinweis ergänzt")
    else:
        print("Einstellungen: Hinweis war schon vorhanden")


if __name__ == "__main__":
    main()
