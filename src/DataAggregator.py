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

    def load_data(self) -> dict:
        """Load attendance record from json and add them to given aggregator

        :return: dictionary of all time attendees for each group
        """
        all_time_attendees = {}
        for group_name in self.group_attendances:
            file = f"data/{group_name}_aggregated_meetings_attendance.json"
            if os.path.exists(file):
                with open(file, 'r', encoding='utf-8') as f:
                    dict_data = json.load(f)

                # converting json dataset from dictionary to dataframe
                df_data = pd.DataFrame.from_dict(dict_data, orient='columns').drop(['aggregations'])
                self.group_attendances[group_name] = df_data

                # getting column names, removing info data and returning in dict
                attendees = set(df_data.columns)
                attendees.difference_update(DATACOLUMNS)
                all_time_attendees[group_name] = attendees

                print(f'{file} loaded.')
            else:
                print(f'{file} does not exists.')

        return all_time_attendees

    def save_data(self, group):
        """Save aggregator to .json and .xlsx

        :param group: dict with group meeting descriptions
        """
        attendance_save = self.group_attendances[group['name']].fillna(0.).copy()
        attendance_save.loc['aggregations'] = (
            pd.Series(attendance_save.mean(), dtype=float, name='aggregations'))

        with open(f"data/{group['name']}_aggregated_meetings_attendance.json", 'w+', encoding='utf-8') as f:
            json.dump(attendance_save.to_dict(), f)
        attendance_save.to_excel(f"data/{group['name']}_aggregated_meetings_attendance.xlsx")

    def update_attendance(self, group):
        """Update data in aggregator with new row and save them

        :param group: dict with group meeting descriptions
        """
        self.store_attendance(group)
        self.save_data(group)

    def update_ids(self, ids):
        with open(f"data/ids.json", 'w+', encoding='utf-8') as f:
            json.dump(ids, f)
        print("Updated dict of ids.")

