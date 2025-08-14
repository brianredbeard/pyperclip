.. _continuous_integration:

======================================
Continuous Integration and Workflows
======================================

The Pyperclip project uses GitHub Actions to automate testing, linting, security scanning, and release packaging. This ensures that every change is validated for quality and compatibility across multiple platforms and Python versions. This document provides an overview of our CI/CD pipelines.

All workflows are configured to use `uv <https://github.com/astral-sh/uv>`_, a fast, modern Python package installer and resolver, to ensure efficient and reproducible builds.

---

Main CI Pipeline (`ci.yaml`)
===========================

This is the primary CI pipeline that validates the correctness and quality of the code.

**Triggers**
------------

This workflow is automatically triggered on the following events, as defined in the ``on`` block of the workflow file:

.. code-block:: yaml

   on:
     push:
       branches: [ main, master ]
     pull_request:
       branches: [ main, master ]

*   **Push:** When a commit is pushed to the ``main`` or ``master`` branches.
*   **Pull Request:** When a pull request is opened, synchronized, or reopened that targets the ``main`` or ``master`` branch.

This configuration ensures that every proposed change is thoroughly tested before it is merged into the main codebase.

Jobs
----

The pipeline consists of three main jobs that run in parallel. The ``fail-fast`` strategy is set to ``false``, meaning that if one job in the test matrix fails, other jobs will continue to run to completion, providing a comprehensive report of all failures.

**1. `test`**
   This job runs the full test suite using `pytest`. It operates on a comprehensive build matrix to ensure cross-platform and cross-version compatibility.

   *   **Operating Systems:** Ubuntu, Windows, and macOS. The macOS tests are run on both Intel (`macos-13`) and Apple Silicon (`macos-latest`) runners to ensure universal compatibility.
   *   **Python Versions:** 3.8, 3.9, 3.10, 3.11, 3.12.
   *   **System Dependencies:** On Linux, it automatically installs ``xclip`` and ``xsel`` to test those clipboard backends. On macOS, it verifies that ``pbcopy`` and ``pbpaste`` are available.

**2. `lint`**
   This job enforces code style and quality standards using Python 3.11. It ensures the codebase remains clean, readable, and consistent.

   *   **Checks Performed:**
       *   ``black --check --diff``: Validates code formatting without making changes.
       *   ``isort --check-only --diff``: Verifies import order.
       *   ``flake8``: Enforces PEP 8 and other style guide rules, ignoring E203 and W503 for compatibility with Black.
       *   ``mypy``: Performs static type checking.

**3. `security`**
   This job scans the codebase for potential security vulnerabilities to ensure the library remains safe to use. Reports are uploaded as build artifacts for review.

   *   **Tools Used:**
       *   ``bandit``: Scans for common security issues in Python code. The results are saved to ``bandit-report.json``.
       *   ``safety``: Checks for known vulnerabilities in the project's dependencies. The results are saved to ``safety-report.json``.

---

Manual Build Workflow (`manual-build.yaml`)
===========================================

This workflow allows for manual execution of the build and test process with customized parameters. It is useful for debugging issues on specific configurations or for generating pre-release artifacts without triggering a full release.

**Trigger**
---------
*   **Manual Trigger (`workflow_dispatch`):** This workflow is run on-demand from the "Actions" tab in the GitHub repository.

Jobs and Inputs
---------------

The workflow uses a `setup` job to dynamically generate a build matrix based on the user's inputs, a `build` job to execute the tests, and a `summary` job to provide a clear report.

*   ``python_versions``: A comma-separated list of Python versions to test against (e.g., `3.10,3.12`).
*   ``platforms``: A comma-separated list of platforms to run on (e.g., `ubuntu-latest,macos-latest`).
*   ``run_extended_tests``: A boolean flag to enable extended tests, including coverage reporting.
*   ``create_release_artifacts``: A boolean flag to build the source distribution (`sdist`) and wheel artifacts.
*   ``test_branch``: The name of the branch to check out and test.

---

Release Workflow (`release.yaml`)
=================================

This workflow automates the entire release process, from building the package to publishing it on PyPI.

**Triggers**
----------
This workflow is triggered in two ways:

*   **Git Tag Push:** Automatically runs when a new tag starting with ``v`` (e.g., ``v1.9.0``) is pushed to the repository. This is the standard method for creating a new release.
*   **Manual Trigger (`workflow_dispatch`):** Can be run manually for special cases, such as re-releasing a version. This requires a ``tag`` input.

Jobs
----

**1. `build-release`**
   Builds the final distribution files on an Ubuntu runner.
   *   Creates both the source distribution (`sdist`) and the universal wheel.
   *   Uses ``twine check`` to validate the generated package metadata.
   *   Uploads the artifacts to be used by subsequent jobs.

**2. `test-release`**
   Tests the packaged artifacts to ensure they are installable and functional across all supported platforms.
   *   Downloads the artifacts created in the `build-release` job.
   *   Runs on a matrix of Ubuntu, Windows, and macOS with various Python versions.
   *   Creates a new virtual environment and installs `pyperclip` from the built wheel to simulate a real user installation.

**3. `publish`**
   Publishes the validated package to PyPI.
   *   **Important Security Guardrail:** This job is protected by a strict `if` condition to prevent accidental or unauthorized publications. It will only run if all of the following are true:
      1. The repository is the main ``asweigart/pyperclip`` repository (not a fork).
      2. The workflow was triggered by a git tag push event.
   *   It is also protected by a GitHub Environment named `release`, which can have its own protection rules (e.g., requiring approval from specific maintainers).
   *   Uses a ``PYPI_API_TOKEN`` secret for secure authentication with the PyPI registry.
