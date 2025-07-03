## v0.2.0 (2025-07-01)

### BREAKING CHANGE

- Removes Component's max_capacity, min_capacity, capacity_factor, and profile attributes; adds max_capacity_profile and min_capacity_profile. Fixes #26; addresses but does not fix #19

### Feat

- add periodic level constraint to model (#24)
- **PriceTakerBuilder**: add ramp limits and ramp freq to pyomo model (#17)

### Refactor

- rework handling of time-series inputs and capacities (#27)
