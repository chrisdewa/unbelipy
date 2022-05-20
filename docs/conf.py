# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'unbelipy'
copyright = '2022, ChrisDewa'
author = 'ChrisDewa'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon'
]

# Autodoc settings
autodoc_typehints = "description"

# Napoleon settings
napolean_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False

# For mapping short alias names
extlinks = {
    'issue': ('https://github.com/chrisdewa/unbelipy/issues/%s', 'GH-'),
    'pr': ('https://github.com/chrisdewa/unbelipy/pulls/%s', 'PR-')
}

# For referencing external documentations
intersphinx_mapping = {
    'py': ('https://docs.python.org/3', None),
    'aio': ('https://docs.aiohttp.org/en/stable/', None)
}

source_suffix = '.rst'

master_doc = 'index'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# HTML and Theme configuration
html_theme = 'sphinx_book_theme'
html_theme_options = {
    'icon_links': [
        {
            'name': 'Github',
            'url': 'https://github.com/chrisdewa/unbelipy',
            'icon': 'fab fa-github-square',
            'type': 'fontawesome'
        }
    ]
}

html_static_path = ['_static']
html_css_files = [
    'css/custom.css'
]
