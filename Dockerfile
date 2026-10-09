# beatjie — MekoTools-Auslieferung als fertiges Abbild
#
# Gebaut wird aus dem festgeschriebenen Quelltext-Abzug des Originals (FASSUNG
# unten). Geändert wird nur, was geändert werden muss:
#   * Die 32 Klangdateien: das Original nennt für keine einzige Datei eine
#     Herkunft (weder Kennzeichnung in der Datei noch Angabe im Werkzeug).
#     Klänge ohne belegbare Herkunft geben wir nicht weiter. An ihre Stelle
#     treten 32 freie Aufnahmen (CC0), siehe klang/ und NOTICE;
#     scripts/klange-setzen.py prüft für jede Datei den Anker und bricht bei
#     Abweichung ab.
#   * Die Zählung im Netz (goatcounter) wird entfernt — zur Laufzeit ruft das
#     Werkzeug keine fremde Adresse auf.
#   * Die Adressangaben in src/app.html zeigen auf unsere Auslieferung.
#   * Im Startbild steht ein Hinweis, dass es sich um eine angepasste Fassung
#     für MekoTools handelt (Auflage der Lizenz CC BY-NC-SA 4.0).
#
# Sonst bleibt das Werkzeug, wie es ist: keine Anmeldung, kein fremder Server.
#
# Die Grundabbilder sind austauschbar: Docker Hub drosselt anonyme Abrufe von
# geteilten Bauservern (HTTP 429). Der Bauablauf versucht es erst amtlich und
# bei Fehlschlag über den öffentlichen Spiegel (siehe .github/workflows).
ARG BASIS_NODE=node:24-bookworm
ARG BASIS_NGINX=nginx:alpine-slim

FROM ${BASIS_NODE} AS bau

# Festgeschriebener Stand: 3e7aea257bf6ecc378067f195a959b3dbbf74035 (2026-06-12).
ARG QUELLE=https://github.com/dindles/beatjie/archive/3e7aea257bf6ecc378067f195a959b3dbbf74035.tar.gz
ARG FASSUNG=3e7aea257bf6ecc378067f195a959b3dbbf74035
# pnpm in einer festen Fassung; die Sperrdatei des Originals gehört dazu.
ARG PNPM=10.30.3

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl python3 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /quelle
RUN curl -fsSL "$QUELLE" | tar xz --strip-components=1 \
 && test -f package.json && test -f src/lib/data/audio-packs.ts \
 && test "$(ls static/audio/*/*.mp3 | wc -l)" = "32"

# Eigene Klänge setzen — mit Ankerprüfung (bricht bei Abweichung ab).
COPY klang /klang
COPY scripts/klange-setzen.py /klange-setzen.py
RUN python3 /klange-setzen.py /quelle /klang

RUN npm install -g pnpm@${PNPM} \
 && pnpm install --frozen-lockfile

# Bauen und die Auslieferung selbst kontrollieren: Startseite, Klänge, Zählung.
RUN pnpm run build \
 && test -s build/index.html \
 && test -s build/audio/0/0_kick-909.mp3 \
 && test "$(ls build/audio/*/*.mp3 | wc -l)" = "32" \
 && ! grep -rq "goatcounter" build/ \
 && echo "--- Buendelgroesse:" && du -sh build \
 && echo "--- Klangdateien:" && ls build/audio/*/*.mp3 | wc -l

FROM ${BASIS_NGINX}
COPY --from=bau /quelle/build/ /usr/share/nginx/html/
COPY config/default.conf /etc/nginx/conf.d/default.conf
# Selbstkontrolle: eine fehlerhafte Konfiguration soll den Bau scheitern lassen
# und nicht erst im Betrieb zu einem Neustart-Kreis führen.
RUN nginx -t
EXPOSE 80
