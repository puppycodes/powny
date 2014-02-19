import datetime
import dateutil.parser


##### Private classes #####
class _Date:
    workdays = tuple(range(0, 5))
    offdays = tuple(range(5, 7))

    def __init__(self, timestr):
        if timestr is not None:
            self.datetime = dateutil.parser.parse(timestr)
        else:
            self.datetime = datetime.datetime.now()

    @staticmethod
    def now():
        return _Date(None)

    @property
    def weekday(self):
        return self.datetime.weekday()

    @property
    def month(self):
        return self.datetime.month

for (name, value) in zip(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec") +
        ("mon", "tue", "wed", "thu", "fri", "sat", "sun"),
        tuple(range(1, 13)) + tuple(range(7)),
    ):
    setattr(_Date, name, value)


##### Public constants #####
BUILTINS_MAP = {
    "date": _Date,
}

