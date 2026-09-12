# setup-alya

[![CI](https://github.com/alya-lang/setup-alya/actions/workflows/test.yml/badge.svg)](https://github.com/alya-lang/setup-alya/actions/workflows/test.yml)
[![License](https://img.shields.io/github/license/alya-lang/setup-alya?color=blue&label=License)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/alya-lang/alya?include_prereleases&label=Alya&color=orange)](https://github.com/alya-lang/alya/releases)

Set up your GitHub Actions workflow with the [Alya](https://github.com/alya-lang/alya) programming language compiler (`alyac`) and add it to `PATH`.

---

## ⚡ Quick Start

Add `alya-lang/setup-alya@v1` to your workflow:

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Set up Alya
    uses: alya-lang/setup-alya@v1
    with:
      version: 'latest'

  - name: Run Alya tests
    run: alyac run tests/test_basic.alya
```

---

## 📖 Usage Examples

### 1. Pin a Specific Version

```yaml
- name: Set up Alya v0.0.14
  uses: alya-lang/setup-alya@v1
  with:
    version: '0.0.14'
```

### 2. Multi-OS Matrix (Linux, Windows, macOS)

```yaml
jobs:
  test:
    name: Test on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Alya Compiler
        uses: alya-lang/setup-alya@v1
        with:
          version: 'latest'

      - name: Verify alyac
        run: alyac --version

      - name: Run test suite
        run: alyac run tests/test_basic.alya
```

### 3. Using Action Outputs

```yaml
- name: Set up Alya
  id: alya
  uses: alya-lang/setup-alya@v1
  with:
    version: 'latest'

- name: Print resolved compiler info
  run: |
    echo "Installed version: ${{ steps.alya.outputs.version }}"
    echo "Binary directory:  ${{ steps.alya.outputs.alyac-path }}"
```

---

## ⚙️ Inputs

| Input | Description | Required | Default |
|:---|:---|:---:|:---:|
| `version` | Target Alya compiler version (e.g. `'0.0.5'`, `'v0.0.5'`, or `'latest'`) | No | `'latest'` |
| `check-checksum` | Verify SHA-256 checksum of the downloaded release archive | No | `'true'` |
| `token` | GitHub token used for API requests (to avoid rate limits) | No | `${{ github.token }}` |

---

## 📤 Outputs

| Output | Description | Example |
|:---|:---|:---|
| `version` | The resolved Alya compiler version | `0.0.14` |
| `alyac-path` | Directory path containing the `alyac` binary | `/home/runner/.alyac/0.0.14/x86_64-linux` |

---

## 🖥️ Platform Support

Pre-built binaries are downloaded directly from official [Alya Releases](https://github.com/alya-lang/alya/releases):

| Operating System | Architecture | Archive Format | Binary |
|:---|:---|:---|:---|
| **Linux** | `x86_64` | `.tar.gz` | `alyac` |
| **macOS** | `arm64` (Apple Silicon) | `.tar.gz` | `alyac` |
| **macOS** | `x86_64` (Intel) | `.tar.gz` | `alyac` |
| **Windows** | `x86_64` | `.zip` | `alyac.exe` |

---

## 📄 License

This action is licensed under the [MIT License](LICENSE).
