import json

import xarray as xr
import pandas as pd
import numpy as np
from collections import OrderedDict

DATACOLUMNS = ['date', 'start', 'end']


class DataAggregator:
    def __init__(self):
        self.meeting_id = 0
        self.attendance = pd.DataFrame(columns=DATACOLUMNS, dtype=float)
        print(self.attendance)

    def store_attendance(self, date, start, end, attendance: dict,no_checks):
        meeting = pd.DataFrame(data=[date, start, end], index=[*DATACOLUMNS]).T
        for id, presence in attendance.items():
            meeting[id] = presence/no_checks
        self.attendance = pd.concat([self.attendance, meeting], ignore_index=True)

    def save_json(self):
        self.attendance = self.attendance.fillna(0.)
        self.attendance.loc['aggregations'] = (
            pd.Series(self.attendance.mean(), dtype=float, name='aggregations'))
        with open(f'agregated_meetings_attendace.json', 'w+', encoding='utf-8') as f:
            json.dump(self.attendance.to_dict(), f)


if __name__ == '__main__':
    dataAggregator = DataAggregator()
    dataAggregator.store_attendance('01/10/2020', '00:38:36', '00:42:04', {'mrkos': 1, 'Tomáš Omasta': 13, 'asd': 10}, 15)
    dataAggregator.store_attendance('01/10/2020', '00:38:36', '00:42:04', {'Tomáš Omasta': 13, 'asd': 10}, 15)
    dataAggregator.store_attendance('01/10/2020', '00:38:36', '00:42:04', {'mrkos': 1, 'Tomáš Omasta': 13, 'asd': 10, 'aas': 123}, 15)
    dataAggregator.store_attendance('01/10/2020', '00:38:36', '00:42:04', {'aas': 123}, 15)
    dataAggregator.save_json()
    dataAggregator.attendance.to_excel("output.xlsx")
    print(dataAggregator.attendance)