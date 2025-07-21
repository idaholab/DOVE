# Quick Start

Once DOVE has been installed, it can be used as a python library. DOVE contains three main types of objects: Resources, Components, and Systems.
- Resources refer to quantities that can be produced, consumed, converterted, and stored. Examples are electricity, heat, hydrogen, etc.
- Components are objects that perform actions on resources. Four types of Components are available in DOVE. Sources produce a specified resource; Sinks consume a specified resource; Converters change one or more resource into one or more other resources; and Storage components store resources across multiple timesteps.
- The System contains all the Resources and Components and is responsible for solving the optimization problem. Systems also take an argument to specify the time window over which the optimization should run.

Consider a simple energy system with a nuclear power plant and generator, wind turbines, and battery storage, connected to a grid. The resource flow for this system is shown below:

.. image:: ../../../images/energy_flow_diagram_minimal.png
   :width: 600

Dispatch for this system can be economically optimized using DOVE in a python script:

.. literalinclude:: ../../../examples/simple_demonstration.py
   :language: python
   :linenos:

This script can be run in the uv environment and will print the dispatch results as well as writing them to a csv file called "simple_demo.csv":
```
>>> uv run python examples/simple_demonstration.py
   nuclear_steam_produces  generator_electricity_produces  ...  grid_electricity_consumes  objective
0                     3.0                             3.0  ...                       -3.0        8.9
1                     3.0                             3.0  ...                       -5.9        8.9
```
> Note that the formatting for this output will differ based on the size of the terminal window.

Here are the formatted results from this script:
|    |   nuclear_steam_produces |   generator_electricity_produces |   generator_steam_consumes |   wind_electricity_produces |   battery_SOC |   battery_charge |   battery_discharge |   grid_electricity_consumes |   objective |
|-------------:|-------------------------:|---------------------------------:|---------------------------:|----------------------------:|--------------:|-----------------:|--------------------:|----------------------------:|------------:|
|            0 |                        3 |                                3 |                         -3 |                           1 |      0.948683 |                1 |                 0   |                        -3   |         8.9 |
|            1 |                        3 |                                3 |                         -3 |                           2 |      0        |                0 |                 0.9 |                        -5.9 |         8.9 |


For additional examples, please see the :doc:`../user-guide/examples.md` page.
