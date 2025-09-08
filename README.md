<img src="./docs/source/assets/DOVE_light_mode.png" width="600">

# Dispatch Optimization Variable Engine (DOVE)
[![tests](https://github.com/idaholab/DOVE/actions/workflows/run-tests.yml/badge.svg?branch=main)](https://github.com/idaholab/DOVE/actions/workflows/run-tests.yml)

DOVE is a python library developed at Idaho National Laboratory that performs dispatch optimization for energy systems. Dispatch in this context refers to the time-dependent activity levels of components in an energy system, bounded by constraints such as component capacities or resource conversion ratios. Within these constraints, DOVE applies user-provided economic data to generate an optimally profitable dispatch solution for the system. Especially well-suited for integrated energy system analysis, DOVE is equipped to handle a system involving an arbitrary number of resources with any number of respective resource markets. Its design prioritizes ease of use, and it features intuitive syntax and a pythonic structure while maintaining the flexibility to handle complex scenarios.

Please see the [repository documentation](https://idaholab.github.io/DOVE) for additional information, including a quick-start demonstration, examples, developer information, and more!

# Installation

Regardless of the installation method you select, you must ensure that you have the necessary solver(s) installed on your system in order to use DOVE. DOVE uses Pyomo for optimization and supports any solver supported by your Pyomo version. Some commonly used solvers include [Cbc](https://github.com/coin-or/Cbc#DOWNLOAD), [Ipopt](https://coin-or.github.io/Ipopt/INSTALL.html), and [GLPK](https://www.gnu.org/software/glpk/#downloading).

## Install from Source
First, ensure that the necessary prerequisites are installed on your system:
- **Python 3.11+** ([Download Python](https://www.python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads))

Now navigate into the desired folder and clone the repository from github:
```
mkdir projects
cd projects
git clone https://github.com/idaholab/DOVE.git
```

Next, the project can be installed using pip:
```
pip install DOVE
```
