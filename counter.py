
from datetime import date


class Counter():

    def __init__(self, cid, ctype, name, increase, value=None, last_update=None):
        self.cid = cid
        self.type = ctype
        self.name = name
        self.increase = int(increase)
        self.value = int(value) if value is not None else int(increase)
        if last_update is not None:
            self.update(last_update)

    def update(self, last_update):
        days_past = (date.today() - last_update).days
        if self.type=="daily":
            self.value += days_past * self.increase
        else:
            self.value += (last_update.weekday() + days_past)//7 * self.increase

    def decrease(self, decrease):
        self.value -= decrease

    def __str__(self):
        return f"{self.name} ({self.type[0].upper()}+{self.increase}): {self.value}"

    def __repr__(self):
        return f"{self.type};{self.name};{self.increase};{self.value};{date.today()}"