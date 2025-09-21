[GUI Plugin] TextDiff - Version 1.3.0 - 09-21-2025

A Calibre GUI plugin for finding text differences in two book formats.

Main features:
--------------
This plugin shows the differences between two selected book formats. 
The formats are first converted to text format (even if the source format is already text) with Calibre's convert utility (https://manual.calibre-ebook.com/generated/en/ebook-convert.html).
If the conversion fails, the format has no text content (as scanned PDF files) or Calibre cannot find an appropriate conversion tool (as Microsoft wordconv).
Then the text files obtained this way are read into memory and possibly edited (removing blank lines, soft hyphens, ...).
Then the compare is done with Python's DiffLib (https://docs.python.org/3/library/difflib.html).
The ratio gives a measure for the similarity of the two texts. 1.0 means the texts are identical, a value near 0.0 means that the texts are complete different. 
The last thing may also occur, when the source format has no text content (as scanned PDF files). Then one should create a new book format (text) with an extra OCR process.

The detailed workflow is as follows:
1. Select a book with at least two formats or two books with at least one format each to compare.
2. Chose two formats.
3. Chose the output format and other comparison options.
4. Hit "Compare".
5. The formats are converted and compared and the result is displayed in the output window. A ratio is also computed and displayed.
6. If wished, copy the comparison output to the clipboard and/or save it to a file and/or save it as book with an suitable format (HTML or text).

If you want to compare other formats, repeat step 1 and hit the "Refresh formats"  button. Then repeat steps 2 - 5.
The "Compare"-Dialog is modeless, what permits to move it around and touch the Calibre screen.

Limitations:
------------
- The converted formats are stored as strings in memory, so extreme large formats may run out of memory. 

Version History:
----------------
Version 1.3.0 - 09-21-2025
- Spanish translation (thanks to dunhill)
- removing soft hyphens in input text
Version 1.2.6 - 10-27-2024
- Some more character replacings.
Version 1.2.5 - 04-23-2024
- Explanation for save diff result as book added.
Version 1.2.4 - 01-07-2024
- Fixing an typo in version 1.2.3 (causes an error, when selecting other output types than "HTML"; thanks to Zillion_).
Version 1.2.3 - 12-28-2023
- Check wether the pdf format is readable ((encrypted pdf's, pdf's with no text layer).
- Substitute different quotes and dashes characters with standard characters before diff (optional).
- Debug print optional.
Version 1.2.2 - 06-29-2023
- Disable buttons to save diff result until a result is generated (Thanks to Robert1a)
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
