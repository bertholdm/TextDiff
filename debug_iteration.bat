rem At a high level, developing and testing changes to a user interface plugin requires these steps:
rem Create/Update Plugin
rem Zip the plugin, replacing the original file
rem Restart Calibre
rem Test, Rinse & Repeat

rem Thankfully all that logic can be done while Calibre is running with a single command line:
calibre -s; sleep 4s; zip -R /path/to/plugin/zip/file.zip *; calibre