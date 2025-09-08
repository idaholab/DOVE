# Quick Start
DOVE contains three main types of objects: Resources, Components, and Systems.
- **Resources** refer to quantities that can be produced, consumed, converterted, and stored. Examples are electricity, heat, hydrogen, etc.
- **Components** are objects that perform actions on resources. Four types of Components are available in DOVE. Sources produce a specified resource; Sinks consume a specified resource; Converters change one or more resource into one or more other resources; and Storage components store resources across multiple timesteps.
- **Systems** each contain a set of Resources and a set of Components and are responsible for solving the optimization problem. Systems also take an argument to specify the time window over which the optimization should run. Usually only one system is created for each dispatch problem.

Consider a simple energy system with a nuclear power plant and generator, wind turbines, and battery storage, connected to a grid. The resource flow for this system is shown below:

```{figure} ../assets/energy_flow_diagram_minimal.png
:width: 600px

Resource Flow Diagram for Simple Dispatch Problem
```

Dispatch for this system can be economically optimized using DOVE in a python script:

```{literalinclude} ../../../examples/simple_demonstration.py
   :language: python
   :linenos:
```

Here are the formatted, complete results from this script:
```{csv-table} Formatted Results from CSV
   :file: ../../../examples/simple_demo.csv
   :header-rows: 1
```

For additional examples, please see the <project:../user-guide/examples.md> page.
