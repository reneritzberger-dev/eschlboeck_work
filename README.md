# Baugruppen-Schwerpunkt

Python-Web-App zum Laden von STEP-Dateien, Positionieren über X/Y/Z und Berechnen des gemeinsamen Massenschwerpunkts. Interaktive 3D-Ansicht mit rotem Schwerpunktmarker.

## Einrichtung und Start

Python 3.12 unter Linux:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

Die Bedienung erfolgt im Browser über den Streamlit-Server. Es werden keine externen API-Schlüssel oder Datenbanken benötigt. Hochgeladene Geometrie wird auf dem App-Server verarbeitet und im Sitzungscache gehalten. Nur vertrauenswürdige CAD-Dateien verwenden; komplexe Modelle können viel Speicher und Rechenzeit benötigen.

## Berechnung

STEP-Einheiten werden durch Open CASCADE nach mm konvertiert. X/Y/Z sind Verschiebungen relativ zum ursprünglichen Dateikoordinatensystem, keine absoluten Schwerpunktkoordinaten. Masse = Volumen × Dichte. Der Gesamtschwerpunkt ist das mit den Massen gewichtete Mittel der verschobenen Bauteilschwerpunkte.

Standarddichte: Stahl, 7850 kg/m³; für jedes Modell editierbar. Mehrere Volumenkörper in einer Datei teilen sich eine Dichte und werden gemeinsam verschoben. Überlappungen werden nicht abgezogen. Es werden geschlossene, gültige Volumenkörper benötigt; Flächenmodelle werden abgewiesen. Drehungen, Materialerkennung und das Speichern von Baugruppen sind derzeit nicht implementiert.

## Tests

```sh
.venv/bin/python -m pytest -q
```

Die Tests erzeugen einen echten STEP-Quader und prüfen Import, Volumen, Schwerpunkt sowie eine versetzte Baugruppe mit unterschiedlichen Dichten.
