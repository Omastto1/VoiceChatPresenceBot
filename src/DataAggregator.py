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

    def save_data(self):
        attendance_save = self.attendance.fillna(0.).copy()
        attendance_save.loc['aggregations'] = (
            pd.Series(attendance_save.mean(), dtype=float, name='aggregations'))

        with open(f'agregated_meetings_attendace.json', 'w+', encoding='utf-8') as f:
            json.dump(attendance_save.to_dict(), f)
        attendance_save.to_excel("output.xlsx")


