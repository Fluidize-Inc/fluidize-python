# Fluidize Client

The Fluidize Client is the primary interface to create and edit projects. There are two interfaces for this, with more on the way.

- **Local Mode**: Works with your local device, uses Docker to sequentially execute nodes.

- **API Mode**: Runs on Fluidize API to manage projects and workflows in the cloud.

## Client API

### FluidizeClient
::: fluidize.client.FluidizeClient
    options:
      show_source: false
      members:
        - mode
        - adapters
        - projects
        - runs

### FluidizeConfig
::: fluidize.config.FluidizeConfig
    options:
      show_source: false
      members:
        - is_local_mode
        - is_api_mode
