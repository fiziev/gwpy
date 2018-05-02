# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2013)
#
# This file is part of GWpy.
#
# GWpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWpy.  If not, see <http://www.gnu.org/licenses/>.

"""tconvert: a utility to convert to and from GPS times.

This method is inspired by the original tconvert utility, written by
Peter Shawhan.
"""

import datetime
from decimal import Decimal

from dateutil import parser as dateparser

from astropy.units import Quantity

from . import (Time, LIGOTimeGPS)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__all__ = ['tconvert', 'to_gps', 'from_gps']


def tconvert(gpsordate='now'):
    """Convert GPS times to ISO-format date-times and vice-versa.

    Parameters
    ----------
    gpsordate : `float`, `astropy.time.Time`, `datetime.datetime`, ...
        input gps or date to convert, many input types are supported

    Returns
    -------
    date : `datetime.datetime` or `LIGOTimeGPS`
        converted gps or date

    Notes
    -----
    If the input object is a `float` or `LIGOTimeGPS`, it will get
    converted from GPS format into a `datetime.datetime`, otherwise
    the input will be converted into `LIGOTimeGPS`.

    Examples
    --------
    Integers and floats are automatically converted from GPS to
    `datetime.datetime`:

    >>> from gwpy.time import tconvert
    >>> tconvert(0)
    datetime.datetime(1980, 1, 6, 0, 0)
    >>> tconvert(1126259462.3910)
    datetime.datetime(2015, 9, 14, 9, 50, 45, 391000)

    while strings are automatically converted to `~gwpy.time.LIGOTimeGPS`:

    >>> to_gps('Sep 14 2015 09:50:45.391')
    LIGOTimeGPS(1126259462, 391000000)

    Additionally, a few special-case words as supported, which all return
    `~gwpy.time.LIGOTimeGPS`:

    >>> tconvert('now')
    >>> tconvert('today')
    >>> tconvert('tomorrow')
    >>> tconvert('yesterday')
    """
    # convert from GPS into datetime
    try:
        float(gpsordate)  # if we can 'float' it, then its probably a GPS time
    except (TypeError, ValueError):
        return to_gps(gpsordate)
    return from_gps(gpsordate)


def to_gps(t, *args, **kwargs):
    """Convert any input date/time into a `LIGOTimeGPS`.

    Any input object that can be cast as a `~astropy.time.Time`
    (with `str` going through the `datetime.datetime`) are acceptable.

    Parameters
    ----------
    t : `float`, `~datetime.datetime`, `~astropy.time.Time`, `str`
        the input time, any object that can be converted into a
        `LIGOTimeGPS`, `~astropy.time.Time`, or `~datetime.datetime`,
        is acceptable.

    *args, **kwargs
        other arguments to pass to pass to `~astropy.time.Time` if given

    Returns
    -------
    gps : `LIGOTimeGPS`
        the number of GPS seconds (non-integer) since the start of the
        epoch (January 6 1980).

    Raises
    ------
    TypeError
        if a `str` input cannot be parsed as a `datetime.datetime`.
    ValueError
        if the input cannot be cast as a `~astropy.time.Time` or
        `LIGOTimeGPS`.

    Examples
    --------
    >>> to_gps('Jan 1 2017')
    LIGOTimeGPS(1167264018, 0)
    >>> to_gps('Sep 14 2015 09:50:45.391')
    LIGOTimeGPS(1126259462, 391000000)

    >>> import datetime
    >>> to_gps(datetime.datetime(2017, 1, 1))
    LIGOTimeGPS(1167264018, 0)

    >>> from astropy.time import Time
    >>> to_gps(Time(57754, format='mjd'))
    LIGOTimeGPS(1167264018, 0)
    """
    # -- convert input to Time, or something we can pass to LIGOTimeGPS

    if isinstance(t, str):  # str -> datetime.datetime
        t = _str_to_datetime(t)

    if isinstance(t, (tuple, list)):  # tuple -> datetime.datetime
        t = datetime.datetime(*t)

    if isinstance(t, datetime.date):  # datetime.datetime -> Time
        t = _datetime_to_time(t)

    if isinstance(t, Quantity):  # Quantity -> float
        t = t.to('second').value

    if isinstance(t, Decimal):  # Decimal -> str
        t = str(t)

    # -- convert to LIGOTimeGPS

    if isinstance(t, Time):
        return _time_to_gps(t, *args, **kwargs)
    try:
        return LIGOTimeGPS(t)
    except (TypeError, ValueError):
        return LIGOTimeGPS(float(t))


def from_gps(gps):
    """Convert a GPS time into a `datetime.datetime`.

    Parameters
    ----------
    gps : `LIGOTimeGPS`, `int`, `float`
        GPS time to convert

    Returns
    -------
    datetime : `datetime.datetime`
        ISO-format datetime equivalent of input GPS time

    Examples
    --------
    >>> from_gps(1167264018)
    datetime.datetime(2017, 1, 1, 0, 0)
    >>> from_gps(1126259462.3910)
    datetime.datetime(2015, 9, 14, 9, 50, 45, 391000)
    """
    try:
        gps = LIGOTimeGPS(gps)
    except (ValueError, TypeError, RuntimeError):
        gps = LIGOTimeGPS(float(gps))
    sec, nano = gps.gpsSeconds, gps.gpsNanoSeconds
    date = Time(sec, format='gps', scale='utc').datetime
    return date + datetime.timedelta(microseconds=nano*1e-3)


# -- utilities ----------------------------------------------------------------
# special case strings

def _now():
    return datetime.datetime.utcnow().replace(microsecond=0)


def _today():
    return datetime.date.today()


def _today_delta(**delta):
    return _today() + datetime.timedelta(**delta)


def _tomorrow():
    return _today_delta(days=1)


def _yesterday():
    return _today_delta(days=-1)


DATE_STRINGS = {
    'now': _now,
    'today': _today,
    'tomorrow': _tomorrow,
    'yesterday': _yesterday,
}


def _str_to_datetime(datestr):
    """Convert `str` to `datetime.datetime`.
    """
    try:  # try known string
        return DATE_STRINGS[str(datestr).lower()]()
    except KeyError:  # any other string
        try:
            return dateparser.parse(datestr)
        except (ValueError, TypeError) as exc:
            exc.args = ("Cannot parse date string {0!r}: {1}".format(
                datestr, exc.args[0]),)
            raise


def _datetime_to_time(dtm):
    # astropy.time.Time requires datetime.datetime
    if not isinstance(dtm, datetime.datetime):
        dtm = datetime.datetime.combine(dtm, datetime.time.min)
    return Time(dtm, scale='utc')


def _time_to_gps(time):
    """Convert a `Time` into `LIGOTimeGPS`.

    This method uses `datetime.datetime` underneath, which restricts
    to microsecond precision by design. This should probably be fixed...

    Parameters
    ----------
    time : `~astropy.time.Time`
        formatted `Time` object to convert

    Returns
    -------
    gps : `LIGOTimeGPS`
        Nano-second precision `LIGOTimeGPS` time
    """
    time = time.utc
    dt = time.datetime
    micro = dt.microsecond if isinstance(dt, datetime.datetime) else 0
    return LIGOTimeGPS(int(time.gps), int(micro*1e3))
