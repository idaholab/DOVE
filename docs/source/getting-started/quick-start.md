# Quick Start

Once DOVE has been installed, it can be used as a library in a python script. DOVE contains three main types of objects: Resources, Components, and Systems.
- **Resources** refer to quantities that can be produced, consumed, converterted, and stored. Examples are electricity, heat, hydrogen, etc.
- **Components** are objects that perform actions on resources. Four types of Components are available in DOVE. Sources produce a specified resource; Sinks consume a specified resource; Converters change one or more resource into one or more other resources; and Storage components store resources across multiple timesteps.
- **Systems** contain sets of Resources and Components and are responsible for solving the optimization problem. Systems also take an argument to specify the time window over which the optimization should run. Usually only one system is created for each dispatch problem.

Consider a simple energy system with a nuclear power plant and generator, wind turbines, and battery storage, connected to a grid. The resource flow for this system is shown below:

```{figure} ../../../images/energy_flow_diagram_minimal.png
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
