# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))


project = "DOVE"
project_copyright = "2024, Battelle Energy Alliance, LLC"
author = "Dylan McDowell"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
]

autosummary_generate = True
# intersphinx_mapping = {
#     "python": ("https://docs.python.org/3", None),
#     "pyomo":  ("https://pyomo.readthedocs.io/en/stable/", None),
# }


templates_path = ["_templates"]
exclude_patterns = []

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]

html_theme_options = {
    "repository_url": "https://github.com/idaholab/DOVE",
    "use_repository_button": True,
    "show_navbar_depth": 1,
    "show_toc_level": 2,
}
