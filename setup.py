# -*- coding: utf-8 -*-

"""
Copyright (c) 2011 Jan Pomikalek

This software is licensed as described in the file LICENSE.rst.
"""

from __future__ import with_statement

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open("README.rst") as readme:
    with open("CHANGELOG.rst") as changelog:
        long_description = readme.read() + "\n\n" + changelog.read()


setup(
    name="jusText",
    version="4.0.0",
    description="Heuristic + learned boilerplate removal (improved jusText fork)",
    long_description=long_description,
    author="Jan Pomikálek",
    author_email="jan.pomikalek@gmail.com",
    maintainer="Michael Ryan",
    maintainer_email="plambdafive@proton.me",
    url="https://github.com/XenonMolecule/jusText",
    license="The BSD 2-Clause License",
    install_requires=[
        'lxml[html_clean] >= 4.4.2',
        'backports.functools-lru-cache; python_version < "3.2"',
        # The bundled 3 MB classifier (auto-used by default) needs these. If any are absent,
        # jusText degrades gracefully to the heuristic classifier. The model was trained with
        # scikit-learn 1.5; major-version drift only warns (and falls back if it ever breaks).
        'scikit-learn >= 1.0',
        'joblib >= 1.0',
        'numpy >= 1.19',
        'rapidfuzz >= 2.0',
    ],
    extras_require={
        # Optional input mojibake repair (justext(..., fix_encoding=True), on by default).
        # Gracefully no-ops if absent, so it stays optional.
        "encoding": ["ftfy >= 6.0"],
        # The fastText-stacked model (best quality): download support + the runtime dep.
        "fasttext": ["fasttext >= 0.9.2", "huggingface_hub >= 0.16"],
    },
    tests_require=[
        "pytest",
        "pytest-cov",
        "coverage",
    ],
    packages=["justext"],
    package_data={"justext": ["stoplists/*.txt", "models/*.joblib"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Pre-processors",
        "Topic :: Text Processing :: Filters",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
)
