# Contract Document: `csv.py`

## Public Re-Exported Functions

The following public functions are imported from `_csv` and re-exported by this module:

```python
reader
writer
register_dialect
unregister_dialect
get_dialect
list_dialects
field_size_limit
```

Their detailed runtime behavior is provided by `_csv`. This module guarantees only that these names are imported into module scope and included in `__all__`.

## `class Dialect`

```python
class Dialect
```

Describes a CSV dialect. Intended to be subclassed.

### Public Attributes

```python
delimiter
quotechar
escapechar
doublequote
skipinitialspace
lineterminator
quoting
```

### Invariants

- A dialect object exposes CSV formatting attributes used by `_csv.Dialect`.
- Base `Dialect` has placeholder attributes initialized to `None`.
- Subclasses may define concrete dialect attributes.
- `_name` defaults to `""`.
- `_valid` defaults to `False`.

### `Dialect.__init__`

```python
def __init__(self)
```

#### Preconditions

- `self` is an instance of `Dialect` or a subclass.
- Required dialect attributes must be acceptable to `_csv.Dialect`.

#### Postconditions / Return Guarantees

- Returns `None`.
- If `self.__class__ != Dialect`, sets `self._valid = True`.
- Calls `self._validate()`.

#### Invariants

- Validation is attempted during construction.
- Subclasses are marked valid before validation.

#### Side Effects / Exceptions

- May raise `csv.Error` if validation by `_csv.Dialect` raises `TypeError`.

### `Dialect._validate`

```python
def _validate(self)
```

#### Preconditions

- `self` exposes dialect attributes expected by `_csv.Dialect`.

#### Postconditions / Return Guarantees

- Returns `None` if `_csv.Dialect(self)` accepts the object.

#### Invariants

- Validation is delegated to `_csv.Dialect`.

#### Side Effects / Exceptions

- Converts `TypeError` from `_csv.Dialect(self)` into `csv.Error` with the same message text.

## `class excel`

```python
class excel(Dialect)
```

Describes the usual properties of Excel-generated CSV files.

### Class Attributes

```python
delimiter = ","
quotechar = '"'
doublequote = True
skipinitialspace = False
lineterminator = "\r\n"
quoting = QUOTE_MINIMAL
```

### Preconditions

- Uses `Dialect` initialization and validation rules.

### Postconditions / Return Guarantees

- Instances are valid dialect objects if class attributes are accepted by `_csv.Dialect`.

### Invariants

- Uses comma as delimiter.
- Uses double quote as quote character.
- Uses CRLF line terminator.
- Uses minimal quoting.

### Side Effects / Exceptions

- At module import time, registered under dialect name `"excel"` via:

```python
register_dialect("excel", excel)
```

- Construction may raise `csv.Error` through `Dialect.__init__`.

## `class excel_tab`

```python
class excel_tab(excel)
```

Describes the usual properties of Excel-generated tab-delimited files.

### Class Attributes

```python
delimiter = "\t"
```

Inherited from `excel`:

```python
quotechar = '"'
doublequote = True
skipinitialspace = False
lineterminator = "\r\n"
quoting = QUOTE_MINIMAL
```

### Preconditions

- Uses `Dialect` initialization and validation rules.

### Postconditions / Return Guarantees

- Instances are valid dialect objects if class attributes are accepted by `_csv.Dialect`.

### Invariants

- Uses tab as delimiter.
- Otherwise inherits Excel CSV formatting behavior.

### Side Effects / Exceptions

- At module import time, registered under dialect name `"excel-tab"` via:

```python
register_dialect("excel-tab", excel_tab)
```

- Construction may raise `csv.Error` through `Dialect.__init__`.

## `class unix_dialect`

```python
class unix_dialect(Dialect)
```

Describes the usual properties of Unix-generated CSV files.

### Class Attributes

```python
delimiter = ","
quotechar = '"'
doublequote = True
skipinitialspace = False
lineterminator = "\n"
quoting = QUOTE_ALL
```

### Preconditions

- Uses `Dialect` initialization and validation rules.

### Postconditions / Return Guarantees

- Instances are valid dialect objects if class attributes are accepted by `_csv.Dialect`.

### Invariants

- Uses comma as delimiter.
- Uses double quote as quote character.
- Uses LF line terminator.
- Quotes all fields.

### Side Effects / Exceptions

- At module import time, registered under dialect name `"unix"` via:

```python
register_dialect("unix", unix_dialect)
```

- Construction may raise `csv.Error` through `Dialect.__init__`.

## `class DictReader`

```python
class DictReader
```

Iterates over CSV rows and returns dictionaries keyed by field names.

### `DictReader.__init__`

```python
def __init__(
    self,
    f,
    fieldnames=None,
    restkey=None,
    restval=None,
    dialect="excel",
    *args,
    **kwds
)
```

#### Preconditions

- `f` is suitable for `_csv.reader`.
- `dialect`, `*args`, and `**kwds` are suitable for `_csv.reader`.
- If `fieldnames` is an iterator object, it must be consumable into a list.

#### Postconditions / Return Guarantees

- Returns `None`.
- If `fieldnames` is an iterator, stores `list(fieldnames)`.
- Stores field names in `self._fieldnames`.
- Stores `restkey`, `restval`, `dialect`.
- Creates `self.reader = reader(f, dialect, *args, **kwds)`.
- Initializes `self.line_num = 0`.

#### Invariants

- `self.reader` is the underlying CSV reader.
- `self.line_num` tracks the underlying reader line number after reads.
- `self.restkey` receives surplus row fields.
- `self.restval` supplies missing row values.

#### Side Effects / Exceptions

- May propagate exceptions raised by `reader(...)`.

### `DictReader.__iter__`

```python
def __iter__(self)
```

#### Preconditions

- None beyond a constructed `DictReader`.

#### Postconditions / Return Guarantees

- Returns `self`.

#### Invariants

- `DictReader` is its own iterator.

#### Side Effects / Exceptions

- None specified.

### `DictReader.fieldnames`

```python
@property
def fieldnames(self)
```

#### Preconditions

- `self.reader` is an iterator yielding CSV rows.

#### Postconditions / Return Guarantees

- If `self._fieldnames` is `None`, attempts to read the next row from `self.reader` and store it as field names.
- If the reader is exhausted, leaves `self._fieldnames` unchanged.
- Updates `self.line_num` from `self.reader.line_num`.
- Returns `self._fieldnames`.

#### Invariants

- Field names are lazily initialized from the first CSV row when not provided.

#### Side Effects / Exceptions

- Consumes one row from the underlying reader when field names are not already set.
- May propagate exceptions from the underlying reader except `StopIteration`, which is handled.

### `DictReader.fieldnames` setter

```python
@fieldnames.setter
def fieldnames(self, value)
```

#### Preconditions

- None specified.

#### Postconditions / Return Guarantees

- Sets `self._fieldnames = value`.
- Returns `None`.

#### Invariants

- Future rows use the assigned field names.

#### Side Effects / Exceptions

- Mutates `self._fieldnames`.

### `DictReader.__next__`

```python
def __next__(self)
```

#### Preconditions

- `self.reader` is an iterator yielding CSV rows.
- `self.fieldnames` is either already set or can be obtained from the reader.
- Field names support `len`, slicing, and iteration when used.

#### Postconditions / Return Guarantees

- Returns a dictionary representing the next non-empty CSV row.
- If `line_num == 0`, initializes field names for side effect.
- Updates `self.line_num` from `self.reader.line_num`.
- Empty rows `[]` are skipped.
- Maps row values to field names using `dict(zip(self.fieldnames, row))`.
- If the row has more values than field names, stores surplus values under `self.restkey`.
- If the row has fewer values than field names, fills missing field names with `self.restval`.

#### Invariants

- Returned rows are dictionaries.
- Blank rows are not returned.

#### Side Effects / Exceptions

- Consumes rows from the underlying reader.
- May raise `StopIteration` when no next data row exists.
- May propagate exceptions from the underlying reader.

### `DictReader.__class_getitem__`

```python
__class_getitem__ = classmethod(types.GenericAlias)
```

#### Preconditions

- Used through class subscription syntax.

#### Postconditions / Return Guarantees

- Provides generic alias behavior for `DictReader[...]`.

#### Invariants

- Does not affect iteration behavior.

#### Side Effects / Exceptions

- Behavior delegated to `types.GenericAlias`.

## `class DictWriter`

```python
class DictWriter
```

Writes dictionaries as CSV rows using configured field names.

### `DictWriter.__init__`

```python
def __init__(
    self,
    f,
    fieldnames,
    restval="",
    extrasaction="raise",
    dialect="excel",
    *args,
    **kwds
)
```

#### Preconditions

- `f` is suitable for `_csv.writer`.
- `fieldnames` is iterable and supports membership checks during row conversion.
- If `fieldnames` is an iterator object, it must be consumable into a list.
- `extrasaction.lower()` must be either `"raise"` or `"ignore"`.

#### Postconditions / Return Guarantees

- Returns `None`.
- If `fieldnames` is an iterator, stores `list(fieldnames)`.
- Stores `self.fieldnames`.
- Stores `self.restval`.
- Stores normalized lowercase `self.extrasaction`.
- Creates `self.writer = writer(f, dialect, *args, **kwds)`.

#### Invariants

- `self.fieldnames` defines output column order.
- `self.restval` is used when a row dictionary lacks a field.
- `self.extrasaction` is either `"raise"` or `"ignore"`.

#### Side Effects / Exceptions

- Raises `ValueError` if `extrasaction` is not `"raise"` or `"ignore"` after lowercasing.
- May propagate exceptions from `writer(...)`.

### `DictWriter.writeheader`

```python
def writeheader(self)
```

#### Preconditions

- `self.fieldnames` is iterable.
- Underlying writer is ready to write a row.

#### Postconditions / Return Guarantees

- Writes a header row where each field name is mapped to itself.
- Returns the result of `self.writerow(header)`.

#### Invariants

- Header column order follows `self.fieldnames`.

#### Side Effects / Exceptions

- Writes to the underlying writer target.
- May propagate exceptions from `writerow`.

### `DictWriter._dict_to_list`

```python
def _dict_to_list(self, rowdict)
```

#### Preconditions

- `rowdict` provides `.keys()` and `.get(key, default)`.
- `self.fieldnames` is iterable.
- When `extrasaction == "raise"`, `rowdict.keys() - self.fieldnames` is supported.

#### Postconditions / Return Guarantees

- Returns a generator producing values for each key in `self.fieldnames`.
- For missing keys, yields `self.restval`.
- If `extrasaction == "ignore"`, extra keys in `rowdict` do not affect the generated output.

#### Invariants

- Generated values follow `self.fieldnames` order.

#### Side Effects / Exceptions

- If `extrasaction == "raise"` and `rowdict` contains fields not in `self.fieldnames`, raises `ValueError`.

### `DictWriter.writerow`

```python
def writerow(self, rowdict)
```

#### Preconditions

- `rowdict` satisfies `_dict_to_list` preconditions.
- Underlying writer supports `.writerow(...)`.

#### Postconditions / Return Guarantees

- Converts `rowdict` to an ordered value generator.
- Returns the result of `self.writer.writerow(...)`.

#### Invariants

- Output column order follows `self.fieldnames`.

#### Side Effects / Exceptions

- Writes one row to the underlying writer target.
- May raise `ValueError` from `_dict_to_list`.
- May propagate exceptions from the underlying writer.

### `DictWriter.writerows`

```python
def writerows(self, rowdicts)
```

#### Preconditions

- `rowdicts` is iterable.
- Each item satisfies `_dict_to_list` preconditions.
- Underlying writer supports `.writerows(...)`.

#### Postconditions / Return Guarantees

- Converts each row dictionary using `_dict_to_list`.
- Returns the result of `self.writer.writerows(...)`.

#### Invariants

- Each output row follows `self.fieldnames` order.

#### Side Effects / Exceptions

- Writes multiple rows to the underlying writer target.
- May raise `ValueError` from `_dict_to_list`.
- May propagate exceptions from the underlying writer.

### `DictWriter.__class_getitem__`

```python
__class_getitem__ = classmethod(types.GenericAlias)
```

#### Preconditions

- Used through class subscription syntax.

#### Postconditions / Return Guarantees

- Provides generic alias behavior for `DictWriter[...]`.

#### Invariants

- Does not affect writing behavior.

#### Side Effects / Exceptions

- Behavior delegated to `types.GenericAlias`.

## `class Sniffer`

```python
class Sniffer
```

Inspects CSV samples to infer formatting characteristics.

### `Sniffer.__init__`

```python
def __init__(self)
```

#### Preconditions

- None.

#### Postconditions / Return Guarantees

- Returns `None`.
- Initializes:

```python
self.preferred = [",", "\t", ";", " ", ":"]
```

#### Invariants

- `self.preferred` is used as a delimiter preference order when multiple candidates are available.

#### Side Effects / Exceptions

- Mutates the instance by setting `preferred`.

### `Sniffer.sniff`

```python
def sniff(self, sample, delimiters=None)
```

#### Preconditions

- `sample` is text suitable for regular-expression matching and delimiter analysis.
- `delimiters`, if provided, is a collection used to restrict delimiter candidates.

#### Postconditions / Return Guarantees

- Returns a dynamically defined subclass of `Dialect`.
- The returned dialect has:
  - `_name = "sniffed"`
  - `lineterminator = "\r\n"`
  - `quoting = QUOTE_MINIMAL`
  - `doublequote` inferred from the sample
  - `delimiter` inferred from the sample
  - `quotechar` inferred from the sample, or `"` if none is inferred
  - `skipinitialspace` inferred from the sample

#### Invariants

- Quote and delimiter guessing is attempted before delimiter-only guessing.
- A delimiter must be determined before a dialect is returned.

#### Side Effects / Exceptions

- Raises `csv.Error("Could not determine delimiter")` if no delimiter is determined.

### `Sniffer._guess_quote_and_delimiter`

```python
def _guess_quote_and_delimiter(self, data, delimiters)
```

#### Preconditions

- `data` is text suitable for `re` matching.
- `delimiters`, if provided, supports membership tests.

#### Postconditions / Return Guarantees

- Returns a tuple:

```python
(quotechar, doublequote, delimiter, skipinitialspace)
```

- If no quoted patterns are found, returns:

```python
("", False, None, 0)
```

- Selects the most frequent quote character among matches.
- Selects the most frequent delimiter among allowed matched delimiters.
- If no delimiter is found but quotes are found, returns delimiter `""`.
- Determines `skipinitialspace` from whether matched delimiter occurrences correspond to matched spaces.
- Determines `doublequote` by searching for repeated quote usage within delimiter boundaries.

#### Invariants

- Delimiter candidates are filtered by `delimiters` when provided.
- Quote character is inferred from matched quoted text.

#### Side Effects / Exceptions

- Uses regular-expression compilation and matching.
- May propagate exceptions from `re` operations or data operations.

### `Sniffer._guess_delimiter`

```python
def _guess_delimiter(self, data, delimiters)
```

#### Preconditions

- `data` is text supporting `.split("\n")`.
- `delimiters`, if provided, supports membership tests.

#### Postconditions / Return Guarantees

- Returns a tuple:

```python
(delimiter, skipinitialspace)
```

- Analyzes non-empty lines from `data`.
- Considers 7-bit ASCII characters as delimiter candidates.
- Computes per-line character frequencies and consistency across rows.
- If exactly one delimiter candidate is found, returns it.
- If multiple delimiter candidates are found, prefers the first present character from:

```python
self.preferred
```

- If no delimiter candidate is found, returns:

```python
("", 0)
```

- Determines `skipinitialspace` by comparing delimiter count in the first row with delimiter-plus-space count.

#### Invariants

- Candidate delimiters must occur with positive expected frequency and positive consistency score.
- Candidate delimiters are restricted to `delimiters` when provided.
- Analysis proceeds in chunks of up to 10 rows.

#### Side Effects / Exceptions

- Performs frequency analysis over input text.
- May propagate exceptions from string or collection operations.

### `Sniffer.has_header`

```python
def has_header(self, sample)
```

#### Preconditions

- `sample` is text suitable for `StringIO`, `sniff`, and `reader`.
- The sample contains at least one row readable by the inferred dialect.

#### Postconditions / Return Guarantees

- Returns `True` if the internal vote indicates the first row is a header.
- Returns `False` otherwise.
- Uses the first row as the candidate header.
- Checks up to 21 subsequent regular rows.
- Skips rows whose column count differs from the candidate header.
- Tracks per-column data characteristics using numeric conversion to `complex` or string length.
- Compares candidate header values against inferred column characteristics to compute a vote.

#### Invariants

- Header inference is based on consistency of column characteristics after the first row.
- Columns with inconsistent characteristics are removed from consideration.

#### Side Effects / Exceptions

- Calls `self.sniff(sample)`.
- Constructs a CSV reader over `StringIO(sample)`.
- Consumes rows from that reader.
- May propagate exceptions from `sniff`, `reader`, `next`, or row processing.
