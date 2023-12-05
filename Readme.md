# lemminx-pre-commit-hook

A [pre-commit](https://pre-commit.com) hook that uses [pylspclient](https://github.com/yeger00/pylspclient) to ask the [LemMinX][[lemminx](https://github.com/eclipse/lemminx)] XML language server to format your files. This is the same formatter that is used in the [RedHat XML extension for VS Code](https://github.com/redhat-developer/vscode-xml).

## Usage

```yaml
  - repo: https://github.com/lalten/lemminx-pre-commit-hook
    rev: v1.0.0
    hooks:
      - id: lemminx-format
```

## Advanced Configuration

The default formatting options are documented in https://github.com/eclipse/lemminx/blob/main/docs/Configuration.md#formatting

You can pass `args: [--settings, "settings.json"]` to the hook to tune this.
