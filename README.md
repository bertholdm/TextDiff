[GUI Plugin] TextDiff - Version 1.2.1 - 03-23-2023

A Calibre GUI plugin for finding text differences in two book formats.

Main features:
--------------
This plugin shows the differences between two selected book formatss. 
The formats are first converted to text format (even if the source format is already text) with Calibre's convert utility (https://manual.calibre-ebook.com/generated/en/ebook-convert.html).
If the conversion fails, the format has no text content (as scanned PDF files) or Calibre cannot find an appropriate conversion tool (as Microsoft wordconv).
Then the text files obtained this way are read into memory and possibly edited (removing blank lines and other changes as described under "Planned Features".
Then the compare is done with Python's DiffLib (https://docs.python.org/3/library/difflib.html).
The ratio gives a measure for the similarity of the two texts. 1.0 means the texts are identical, A value near 0.0 means, that the texts are complete different. 
The last thing may also occur, when the source format has no text content (as scanned PDF files). Then one should create a new book format (text) with an OCR process.

The detailed workflow is as follows:
1. Select a book with at least two formats or two books with at least one format each to compare.
2. Chose two formats.
3. Chose the output format and other comparison options.
4. Hit "Compare".
5. The formats are converted and compared and the output is displayed in the output window. A ratio is also computed and displayed.
6. If wished, copy the comparison output to the clipboard and/or save it to a file and/or save it as book with an suitable format (HTML or text).

If you want to compare other formats, repeat step 1 and hit the "Refresh formats"  button. Then repeat steps 2 - 5.
The "Compare"-Dialog is modeless, what permits to move it around and touch the Calibre screen.

Planned Features:
-----------------
- Remove soft hyphens before conversion.
- Custom characters to ignore ("char junk", e. g. "" vs. »«). 

Limitations:
------------
- The converted formats are stored as strings in memory, so large formats may run out of memory. 

Version History:
----------------
Version 1.2.1 - 03-23-2023
- Switch between context line processing by plugin or by Difflib
Version 1.2.0 - 03-22-2023
- Abort compare with message if convert has no result.
- Hide identical lines, but with the option to display a number of context lines. Closes enhancement request #1.)
Version 1.1.2 - 02-03-2023
- Adding double-quotes for the --sr1-search value: --sr1-search "(?m)^\s*$"
  to avoid "syntax error near unexpected token \`('" on Mac. (Thanks to irinel-dan.)
Version 1.1.1 - 11-30-2022
- Handle save file dialog with no user path/file choice.
Version 1.1.0 - 11-26-2022
- Changed tool button behavior: show compare dialog when icon clicked, show menu when arrow clicked (thanks to Comfy.n)
- Inverting HTML/CSS back colors (highlighting diffs) in dark mode (thanks to Comfy.n and Kovidgoyal)
Version 1.0.0 11-20-2022
- Initial release.

Installation:
-------------
Download the attached zip file and install the plugin as described in the plugins thread on mobileread.
You need to add the calibre path to your $PATH variable.

To report Bugs and suggestions:
-------------------------------
If you find any issues or have suggestions, please report them on GitHub or in the MobileRead Forum.

---

[GUI-Plugin] TextDiff - Version 1.2.1 - 03-23-2023

Ein Calibre GUI-Plugin zum Finden von Textunterschieden in zwei Buchformaten.

Haupteigenschaften:
-------------------
Dieses Plugin zeigt die Unterschiede zwischen zwei ausgewählten Buchformaten.
Die Formate wurden zunächst in Textformat konvertiert (auch wenn das Ausgangsformat bereits Text ist).
Wenn die Konvertierung fehlschlägt, kann das daran liegen, dass das Format keinen text enthält (wie z. B. bei gescannten PDF-Dateien) oder Calibre ein Konvertierungstool nicht finden kann (wie z. B. Microsoft wordconv).
Dann werden die Textdateien in den Speicher eingelesen und eventuell manipuliert (Leerzeilen und Ähnliches entfernen, wie unter "Geplante Features" beschrieben).
mit dem Konvertierungsprogramm von Calibre (https://manual.calibre-ebook.com/generated/en/ebook-convert.html).
Dann wird der Vergleich mit Pythons DiffLib (https://docs.python.org/3/library/difflib.html) durchgeführt.
Das Verhältnis gibt ein Maß für die Ähnlichkeit der beiden Texte an. 1,0 bedeutet, dass die Texte identisch sind, ein Wert nahe 0,0 bedeutet, dass die Texte völlig unterschiedlich sind.
Letzteres kann auch passieren, wenn das Quellformat keinen Textinhalt hat (wie gescannte PDF-Dateien). Dann sollte man ein neues Buch-Format (Text) mit einem OCR-Prozess erzeugen.

Der detaillierte Arbeitsablauf ist wie folgt:
1. Wählen Sie ein Buch mit mindestens zwei Formaten zum Vergleichen oder zwei Bücher mit jeweils mindestens einem Format aus.
2. Wählen Sie zwei Formate aus.
3. Wählen Sie das Ausgabeformat und andere Vergleichsoptionen.
4. Klicken Sie auf "Vergleichen".
5. Die Formate werden konvertiert und verglichen und die Ausgabe wird im Ausgabefenster angezeigt. Ein Verhältnis wird ebenfalls berechnet und angezeigt.
6. Falls gewünscht, kopieren Sie die Vergleichsausgabe in die Zwischenablage und/oder speichern Sie sie in einer Datei und/oder speichern Sie sie als Buch in einem geeigneten Format (HTML oder Text).

Wenn Sie andere Formate vergleichen möchten, wiederholen Sie Schritt 1 und klicken Sie auf die Schaltfläche "Formate aktualisieren".
Der "Vergleichen"-Dialog ist moduslos, was es erlaubt, ihn zu verschieben, und den darunterliegenden Calibre-Bildschirm zu steuern.

Geplante Funktionen:
--------------------
- Weiche Bindestriche vor der Konvertierung entfernen.
- Benutzerdefinierte Zeichen, die ignoriert werden sollen ("Zeichenmüll", z. B. "" vs. »«).

Einschränkungen:
----------------
- Die konvertierten Formate werden als Strings im Speicher gehalten, daher kann es bei großen Formaten zu Speichermangel kommen. 

Versionsgeschichte:
-------------------
Version 1.2.1 - 03-23-2023
- Wahl zwischen Kontext-Verarbeitung durch Plugin oder Difflib.
Version 1.2.0 - 03-22-2023
- Abbruch mit Fehlermeldung, wenn mindestens eine Konvertierung in das Textformat fehlschlägt.
- Verbergen identischer Zeilen mit der Option, n Kontext-Zeilen darzustellen.
Version 1.1.2 - 02-03-2023
- Doppelte Anführungszeichen hinzugefügt für den Wert des Parameter --sr1-search value: --sr1-search "(?m)^\s*$"
  zur Vermeidung der Meldung "syntax error near unexpected token \`('" auf dem Mac. (Danke an irinel-dan.)
Version 1.1.1 - 11-30-2022
- Abfangen im "Datei speichern"-Dialog, dass kein Format ausgewählt.
Version 1.1.0 - 26.11.2022
- Geändertes Verhalten der Werkzeugschaltfläche: Vergleichsdialog anzeigen, wenn auf das Symbol geklickt wird, Menü anzeigen, wenn auf den Pfeil geklickt wird (Dank an Comfy.n)
- Invertieren von HTML/CSS-Hintergrundfarben (Hervorheben von Unterschieden) im Dunkelmodus (Dank an Comfy.n und Kovidgoyal)
Version 1.0.0 20.11.2022
Erstveröffentlichung.

Installation:
-------------
Laden Sie die angehängte ZIP-Datei herunter und installieren Sie das Plugin wie im Thread "Einführung in Plugins" auf mobileread beschrieben.
Vergessen Sie nicht, Calibre in Ihre PATH-Variable aufzunehmen.

So melden Sie Fehler und Vorschläge:
------------------------------------
Wenn Sie Probleme finden oder Vorschläge haben, melden Sie diese bitte auf GitHub oder im MobileRead-Forum.
