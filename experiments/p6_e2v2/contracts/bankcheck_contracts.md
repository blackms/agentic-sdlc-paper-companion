# Contract Document: `bankcheck`

## `Reporter.ok`

**Signature**

```python
Reporter.ok(self, msg: str) -> None
```

**Preconditions**

- `msg` is expected to be string-format-compatible.

**Postconditions / Return Guarantees**

- Returns `None`.
- Writes `[OK]   {msg}` to standard output.

**Invariants**

- Does not modify `self.exit_code`.

**Side Effects**

- Performs console output via `print`.

---

## `Reporter.warn`

**Signature**

```python
Reporter.warn(self, msg: str) -> None
```

**Preconditions**

- `msg` is expected to be string-format-compatible.

**Postconditions / Return Guarantees**

- Returns `None`.
- Writes `[WARN] {msg}` to standard output.

**Invariants**

- Does not modify `self.exit_code`.

**Side Effects**

- Performs console output via `print`.

---

## `Reporter.fail`

**Signature**

```python
Reporter.fail(self, msg: str) -> None
```

**Preconditions**

- `msg` is expected to be string-format-compatible.
- `self.exit_code` exists and is comparable with `EXIT_FAIL`.

**Postconditions / Return Guarantees**

- Returns `None`.
- Writes `[FAIL] {msg}` to standard output.
- Ensures `self.exit_code >= EXIT_FAIL`.

**Invariants**

- `self.exit_code` is monotonic: this method never lowers it.

**Side Effects**

- Mutates `self.exit_code` when it is below `EXIT_FAIL`.
- Performs console output via `print`.

---

## `Reporter.config_error`

**Signature**

```python
Reporter.config_error(self, msg: str) -> None
```

**Preconditions**

- `msg` is expected to be string-format-compatible.
- `self.exit_code` exists and is comparable with `EXIT_CONFIG_ERROR`.

**Postconditions / Return Guarantees**

- Returns `None`.
- Writes `[CFG]  {msg}` to standard error.
- Ensures `self.exit_code >= EXIT_CONFIG_ERROR`.

**Invariants**

- `self.exit_code` is monotonic: this method never lowers it.

**Side Effects**

- Mutates `self.exit_code` when it is below `EXIT_CONFIG_ERROR`.
- Performs console output to `sys.stderr`.

---

## `load_yaml_file`

**Signature**

```python
def load_yaml_file(path: Path) -> dict
```

**Preconditions**

- `path` identifies a readable UTF-8 text file.
- File contents are expected to be valid YAML.
- Parsed YAML is expected by callers to be a dictionary-compatible object.

**Postconditions / Return Guarantees**

- Opens `path` in read mode with UTF-8 encoding.
- Returns the result of `yaml.safe_load(fh)`.

**Invariants**

- Does not mutate `path`.
- Does not modify filesystem contents.

**Side Effects**

- Reads from the filesystem.
- May propagate file I/O exceptions.
- May propagate YAML parsing exceptions from `yaml.safe_load`.

---

## `load_json_file`

**Signature**

```python
def load_json_file(path: Path) -> dict
```

**Preconditions**

- `path` identifies a readable UTF-8 text file.
- File contents are expected to be valid JSON.
- Parsed JSON is expected by callers to be a dictionary-compatible object.

**Postconditions / Return Guarantees**

- Opens `path` in read mode with UTF-8 encoding.
- Returns the result of `json.load(fh)`.

**Invariants**

- Does not mutate `path`.
- Does not modify filesystem contents.

**Side Effects**

- Reads from the filesystem.
- May propagate file I/O exceptions.
- May propagate `json.JSONDecodeError`.

---

## `load_profile`

**Signature**

```python
def load_profile(repo_root: Path, override: Path | None = None) -> dict | None
```

**Preconditions**

- `repo_root` is a `Path`.
- If supplied, `override` is a `Path`.
- The selected profile path, when present, is expected to contain readable YAML.

**Postconditions / Return Guarantees**

- Uses `override` when provided; otherwise uses `repo_root / ".banking-profile"`.
- Returns `None` if the selected path is not a file.
- Otherwise returns the result of `load_yaml_file(path)`.

**Invariants**

- Does not mutate `repo_root` or `override`.
- Does not modify filesystem contents.

**Side Effects**

- Checks filesystem metadata with `Path.is_file`.
- Reads YAML from disk when the profile file exists.
- May propagate exceptions from `load_yaml_file`.

---

## `file_matches_globs`

**Signature**

```python
def file_matches_globs(rel_path: str, patterns: Iterable[str]) -> bool
```

**Preconditions**

- `rel_path` is a string path.
- `patterns` is an iterable of glob pattern strings accepted by `fnmatch.fnmatch`.

**Postconditions / Return Guarantees**

- Returns `True` if any pattern matches `rel_path`.
- Returns `False` otherwise.
- Always returns a `bool`.

**Invariants**

- Does not mutate `rel_path`.
- Does not mutate `patterns`.

**Side Effects**

- Consumes the `patterns` iterable as needed.
- No file I/O.

---

## `function_is_exempted`

**Signature**

```python
def function_is_exempted(
    rel_file: str,
    func_name: str,
    exemptions: list[dict],
) -> tuple[bool, str]
```

**Preconditions**

- `rel_file` is a relative file path string.
- `func_name` is a function name string.
- Each exemption considered by the function is expected to contain `"path"` and `"function_pattern"` keys.
- Exemption `"reason"` is optional.

**Postconditions / Return Guarantees**

- Returns `(True, reason)` for the first exemption whose path glob matches `rel_file` and function glob matches `func_name`.
- If the matching exemption has no `"reason"`, the returned reason is `""`.
- Returns `(False, "")` when no exemption matches.
- Always returns a 2-tuple of `(bool, str)`.

**Invariants**

- Does not mutate `rel_file`, `func_name`, or `exemptions`.

**Side Effects**

- No file I/O.
- May raise lookup-related exceptions if an exemption lacks required keys.

---

## `iter_files_under_sensitive`

**Signature**

```python
def iter_files_under_sensitive(
    repo_root: Path,
    sensitive_paths: list[str],
) -> Iterable[Path]
```

**Preconditions**

- `repo_root` is a `Path`.
- `sensitive_paths` contains glob pattern strings.
- Patterns ending in `"/**"` are treated as recursive directory roots.

**Postconditions / Return Guarantees**

- Yields each matching file path at most once.
- For patterns ending in `"/**"`, recursively yields files under the corresponding directory.
- For other patterns, yields files matched by `repo_root.glob(pattern)`.
- Yields `Path` objects.

**Invariants**

- Does not mutate `repo_root` or `sensitive_paths`.
- Maintains a per-iteration `seen` set to avoid duplicate yielded files.

**Side Effects**

- Reads filesystem metadata.
- Traverses directories using `rglob` or `glob`.
- Does not modify filesystem contents.

---

## `cmd_profile_validate`

**Signature**

```python
def cmd_profile_validate(args: argparse.Namespace) -> int
```

**Preconditions**

- `args.repo_root` is present and path-like.
- `args.profile` is present and either falsey or path-like.
- The profile file, when present, is expected to be YAML.
- `PROFILE_SCHEMA_PATH` is expected to identify a JSON schema file.

**Postconditions / Return Guarantees**

- Returns an integer exit code.
- Returns `EXIT_CONFIG_ERROR` if the profile file is absent, invalid YAML, or the schema cannot be loaded.
- Returns `EXIT_OK` when the profile validates with no schema errors.
- Returns `EXIT_FAIL` when schema validation reports errors.

**Invariants**

- Does not modify repository files.
- Reporter exit code only increases in severity.

**Side Effects**

- Reads profile YAML and profile schema JSON.
- Writes status lines to stdout or stderr.
- Catches `yaml.YAMLError`, `FileNotFoundError`, and `json.JSONDecodeError` in the documented validation paths.

---

## `cmd_review_validate`

**Signature**

```python
def cmd_review_validate(args: argparse.Namespace) -> int
```

**Preconditions**

- `args.repo_root` is present and path-like.
- `args.branch` is present as a branch or review-directory name.
- Review JSON files are expected under `.claude/reviews/<branch>`, with `/` in branch names mapped to `__`.
- Manifest and findings schema files are expected to be readable JSON schemas.

**Postconditions / Return Guarantees**

- Returns an integer exit code.
- Uses the filesystem-safe branch directory, falling back to the literal branch directory when present.
- Returns `EXIT_CONFIG_ERROR` if no review directory is found.
- Returns `EXIT_FAIL` if no JSON files are present or validation errors are found.
- Returns `EXIT_OK` when all discovered JSON files validate.

**Invariants**

- Does not modify review files.
- Reporter exit code only increases in severity.

**Side Effects**

- Reads schema JSON files.
- Reads review JSON files.
- Writes validation status to stdout or stderr.
- Catches `json.JSONDecodeError` for review files.

---

## `cmd_contract_presence`

**Signature**

```python
def cmd_contract_presence(args: argparse.Namespace) -> int
```

**Preconditions**

- `args.repo_root` is present and path-like.
- `args.profile` is present and either falsey or path-like.
- The loaded profile is expected to provide optional `sensitive_paths` and `contract_exemptions`.
- Sensitive Python files are expected to be UTF-8 readable.

**Postconditions / Return Guarantees**

- Returns an integer exit code.
- Returns `EXIT_CONFIG_ERROR` when no banking profile is found.
- For Python files in sensitive paths, reports whether each discovered function has a matching contract name or exemption.
- Reports non-Python sensitive files as skipped warnings.
- Returns `EXIT_FAIL` if any checked function is missing a contract block or if a sensitive Python file cannot be read.

**Invariants**

- Does not modify source files or profile files.
- Reporter exit code only increases in severity.
- Each sensitive file yielded by `iter_files_under_sensitive` is processed at most once.

**Side Effects**

- Reads profile YAML.
- Reads source files.
- Writes status lines to stdout or stderr.
- Catches `OSError` and `UnicodeDecodeError` while reading source files.

---

## `cmd_contract_validate`

**Signature**

```python
def cmd_contract_validate(args: argparse.Namespace) -> int
```

**Preconditions**

- `args.repo_root` is present and path-like.
- `args.profile` is present and either falsey or path-like.
- The loaded profile is expected to provide optional `sensitive_paths`.
- `CONTRACT_SCHEMA_PATH` is expected to identify a readable JSON schema.
- Contract blocks are expected to be YAML mappings.

**Postconditions / Return Guarantees**

- Returns an integer exit code.
- Returns `EXIT_CONFIG_ERROR` when no banking profile is found.
- Validates each extracted contract block against the contract schema.
- Emits a warning when no contract blocks are found.
- Returns `EXIT_FAIL` if any contract block has a parse error or schema validation error.
- Returns `EXIT_OK` when all found contract blocks validate and no failures are recorded.

**Invariants**

- Does not modify source files, profile files, or schema files.
- Reporter exit code only increases in severity.

**Side Effects**

- Reads profile YAML.
- Reads contract schema JSON.
- Reads sensitive-path files.
- Writes status lines to stdout or stderr.
- Catches `OSError` and `UnicodeDecodeError` while reading sensitive files.

---

## `cmd_floats_check`

**Signature**

```python
def cmd_floats_check(args: argparse.Namespace) -> int
```

**Preconditions**

- `args.repo_root` is present and path-like.
- `args.profile` is present and either falsey or path-like.
- The loaded profile is expected to provide optional `sensitive_paths`.
- Files with extensions listed in `FLOAT_PATTERNS` are expected to be UTF-8 readable for scanning.

**Postconditions / Return Guarantees**

- Returns an integer exit code.
- Returns `EXIT_CONFIG_ERROR` when no banking profile is found.
- Scans sensitive files with known extensions for configured float-related regex patterns.
- Returns `EXIT_FAIL` if any pattern match is reported.
- Returns `EXIT_OK` when checked files contain no matches.
- Emits warnings for skipped extensions and for no known-extension files.

**Invariants**

- Does not modify scanned files.
- Reporter exit code only increases in severity.
- `FLOAT_PATTERNS` is read but not mutated.

**Side Effects**

- Reads profile YAML.
- Reads sensitive-path files.
- Writes status lines to stdout or stderr.
- Catches `OSError` and `UnicodeDecodeError` while reading scanned files.

---

## `cmd_review_gate`

**Signature**

```python
def cmd_review_gate(args: argparse.Namespace) -> int
```

**Preconditions**

- `args.repo_root` is present and path-like.
- `args.branch` is present.
- Review data is expected under `.claude/reviews/<branch>` or literal branch directory.
- Round JSON documents are expected to contain review metadata such as `agent`, `round`, `verdict`, `findings`, and acknowledgements when applicable.

**Postconditions / Return Guarantees**

- Returns an integer exit code.
- Returns `EXIT_CONFIG_ERROR` when the review directory is not found.
- Returns `EXIT_FAIL` when required review gate conditions are not met.
- Returns `EXIT_OK` when all gate checks pass.
- Checks for:
  - `manifest.json` presence.
  - Latest round data for `code-reviewer`.
  - Latest round data for `math-auditor`.
  - Code reviewer latest verdict equal to `"approve"`.
  - Non-empty math auditor `contract_only_summary`.
  - Resolved acknowledgements for blocker and major findings.

**Invariants**

- Does not modify review files.
- Reporter exit code only increases in severity.
- Findings are deduplicated by `id`, with later files overwriting earlier entries in sorted filename order.

**Side Effects**

- Reads review JSON files.
- Reads filesystem metadata.
- Writes status lines to stdout or stderr.
- Catches `json.JSONDecodeError` while reading round files.

---

## `cmd_all`

**Signature**

```python
def cmd_all(args: argparse.Namespace) -> int
```

**Preconditions**

- `args.repo_root` is present and path-like.
- `args.branch` may be present.
- If `.banking-profile` exists, all standalone checks expect their normal profile, schema, and source-file inputs.

**Postconditions / Return Guarantees**

- Returns an integer exit code.
- Returns `EXIT_OK` immediately when `.banking-profile` is absent.
- Otherwise runs:
  - `cmd_profile_validate`
  - `cmd_contract_validate`
  - `cmd_contract_presence`
  - `cmd_floats_check`
- Also runs `cmd_review_validate` and `cmd_review_gate` when `args.branch` is provided.
- Returns the maximum exit code produced by invoked checks.

**Invariants**

- Does not directly modify repository files.
- Aggregated exit code is monotonic across invoked checks.

**Side Effects**

- Reads filesystem metadata.
- Invokes other command functions, inheriting their read and output side effects.
- Writes section headers and final aggregate status to stdout.

---

## `build_parser`

**Signature**

```python
def build_parser() -> argparse.ArgumentParser
```

**Preconditions**

- No input arguments.
- `argparse` is available.

**Postconditions / Return Guarantees**

- Returns an `argparse.ArgumentParser`.
- Parser program name is `"bankcheck"`.
- Parser includes global `--repo-root`.
- Parser defines required subcommands:
  - `profile-validate`
  - `review-validate`
  - `contract-presence`
  - `contract-validate`
  - `floats-check`
  - `review-gate`
  - `all`
- Each subcommand is configured with its corresponding handler through `set_defaults(func=...)`.

**Invariants**

- Does not mutate module constants.
- Constructs a new parser on each call.

**Side Effects**

- Allocates parser and subparser objects.
- No file I/O.

---

## `main`

**Signature**

```python
def main(argv: list[str] | None = None) -> int
```

**Preconditions**

- `argv`, when provided, is a list of command-line argument strings compatible with `argparse`.
- When `argv` is `None`, command-line arguments are taken from process context by `argparse`.

**Postconditions / Return Guarantees**

- Returns an integer exit code.
- Builds the CLI parser.
- Parses arguments.
- Invokes the selected subcommand handler through `args.func(args)`.
- Returns `EXIT_CONFIG_ERROR` after printing help if no handler is present.

**Invariants**

- Does not mutate `argv`.
- Delegates command behavior to the selected handler.

**Side Effects**

- May read process command-line context through `argparse`.
- May write help text to stdout.
- Invokes selected command function, inheriting its side effects.
- May raise `SystemExit` from `argparse` argument parsing behavior.
