# CI/CD & Automated Publishing

0xMemory uses GitHub Actions to automate testing, linting, and publishing to PyPI.

## 🧪 Continuous Integration (`ci.yml`)

The CI workflow runs on every push to `main` and every Pull Request.

- **Python Versions**: 3.11, 3.12
- **Linters**: `ruff` (formatting/logic), `mypy` (types)
- **Tests**: `pytest` with 54 unit and 18 integration tests
- **Coverage**: Generates coverage reports for verification

## 🚀 Continuous Deployment (`publish.yml`)

We use **Trusted Publishing** (OIDC) to securely upload to PyPI without storing permanent secrets in GitHub.

### Setup Instructions

To enable auto-publishing for this repository:

1.  Log in to [PyPI.org](https://pypi.org).
2.  Go to your project: **0xmemory** -> **Publishing**.
3.  Click **"Add a new release publisher"**.
4.  Select **GitHub**.
5.  Fill in the details:
    - **Owner**: `MANOJ-80`
    - **Repository**: `0xMemory`
    - **Workflow name**: `publish.yml`
    - **Environment name**: `pypi`
6.  Click **Add**.

### Current Configuration

The following image shows a successful configuration of the Trusted Publisher on PyPI:

![PyPI Trusted Publisher Configuration](media/pypi_trusted_publisher.png)

## 📦 Release Process

1.  **Tag**: Create a new version tag (e.g., `git tag v1.1.0`).
2.  **Push**: Push the tag to GitHub (`git push origin v1.1.0`).
3.  **Release**: Go to GitHub -> Releases -> Draft a new release using the tag.
4.  **Auto-Publish**: Once the release is "Published", the `publish.yml` workflow will automatically build and upload the package to PyPI.
