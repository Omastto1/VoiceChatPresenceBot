import json
import os

import xarray as xr
import pandas as pd
import numpy as np
from collections import OrderedDict

DATACOLUMNS = ['date', 'start', 'end']


class DataAggregator:
    def __init__(self, group_names):
        """

        :param group_names: list of group names
        """
        self.meeting_id = 0
        self.group_attendances = {group_name: pd.DataFrame(columns=DATACOLUMNS, dtype=float) for group_name in group_names}
        if not os.path.isdir('./data'):
            os.mkdir('./data')

    def store_attendance(self, group):
        """Add new meeting record to aggregator

        :param group: dict with group meeting descriptions
        """
        meeting = pd.DataFrame(data=[group['meeting_date'], group['meeting_start'], group['meeting_end']],
                               index=[*DATACOLUMNS]).T
        for id, presence in group['attendance'].items():
            meeting[id] = presence/group['counter']
        self.group_attendances[group['name']] = pd.concat([self.group_attendances[group['name']], meeting], ignore_index=True)

    def save_data(self, group):
        """Save aggregator to .json and .xlsx

        :param group: dict with group meeting descriptions
        """
        attendance_save = self.group_attendances[group['name']].fillna(0.).copy()
        attendance_save.loc['aggregations'] = (
            pd.Series(attendance_save.mean(), dtype=float, name='aggregations'))

        with open(f"data/{group['name']}_aggregated_meetings_attendace.json", 'w+', encoding='utf-8') as f:
            json.dump(attendance_save.to_dict(), f)
        attendance_save.to_excel(f"data/{group['name']}_aggregated_meetings_attendace.xlsx")

    def update_attendance(self, group):
        """Update data in aggregator with new row and save them

        :param group: dict with group meeting descriptions
        """
        self.store_attendance(group)
        self.save_data(group)


