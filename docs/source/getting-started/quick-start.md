# Quick Start
```{include} ../../../README.md
:start-after: Quick-Start
:end-before: <img
```

```{figure} ../assets/energy_flow_diagram_minimal.png
:width: 600px

Resource Flow Diagram for Simple Dispatch Problem
```

Dispatch for this system can be economically optimized using DOVE in a python script:

```{literalinclude} ../../../examples/simple_demonstration.py
   :language: python
   :linenos:
```

This script can be run in the uv environment and will print the dispatch results as well as writing them to a CSV file called "simple_demo.csv":
```
>>> uv run python examples/simple_demonstration.py
   nuclear_steam_produces  ...  objective
0                     3.0  ...        8.9
1                     3.0  ...        8.9
```
```{note}
   The formatting for this output will differ based on the size of the terminal window.
```

Here are the formatted, complete results from this script:
```{csv-table} Formatted Results from CSV
   :file: ../../../examples/simple_demo.csv
   :header-rows: 1
```

For additional examples, please see the <project:../user-guide/examples.md> page.
