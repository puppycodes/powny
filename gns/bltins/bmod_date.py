import datetime
import dateutil.parser


##### Private classes #####
class _Date:
    def __init__(self, timestr = None):
        if timestr is not None:
            self._datetime = dateutil.parser.parse(timestr)
        else:
            self._datetime = datetime.datetime.now()

    @staticmethod
    def now(timestr):
        return _Date(timestr)

    def get_datetime(self):
        return self._datetime

    def is_workday(self = None):
        return ( (self or _Date()).get_datetime().weekday() in tuple(range(0, 5)) )

    def is_offday(self = None):
        return ( (self or _Date()).get_datetime().weekday() in tuple(range(5, 7)) )

    def get_day(self = None):
        return (self or _Date()).get_datetime().weekday()

    def get_month(self = None):
        return (self or _Date()).get_datetime().month

for (name, value) in zip(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec") +
        ("mon", "tue", "wed", "thu", "fri", "sat", "sun"),
        tuple(range(1, 13)) + tuple(range(7)),
    ):
    setattr(_Date, name, value)

