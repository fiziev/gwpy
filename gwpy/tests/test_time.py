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

"""Tests for :mod:`gwpy.time`
"""

from datetime import datetime
from decimal import Decimal

import pytest

import numpy

from freezegun import freeze_time

from astropy.time import Time
from astropy.units import (UnitConversionError, Quantity)

from glue.lal import LIGOTimeGPS as GlueGPS

from gwpy import time
from gwpy.time import LIGOTimeGPS

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

GW150914 = LIGOTimeGPS(1126259462, 391000000)
GW150914_DT = datetime(2015, 9, 14, 9, 50, 45, 391000)
FREEZE = '2015-09-14 09:50:45.391'
NOW = 1126259462
TODAY = 1126224017
TOMORROW = 1126310417
YESTERDAY = 1126137617


def _test_with_errors(func, in_, out):
    # assert error
    if isinstance(out, type) and issubclass(out, Exception):
        with pytest.raises(out):
            func(in_)
    # assert not error
    else:
        with freeze_time(FREEZE):
            assert func(in_) == out


# -- test functions -----------------------------------------------------------

@pytest.mark.parametrize('in_, out', [
    (1126259462, int(GW150914)),
    (LIGOTimeGPS(1126259462, 391000000), GW150914),
    ('Jan 1 2017', 1167264018),
    ('Sep 14 2015 09:50:45.391', GW150914),
    ((2017, 1, 1), 1167264018),
    (datetime(2017, 1, 1), 1167264018),
    (Time(57754, format='mjd'), 1167264018),
    (Time(57754.0001, format='mjd'), LIGOTimeGPS(1167264026, 640000000)),
    (Quantity(1167264018, 's'), 1167264018),
    (Decimal('1126259462.391000000'), GW150914),
    (GlueGPS(GW150914.gpsSeconds, GW150914.gpsNanoSeconds), GW150914),
    (numpy.int32(NOW), NOW),  # fails with lal-6.18.0
    ('now', NOW),
    ('today', TODAY),
    ('tomorrow', TOMORROW),
    ('yesterday', YESTERDAY),
    (Quantity(1, 'm'), UnitConversionError),
    ('random string', ValueError),
])
def test_to_gps(in_, out):
    """Test :func:`gwpy.time.to_gps`
    """
    _test_with_errors(time.to_gps, in_, out)


@pytest.mark.parametrize('in_, out', [
    (1167264018, datetime(2017, 1, 1)),
    ('1167264018', datetime(2017, 1, 1)),
    (1126259462.391, datetime(2015, 9, 14, 9, 50, 45, 391000)),
    ('1.13e9', datetime(2015, 10, 27, 16, 53, 3)),
    (GlueGPS(GW150914.gpsSeconds, GW150914.gpsNanoSeconds), GW150914_DT),
    ('test', ValueError),
])
def test_from_gps(in_, out):
    """Test :func:`gwpy.time.from_gps`
    """
    _test_with_errors(time.from_gps, in_, out)


@pytest.mark.parametrize('in_, out', [
    (float(GW150914), GW150914_DT),
    (GW150914, GW150914_DT),
    (GW150914_DT, GW150914),
    (GlueGPS(float(GW150914)), GW150914_DT),
    ('now', NOW),
    ('today', TODAY),
    ('tomorrow', TOMORROW),
    ('yesterday', YESTERDAY),
])
def test_tconvert(in_, out):
    """Test :func:`gwpy.time.tconvert`
    """
    _test_with_errors(time.tconvert, in_, out)
