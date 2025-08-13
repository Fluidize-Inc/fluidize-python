# Fluidize

[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/fluidize?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/fluidize/)
[![License](https://img.shields.io/github/license/Fluidize-Inc/fluidize-python?style=for-the-badge)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen?style=for-the-badge&logo=gitbook&logoColor=white)](https://Fluidize-Inc.github.io/fluidize-python/)

**Open Foundation for AI-Driven Scientific Computing**

Fluidize is a Python library that establishes a standard for AI-orchestrated scientific computing. With this common framework, agents can automatically build, configure, and run computational pipelines across different domains and platforms.


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

Example projects are located in this folder: [example/](example/)


## The Problem

Students and researchers face significant barriers when exploring different ideas and simulation tools.

- **Setup**: Often setting up other's code in research takes a really long time.
- **Diversified Architecture**: People use different tools to develop their science softwares. The specificy and complexity of these programs make them
- **Time drain**: Following good software engineering practices is ideal in theory, but in practice doing so comes at a cost of immediately obtaining results.
- **Reproducibility challenges**: It's difficult to share and reproduce experiments
- **Scaling barriers**: Moving from local prototypes to cloud or dedicated cluster is often time consuming and difficult

## The Solution

Fluidize provides a standardized wrapper that transforms complex scientific software into modular, AI-orchestratable components. This enables:

- **Single API endpoint** for arbitrarily complex scientific computing software, any language, any software
- **Easy orchestration** of tools that don't work well together.
- **Consistent I/O patterns** across all simulations

This is done with virtually no changes to the existing codebase.

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

## Roadmap

This is just the beginning of what we think is a really exciting new era for how we learn science and do research. We will be releasing the following tools built from this framework:

- **Fluidize Playground**: Automatically explore and build simulation pipelines with natural language.
- **Auto-Fluidize**: Automatically convert obscure scientific software to run anywhere


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
