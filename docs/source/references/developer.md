# Developer Reference

## 👋 Welcome!

This guide will walk you through setting up your development environment, adhering to code standards, running tests, and submitting your contributions effectively.

---

## 🛠️ Prerequisites

Ensure the following tools are installed on your system:

  - **Python 3.11+** [Download Python](https://www.python.org/downloads/)
  - **Git** [Download Git](https://git-scm.com/downloads)
  - **uv** (Python package and environment manager)
  - **pre-commit** (Framework for managing Git hooks)
  - **An IDE or text editor** with Python support (e.g., VSCode, PyCharm)

---

## 📦 Setting Up the Project

### 1. Clone the Repository

Replace `<REPO_URL>` with the URL of your DOVE repository:

```bash
git clone <REPO_URL>
cd dove
```

### 2. Install Dependencies

Use `uv` to synchronize your environment with the project's lockfile:

```bash
uv sync --all-packages
```

> **Note:** This command installs both runtime and development dependencies as specified in your `pyproject.toml` and `uv.lock` files.

---

## ✅ Configure Pre-Commit Hooks

Set up Git hooks to enforce code quality checks automatically:

```bash
pre-commit install --install-hooks
```

> **Optional:** To run all hooks on all files manually:
> ```bash
> pre-commit run --all-files
> ```

---

## 🧪 Development Workflow

### 1. Create a Feature Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
```

Replace `your-feature-name` with a descriptive name for your feature or fix.

### 2. Linting and Formatting with Ruff
- **Check code for linting errors:**
```bash
uv run ruff check .
```
- **Automatically fix linting errors:**
```bash
uv run ruff check --fix
```
- **Format code according to style guidelines:**
```bash
uv run ruff format .
```
> **Note:** Ruff configurations are defined in `pyproject.toml`.

### 3. Run Tests with Pytest

- **Execute all tests:**

```bash
uv run pytest
```

- **Run tests with coverage report:**
```bash
uv run pytest --cov
```

---

## 📝 Commit Your Changes

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for clear and consistent commit messages.

**Commit using Commitizen:**
```bash
uv run cz commit
```

This will guide you through crafting a standardized commit message.

---

## 🚀 Push and Create a Pull Request

1. **Push your branch to the remote repository:**

```bash
git push origin feature/your-feature-name
```

2. **Open a Pull Request (PR):**

- Navigate to your repository on GitHub.
- Click on "Compare & pull request" for your recently pushed branch.
- Fill out the PR template, detailing your changes and any relevant information.

3. **Address Feedback:**

- Respond to any code review comments.
- Make necessary changes and push them to your branch; the PR will update automatically.

---

## 🧰 Summary of Common Commands

  | Task                    | Command                                |
  | ----------------------- | -------------------------------------- |
  | Clone repository        | `git clone <REPO_URL>`                 |
  | Install dependencies    | `uv pip sync --all-packages`           |
  | Set up pre-commit hooks | `pre-commit install --install-hooks`   |
  | Create a new branch     | `git checkout -b feature/your-feature` |
  | Lint code               | `uv run ruff check .`                  |
  | Fix linting issues      | `uv run ruff check --fix`              |
  | Format code             | `uv run ruff format .`                 |
  | Run tests               | `uv run pytest`                        |
  | Run tests with coverage | `uv run pytest --cov`                  |
  | Commit changes          | `uv run cz commit`                     |
  | Push branch to remote   | `git push origin feature/your-feature` |

---

## 📚 Additional Resources

  - **`pyproject.toml`**: Contains project metadata and tool configurations.
  - **`.pre-commit-config.yaml`**: Defines the pre-commit hooks used in the project.

---

**Happy Coding!** If you encounter any issues or have questions, feel free to reach out to the project maintainers or open an issue in the repository.
