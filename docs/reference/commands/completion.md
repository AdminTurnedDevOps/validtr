# `validtr completion`

Generate shell autocompletion script.

## Usage

```bash
validtr completion <shell>
```

Supported shells (from Cobra completion command):

- `bash`
- `zsh`
- `fish`
- `powershell`

## Examples

```bash
validtr completion zsh > _validtr
validtr completion bash > validtr.bash
```

Refer to shell-specific startup config to load generated script.
