# Fluidize

[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/fluidize?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/fluidize/)
[![License](https://img.shields.io/github/license/Fluidize-Inc/fluidize-python?style=for-the-badge)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen?style=for-the-badge&logo=gitbook&logoColor=white)](https://Fluidize-Inc.github.io/fluidize-python/)


**Open Foundation for AI-Driven Scientific Computing**

Fluidize library provides the foundational types and abstractions for building and executing AI-orchestrated scientific computing pipelines. This allows agents to automatically orchestrate, configure, and iterate through computational pipeline with minimal prompting.

Fluidize is a Python library that establishes a standard for AI-orchestrated scientific computing. With this common framework, agents can automatically build, configure, and run computational pipelines across different domains and platforms.


**The Problem**

Students and researchers face significant barriers while translating their ideas into production ready pipelines:

-
- Time spent on software engineering instead of research

---

## Getting Started

### Requirements

- Python 3.9+
- Docker (for local execution)

### Install from PyPI

```bash
pip install fluidize
```

### Development Installation

```bash
git clone https://github.com/Fluidize-Inc/fluidize-python.git
cd fluidize-python
make install
```

---

### Basic Usage

```python
from fluidize import FluidizeClient

client = FluidizeClient()

# Create a new project
project = client.projects.create(name="My Project")

# Load a project
loaded_project = client.projects.get(project_id=project.id)

# Run Project
loaded_project.run.run_flow()

```

---


## 📚 Documentation

- **[API Documentation](https://Fluidize-Inc.github.io/fluidize-python/)** - Complete API reference
- **[Interactive Demo](utils/fluidize_demo.ipynb)** - Jupyter notebook walkthrough
- **[Examples](examples/)** - Examples

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contributing Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Run quality checks: `make check`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open a Pull Request


We are looking to collaborate with researchers who are interested in ...

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact

Henry Bae - henry@fluidize.ai



---

What should the documentation contain:

- Overview of Fluidize Project


- Overview of Fluidize Node
- Overview of Fluidize Workflow

---

<p align="center">
  <strong>Built with ❤️ by the Fluidize team</strong><br>
  <em> </em>
</p>
