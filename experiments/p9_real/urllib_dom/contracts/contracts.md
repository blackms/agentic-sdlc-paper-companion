# Contract Document: URL Parsing Module

## `clear_cache()`

**Signature:** `clear_cache()`

**Preconditions:** None.

**Postconditions / Return Guarantees:**
- Clears internal caches used by URL splitting and byte quoting.
- Returns `None`.

**Invariants:**
- Does not change parsing or quoting semantics.

**Side Effects / Exceptions:**
- Mutates internal cache state.
- No specified exceptions.

---

## `urlparse`

**Signature:** `urlparse(url, scheme='', allow_fragments=True)`

**Preconditions:**
- `url` and `scheme` must both be string-like of compatible type: both `str`, or both bytes-compatible, except empty defaults.
- Bytes inputs are decoded using ASCII with strict errors.

**Postconditions / Return Guarantees:**
- Returns a `ParseResult` for `str` input or `ParseResultBytes` for bytes input.
- Result fields are:
  `scheme`, `netloc`, `path`, `params`, `query`, `fragment`.
- Uses `scheme` as the default scheme when no scheme is present in `url`.
- Does not expand percent escapes.
- If `allow_fragments` is false, fragments are not separated.
- Splits path parameters only for schemes listed in `uses_params`.

**Invariants:**
- Returned result is tuple-compatible and has named fields.
- Result supports `geturl()`.
- Results containing `netloc` expose `username`, `password`, `hostname`, and `port`.

**Side Effects / Exceptions:**
- May raise `TypeError` when mixing `str` and non-`str` arguments.
- May raise `UnicodeDecodeError` for non-ASCII bytes input.
- May raise `ValueError` for invalid bracketed host or invalid netloc normalization.

---

## `urlsplit`

**Signature:** `urlsplit(url, scheme='', allow_fragments=True)`

**Preconditions:**
- `url` and `scheme` must both be compatible string types.
- Bytes inputs must be ASCII-decodable.
- `allow_fragments` is interpreted as `bool(allow_fragments)`.

**Postconditions / Return Guarantees:**
- Returns a `SplitResult` for `str` input or `SplitResultBytes` for bytes input.
- Result fields are:
  `scheme`, `netloc`, `path`, `query`, `fragment`.
- Leading WHATWG C0 control characters and spaces are stripped from `url`.
- C0 unsafe URL bytes `\t`, `\r`, and `\n` are removed from `url` and `scheme`.
- Scheme names are lowercased when detected.
- Does not expand percent escapes.

**Invariants:**
- Function is cached with typed cache keys.
- Returned result is tuple-compatible and has named fields.
- Results expose `username`, `password`, `hostname`, and `port`.

**Side Effects / Exceptions:**
- May raise `TypeError` when mixing incompatible argument types.
- May raise `UnicodeDecodeError` for non-ASCII bytes input.
- May raise `ValueError` for invalid IPv6-style bracket use, invalid bracketed host, or invalid netloc normalization.

---

## `urlunparse`

**Signature:** `urlunparse(components)`

**Preconditions:**
- `components` must provide exactly six compatible components:
  `scheme`, `netloc`, `path`, `params`, `query`, `fragment`.
- Components must be all `str` or all bytes-compatible.

**Postconditions / Return Guarantees:**
- Combines parsed URL components into a URL string or bytes object.
- If `params` is non-empty, appends it to the path after `;`.
- May omit redundant delimiters such as an empty query marker.

**Invariants:**
- Output type corresponds to input component type.

**Side Effects / Exceptions:**
- May raise unpacking errors if component count is not six.
- May raise `TypeError` for mixed string and bytes-compatible components.
- May raise encoding or decoding exceptions during coercion.

---

## `urlunsplit`

**Signature:** `urlunsplit(components)`

**Preconditions:**
- `components` must provide exactly five compatible components:
  `scheme`, `netloc`, `path`, `query`, `fragment`.
- Components must be all `str` or all bytes-compatible.

**Postconditions / Return Guarantees:**
- Combines split URL components into a complete URL.
- Inserts `//` where required by netloc or applicable scheme rules.
- Prefixes query with `?` only when query is non-empty.
- Prefixes fragment with `#` only when fragment is non-empty.
- May omit unnecessary delimiters.

**Invariants:**
- Output type corresponds to input component type.

**Side Effects / Exceptions:**
- May raise unpacking errors if component count is not five.
- May raise `TypeError` for mixed component types.
- May raise encoding or decoding exceptions during coercion.

---

## `urljoin`

**Signature:** `urljoin(base, url, allow_fragments=True)`

**Preconditions:**
- `base` and `url` must be compatible string types when both are non-empty.
- Bytes inputs must be ASCII-decodable.

**Postconditions / Return Guarantees:**
- Returns an absolute interpretation of `url` relative to `base`.
- If `base` is empty, returns `url`.
- If `url` is empty, returns `base`.
- Preserves absolute `url` when its scheme differs from `base` or is not relative.
- Resolves `.` and `..` path segments.
- Carries over base scheme, netloc, path, params, or query where required by URL joining rules.

**Invariants:**
- Output type follows the coerced input type.

**Side Effects / Exceptions:**
- May raise `TypeError`, `UnicodeDecodeError`, or `ValueError` from parsing/coercion.

---

## `urldefrag`

**Signature:** `urldefrag(url)`

**Preconditions:**
- `url` must be `str` or bytes-compatible.
- Bytes input must be ASCII-decodable.

**Postconditions / Return Guarantees:**
- Returns `DefragResult` or `DefragResultBytes`.
- Result fields are:
  `url`, `fragment`.
- If `url` contains a fragment, the returned `url` excludes it and `fragment` contains it.
- If no fragment exists, `fragment` is the empty string or empty bytes.

**Invariants:**
- `result.geturl()` reconstructs the defragmented URL plus fragment when present.

**Side Effects / Exceptions:**
- May raise parsing/coercion exceptions.

---

## `unquote_to_bytes`

**Signature:** `unquote_to_bytes(string)`

**Preconditions:**
- `string` must be string-like with `.split`, or bytes-like / bytearray-like.
- `str` input is encoded as UTF-8 before percent decoding.

**Postconditions / Return Guarantees:**
- Returns `bytes`.
- Replaces valid `%xx` escapes with corresponding byte values.
- Invalid percent escapes are preserved with `%`.

**Invariants:**
- Empty input returns `b''`.

**Side Effects / Exceptions:**
- May raise attribute/type errors if input is not string-like or bytes-like.

---

## `unquote`

**Signature:** `unquote(string, encoding='utf-8', errors='replace')`

**Preconditions:**
- `string` must be `str` or `bytes`.
- `encoding` and `errors` are accepted by `bytes.decode`.

**Postconditions / Return Guarantees:**
- Returns `str`.
- Replaces percent escapes with decoded characters.
- Bytes input is percent-decoded and then decoded using `encoding` and `errors`.
- If `encoding` is `None`, UTF-8 is used.
- If `errors` is `None`, `'replace'` is used.
- If no `%` exists in a `str`, returns the original string object.

**Invariants:**
- Non-ASCII portions of `str` input are preserved except where percent-decoded ASCII runs produce decoded text.

**Side Effects / Exceptions:**
- May raise decoding exceptions depending on `errors`.
- May raise attribute/type errors for unsupported input.

---

## `unquote_plus`

**Signature:** `unquote_plus(string, encoding='utf-8', errors='replace')`

**Preconditions:**
- `string` must support `.replace('+', ' ')`.
- Intended for string form values.

**Postconditions / Return Guarantees:**
- Replaces plus signs with spaces.
- Then applies `unquote`.
- Returns `str`.

**Invariants:**
- Percent-decoding behavior matches `unquote`.

**Side Effects / Exceptions:**
- May raise exceptions from `.replace` or `unquote`.

---

## `parse_qs`

**Signature:** `parse_qs(qs, keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None, separator='&')`

**Preconditions:**
- `qs` is a percent-encoded query string or bytes-like query.
- `separator` must be non-empty `str` or `bytes`.
- `encoding` and `errors` are used for decoding string query components.

**Postconditions / Return Guarantees:**
- Returns a dictionary.
- Keys are query parameter names.
- Values are lists of values for each name.
- Delegates field parsing to `parse_qsl`.
- Repeated names accumulate values in insertion order.

**Invariants:**
- Output grouping preserves the pair order produced by `parse_qsl`.

**Side Effects / Exceptions:**
- May raise `ValueError` from `parse_qsl` for invalid separator, strict parsing errors, or field count limit.
- May raise type or decoding exceptions from `parse_qsl`.

---

## `parse_qsl`

**Signature:** `parse_qsl(qs, keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None, separator='&')`

**Preconditions:**
- `separator` must be a non-empty `str` or `bytes`.
- `qs` may be `str` or bytes-like.
- Bytes-like `qs` must be acceptable to `memoryview`.
- If `max_num_fields` is not `None`, it must be comparable with an integer field count.

**Postconditions / Return Guarantees:**
- Returns a list of `(name, value)` pairs.
- For `str` input, names and values are decoded with `unquote_plus`.
- For bytes-like input, names and values are returned as bytes after replacing `+` with space and percent-decoding.
- Blank values are included only when `keep_blank_values` is true.
- Empty query input returns `[]`.
- Field splitting uses `separator`.

**Invariants:**
- Pair order follows the order in the query string.
- A field contributes a pair only when it has a value or blank values are retained.

**Side Effects / Exceptions:**
- Raises `ValueError` if `separator` is invalid.
- Raises `ValueError` if `strict_parsing` is true and a field lacks `=`.
- Raises `ValueError` if `max_num_fields` is exceeded.
- May raise encoding/type exceptions for incompatible separator or query values.

---

## `quote`

**Signature:** `quote(string, safe='/', encoding=None, errors=None)`

**Preconditions:**
- `string` must be `str` or bytes-like accepted by `quote_from_bytes`.
- `safe` may be `str` or bytes-like.
- `encoding` and `errors` must not be supplied when `string` is bytes.

**Postconditions / Return Guarantees:**
- Returns an ASCII `str`.
- Percent-escapes characters not in the always-safe set or `safe`.
- For `str` input, encodes using `encoding` and `errors`.
- Defaults to UTF-8 and strict encoding for `str`.
- Empty `str` input returns the same empty string.

**Invariants:**
- Always-safe characters are letters, digits, `_`, `.`, `-`, and `~`.
- Default `safe` preserves `/`.

**Side Effects / Exceptions:**
- Raises `TypeError` if `encoding` or `errors` is supplied for bytes input.
- May raise `UnicodeEncodeError` for `str` input with strict encoding.
- May raise `TypeError` from `quote_from_bytes`.

---

## `quote_plus`

**Signature:** `quote_plus(string, safe='', encoding=None, errors=None)`

**Preconditions:**
- Same as `quote`.
- `safe` must be compatible with adding a space of matching type.

**Postconditions / Return Guarantees:**
- Returns an ASCII `str`.
- Like `quote`, but spaces are encoded as `+`.
- Literal plus signs are escaped unless included in `safe`.
- Does not default `safe` to `/`.

**Invariants:**
- When input contains no spaces, result is the same as `quote(string, safe, encoding, errors)`.

**Side Effects / Exceptions:**
- Same as `quote`.

---

## `quote_from_bytes`

**Signature:** `quote_from_bytes(bs, safe='/')`

**Preconditions:**
- `bs` must be `bytes` or `bytearray`.
- `safe` may be `str` or bytes-like.
- If `safe` is `str`, non-ASCII characters are ignored when converting to bytes.

**Postconditions / Return Guarantees:**
- Returns an ASCII `str`.
- Percent-escapes bytes not in the always-safe set or `safe`.
- Empty input returns `''`.
- If all bytes are safe, returns `bs.decode()`.

**Invariants:**
- Percent escapes use uppercase hexadecimal digits.

**Side Effects / Exceptions:**
- Raises `TypeError` if `bs` is not `bytes` or `bytearray`.
- May raise type errors when `safe` is not iterable bytes-like or string-like.

---

## `urlencode`

**Signature:** `urlencode(query, doseq=False, safe='', encoding=None, errors=None, quote_via=quote_plus)`

**Preconditions:**
- `query` must be a mapping with `.items()` or a sequence of two-element tuples.
- Query keys and values may be strings, bytes, or objects convertible with `str`.
- `quote_via` must accept the call forms used by this function.
- If `doseq` is true, non-string, non-bytes values with `len()` are treated as sequences.

**Postconditions / Return Guarantees:**
- Returns a URL query string.
- Encodes each key-value pair as `key=value`.
- Joins pairs with `&`.
- Mapping input is processed through `.items()`.
- Sequence input preserves parameter order.
- With `doseq=True`, sequence values produce one parameter per element.

**Invariants:**
- Bytes keys/values are quoted without `encoding` and `errors`.
- Non-bytes keys/values are converted with `str()` before quoting.

**Side Effects / Exceptions:**
- Raises `TypeError` if `query` is not a valid mapping or non-string sequence of pairs.
- May raise exceptions from `quote_via`, `str`, iteration, or sequence handling.

---

## `to_bytes`

**Signature:** `to_bytes(url)`

**Preconditions:**
- `url` may be `str` or another object.

**Postconditions / Return Guarantees:**
- Emits a deprecation warning.
- Returns `_to_bytes(url)`.
- For ASCII `str`, returns an ASCII-only string.
- For non-`str`, returns the original object.

**Invariants:**
- Does not encode non-string objects.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.
- May raise `UnicodeError` for non-ASCII string input.

---

## `unwrap`

**Signature:** `unwrap(url)`

**Preconditions:**
- `url` must be convertible with `str(url)`.

**Postconditions / Return Guarantees:**
- Returns a stripped string.
- If enclosed in `<...>`, removes the surrounding angle brackets and strips again.
- If the resulting string starts with `URL:`, removes that prefix and strips again.
- Otherwise returns the stripped string unchanged.

**Invariants:**
- Return type is always `str`.

**Side Effects / Exceptions:**
- May raise exceptions from `str(url)`.

---

## Deprecated Split Helpers

These functions emit `DeprecationWarning` and delegate to their underscored implementations.

### `splittype`

**Signature:** `splittype(url)`

**Guarantees:**
- Returns `(scheme, data)` if `url` matches `scheme:data`, where `scheme` is lowercased.
- Otherwise returns `(None, url)`.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

### `splithost`

**Signature:** `splithost(url)`

**Guarantees:**
- For URLs matching `//host/path`, returns `(host, path)`.
- Ensures returned path starts with `/` when path exists.
- Otherwise returns `(None, url)`.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

### `splituser`

**Signature:** `splituser(host)`

**Guarantees:**
- Splits at the last `@`.
- Returns `(user, host)` when user info exists.
- Returns `(None, host)` otherwise.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

### `splitpasswd`

**Signature:** `splitpasswd(user)`

**Guarantees:**
- Splits at the first `:`.
- Returns `(user, passwd)` when password exists.
- Returns `(user, None)` otherwise.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

### `splitport`

**Signature:** `splitport(host)`

**Guarantees:**
- Returns `(host, port)` when `host` ends with `:<digits>`.
- Returns `(host, None)` otherwise.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

### `splitnport`

**Signature:** `splitnport(host, defport=-1)`

**Guarantees:**
- Splits host and port at the last `:`.
- Returns numeric port when present and valid ASCII digits.
- Returns `defport` when no port delimiter is found.
- Returns `None` as port when a delimiter exists but the port is not valid numeric text.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

### `splitquery`

**Signature:** `splitquery(url)`

**Guarantees:**
- Splits at the last `?`.
- Returns `(path, query)` when query delimiter exists.
- Returns `(url, None)` otherwise.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

### `splittag`

**Signature:** `splittag(url)`

**Guarantees:**
- Splits at the last `#`.
- Returns `(path, tag)` when tag delimiter exists.
- Returns `(url, None)` otherwise.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

### `splitattr`

**Signature:** `splitattr(url)`

**Guarantees:**
- Splits on `;`.
- Returns `(path, attrs)`, where `attrs` is a list of remaining components.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

### `splitvalue`

**Signature:** `splitvalue(attr)`

**Guarantees:**
- Splits at the first `=`.
- Returns `(attr, value)` when value delimiter exists.
- Returns `(attr, None)` otherwise.

**Side Effects / Exceptions:**
- Emits `DeprecationWarning`.

---

# Public Result Classes

## `DefragResult`

**Signature:** `DefragResult(url, fragment)`

**Preconditions:**
- Intended for string URL and fragment components.

**Postconditions / Return Guarantees:**
- Tuple-compatible two-field result.
- Fields:
  `url`, `fragment`.
- `url` is the URL without fragment identifier.
- `fragment` is the separated fragment identifier.

**Methods:**
- `geturl(self)`: returns `url + '#' + fragment` when `fragment` is non-empty; otherwise returns `url`.
- `encode(self, encoding='ascii', errors='strict')`: returns `DefragResultBytes` with each component encoded.

**Invariants:**
- Immutable namedtuple-style object.
- Has no instance `__dict__`.

**Side Effects / Exceptions:**
- `encode` may raise encoding exceptions.

---

## `DefragResultBytes`

**Signature:** `DefragResultBytes(url, fragment)`

**Preconditions:**
- Intended for bytes URL and fragment components.

**Postconditions / Return Guarantees:**
- Tuple-compatible two-field result.
- Fields:
  `url`, `fragment`.

**Methods:**
- `geturl(self)`: returns `url + b'#' + fragment` when `fragment` is non-empty; otherwise returns `url`.
- `decode(self, encoding='ascii', errors='strict')`: returns `DefragResult` with each component decoded.

**Invariants:**
- Immutable namedtuple-style object.
- Has no instance `__dict__`.

**Side Effects / Exceptions:**
- `decode` may raise decoding exceptions.

---

## `SplitResult`

**Signature:** `SplitResult(scheme, netloc, path, query, fragment)`

**Preconditions:**
- Intended for string URL components.

**Postconditions / Return Guarantees:**
- Tuple-compatible five-field result.
- Fields:
  `scheme`, `netloc`, `path`, `query`, `fragment`.
- `geturl()` reconstructs a URL using `urlunsplit(self)`.

**Properties:**
- `username`: user name from `netloc`, or `None`.
- `password`: password from `netloc`, or `None`.
- `hostname`: host name lowercased, preserving IPv6 zone suffix casing after `%`, or `None`.
- `port`: integer port, or `None`.

**Methods:**
- `encode(self, encoding='ascii', errors='strict')`: returns `SplitResultBytes`.

**Invariants:**
- Immutable namedtuple-style object.
- Has no instance `__dict__`.

**Side Effects / Exceptions:**
- `port` may raise `ValueError` if the port is non-numeric or outside `0..65535`.
- `encode` may raise encoding exceptions.

---

## `SplitResultBytes`

**Signature:** `SplitResultBytes(scheme, netloc, path, query, fragment)`

**Preconditions:**
- Intended for bytes URL components.

**Postconditions / Return Guarantees:**
- Tuple-compatible five-field result.
- Fields:
  `scheme`, `netloc`, `path`, `query`, `fragment`.
- `geturl()` reconstructs a URL using `urlunsplit(self)`.

**Properties:**
- `username`: user name from `netloc`, or `None`.
- `password`: password from `netloc`, or `None`.
- `hostname`: host name lowercased, preserving IPv6 zone suffix casing after `b'%'`, or `None`.
- `port`: integer port, or `None`.

**Methods:**
- `decode(self, encoding='ascii', errors='strict')`: returns `SplitResult`.

**Invariants:**
- Immutable namedtuple-style object.
- Has no instance `__dict__`.

**Side Effects / Exceptions:**
- `port` may raise `ValueError` if the port is non-numeric or outside `0..65535`.
- `decode` may raise decoding exceptions.

---

## `ParseResult`

**Signature:** `ParseResult(scheme, netloc, path, params, query, fragment)`

**Preconditions:**
- Intended for string URL components.

**Postconditions / Return Guarantees:**
- Tuple-compatible six-field result.
- Fields:
  `scheme`, `netloc`, `path`, `params`, `query`, `fragment`.
- `geturl()` reconstructs a URL using `urlunparse(self)`.

**Properties:**
- `username`: user name from `netloc`, or `None`.
- `password`: password from `netloc`, or `None`.
- `hostname`: host name lowercased, preserving IPv6 zone suffix casing after `%`, or `None`.
- `port`: integer port, or `None`.

**Methods:**
- `encode(self, encoding='ascii', errors='strict')`: returns `ParseResultBytes`.

**Invariants:**
- Immutable namedtuple-style object.
- Has no instance `__dict__`.

**Side Effects / Exceptions:**
- `port` may raise `ValueError` if the port is non-numeric or outside `0..65535`.
- `encode` may raise encoding exceptions.

---

## `ParseResultBytes`

**Signature:** `ParseResultBytes(scheme, netloc, path, params, query, fragment)`

**Preconditions:**
- Intended for bytes URL components.

**Postconditions / Return Guarantees:**
- Tuple-compatible six-field result.
- Fields:
  `scheme`, `netloc`, `path`, `params`, `query`, `fragment`.
- `geturl()` reconstructs a URL using `urlunparse(self)`.

**Properties:**
- `username`: user name from `netloc`, or `None`.
- `password`: password from `netloc`, or `None`.
- `hostname`: host name lowercased, preserving IPv6 zone suffix casing after `b'%'`, or `None`.
- `port`: integer port, or `None`.

**Methods:**
- `decode(self, encoding='ascii', errors='strict')`: returns `ParseResult`.

**Invariants:**
- Immutable namedtuple-style object.
- Has no instance `__dict__`.

**Side Effects / Exceptions:**
- `port` may raise `ValueError` if the port is non-numeric or outside `0..65535`.
- `decode` may raise decoding exceptions.

---

## `ResultBase`

**Signature:** `ResultBase`

**Contract:**
- Public alias for the string netloc result mixin used by structured URL results.
- Provides netloc-derived properties:
  `username`, `password`, `hostname`, and `port`.

**Side Effects / Exceptions:**
- `port` may raise `ValueError` for invalid or out-of-range port text.
