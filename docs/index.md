# Fluidize

[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/fluidize?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/fluidize/)
[![License](https://img.shields.io/github/license/Fluidize-Inc/fluidize-python?style=for-the-badge)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen?style=for-the-badge&logo=gitbook&logoColor=white)](https://Fluidize-Inc.github.io/fluidize-python/)

## About

 **fluidize-python** is a library for building modular, reproducible scientific computing pipelines. It provides a unified interface to a wide range of physical simulation tools, eliminating the need to navigate the inconsistent, incomplete instructions that often vary from tool to tool.

This library marks our first step toward AI-orchestrated scientific computing. By standardizing tools and practices within our framework, AI agents can automatically build, configure, and execute computational pipelines across domains and simulation platforms.

Our goal is to improve today’s simulation tools so AI can assist researchers and scientists in accelerating the pace of innovation and scientific discovery.

## Installation

### Prerequesites:

- Python 3.9+
- Docker Desktop (for local execution). Download and install Docker Desktop from https://docs.docker.com/desktop/.

  After installation, verify with:
  ```bash
  docker --version
  ```



### From PyPI
```bash
pip install fluidize
```

### From Source
```bash
git clone https://github.com/Fluidize-Inc/fluidize-python.git
cd fluidize-python
make install
```

## Run Examples

Example projects are located in this folder: [examples/](examples/). There you can find an [Jupyter Notebook](examples/demo.ipynb) of a simple simulation

## Architecture

At Fluidize, we believe strong organization leads to better reproducibility and scalability.

We treat each simulation pipeline as an individual project. Within projects, each pipeline is treated as a DAG (directed acyclic graph), where nodes represent individual pieces of scientific software (e.g. inputs, solvers, visualization tools, etc.) and edges represent data flow between nodes.


### Nodes
Nodes are the foundational building blocks of simulation pipelines. Each node represents a computational unit with:

| File | Purpose |
|------|---------|
| `properties.yaml` | Container configuration, working directory, and output paths |
| `metadata.yaml` | Node description, version, authors, and repository URL |
| `Dockerfile` | Environment setup and dependency installation |
| `parameters.json` | Tunable parameters for experiments |
| `main.sh` | Execution script for the source code |
| `source/` | Original scientific computing code |

**Key Features:** <br>
- Predictable input/output paths <br>
- Modular and extensible design <br>
- No source code modification required <br>
- Automated node generation support (Public launch soon)


### Projects

Projects store a simple data layer for managing individual modules within a pipeline.

| File | Purpose |
|------|---------|
| `graph.json` | Node (scientific software) and edge (data flow) definitions |
| `metadata.yaml` | Project description and configuration |


### Runs

Pipelines can be executed both locally and on the cloud. Local execution is handled by Docker engine. Cloud execution is routed through our API, and uses the Kubernetes engine with Argo Workflow Manager.

## Contributing

We would love to collaborate with you! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

Also - we would love to help streamline your pipeline! Please reach out to us at [founders@fluidize.ai](mailto:founders@fluidize.ai).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
