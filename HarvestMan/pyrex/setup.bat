@echo off
rem setup file for building Pyrex extension modules
rem set the environment variable 'MODULE' to the name of the
rem pyrex module you want to build before using this.
rem This file should be used on a Windows box.
python setup.py build_ext --inplace