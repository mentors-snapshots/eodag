#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# eodag documentation build configuration file, created by
# sphinx-quickstart on Thu Feb  1 09:22:31 2018.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
from importlib.metadata import metadata
from typing import Dict

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = "3"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "nbsphinx",
    "sphinx_copybutton",
]

# Notebook integration parameters
nbsphinx_execute = "never"

# This is going to generate a banner on top of each notebook
nbsphinx_prolog = """
{% set docname = env.doc2path(env.docname, base=None) %}

.. hint::

   You can run this notebook in a live session with |Binder|.

.. |Binder| image:: https://static.mybinder.org/badge.svg
   :target: https://mybinder.org/v2/gh/CS-SI/eodag/master?urlpath=lab/tree/docs/api_user_guide/{{ docname }}
"""

# sphinx-copybutton configurations
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# Scan all found documents for autosummary directives, and to generate stub
# pages for each
autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = metadata("eodag")["Name"]
author = metadata("eodag")["Author"]
copyright = "2018-2022, CS GROUP - France, https://www.csgroup.eu"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = metadata("eodag")["Version"]
# The full version, including alpha/beta/rc tags.
release = version

today_fmt = "%Y-%m-%d"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**.ipynb_checkpoints",
    "notebooks/intro_notebooks.ipynb",
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {
#     "logo": "eodag_logo.png",
#     "logo_name": False,
#     "fixed_sidebar": True,
#     "show_powered_by": False,
#     "github_user": "CS-SI",
#     "github_repo": "eodag",
#     "github_type": "star",
#     "github_banner": True,
#     "page_width": "1140px",
#     "pre_bg": "#eeffcc",
# }

html_theme_options = {
    "repository_url": "https://github.com/CS-SI/eodag",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "repository_branch": "develop",
    "path_to_docs": "docs",
    "use_download_button": True,
    "logo": {
        "image_light": "_static/eodag_logo_160.png",
        "image_dark": "_static/eodag_logo_160r.png",
    },
}

html_logo = "_static/eodag_logo.png"
html_title = ""

html_favicon = "_static/favicon-32x32.png"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "custom.css",
]

html_js_files = []

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.

html_show_sourcelink = False

html_last_updated_fmt = today_fmt

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "eodagdoc"

# -- Options for LaTeX output ---------------------------------------------

latex_elements: Dict[str, str] = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "eodag.tex",
        "eodag Documentation",
        "CS GROUP - France (CSSI)",
        "manual",
    )
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "eodag", "eodag Documentation", [author], 1)]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "eodag",
        "eodag Documentation",
        author,
        "eodag",
        "One line description of project.",
        "Miscellaneous",
    )
]

extlinks = {
    "issue": ("https://github.com/CS-SI/eodag/issues/%s", "#%s"),
    "pull": ("https://github.com/CS-SI/eodag/pull/%s", "#%s"),
}

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    # python-requests url temporary changed
    # https://github.com/psf/requests/issues/6140#issuecomment-1135071992
    "python-requests": ("https://requests.readthedocs.io/en/stable/", None),
    "shapely": ("https://shapely.readthedocs.io/en/stable/", None),
}


def _html_page_context(app, pagename, templatename, context, doctree):
    # Disable edit button for docstring generated pages
    if "generated" in pagename:
        context["theme_use_edit_page_button"] = False


def setup(app):
    """dummy docstring for pydocstyle"""
    app.connect("html-page-context", _html_page_context)
