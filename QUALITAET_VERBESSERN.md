# Qualität der OCR-Ergebnisse verbessern

## 🎯 Übersicht

Die Qualität der OCR-Ergebnisse hängt von mehreren Faktoren ab. Hier sind die wichtigsten Methoden zur Verbesserung.

---

## 1. 📝 Prompt-Optimierung (Einfachste Methode)

### Problem
Vage Fragen führen zu vagen Antworten.

### Lösung: Spezifische Fragen stellen

**❌ Schlecht:**
- "Was ist hier?"
- "Zeig mir die Maße"

**✅ Gut:**
- "Was ist der Außendurchmesser in Millimeter mit Toleranz?"
- "Liste alle Maße im Format: Name, Wert, Einheit, Toleranz auf"
- "Extrahiere die Stückliste als Tabelle mit Spalten: Position, Menge, Benennung, Sachnummer"

### Beispiele für optimierte Prompts:

```
# Für Maße
"Extrahiere alle Längenmaße mit folgenden Informationen:
- Maßwert (z.B. 35)
- Einheit (mm, cm, etc.)
- Toleranz falls vorhanden (±0,5)
- Position im Dokument
Liste sie in einer Tabelle auf."

# Für Teilenummern
"Finde alle Teilenummern im Format P/N: XXX oder ähnlich.
Gib für jede Nummer an:
- Die vollständige Nummer
- Zugehörige Beschreibung
- Menge falls angegeben"

# Für Materialien
"Welches Material wird verwendet?
Suche nach:
- Werkstoffnummer (z.B. 17Cr3)
- Materialnormen (DIN, ISO)
- Oberflächenbehandlung
- Härteangaben"
```

---

## 2. 🖼️ Bildqualität verbessern

### Mindestanforderungen:
- **Auflösung**: Mindestens 1500px Breite
- **Format**: JPG, PNG, oder PDF
- **Dateigröße**: Bis 100MB

### Tipps für bessere Scans:

1. **Hohe DPI-Einstellung**
   - Mindestens 300 DPI scannen
   - Für alte/schlecht lesbare Zeichnungen: 600 DPI

2. **Guter Kontrast**
   - Schwarze Linien auf weißem Hintergrund
   - Keine stark vergilbten Originale

3. **Scharfe Bilder**
   - Fokus korrekt einstellen
   - Keine Bewegungsunschärfe
   - Kamera sollte parallel zur Zeichnung sein

4. **Gute Beleuchtung**
   - Gleichmäßige Ausleuchtung
   - Keine Schatten oder Reflexionen
   - Tageslicht oder kaltweiße LED

### Automatisches Preprocessing

Das System wendet automatisch an:
- Kontrastverstärkung
- Schärfung
- Helligkeitsanpassung
- Hochskalierung bei kleinen Bildern

**Für sehr schlechte Qualität**: Fügen Sie `aggressive_preprocessing=true` hinzu (Coming Soon)

---

## 3. ⚙️ Model-Parameter anpassen

### Aktuelle Einstellungen (in `backend/ocr_service.py`):

```python
sampling_params = SamplingParams(
    temperature=0.0,        # Deterministisch (keine Zufälligkeit)
    max_tokens=8192,       # Maximale Antwortlänge
    logits_processors=[...] # Verhindert Wiederholungen
)
```

### Mögliche Optimierungen:

#### A) Längere Antworten erlauben
```python
max_tokens=16384  # Für sehr lange Stücklisten
```

#### B) Mehr Kontext verwenden
```python
# In _initialize_model()
max_model_len=16384  # Mehr Input-Token
```

#### C) Bessere Bildauflösung
```python
# In process_technical_drawing()
base_size=1280,    # Statt 1024
image_size=768,    # Statt 640
```

**⚠️ Achtung**: Höhere Werte = mehr GPU-Speicher & langsamere Verarbeitung

---

## 4. 🎨 Zeichnungstyp-spezifische Optimierung

### Für mechanische Zeichnungen:
```
"Analysiere diese mechanische Zeichnung.
Extrahiere:
1. Alle Hauptmaße (Längen, Durchmesser, Radien)
2. Toleranzen und Passungen (z.B. H7/g6)
3. Oberflächengüten (Ra, Rz Werte)
4. Werkstoffangaben
5. Wärmebehandlungen
Format als strukturierte Liste."
```

### Für Elektropläne:
```
"Analysiere diesen Schaltplan.
Identifiziere:
1. Bauteile mit Bezeichnern (R1, C5, etc.)
2. Bauteilwerte (10kΩ, 100µF, etc.)
3. Verbindungen zwischen Bauteilen
4. Spannungsangaben
Liste als Tabelle auf."
```

### Für Baupläne:
```
"Analysiere diesen Bauplan.
Extrahiere:
1. Raumbezeichnungen und Nummern
2. Flächen in m²
3. Wandstärken
4. Höhenangaben
5. Türen und Fenster mit Maßen
Strukturiere nach Geschossen."
```

---

## 5. 🔄 Mehrstufige Verarbeitung

### Strategie: Erst überblicken, dann detaillieren

**Schritt 1: Überblick**
```
"Gib einen Überblick über diese technische Zeichnung:
- Was für ein Bauteil wird dargestellt?
- Welche Ansichten sind vorhanden (Vorder-, Seiten-, Draufsicht)?
- Welche Informationen sind in den einzelnen Bereichen?"
```

**Schritt 2: Details**
```
"Konzentriere dich auf die Vorderansicht.
Extrahiere alle Maße in dieser Ansicht."
```

**Schritt 3: Spezifische Elemente**
```
"Extrahiere nur die Gewindemaße (M8, M12, etc.)
mit ihren Tiefen und Steigungen."
```

---

## 6. 🎯 Grounding (Bounding Boxes) nutzen

Das `<|grounding|>` Tag ist **essentiell** für visuelle Lokalisierung!

### Aktiviert automatisch:
- Bounding Boxes um erkannte Elemente
- Koordinaten im Response
- Visuelle Verifikation möglich

### Ohne grounding:
- Nur Text-Antworten
- Keine räumliche Information
- Schwerer zu verifizieren

**Aktueller Stand**: Wird automatisch in allen Fragen eingefügt ✅

---

## 7. 📊 Strukturierte Ausgabe erzwingen

### Markdown-Tabellen verlangen:

```
"Erstelle eine Markdown-Tabelle mit ALLEN Maßen:
| Bezeichnung | Wert | Einheit | Toleranz | Position |
|-------------|------|---------|----------|----------|
| Beispiel | 35 | mm | ±0,1 | Hauptlänge |

WICHTIG: Vervollständige die Tabelle mit ALLEN gefundenen Maßen!"
```

### JSON-Format (für Weiterverarbeitung):

```
"Extrahiere alle Teilenummern als JSON:
{
  \"parts\": [
    {
      \"number\": \"P/N-12345\",
      \"description\": \"Gehäuse\",
      \"quantity\": 1,
      \"material\": \"Aluminium\"
    }
  ]
}
Gib NICHTS außer dem JSON zurück!"
```

---

## 8. 🔍 Spezielle Symbole und Normen

### DIN/ISO-Normen referenzieren:

```
"Finde alle Normverweise (DIN, ISO, EN) in dieser Zeichnung.
Liste für jeden Verweis:
- Normbezeichnung (z.B. DIN 509)
- Kontext (wofür wird es verwendet)
- Parameter falls angegeben"
```

### Technische Symbole:

```
"Identifiziere alle technischen Symbole:
- Schweißsymbole
- Oberflächensymbole (Rauheitssymbole)
- Formtoleranzsymbole
- Maßpfeilrichtungen
Erkläre die Bedeutung jedes Symbols."
```

---

## 9. ⏱️ Performance vs. Qualität

### Schneller (niedriger Qualität):
```python
base_size=768
image_size=512
crop_mode=False
```

### Genauer (langsamer):
```python
base_size=1280
image_size=768
crop_mode=True
```

### Für Ihre Anwendung (Balance):
```python
base_size=1024  # Standard
image_size=640  # Standard
crop_mode=True  # Aktiviert für komplexe Zeichnungen
```

---

## 10. 🐛 Debugging und Validierung

### Prüfen Sie die Qualität:

1. **Vergleichen Sie mit Original**
   - Sind alle Maße erkannt?
   - Stimmen die Werte?
   - Sind Bounding Boxes an richtiger Stelle?

2. **Zweite Frage stellen**
   ```
   "Überprüfe deine vorherige Antwort.
   Hast du alle Maße in der Zeichnung gefunden?
   Kontrolliere besonders die Bereiche X und Y."
   ```

3. **Spezifische Nachfrage**
   ```
   "Du hast Maß A nicht erwähnt. Bitte ergänze!"
   ```

---

## 📝 Quick Reference: Beste Praktiken

### ✅ DO:
- Hochauflösende Bilder (>1500px)
- Spezifische, strukturierte Fragen
- `<|grounding|>` verwenden (passiert automatisch)
- Markdown/JSON-Format verlangen
- Mehrstufige Verarbeitung für komplexe Zeichnungen
- Ergebnisse validieren und nachfragen

### ❌ DON'T:
- Niedrige Auflösung (<800px)
- Vage Fragen ("was steht hier?")
- Erwartung, dass ALLES in einer Frage erkannt wird
- Unscharfe oder verwackelte Fotos
- Stark verschmutzte Originale

---

## 🚀 Geplante Verbesserungen

### In Entwicklung:
- [ ] Automatisches Preprocessing (Kontrast, Schärfe)
- [ ] Bildqualitäts-Analyse vor Verarbeitung
- [ ] Batch-Verarbeitung mehrerer Ansichten
- [ ] Template-basierte Extraktion für wiederkehrende Formate
- [ ] RAG-System für technische Normen
- [ ] Fine-Tuning auf spezifische Zeichnungstypen

---

## 💡 Beispiel-Workflow für optimale Qualität

```markdown
1. Bild hochladen (min. 1500px, scharf, guter Kontrast)

2. Erste Frage (Überblick):
   "Beschreibe diese technische Zeichnung:
   - Bauteiltyp
   - Ansichten
   - Wichtige Bereiche"

3. Zweite Frage (Hauptmaße):
   "Extrahiere alle Hauptmaße als Tabelle:
   | Bezeichnung | Wert | Einheit | Toleranz |"

4. Dritte Frage (Spezifisches):
   "Liste alle Gewindemaße mit Steigung auf"

5. Vierte Frage (Metadaten):
   "Extrahiere:
   - Zeichnungsnummer
   - Maßstab
   - Material
   - Datum/Revision"

6. Validierung:
   "Hast du alle Informationen im Schriftfeld erfasst?"
```

---

## 📞 Weitere Hilfe

Bei anhaltenden Qualitätsproblemen:
1. Bildqualität prüfen (siehe Abschnitt 2)
2. Prompt optimieren (siehe Abschnitt 1)
3. Parameter anpassen (siehe Abschnitt 3)
4. Mehrstufig verarbeiten (siehe Abschnitt 5)

**Hardware-Anforderungen beachten**:
- GPU: Mindestens 20GB VRAM
- CPU: Multicore für Preprocessing
- RAM: Mindestens 32GB empfohlen
