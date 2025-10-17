# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import sphinx_rtd_theme
sys.path.insert(0, os.path.abspath('../../../src'))

project = 'Luck'
copyright = '2025, Julian D. Londono H.'
author = 'Julian D. Londono H.'
release = 'v1.0.0'

# -- General configuration ---------------------------------------------------

# Useful extensions for Python and PyQt6
extensions = [
    'sphinx.ext.autodoc',            # Documents classes, methods, attributes
    'sphinx.ext.napoleon',           # Allow Google or NumPy style docstrings
    'sphinx.ext.viewcode',           # Add links to source code
    'sphinx_autodoc_typehints',      # Displays parameter types and returns
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# Visual theme (you can change it to 'alabaster' if you want)
html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']

# -- Autodoc configuration ---------------------------------------------------

# Sort members in the same order as in the code
autodoc_member_order = 'bysource'

# Show private members if desired (optional)
# autodoc_default_options = {'private-members': True}

# Include class attribute docstrings
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}