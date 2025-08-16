# Fluidize

[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/fluidize?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/fluidize/)
[![License](https://img.shields.io/github/license/Fluidize-Inc/fluidize-python?style=for-the-badge)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen?style=for-the-badge&logo=gitbook&logoColor=white)](https://Fluidize-Inc.github.io/fluidize-python/)

### An Open Framework for AI-Driven Scientific Computing

 **fluidize-python** is a library for building modular, reproducible scientific computing pipelines. It provides a unified interface to a wide range of physical simulation tools, eliminating the need to navigate the inconsistent, incomplete instructions that often vary from tool to tool.

This library marks our first step toward AI-orchestrated scientific computing. By standardizing tools and practices within our framework, AI agents can automatically build, configure, and execute computational pipelines across domains and simulation platforms. Our goal is to improve today’s simulation tools so AI can assist researchers and scientists in accelerating the pace of innovation and scientific discovery.

## Quick Start

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


## The Problem

Students and researchers face significant barriers when working with different simulation tools:

- **Setup overhead** – Installing and configuring someone else’s research code can take an enormous amount of time.
- **Diverse architectures** – Scientific software is built using a wide range of tools and architectures, each with its own complexities and quirks.
- **Time drain** – Good software engineering practices are important, but in practice they often slow down the process of getting immediate results.
- **Reproducibility issues** – Sharing and reproducing experiments is frequently cumbersome and error-prone.
- **Scaling friction** – Moving from a local prototype to a cloud environment or dedicated compute cluster can be slow and difficult.

## The Solution

Fluidize provides a standardized wrapper that turns complex scientific software into modular components. This makes it possible to:

- **Expose a single API endpoint** for any scientific computing software—any language, any tool, any complexity.
- **Easily connect** tools that were never designed to work together.
- **Adopt consistent I/O patterns** across all simulations.

All of this works with **minimal or no changes** to the existing codebase, allowing our framework to scale effortlessly to any repository.

## Architecture

### Nodes
The foundational building blocks of Fluidize. Each node encapsulates a computational unit with:

| File | Purpose |
|------|---------|
| `properties.yaml` | Container configuration, working directory, and output paths |
| `metadata.yaml` | Node description, version, authors, and repository URL |
| `Dockerfile` | Environment setup and dependency installation |
| `parameters.json` | Tunable parameters for experiments |
| `main.sh` | Execution script for the source code |
| `source/` | Original scientific computing code |

**Key Features:**
- Predictable input/output paths
- Modular and extensible design
- No source code modification required
- Automated node generation support (Public launch soon)

### Projects
The project currently hosts a simple layer for composing and managing multiple nodes:

| File | Purpose |
|------|---------|
| `graph.json` | Node connectivity and data flow definition |
| `metadata.yaml` | Project description and configuration |


Docker engine is used for local execution. With API calls, we use the Kubernetes engine with Argo Workflow Manager.




## Documentation

Comprehensive documentation is available at [https://Fluidize-Inc.github.io/fluidize-python/](https://Fluidize-Inc.github.io/fluidize-python/)

- [Getting Started Guide](https://Fluidize-Inc.github.io/fluidize-python/getting-started)
- [Node Creation Tutorial](https://Fluidize-Inc.github.io/fluidize-python/nodes)
- [Project Orchestration](https://Fluidize-Inc.github.io/fluidize-python/projects)
- [API Reference](https://Fluidize-Inc.github.io/fluidize-python/api)

## Contributing

We would love contributions and collaborations! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

Also - we would love to help streamline your research pipeline! Please reach out at [henry@fluidize.ai](mailto:henry@fluidize.ai) or [henrybae@g.harvard.edu](mailto:henrybae@g.harvard.edu).


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
