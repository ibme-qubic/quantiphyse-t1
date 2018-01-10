#!/usr/bin/env python
import numpy
import os
import sys
import shutil

from setuptools import setup

desc = "Quantiphyse plugin for ASL"
version = "0.0.1"

# setup parameters
setup(name='qp-fabber-t1',
      cmdclass={},
      version=version,
      description=desc,
      long_description=desc,
      author='Michael Chappell, Martin Craig',
      author_email='martin.craig@eng.ox.ac.uk',
      packages=['fabber_t1'],
      include_package_data=True,
      data_files=[],
      setup_requires=[],
      install_requires=[],
      classifiers=["Programming Language :: Python :: 2.7",
                   "Development Status:: 3 - Alpha",
                   'Programming Language :: Python',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: POSIX',
                   "Intended Audience :: Education",
                   "Intended Audience :: Science/Research",
                   "Intended Audience :: End Users/Desktop",
                   "Topic :: Scientific/Engineering :: Bio-Informatics",],
)

