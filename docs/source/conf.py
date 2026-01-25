import os
import sys
from pathlib import Path

CONF_DIR = Path(__file__).resolve().parent

DOCS_DIR = CONF_DIR.parent

PROJECT_ROOT = DOCS_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))

print(">>> DEBUG: Sphinx sys.path appended:", PROJECT_ROOT)

project = 'Banking System'
copyright = '2025, Диана Варзина'
author = 'Диана Варзина'

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

templates_path = ['_templates']
exclude_patterns = []

language = 'ru'

html_theme = 'alabaster'
html_static_path = ['_static']

