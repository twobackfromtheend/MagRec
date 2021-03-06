import numpy as np
import pandas as pd
from datetime import timedelta
from heliopy.data import ulysses

from data_handler.data_importer.imported_data import ImportedData


class UlyssesData(ImportedData):
    def __init__(self, start_date: str = '27/01/1998', duration: int = 15, start_hour: int = 0, probe: str = 'ulysses'):
        """
        :param start_date: string of 'DD/MM/YYYY'
        :param duration: int in hours
        :param start_hour: int from 0 to 23 indicating starting hour of given start_date
        :param probe: name
        """
        super().__init__(start_date, duration, start_hour, probe)
        self.data = self.get_imported_data()

        if len(self.data) == 0:
            raise RuntimeWarning('Created UlyssesData object has retrieved no data: {}'.format(self))

    def __repr__(self):
        return '{}: at {:%H:%M %d/%m/%Y} by probe {}. Data has {} entries.'.format(self.__class__.__name__,
                                                                                   self.start_datetime,
                                                                                   self.probe,
                                                                                   len(self.data))

    def get_imported_data(self):
        data_b = ulysses.fgm_hires(self.start_datetime, self.end_datetime)
        data_v = ulysses.swoops_ions(self.start_datetime, self.end_datetime)
        data_b = data_b.data  # fgm_hires now returns a time series (sunpy)
        data_v = data_v.data  # swoops_ions now returns a time series (sunpy)
        indices = [pd.Timestamp(index).to_pydatetime() for index in data_v.index.values]
        combined_data = pd.DataFrame(index=indices)
        iteration = 0
        for index in indices:
            interval = 2
            if iteration != 0 and iteration != len(indices) - 1:
                interval = (indices[iteration + 1] - indices[iteration - 1]).total_seconds() / 60
            combined_data.loc[index, 'vp_x'] = data_v.loc[index, 'v_r']
            combined_data.loc[index, 'vp_y'] = data_v.loc[index, 'v_t']
            combined_data.loc[index, 'vp_z'] = data_v.loc[index, 'v_n']
            combined_data.loc[index, 'n_p'] = data_v.loc[index, 'n_p']
            combined_data.loc[index, 'Tp_par'] = data_v.loc[index, 'T_p_large']
            combined_data.loc[index, 'Tp_perp'] = data_v.loc[index, 'T_p_small']
            combined_data.loc[index, 'r_sun'] = data_v.loc[index, 'r']
            combined_data.loc[index, 'Bx'] = np.mean(
                data_b.loc[index - timedelta(minutes=interval):index + timedelta(minutes=interval), 'Bx'])
            combined_data.loc[index, 'By'] = np.mean(
                data_b.loc[index - timedelta(minutes=interval):index + timedelta(minutes=interval), 'By'])
            combined_data.loc[index, 'Bz'] = np.mean(
                data_b.loc[index - timedelta(minutes=interval):index + timedelta(minutes=interval), 'Bz'])

            iteration += 1

        return combined_data


if __name__ == '__main__':
    x = UlyssesData()
    print(x.data)
