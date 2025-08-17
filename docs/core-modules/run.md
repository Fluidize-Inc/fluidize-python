# Run Module

## Run Management

::: fluidize.managers.runs.RunsManager
    options:
      show_source: false
      heading_level: 3
      show_root_heading: true
      members:
        - run_flow
        - list
        - get_status

## Run Execution

::: fluidize.core.modules.run.RunJob
    options:
      show_source: false
      heading_level: 3
      show_signature: false
      show_root_heading: true

::: fluidize.core.modules.run.project.ProjectRunner
    options:
      show_source: false
      heading_level: 3
      show_root_heading: true
