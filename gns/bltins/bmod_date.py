import time


##### Private constants #####
_FIELDS_ORDER = ("tm_year", "tm_mon", "tm_mday", "tm_hour", "tm_min", "tm_sec")
_FORMATS = (
    ("%H:%M",    ("tm_hour", "tm_min")),
    ("%H:%M:%S", ("tm_hour", "tm_min", "tm_sec")),
    ("%Y-%m-%d", ("tm_year", "tm_mon", "tm_mday")),
    ("%Y-%m-%d %H:%M:%S", _FIELDS_ORDER),
)


##### Private classes #####
class _Date:
    def __init__(self, date = None):
        self._st_time = None
        self._fields = ()

        if date is None:
            self._st_time = time.localtime()
        else:
            for (date_format, fields) in _FORMATS:
                try:
                    self._st_time = time.strptime(date, date_format)
                except ValueError:
                    continue
                self._fields = fields
            if self._st_time is None:
                raise ValueError("Unknown format: {}".format(date))


    ### Public ###

    def get_value(self):
        return time.mktime(self._st_time)

    def get_fields(self):
        return self._fields

    def get_field(self, field):
        return getattr(self._st_time, field)


    ### Private ###

    def _extract_fields(self, other):
        local_fields = set(self.get_fields() or _FIELDS_ORDER)
        other_fields = set(other.get_fields() or _FIELDS_ORDER)
        fields = local_fields.intersection(other_fields)
        values = []
        for field in _FIELDS_ORDER:
            if field not in fields:
                continue
            values.append((self.get_field(field), other.get_field(field)))
        return values

    def _less_then(self, other):
        for (local_value, other_value) in self._extract_fields(other):
            if local_value < other_value:
                return True
        return False

    def _equal(self, other):
        for (local_value, other_value) in self._extract_fields(other):
            if local_value != other_value:
                return False
        return True

    ###

    def __lt__(self, other):
        return self._less_then(other)

    def __le__(self, other):
        return ( self._less_then(other) or self._equal(other) )

    def __eq__(self, other):
        return self._equal(other)

    def __ne__(self, other):
        return not self._equal(other)

    def __gt__(self, other):
        return ( other < self )

    def __ge__(self, other):
        return ( other < self or other == self )


    ### Classmethods ###

    def is_weekday(self = None):
        return ( (self or _Date()).get_field(field) in tuple(range(0, 5)) )

    def is_offday(self = None):
        return ( (self or _Date()).get_field(field) in tuple(range(5, 7)) )

for (name, field, value) in (
        ("is_jan", "tm_mon", 1),
        ("is_feb", "tm_mon", 2),
        ("is_mar", "tm_mon", 3),
        ("is_apr", "tm_mon", 4),
        ("is_may", "tm_mon", 5),
        ("is_jun", "tm_mon", 6),
        ("is_jul", "tm_mon", 7),
        ("is_aug", "tm_mon", 8),
        ("is_sep", "tm_mon", 9),
        ("is_oct", "tm_mon", 10),
        ("is_nov", "tm_mon", 11),
        ("is_dec", "tm_mon", 12),

        ("is_mon", "tm_wday", 0),
        ("is_tue", "tm_wday", 1),
        ("is_wed", "tm_wday", 2),
        ("is_thu", "tm_wday", 3),
        ("is_fri", "tm_wday", 4),
        ("is_sat", "tm_wday", 5),
        ("is_sun", "tm_wday", 6),
    ):
    def __make_method(field, value):
        return ( lambda self = None: (self or _Date()).get_field(field) == value )
    setattr(_Date, name, __make_method(field, value))


##### Public constants #####
BUILTINS_MAP = {
    "date": _Date,
}

