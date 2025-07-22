# Installation

Regardless of the installation method you select, you must ensure that you have the necessary solver(s) installed on your system in order to use DOVE. DOVE uses Pyomo for optimization and supports any solver supported by your Pyomo version.

---

## Install Using Pip (Recommended) (TODO: Waiting on PyPI release)
If you do not need access to the source code for DOVE, the simplest method of installation is to run the following:
```
pip install dove-inl
```
```{warning}
   This command does not yet work because DOVE has not yet been added to PyPI!
```

---

## Install from Source
DOVE may be downloaded from source according to the procedure outlined below. If you would like to contribute to DOVE, please refer to the <project:../references/developer.md> page. If you are not interested in contributing but would still like access to the source code, these instructions are sufficient.

First, ensure that the necessary prerequisites are installed on your system:
- **Python 3.11+** ([Download Python](https://www.python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads))
- **uv** ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))

Now navigate into the desired folder and clone the repository from github:
```
mkdir projects
cd projects
git clone https://github.com/idaholab/DOVE.git
```
Next, dependencies can be installed using uv while in the DOVE directory:
```
cd DOVE
uv sync
```
```{note}
   This command also automatically creates an environment located at `DOVE/.venv`, in which the dependencies are installed. Prepending `uv run` to commands while in the DOVE directory will automatically load this environment.
```

Finally, to verify your installation, run tests:
```
uv run pytest
```
