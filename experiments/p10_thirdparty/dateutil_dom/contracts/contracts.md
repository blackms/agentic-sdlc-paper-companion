# Contracts: dateutil_dom

## Module overview
(2-3 sentences: what the module does at a high level)

## Function/method contracts
For each top-level function and class method, document:
- **Signature**
- **Pre-conditions** (what must be true before calling)
- **Post-conditions** (what must be true after returning)
- **Invariants** (properties preserved)
- **Edge cases** (boundary conditions, exceptional inputs)
- **Operator-level invariants** if any (off-by-one, sign, comparison direction)

Be explicit and complete. The contract must be detailed enough that a reviewer who has NEVER seen the module could detect bugs by checking implementation against contracts.

CODE TO ANALYZE:
# -*- coding: utf-8 -*-
import datetime
import calendar

import operator
from math import copysign

from six import integer_types
from warnings import warn

from ._common import weekday

MO, TU, WE, TH, FR, SA, SU = weekdays = tuple(weekday(x) for x in range(7))

__all__ = ["relativedelta", "MO", "TU", "WE", "TH", "FR", "SA", "SU"]


class relativedelta(object):
    """
    The relativedelta type is designed to be applied to an existing datetime and
    can replace specific components of that datetime, or represents an interval
    of time.

    It is based on the specification of the excellent work done by M.-A. Lemburg
    in his
    `mx.DateTime <https://www.egenix.com/products/python/mxBase/mxDateTime/>`_ extension.
    However, notice that this type does *NOT* implement the same algorithm as
    his work. Do *NOT* expect it to behave like mx.DateTime's counterpart.

    There are two different ways to build a relativedelta instance. The
    first one is passing it two date/datetime classes::

        relativedelta(datetime1, datetime2)

    The second one is passing it any number of the following keyword arguments::

        relativedelta(arg1=x,arg2=y,arg3=z...)

        year, month, day, hour, minute, second, microsecond:
            Absolute information (argument is singular); adding or subtracting a
            relativedelta with absolute information does not perform an arithmetic
            operation, but rather REPLACES the corresponding value in the
            original datetime with the value(s) in relativedelta.

        years, months, weeks, days, hours, minutes, seconds, microseconds:
            Relative information, may be negative (argument is plural); adding
            or subtracting a relativedelta with relative information performs
            the corresponding arithmetic operation on the original datetime value
            with the information in the relativedelta.

        weekday:
            One of the weekday instances (MO, TU, etc) available in the
            relativedelta module. These instances may receive a parameter N,
            specifying the Nth weekday, which could be positive or negative
            (like MO(+1) or MO(-2)). Not specifying it is the same as specifying
            +1. You can also use an integer, where 0=MO. This argument is always
            relative e.g. if the calculated date is already Monday, using MO(1)
            or MO(-1) won't change the day. To effectively make it absolute, use
            it in combination with the day argument (e.g. day=1, MO(1) for first
            Monday of the month).

        leapdays:
            Will add given days to the date found, if year is a leap
            year, and the date found is post 28 of february.

        yearday, nlyearday:
            Set the yearday or the non-leap year day (jump leap days).
            These are converted to day/month/leapdays information.

    There are relative and absolute forms of the keyword
    arguments. The plural is relative, and the singular is
    absolute. For each argument in the order below, the absolute form
    is applied first (by setting each attribute to that value) and
    then the relative form (by adding the value to the attribute).

    The order of attributes considered when this relativedelta is
    added to a datetime is:

    1. Year
    2. Month
    3. Day
    4. Hours
    5. Minutes
    6. Seconds
    7. Microseconds

    Finally, weekday is applied, using the rule described above.

    For example

    >>> from datetime import datetime
    >>> from dateutil.relativedelta import relativedelta, MO
    >>> dt = datetime(2018, 4, 9, 13, 37, 0)
    >>> delta = relativedelta(hours=25, day=1, weekday=MO(1))
    >>> dt + delta
    datetime.datetime(2018, 4, 2, 14, 37)

    First, the day is set to 1 (the first of the month), then 25 hours
    are added, to get to the 2nd day and 14th hour, finally the
    weekday is applied, but since the 2nd is already a Monday there is
    no effect.

    """

    def __init__(self, dt1=None, dt2=None,
                 years=0, months=0, days=0, leapdays=0, weeks=0,
                 hours=0, minutes=0, seconds=0, microseconds=0,
                 year=None, month=None, day=None, weekday=None,
                 yearday=None, nlyearday=None,
                 hour=None, minute=None, second=None, microsecond=None):

        if dt1 and dt2:
            # datetime is a subclass of date. So both must be date
            if not (isinstance(dt1, datetime.date) and
                    isinstance(dt2, datetime.date)):
                raise TypeError("relativedelta only diffs datetime/date")

            # We allow two dates, or two datetimes, so we coerce them to be
            # of the same type
            if (isinstance(dt1, datetime.datetime) !=
                    isinstance(dt2, datetime.datetime)):
                if not isinstance(dt1, datetime.datetime):
                    dt1 = datetime.datetime.fromordinal(dt1.toordinal())
                elif not isinstance(dt2, datetime.datetime):
                    dt2 = datetime.datetime.fromordinal(dt2.toordinal())

            self.years = 0
            self.months = 0
            self.days = 0
            self.leapdays = 0
            self.hours = 0
            self.minutes = 0
            self.seconds = 0
            self.microseconds = 0
            self.year = None
            self.month = None
            self.day = None
            self.weekday = None
            self.hour = None
            self.minute = None
            self.second = None
            self.microsecond = None
            self._has_time = 0

            # Get year / month delta between the two
            months = (dt1.year - dt2.year) * 12 + (dt1.month - dt2.month)
            self._set_months(months)

            # Remove the year/month delta so the timedelta is just well-defined
            # time units (seconds, days and microseconds)
            dtm = self.__radd__(dt2)

            # If we've overshot our target, make an adjustment
            if dt1 < dt2:
                compare = operator.gt
                increment = 1
            else:
                compare = operator.lt
                increment = -1

            while compare(dt1, dtm):
                months += increment
                self._set_months(months)
                dtm = self.__radd__(dt2)

            # Get the timedelta between the "months-adjusted" date and dt1
            delta = dt1 - dtm
            self.seconds = delta.seconds + delta.days * 86400
            self.microseconds = delta.microseconds
        else:
            # Check for non-integer values in integer-only quantities
            if any(x is not None and x != int(x) for x in (years, months)):
                raise ValueError("Non-integer years and months are "
                                 "ambiguous and not currently supported.")

            # Relative information
            self.years = int(years)
            self.months = int(months)
            self.days = days + weeks * 7
            self.leapdays = leapdays
            self.hours = hours
            self.minutes = minutes
            self.seconds = seconds
            self.microseconds = microseconds

            # Absolute information
            self.year = year
            self.month = month
            self.day = day
            self.hour = hour
            self.minute = minute
            self.second = second
            self.microsecond = microsecond

            if any(x is not None and int(x) != x
                   for x in (year, month, day, hour,
                             minute, second, microsecond)):
                # For now we'll deprecate floats - later it'll be an error.
                warn("Non-integer value passed as absolute information. " +
                     "This is not a well-defined condition and will raise " +
                     "errors in future versions.", DeprecationWarning)

            if isinstance(weekday, integer_types):
                self.weekday = weekdays[weekday]
            else:
                self.weekday = weekday

            yday = 0
            if nlyearday:
                yday = nlyearday
            elif yearday:
                yday = yearday
                if yearday > 59:
                    self.leapdays = -1
            if yday:
                ydayidx = [31, 59, 90, 120, 151, 181, 212,
                           243, 273, 304, 334, 366]
                for idx, ydays in enumerate(ydayidx):
                    if yday <= ydays:
                        self.month = idx+1
                        if idx == 0:
                            self.day = yday
                        else:
                            self.day = yday-ydayidx[idx-1]
                        break
                else:
                    raise ValueError("invalid year day (%d)" % yday)

        self._fix()

    def _fix(self):
        if abs(self.microseconds) > 999999:
            s = _sign(self.microseconds)
            div, mod = divmod(self.microseconds * s, 1000000)
            self.microseconds = mod * s
            self.seconds += div * s
        if abs(self.seconds) > 59:
            s = _sign(self.seconds)
            div, mod = divmod(self.seconds * s, 60)
            self.seconds = mod * s
            self.minutes += div * s
        if abs(self.minutes) > 59:
            s = _sign(self.minutes)
            div, mod = divmod(self.minutes * s, 60)
            self.minutes = mod * s
            self.hours += div * s
        if abs(self.hours) > 23:
            s = _sign(self.hours)
            div, mod = divmod(self.hours * s, 24)
            self.hours = mod * s
            self.days += div * s
        if abs(self.months) > 11:
            s = _sign(self.months)
            div, mod = divmod(self.months * s, 12)
            self.months = mod * s
            self.years += div * s
        if (self.hours or self.minutes or self.seconds or self.microseconds
                or self.hour is not None or self.minute is not None or
                self.second is not None or self.microsecond is not None):
            self._has_time = 1
        else:
            self._has_time = 0

    @property
    def weeks(self):
        return int(self.days / 7.0)

    @weeks.setter
    def weeks(self, value):
        self.days = self.days - (self.weeks * 7) + value * 7

    def _set_months(self, months):
        self.months = months
        if abs(self.months) > 11:
            s = _sign(self.months)
            div, mod = divmod(self.months * s, 12)
            self.months = mod * s
            self.years = div * s
        else:
            self.years = 0

    def normalized(self):
        """
        Return a version of this object represented entirely using integer
        values for the relative attributes.

        >>> relativedelta(days=1.5, hours=2).normalized()
        relativedelta(days=+1, hours=+14)

        :return:
            Returns a :class:`dateutil.relativedelta.relativedelta` object.
        """
        # Cascade remainders down (rounding each to roughly nearest microsecond)
        days = int(self.days)

        hours_f = round(self.hours + 24 * (self.days - days), 11)
        hours = int(hours_f)

        minutes_f = round(self.minutes + 60 * (hours_f - hours), 10)
        minutes = int(minutes_f)

        seconds_f = round(self.seconds + 60 * (minutes_f - minutes), 8)
        seconds = int(seconds_f)

        microseconds = round(self.microseconds + 1e6 * (seconds_f - seconds))

        # Constructor carries overflow back up with call to _fix()
        return self.__class__(years=self.years, months=self.months,
                              days=days, hours=hours, minutes=minutes,
                              seconds=seconds, microseconds=microseconds,
                              leapdays=self.leapdays, year=self.year,
                              month=self.month, day=self.day,
                              weekday=self.weekday, hour=self.hour,
                              minute=self.minute, second=self.second,
                              microsecond=self.microsecond)

    def __add__(self, other):
        if isinstance(other, relativedelta):
            return self.__class__(years=other.years + self.years,
                                 months=other.months + self.months,
                                 days=other.days + self.days,
                                 hours=other.hours + self.hours,
                                 minutes=other.minutes + self.minutes,
                                 seconds=other.seconds + self.seconds,
                                 microseconds=(other.microseconds +
                                               self.microseconds),
                                 leapdays=other.leapdays or self.leapdays,
                                 year=(other.year if other.year is not None
                                       else self.year),
                                 month=(other.month if other.month is not None
                                        else self.month),
                                 day=(other.day if other.day is not None
                                      else self.day),
                                 weekday=(other.weekday if other.weekday is not None
                                          else self.weekday),
                                 hour=(other.hour if other.hour is not None
                                       else self.hour),
                                 minute=(other.minute if other.minute is not None
                                         else self.minute),
                                 second=(other.second if other.second is not None
                                         else self.second),
                                 microsecond=(other.microsecond if other.microsecond
                                              is not None else
                                              self.microsecond))
        if isinstance(other, datetime.timedelta):
            return self.__class__(years=self.years,
                                  months=self.months,
                                  days=self.days + other.days,
                                  hours=self.hours,
                                  minutes=self.minutes,
                                  seconds=self.seconds + other.seconds,
                                  microseconds=self.microseconds + other.microseconds,
                                  leapdays=self.leapdays,
                                  year=self.year,
                                  month=self.month,
                                  day=self.day,
                                  weekday=self.weekday,
                                  hour=self.hour,
                                  minute=self.minute,
                                  second=self.second,
                                  microsecond=self.microsecond)
        if not isinstance(other, datetime.date):
            return NotImplemented
        elif self._has_time and not isinstance(other, datetime.datetime):
            other = datetime.datetime.fromordinal(other.toordinal())
        year = (self.year or other.year)+self.years
        month = self.month or other.month
        if self.months:
            assert 1 <= abs(self.months) <= 12
            month += self.months
            if month > 12:
                year += 1
                month -= 12
            elif month < 1:
                year -= 1
                month += 12
        day = min(calendar.monthrange(year, month)[1],
                  self.day or other.day)
        repl = {"year": year, "month": month, "day": day}
        for attr in ["hour", "minute", "second", "microsecond"]:
            value = getattr(self, attr)
            if value is not None:
                repl[attr] = value
        days = self.days
        if self.leapdays and month > 2 and calendar.isleap(year):
            days += self.leapdays
        ret = (other.replace(**repl)
               + datetime.timedelta(days=days,
                                    hours=self.hours,
                                    minutes=self.minutes,
                                    seconds=self.seconds,
                                    microseconds=self.microseconds))
        if self.weekday:
            weekday, nth = self.weekday.weekday, self.weekday.n or 1
            jumpdays = (abs(nth) - 1) * 7
            if nth > 0:
                jumpdays += (7 - ret.weekday() + weekday) % 7
            else:
                jumpdays += (ret.weekday() - weekday) % 7
                jumpdays *= -1
            ret += datetime.timedelta(days=jumpdays)
        return ret

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return self.__neg__().__radd__(other)

    def __sub__(self, other):
        if not isinstance(other, relativedelta):
            return NotImplemented   # In case the other object defines __rsub__
        return self.__class__(years=self.years - other.years,
                             months=self.months - other.months,
                             days=self.days - other.days,
                             hours=self.hours - other.hours,
                             minutes=self.minutes - other.minutes,
                             seconds=self.seconds - other.seconds,
                             microseconds=self.microseconds - other.microseconds,
                             leapdays=self.leapdays or other.leapdays,
                             year=(self.year if self.year is not None
                                   else other.year),
                             month=(self.month if self.month is not None else
                                    other.month),
                             day=(self.day if self.day is not None else
                                  other.day),
                             weekday=(self.weekday if self.weekday is not None else
                                      other.weekday),
                             hour=(self.hour if self.hour is not None else
                                   other.hour),
                             minute=(self.minute if self.minute is not None else
                                     other.minute),
                             second=(self.second if self.second is not None else
                                     other.second),
                             microsecond=(self.microsecond if self.microsecond
                                          is not None else
                                          other.microsecond))

    def __abs__(self):
        return self.__class__(years=abs(self.years),
                              months=abs(self.months),
                              days=abs(self.days),
                              hours=abs(self.hours),
                              minutes=abs(self.minutes),
                              seconds=abs(self.seconds),
                              microseconds=abs(self.microseconds),
                              leapdays=self.leapdays,
                              year=self.year,
                              month=self.month,
                              day=self.day,
                              weekday=self.weekday,
                              hour=self.hour,
                              minute=self.minute,
                              second=self.second,
                              microsecond=self.microsecond)

    def __neg__(self):
        return self.__class__(years=-self.years,
                             months=-self.months,
                             days=-self.days,
                             hours=-self.hours,
                             minutes=-self.minutes,
                             seconds=-self.seconds,
                             microseconds=-self.microseconds,
                             leapdays=self.leapdays,
                             year=self.year,
                             month=self.month,
                             day=self.day,
                             weekday=self.weekday,
                             hour=self.hour,
                             minute=self.minute,
                             second=self.second,
                             microsecond=self.microsecond)

    def __bool__(self):
        return not (not self.years and
                    not self.months and
                    not self.days and
                    not self.hours and
                    not self.minutes and
                    not self.seconds and
                    not self.microseconds and
                    not self.leapdays and
                    self.year is None and
                    self.month is None and
                    self.day is None and
                    self.weekday is None and
                    self.hour is None and
                    self.minute is None and
                    self.second is None and
                    self.microsecond is None)
    # Compatibility with Python 2.x
    __nonzero__ = __bool__

    def __mul__(self, other):
        try:
            f = float(other)
        except TypeError:
            return NotImplemented

        return self.__class__(years=int(self.years * f),
                             months=int(self.months * f),
                             days=int(self.days * f),
                             hours=int(self.hours * f),
                             minutes=int(self.minutes * f),
                             seconds=int(self.seconds * f),
                             microseconds=int(self.microseconds * f),
                             leapdays=self.leapdays,
                             year=self.year,
                             month=self.month,
                             day=self.day,
                             weekday=self.weekday,
                             hour=self.hour,
                             minute=self.minute,
                             second=self.second,
                             microsecond=self.microsecond)

    __rmul__ = __mul__

    def __eq__(self, other):
        if not isinstance(other, relativedelta):
            return NotImplemented
        if self.weekday or other.weekday:
            if not self.weekday or not other.weekday:
                return False
            if self.weekday.weekday != other.weekday.weekday:
                return False
            n1, n2 = self.weekday.n, other.weekday.n
            if n1 != n2 and not ((not n1 or n1 == 1) and (not n2 or n2 == 1)):
                return False
        return (self.years == other.years and
                self.months == other.months and
                self.days == other.days and
                self.hours == other.hours and
                self.minutes == other.minutes and
                self.seconds == other.seconds and
                self.microseconds == other.microseconds and
                self.leapdays == other.leapdays and
                self.year == other.year and
                self.month == other.month and
                self.day == other.day and
                self.hour == other.hour and
                self.minute == other.minute and
                self.second == other.second and
                self.microsecond == other.microsecond)

    def __hash__(self):
        return hash((
            self.weekday,
            self.years,
            self.months,
            self.days,
            self.hours,
            self.minutes,
            self.seconds,
            self.microseconds,
            self.leapdays,
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
            self.microsecond,
        ))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __div__(self, other):
        try:
            reciprocal = 1 / float(other)
        except TypeError:
            return NotImplemented

        return self.__mul__(reciprocal)

    __truediv__ = __div__

    def __repr__(self):
        l = []
        for attr in ["years", "months", "days", "leapdays",
                     "hours", "minutes", "seconds", "microseconds"]:
            value = getattr(self, attr)
            if value:
                l.append("{attr}={value:+g}".format(attr=attr, value=value))
        for attr in ["year", "month", "day", "weekday",
                     "hour", "minute", "second", "microsecond"]:
            value = getattr(self, attr)
            if value is not None:
                l.append("{attr}={value}".format(attr=attr, value=repr(value)))
        return "{classname}({attrs})".format(classname=self.__class__.__name__,
                                             attrs=", ".join(l))


def _sign(x):
    return int(copysign(1, x))

# vim:ts=4:sw=4:et
2026-05-10T20:17:59.237179Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when Auth(TokenRefreshFailed("Server returned error response: invalid_grant: Invalid refresh token"))
codex
# Contracts: dateutil_dom

## Module overview
This module defines weekday constants (`MO` through `SU`) and a `relativedelta` class for representing calendar-aware differences or transformations applied to `datetime.date` and `datetime.datetime` values. A `relativedelta` can contain both relative fields, such as `years=+1`, and absolute replacement fields, such as `month=1`; when applied to a date, absolute fields are applied first, then relative fields, then weekday adjustment.

## Shared model and invariants

A `relativedelta` instance has these stored fields:

- Relative fields: `years`, `months`, `days`, `leapdays`, `hours`, `minutes`, `seconds`, `microseconds`
- Absolute fields: `year`, `month`, `day`, `hour`, `minute`, `second`, `microsecond`
- Weekday field: `weekday`
- Internal flag: `_has_time`

Relative plural fields are arithmetic offsets. Absolute singular fields replace the corresponding component when the delta is applied.

Application order to a date/datetime is:

1. year absolute, then `years`
2. month absolute, then `months`
3. day absolute, clamped to the last valid day of target month
4. absolute time fields
5. relative `days`, `hours`, `minutes`, `seconds`, `microseconds`
6. `weekday`

After normalization by `_fix()`:

- `abs(microseconds) <= 999999`
- `abs(seconds) <= 59`
- `abs(minutes) <= 59`
- `abs(hours) <= 23`
- `abs(months) <= 11`
- overflow is carried toward larger units with the same sign
- `_has_time == 1` iff any relative time field is non-zero or any absolute time field is not `None`

## Function/method contracts

### `relativedelta.__init__`

**Signature**

```python
relativedelta(
    dt1=None, dt2=None,
    years=0, months=0, days=0, leapdays=0, weeks=0,
    hours=0, minutes=0, seconds=0, microseconds=0,
    year=None, month=None, day=None, weekday=None,
    yearday=None, nlyearday=None,
    hour=None, minute=None, second=None, microsecond=None
)
```

**Pre-conditions**

- If both `dt1` and `dt2` are truthy, both must be `datetime.date` or `datetime.datetime`.
- If exactly one of `dt1` or `dt2` is supplied, constructor uses keyword mode and ignores the lone date argument.
- `years` and `months` must be integer-valued; non-integer values raise `ValueError`.
- `weekday`, if integer, must index `weekdays`, where `0 == MO` and `6 == SU`; invalid indexes propagate `IndexError`.
- `yearday` and `nlyearday`, if supplied, must be in the supported day-of-year range `1..366`.

**Post-conditions**

- In diff mode, the instance represents a calendar-aware delta such that applying it to `dt2` reaches `dt1` according to this module’s month adjustment algorithm.
- In keyword mode, relative fields and absolute fields are stored from arguments, with `weeks` converted into `days += weeks * 7`.
- If `weekday` is an integer, it is converted to the corresponding weekday object.
- If `yearday` or `nlyearday` is supplied, it is converted into `month`, `day`, and possibly `leapdays`.
- `_fix()` has been called before returning.

**Invariants**

- Date/datetime diff mode initializes all absolute fields and `weekday` to `None`.
- Date/datetime diff mode stores residual sub-month difference in `seconds` and `microseconds`.
- `yearday` takes precedence only when `nlyearday` is absent.
- `nlyearday` does not set `leapdays`; `yearday > 59` sets `leapdays = -1`.

**Edge cases**

- Mixed `date`/`datetime` diff inputs are coerced to matching `datetime` type using ordinal date at midnight.
- `dt1` or `dt2` values that are falsy are not treated as diff inputs because the branch checks truthiness.
- Non-integer absolute values emit `DeprecationWarning` but are still stored.
- `yearday=366` maps to December 32 internally before downstream validity is enforced by later use; values greater than 366 raise `ValueError`.

**Operator-level invariants**

- Diff-mode month correction moves by `+1` month when `dt1 < dt2`, otherwise by `-1` month.
- Overshoot loop continues while `dtm` has passed the target in the comparison direction.

---

### `relativedelta._fix`

**Signature**

```python
_fix(self)
```

**Pre-conditions**

- Relative fields are numeric and support `abs`, multiplication by sign, `divmod`, and addition.
- Object has all expected relative and absolute time attributes.

**Post-conditions**

- Carries overflow upward:
  - microseconds to seconds
  - seconds to minutes
  - minutes to hours
  - hours to days
  - months to years
- Sets `_has_time` to `1` if any time-related relative or absolute field exists, else `0`.

**Invariants**

- Sign is preserved during carry.
- Calendar-relative units are only normalized through months-to-years; days are not normalized into months or years.
- `_fix()` does not change absolute date fields, `weekday`, or `leapdays`.

**Edge cases**

- Boundary values with absolute value exactly equal to limit are not carried: `seconds=59`, `hours=23`, `months=11`.
- Negative overflows carry using the sign of the original field.

**Operator-level invariants**

- Carry condition uses `>` not `>=`.
- Carry uses `divmod(abs(value), unit)` and reapplies original sign.

---

### `relativedelta.weeks`

**Signature**

```python
@property
weeks(self) -> int
```

**Pre-conditions**

- `self.days` is numeric.

**Post-conditions**

- Returns `int(self.days / 7.0)`.

**Invariants**

- Does not mutate the instance.
- Weeks are derived from `days`; no independent weeks field is stored.

**Edge cases**

- Fractional days are divided by `7.0` and truncated by `int`.
- Negative days truncate toward zero because Python `int(float)` truncates toward zero.

**Operator-level invariants**

- Uses floating-point division, not floor division.

---

### `relativedelta.weeks` setter

**Signature**

```python
weeks(self, value)
```

**Pre-conditions**

- `self.days` and `value` are numeric.
- Current `self.weeks` can be computed.

**Post-conditions**

- Replaces only the week-derived portion of `days`:
  `self.days = self.days - self.weeks * 7 + value * 7`.

**Invariants**

- Preserves non-week remainder days.
- Does not call `_fix()`.

**Edge cases**

- Fractional `value` may produce fractional `days`.
- Negative `days` uses getter truncation toward zero.

**Operator-level invariants**

- Existing week component is removed before new week component is added.

---

### `relativedelta._set_months`

**Signature**

```python
_set_months(self, months)
```

**Pre-conditions**

- `months` is numeric and compatible with `abs`, `divmod`, and sign operations.

**Post-conditions**

- Stores `months` normalized into `self.years` and `self.months`.
- If `abs(months) > 11`, years receive whole 12-month groups and months receive the signed remainder.
- If `abs(months) <= 11`, `self.years` is set to `0`.

**Invariants**

- After return, `abs(self.months) <= 11`.
- Sign of months and derived years follows sign of input.

**Edge cases**

- `months=12` becomes `years=1, months=0`.
- `months=-13` becomes `years=-1, months=-1`.

**Operator-level invariants**

- Normalization threshold is `> 11`.

---

### `relativedelta.normalized`

**Signature**

```python
normalized(self) -> relativedelta
```

**Pre-conditions**

- Relative day/time fields are numeric.
- Class constructor accepts the same field set as `relativedelta`.

**Post-conditions**

- Returns a new instance with relative `days`, `hours`, `minutes`, `seconds`, and `microseconds` represented as integer-valued components.
- Absolute fields, `weekday`, `leapdays`, `years`, and `months` are preserved.
- Original instance is not mutated.

**Invariants**

- Fractional days cascade into hours, then minutes, then seconds, then microseconds.
- Constructor `_fix()` may carry overflow back upward.

**Edge cases**

- Rounds intermediate cascades to limit floating-point drift:
  hours to 11 decimals, minutes to 10, seconds to 8.
- Negative fractional values truncate via `int`.

**Operator-level invariants**

- Cascade direction is strictly smaller units only before constructor normalization.

---

### `relativedelta.__add__`

**Signature**

```python
__add__(self, other)
```

**Pre-conditions**

- `other` must be one of:
  - `relativedelta`
  - `datetime.timedelta`
  - `datetime.date` or `datetime.datetime`
- For date application, resulting absolute replacement values must be valid for `datetime.replace`, except day is clamped to target month length.

**Post-conditions**

- With `relativedelta`: returns a new combined delta.
- With `timedelta`: returns a new delta with `days`, `seconds`, and `microseconds` increased by the timedelta values.
- With `date`/`datetime`: returns the transformed date/datetime.
- With unsupported types: returns `NotImplemented`.

**Invariants**

- Adding two deltas sums relative fields.
- Absolute fields from `other` override `self` when `other` provides non-`None` values.
- `leapdays` is selected as `other.leapdays or self.leapdays`.
- Applying to a `date` with time components promotes it to `datetime` at midnight.
- Applying to a `datetime` preserves datetime type.

**Edge cases**

- Month arithmetic adjusts by at most one year because `_fix()` guarantees `abs(months) <= 11`.
- Target day is `min(last_day_of_target_month, absolute_or_original_day)`.
- `leapdays` applies only when target month is after February and target year is leap.
- Weekday adjustment is relative: if already on requested weekday and `nth` is `1` or `-1`, no movement occurs.

**Operator-level invariants**

- Year is computed as `(self.year or other.year) + self.years`.
- Month is computed as `self.month or other.month`, then adjusted by `self.months`.
- Positive weekday jump:
  `(7 - ret.weekday() + target_weekday) % 7 + (nth - 1) * 7`
- Negative weekday jump:
  `-((ret.weekday() - target_weekday) % 7 + (abs(nth) - 1) * 7)`

---

### `relativedelta.__radd__`

**Signature**

```python
__radd__(self, other)
```

**Pre-conditions**

- Same as `__add__`.

**Post-conditions**

- Returns `self.__add__(other)`.

**Invariants**

- Makes `date + relativedelta` and `relativedelta + date` equivalent.

**Edge cases**

- Unsupported types return `NotImplemented` through `__add__`.

**Operator-level invariants**

- No independent arithmetic is performed.

---

### `relativedelta.__rsub__`

**Signature**

```python
__rsub__(self, other)
```

**Pre-conditions**

- `other` must support addition with the negated delta.

**Post-conditions**

- Returns `other + (-self)` using `self.__neg__().__radd__(other)`.

**Invariants**

- Subtracting a delta from a date is equivalent to adding the negated relative fields.

**Edge cases**

- Absolute fields are preserved during negation, so subtraction does not invert absolute replacements.

**Operator-level invariants**

- Negation happens before right-addition.

---

### `relativedelta.__sub__`

**Signature**

```python
__sub__(self, other)
```

**Pre-conditions**

- `other` must be a `relativedelta`; otherwise returns `NotImplemented`.

**Post-conditions**

- Returns a new delta with relative fields subtracted.
- Absolute fields from `self` are kept when non-`None`; otherwise fields from `other` are used.
- `leapdays` is selected as `self.leapdays or other.leapdays`.

**Invariants**

- Original operands are not mutated.
- Result constructor normalizes relative overflow.

**Edge cases**

- Absolute fields are not arithmetically subtracted.
- `weekday` is selected, not subtracted.

**Operator-level invariants**

- Relative subtraction direction is `self.field - other.field`.

---

### `relativedelta.__abs__`

**Signature**

```python
__abs__(self)
```

**Pre-conditions**

- Relative fields support `abs`.

**Post-conditions**

- Returns a new delta with absolute values of relative fields.
- Absolute fields, `weekday`, and `leapdays` are preserved unchanged.

**Invariants**

- Original instance is not mutated.

**Edge cases**

- Negative `leapdays` remains negative.

**Operator-level invariants**

- Only plural relative fields are passed through `abs()`.

---

### `relativedelta.__neg__`

**Signature**

```python
__neg__(self)
```

**Pre-conditions**

- Relative fields support unary negation.

**Post-conditions**

- Returns a new delta with relative fields negated.
- Absolute fields, `weekday`, and `leapdays` are preserved unchanged.

**Invariants**

- Original instance is not mutated.

**Edge cases**

- Absolute replacement fields are not removed or inverted.

**Operator-level invariants**

- Only plural relative fields are sign-flipped.

---

### `relativedelta.__bool__` / `__nonzero__`

**Signature**

```python
__bool__(self) -> bool
__nonzero__ = __bool__
```

**Pre-conditions**

- Instance has all expected fields.

**Post-conditions**

- Returns `False` only when all relative fields are zero/falsy, all absolute fields are `None`, `weekday is None`, and `leapdays` is falsy.
- Returns `True` otherwise.

**Invariants**

- Does not mutate instance.
- Python 2 compatibility alias has identical behavior.

**Edge cases**

- Absolute field value `0` is truthy for this contract if it is not `None`.
- `weekday` makes the delta truthy even if all numeric fields are zero.

**Operator-level invariants**

- Absolute fields are checked with `is None`, not truthiness.

---

### `relativedelta.__mul__` / `__rmul__`

**Signature**

```python
__mul__(self, other)
__rmul__ = __mul__
```

**Pre-conditions**

- `other` must be convertible to `float`; otherwise returns `NotImplemented`.

**Post-conditions**

- Returns a new delta with relative fields multiplied by `float(other)` and truncated through `int`.
- Absolute fields, `weekday`, and `leapdays` are preserved unchanged.

**Invariants**

- Original instance is not mutated.
- Multiplication is symmetric through `__rmul__`.

**Edge cases**

- Fractional products truncate toward zero.
- Multiplying by negative values flips signs of relative fields.
- `leapdays` is not multiplied.

**Operator-level invariants**

- Conversion is `f = float(other)`.
- Each relative result is `int(field * f)`.

---

### `relativedelta.__eq__`

**Signature**

```python
__eq__(self, other)
```

**Pre-conditions**

- `other` may be any object.

**Post-conditions**

- Returns `NotImplemented` if `other` is not a `relativedelta`.
- Returns `True` only if all relative fields, absolute fields, and `leapdays` are equal and weekday values are equivalent.
- Treats weekday `n=None` and `n=1` as equivalent.

**Invariants**

- Does not mutate either operand.

**Edge cases**

- If exactly one operand has `weekday`, equality is `False`.
- If weekday numbers differ, equality is `False`.
- Weekday `n` values differ only acceptably when both represent first occurrence/default.

**Operator-level invariants**

- Weekday comparison is performed before comparing scalar fields.

---

### `relativedelta.__hash__`

**Signature**

```python
__hash__(self) -> int
```

**Pre-conditions**

- All included fields are hashable.

**Post-conditions**

- Returns hash of tuple containing weekday, all relative fields, `leapdays`, and all absolute fields.

**Invariants**

- Does not mutate instance.

**Edge cases**

- Hash includes raw `weekday`; equality treats `weekday.n=None` and `weekday.n=1` as equal, so compatible hashing depends on weekday objects hashing those equivalently.

**Operator-level invariants**

- Tuple field order is fixed and must remain stable.

---

### `relativedelta.__ne__`

**Signature**

```python
__ne__(self, other)
```

**Pre-conditions**

- None beyond `__eq__`.

**Post-conditions**

- Returns `not self.__eq__(other)`.

**Invariants**

- Does not mutate operands.

**Edge cases**

- If `__eq__` returns `NotImplemented`, this method returns `False` because `not NotImplemented` is `False`.

**Operator-level invariants**

- No independent inequality comparison is performed.

---

### `relativedelta.__div__` / `__truediv__`

**Signature**

```python
__div__(self, other)
__truediv__ = __div__
```

**Pre-conditions**

- `other` must be convertible to `float`; otherwise returns `NotImplemented`.
- `float(other)` must be non-zero; zero propagates `ZeroDivisionError`.

**Post-conditions**

- Returns `self * (1 / float(other))`.
- Absolute fields, `weekday`, and `leapdays` are preserved via multiplication contract.

**Invariants**

- Original instance is not mutated.
- Python 2 and Python 3 division paths are identical.

**Edge cases**

- Fractional division results truncate toward zero through `__mul__`.
- Division by unsupported type returns `NotImplemented`.

**Operator-level invariants**

- Reciprocal is computed before multiplication.

---

### `relativedelta.__repr__`

**Signature**

```python
__repr__(self) -> str
```

**Pre-conditions**

- Instance has all expected fields.

**Post-conditions**

- Returns string of the form `relativedelta(...)` or subclass name with non-empty fields listed.
- Relative non-zero fields are formatted with signed general numeric format.
- Absolute fields and `weekday` are included when not `None`.

**Invariants**

- Does not mutate instance.
- Field order in representation is fixed.

**Edge cases**

- Zero/falsy relative fields are omitted.
- Absolute value `0` is included because the check is `is not None`.

**Operator-level invariants**

- Relative fields use `"{value:+g}"`; absolute fields use `repr(value)`.

---

### `_sign`

**Signature**

```python
_sign(x) -> int
```

**Pre-conditions**

- `x` must be accepted by `math.copysign`.

**Post-conditions**

- Returns `1` for positive values and positive zero.
- Returns `-1` for negative values and negative zero.

**Invariants**

- Does not mutate input.

**Edge cases**

- `_sign(0)` returns `1`.
- `_sign(-0.0)` returns `-1`.

**Operator-level invariants**

- Implemented as `int(copysign(1, x))`.
tokens used
23.334
# Contracts: dateutil_dom

## Module overview
This module defines weekday constants (`MO` through `SU`) and a `relativedelta` class for representing calendar-aware differences or transformations applied to `datetime.date` and `datetime.datetime` values. A `relativedelta` can contain both relative fields, such as `years=+1`, and absolute replacement fields, such as `month=1`; when applied to a date, absolute fields are applied first, then relative fields, then weekday adjustment.

## Shared model and invariants

A `relativedelta` instance has these stored fields:

- Relative fields: `years`, `months`, `days`, `leapdays`, `hours`, `minutes`, `seconds`, `microseconds`
- Absolute fields: `year`, `month`, `day`, `hour`, `minute`, `second`, `microsecond`
- Weekday field: `weekday`
- Internal flag: `_has_time`

Relative plural fields are arithmetic offsets. Absolute singular fields replace the corresponding component when the delta is applied.

Application order to a date/datetime is:

1. year absolute, then `years`
2. month absolute, then `months`
3. day absolute, clamped to the last valid day of target month
4. absolute time fields
5. relative `days`, `hours`, `minutes`, `seconds`, `microseconds`
6. `weekday`

After normalization by `_fix()`:

- `abs(microseconds) <= 999999`
- `abs(seconds) <= 59`
- `abs(minutes) <= 59`
- `abs(hours) <= 23`
- `abs(months) <= 11`
- overflow is carried toward larger units with the same sign
- `_has_time == 1` iff any relative time field is non-zero or any absolute time field is not `None`

## Function/method contracts

### `relativedelta.__init__`

**Signature**

```python
relativedelta(
    dt1=None, dt2=None,
    years=0, months=0, days=0, leapdays=0, weeks=0,
    hours=0, minutes=0, seconds=0, microseconds=0,
    year=None, month=None, day=None, weekday=None,
    yearday=None, nlyearday=None,
    hour=None, minute=None, second=None, microsecond=None
)
```

**Pre-conditions**

- If both `dt1` and `dt2` are truthy, both must be `datetime.date` or `datetime.datetime`.
- If exactly one of `dt1` or `dt2` is supplied, constructor uses keyword mode and ignores the lone date argument.
- `years` and `months` must be integer-valued; non-integer values raise `ValueError`.
- `weekday`, if integer, must index `weekdays`, where `0 == MO` and `6 == SU`; invalid indexes propagate `IndexError`.
- `yearday` and `nlyearday`, if supplied, must be in the supported day-of-year range `1..366`.

**Post-conditions**

- In diff mode, the instance represents a calendar-aware delta such that applying it to `dt2` reaches `dt1` according to this module’s month adjustment algorithm.
- In keyword mode, relative fields and absolute fields are stored from arguments, with `weeks` converted into `days += weeks * 7`.
- If `weekday` is an integer, it is converted to the corresponding weekday object.
- If `yearday` or `nlyearday` is supplied, it is converted into `month`, `day`, and possibly `leapdays`.
- `_fix()` has been called before returning.

**Invariants**

- Date/datetime diff mode initializes all absolute fields and `weekday` to `None`.
- Date/datetime diff mode stores residual sub-month difference in `seconds` and `microseconds`.
- `yearday` takes precedence only when `nlyearday` is absent.
- `nlyearday` does not set `leapdays`; `yearday > 59` sets `leapdays = -1`.

**Edge cases**

- Mixed `date`/`datetime` diff inputs are coerced to matching `datetime` type using ordinal date at midnight.
- `dt1` or `dt2` values that are falsy are not treated as diff inputs because the branch checks truthiness.
- Non-integer absolute values emit `DeprecationWarning` but are still stored.
- `yearday=366` maps to December 32 internally before downstream validity is enforced by later use; values greater than 366 raise `ValueError`.

**Operator-level invariants**

- Diff-mode month correction moves by `+1` month when `dt1 < dt2`, otherwise by `-1` month.
- Overshoot loop continues while `dtm` has passed the target in the comparison direction.

---

### `relativedelta._fix`

**Signature**

```python
_fix(self)
```

**Pre-conditions**

- Relative fields are numeric and support `abs`, multiplication by sign, `divmod`, and addition.
- Object has all expected relative and absolute time attributes.

**Post-conditions**

- Carries overflow upward:
  - microseconds to seconds
  - seconds to minutes
  - minutes to hours
  - hours to days
  - months to years
- Sets `_has_time` to `1` if any time-related relative or absolute field exists, else `0`.

**Invariants**

- Sign is preserved during carry.
- Calendar-relative units are only normalized through months-to-years; days are not normalized into months or years.
- `_fix()` does not change absolute date fields, `weekday`, or `leapdays`.

**Edge cases**

- Boundary values with absolute value exactly equal to limit are not carried: `seconds=59`, `hours=23`, `months=11`.
- Negative overflows carry using the sign of the original field.

**Operator-level invariants**

- Carry condition uses `>` not `>=`.
- Carry uses `divmod(abs(value), unit)` and reapplies original sign.

---

### `relativedelta.weeks`

**Signature**

```python
@property
weeks(self) -> int
```

**Pre-conditions**

- `self.days` is numeric.

**Post-conditions**

- Returns `int(self.days / 7.0)`.

**Invariants**

- Does not mutate the instance.
- Weeks are derived from `days`; no independent weeks field is stored.

**Edge cases**

- Fractional days are divided by `7.0` and truncated by `int`.
- Negative days truncate toward zero because Python `int(float)` truncates toward zero.

**Operator-level invariants**

- Uses floating-point division, not floor division.

---

### `relativedelta.weeks` setter

**Signature**

```python
weeks(self, value)
```

**Pre-conditions**

- `self.days` and `value` are numeric.
- Current `self.weeks` can be computed.

**Post-conditions**

- Replaces only the week-derived portion of `days`:
  `self.days = self.days - self.weeks * 7 + value * 7`.

**Invariants**

- Preserves non-week remainder days.
- Does not call `_fix()`.

**Edge cases**

- Fractional `value` may produce fractional `days`.
- Negative `days` uses getter truncation toward zero.

**Operator-level invariants**

- Existing week component is removed before new week component is added.

---

### `relativedelta._set_months`

**Signature**

```python
_set_months(self, months)
```

**Pre-conditions**

- `months` is numeric and compatible with `abs`, `divmod`, and sign operations.

**Post-conditions**

- Stores `months` normalized into `self.years` and `self.months`.
- If `abs(months) > 11`, years receive whole 12-month groups and months receive the signed remainder.
- If `abs(months) <= 11`, `self.years` is set to `0`.

**Invariants**

- After return, `abs(self.months) <= 11`.
- Sign of months and derived years follows sign of input.

**Edge cases**

- `months=12` becomes `years=1, months=0`.
- `months=-13` becomes `years=-1, months=-1`.

**Operator-level invariants**

- Normalization threshold is `> 11`.

---

### `relativedelta.normalized`

**Signature**

```python
normalized(self) -> relativedelta
```

**Pre-conditions**

- Relative day/time fields are numeric.
- Class constructor accepts the same field set as `relativedelta`.

**Post-conditions**

- Returns a new instance with relative `days`, `hours`, `minutes`, `seconds`, and `microseconds` represented as integer-valued components.
- Absolute fields, `weekday`, `leapdays`, `years`, and `months` are preserved.
- Original instance is not mutated.

**Invariants**

- Fractional days cascade into hours, then minutes, then seconds, then microseconds.
- Constructor `_fix()` may carry overflow back upward.

**Edge cases**

- Rounds intermediate cascades to limit floating-point drift:
  hours to 11 decimals, minutes to 10, seconds to 8.
- Negative fractional values truncate via `int`.

**Operator-level invariants**

- Cascade direction is strictly smaller units only before constructor normalization.

---

### `relativedelta.__add__`

**Signature**

```python
__add__(self, other)
```

**Pre-conditions**

- `other` must be one of:
  - `relativedelta`
  - `datetime.timedelta`
  - `datetime.date` or `datetime.datetime`
- For date application, resulting absolute replacement values must be valid for `datetime.replace`, except day is clamped to target month length.

**Post-conditions**

- With `relativedelta`: returns a new combined delta.
- With `timedelta`: returns a new delta with `days`, `seconds`, and `microseconds` increased by the timedelta values.
- With `date`/`datetime`: returns the transformed date/datetime.
- With unsupported types: returns `NotImplemented`.

**Invariants**

- Adding two deltas sums relative fields.
- Absolute fields from `other` override `self` when `other` provides non-`None` values.
- `leapdays` is selected as `other.leapdays or self.leapdays`.
- Applying to a `date` with time components promotes it to `datetime` at midnight.
- Applying to a `datetime` preserves datetime type.

**Edge cases**

- Month arithmetic adjusts by at most one year because `_fix()` guarantees `abs(months) <= 11`.
- Target day is `min(last_day_of_target_month, absolute_or_original_day)`.
- `leapdays` applies only when target month is after February and target year is leap.
- Weekday adjustment is relative: if already on requested weekday and `nth` is `1` or `-1`, no movement occurs.

**Operator-level invariants**

- Year is computed as `(self.year or other.year) + self.years`.
- Month is computed as `self.month or other.month`, then adjusted by `self.months`.
- Positive weekday jump:
  `(7 - ret.weekday() + target_weekday) % 7 + (nth - 1) * 7`
- Negative weekday jump:
  `-((ret.weekday() - target_weekday) % 7 + (abs(nth) - 1) * 7)`

---

### `relativedelta.__radd__`

**Signature**

```python
__radd__(self, other)
```

**Pre-conditions**

- Same as `__add__`.

**Post-conditions**

- Returns `self.__add__(other)`.

**Invariants**

- Makes `date + relativedelta` and `relativedelta + date` equivalent.

**Edge cases**

- Unsupported types return `NotImplemented` through `__add__`.

**Operator-level invariants**

- No independent arithmetic is performed.

---

### `relativedelta.__rsub__`

**Signature**

```python
__rsub__(self, other)
```

**Pre-conditions**

- `other` must support addition with the negated delta.

**Post-conditions**

- Returns `other + (-self)` using `self.__neg__().__radd__(other)`.

**Invariants**

- Subtracting a delta from a date is equivalent to adding the negated relative fields.

**Edge cases**

- Absolute fields are preserved during negation, so subtraction does not invert absolute replacements.

**Operator-level invariants**

- Negation happens before right-addition.

---

### `relativedelta.__sub__`

**Signature**

```python
__sub__(self, other)
```

**Pre-conditions**

- `other` must be a `relativedelta`; otherwise returns `NotImplemented`.

**Post-conditions**

- Returns a new delta with relative fields subtracted.
- Absolute fields from `self` are kept when non-`None`; otherwise fields from `other` are used.
- `leapdays` is selected as `self.leapdays or other.leapdays`.

**Invariants**

- Original operands are not mutated.
- Result constructor normalizes relative overflow.

**Edge cases**

- Absolute fields are not arithmetically subtracted.
- `weekday` is selected, not subtracted.

**Operator-level invariants**

- Relative subtraction direction is `self.field - other.field`.

---

### `relativedelta.__abs__`

**Signature**

```python
__abs__(self)
```

**Pre-conditions**

- Relative fields support `abs`.

**Post-conditions**

- Returns a new delta with absolute values of relative fields.
- Absolute fields, `weekday`, and `leapdays` are preserved unchanged.

**Invariants**

- Original instance is not mutated.

**Edge cases**

- Negative `leapdays` remains negative.

**Operator-level invariants**

- Only plural relative fields are passed through `abs()`.

---

### `relativedelta.__neg__`

**Signature**

```python
__neg__(self)
```

**Pre-conditions**

- Relative fields support unary negation.

**Post-conditions**

- Returns a new delta with relative fields negated.
- Absolute fields, `weekday`, and `leapdays` are preserved unchanged.

**Invariants**

- Original instance is not mutated.

**Edge cases**

- Absolute replacement fields are not removed or inverted.

**Operator-level invariants**

- Only plural relative fields are sign-flipped.

---

### `relativedelta.__bool__` / `__nonzero__`

**Signature**

```python
__bool__(self) -> bool
__nonzero__ = __bool__
```

**Pre-conditions**

- Instance has all expected fields.

**Post-conditions**

- Returns `False` only when all relative fields are zero/falsy, all absolute fields are `None`, `weekday is None`, and `leapdays` is falsy.
- Returns `True` otherwise.

**Invariants**

- Does not mutate instance.
- Python 2 compatibility alias has identical behavior.

**Edge cases**

- Absolute field value `0` is truthy for this contract if it is not `None`.
- `weekday` makes the delta truthy even if all numeric fields are zero.

**Operator-level invariants**

- Absolute fields are checked with `is None`, not truthiness.

---

### `relativedelta.__mul__` / `__rmul__`

**Signature**

```python
__mul__(self, other)
__rmul__ = __mul__
```

**Pre-conditions**

- `other` must be convertible to `float`; otherwise returns `NotImplemented`.

**Post-conditions**

- Returns a new delta with relative fields multiplied by `float(other)` and truncated through `int`.
- Absolute fields, `weekday`, and `leapdays` are preserved unchanged.

**Invariants**

- Original instance is not mutated.
- Multiplication is symmetric through `__rmul__`.

**Edge cases**

- Fractional products truncate toward zero.
- Multiplying by negative values flips signs of relative fields.
- `leapdays` is not multiplied.

**Operator-level invariants**

- Conversion is `f = float(other)`.
- Each relative result is `int(field * f)`.

---

### `relativedelta.__eq__`

**Signature**

```python
__eq__(self, other)
```

**Pre-conditions**

- `other` may be any object.

**Post-conditions**

- Returns `NotImplemented` if `other` is not a `relativedelta`.
- Returns `True` only if all relative fields, absolute fields, and `leapdays` are equal and weekday values are equivalent.
- Treats weekday `n=None` and `n=1` as equivalent.

**Invariants**

- Does not mutate either operand.

**Edge cases**

- If exactly one operand has `weekday`, equality is `False`.
- If weekday numbers differ, equality is `False`.
- Weekday `n` values differ only acceptably when both represent first occurrence/default.

**Operator-level invariants**

- Weekday comparison is performed before comparing scalar fields.

---

### `relativedelta.__hash__`

**Signature**

```python
__hash__(self) -> int
```

**Pre-conditions**

- All included fields are hashable.

**Post-conditions**

- Returns hash of tuple containing weekday, all relative fields, `leapdays`, and all absolute fields.

**Invariants**

- Does not mutate instance.

**Edge cases**

- Hash includes raw `weekday`; equality treats `weekday.n=None` and `weekday.n=1` as equal, so compatible hashing depends on weekday objects hashing those equivalently.

**Operator-level invariants**

- Tuple field order is fixed and must remain stable.

---

### `relativedelta.__ne__`

**Signature**

```python
__ne__(self, other)
```

**Pre-conditions**

- None beyond `__eq__`.

**Post-conditions**

- Returns `not self.__eq__(other)`.

**Invariants**

- Does not mutate operands.

**Edge cases**

- If `__eq__` returns `NotImplemented`, this method returns `False` because `not NotImplemented` is `False`.

**Operator-level invariants**

- No independent inequality comparison is performed.

---

### `relativedelta.__div__` / `__truediv__`

**Signature**

```python
__div__(self, other)
__truediv__ = __div__
```

**Pre-conditions**

- `other` must be convertible to `float`; otherwise returns `NotImplemented`.
- `float(other)` must be non-zero; zero propagates `ZeroDivisionError`.

**Post-conditions**

- Returns `self * (1 / float(other))`.
- Absolute fields, `weekday`, and `leapdays` are preserved via multiplication contract.

**Invariants**

- Original instance is not mutated.
- Python 2 and Python 3 division paths are identical.

**Edge cases**

- Fractional division results truncate toward zero through `__mul__`.
- Division by unsupported type returns `NotImplemented`.

**Operator-level invariants**

- Reciprocal is computed before multiplication.

---

### `relativedelta.__repr__`

**Signature**

```python
__repr__(self) -> str
```

**Pre-conditions**

- Instance has all expected fields.

**Post-conditions**

- Returns string of the form `relativedelta(...)` or subclass name with non-empty fields listed.
- Relative non-zero fields are formatted with signed general numeric format.
- Absolute fields and `weekday` are included when not `None`.

**Invariants**

- Does not mutate instance.
- Field order in representation is fixed.

**Edge cases**

- Zero/falsy relative fields are omitted.
- Absolute value `0` is included because the check is `is not None`.

**Operator-level invariants**

- Relative fields use `"{value:+g}"`; absolute fields use `repr(value)`.

---

### `_sign`

**Signature**

```python
_sign(x) -> int
```

**Pre-conditions**

- `x` must be accepted by `math.copysign`.

**Post-conditions**

- Returns `1` for positive values and positive zero.
- Returns `-1` for negative values and negative zero.

**Invariants**

- Does not mutate input.

**Edge cases**

- `_sign(0)` returns `1`.
- `_sign(-0.0)` returns `-1`.

**Operator-level invariants**

- Implemented as `int(copysign(1, x))`.
