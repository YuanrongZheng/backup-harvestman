rem Batch file for creating py2exe executable for Harvestman
@echo off
python install.py py2exe -O2 --packages=encodings --force-imports encodings
