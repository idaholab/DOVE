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

```{include} ../../../README.md
:start-line: 76
:end-line: 84
```

Here are the formatted, complete results from this script:
```{csv-table} Formatted Results from CSV
   :file: ../../../examples/simple_demo.csv
   :header-rows: 1
```

For additional examples, please see the <project:../user-guide/examples.md> page.
