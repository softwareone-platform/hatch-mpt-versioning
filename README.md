# hatch-mpt-versioning

Hatchling version source plugin that derives a PEP 440 version from `git describe`.

## Usage

In a consuming project's `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.21.0", "hatch-mpt-versioning>=0.1.0"]
build-backend = "hatchling.build"

[project]
dynamic = ["version"]

[tool.hatch.version]
source = "mpt-git-describe"
```

## Version format

Given `git describe --tags --long --always --abbrev=7 --dirty`, parse `TAG-DISTANCE-gSHA[-dirty]`:

- `DISTANCE == 0` and clean: `TAG`
- `DISTANCE > 0` and tag `X.Y.0`: `X.Y.DISTANCE+gSHA`
- if dirty: append `.dirty` to local part → `...+gSHA.dirty`

