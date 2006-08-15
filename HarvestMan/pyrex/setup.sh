#! /bin/bash

# setup file for building Pyrex extension modules
# Export the environment variable 'MODULE' to the name of the
# pyrex module you want to build before using this.
# This file should be used on a Unix/Linux box.
/usr/bin/env python setup.py build_ext --inplace
