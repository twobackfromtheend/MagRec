from data_handler.orbit_with_spice import kernel_loader, orbit_times_generator, orbit_generator
import numpy as np
import pandas as pd
from data_handler.data_importer.imported_data import ImportedData
from data_handler.data_importer.helios_data import HeliosData
from data_handler.data_importer.ulysses_data import UlyssesData
from datetime import timedelta
import heliopy.spice as spice
from typing import List


def find_radii(orbiter: spice.Trajectory, radius: float = 0.4):
    """
    Finds all dates at which the radius from the sun is smaller than a given radius
    Much faster than other methods because different way of importing data
    :param radius: radius below which we want the data
    :return: a pandas data frame with the reduced data
    """
    radii = np.sqrt(orbiter.x ** 2 + orbiter.y ** 2 + orbiter.z ** 2)
    orbiter_data = pd.DataFrame(
        data={'Times': orbiter.times, 'X': orbiter.x, 'Y': orbiter.y, 'Z': orbiter.z, 'radius': radii})
    reduced = orbiter_data['radius'] < radius
    reduced_data = orbiter_data[reduced]
    if len(reduced_data) <2:
        raise IndexError('The data is too small')
    return reduced_data


def get_time_indices(reduced_data: pd.DataFrame) -> list:
    """
    We want to make shorter lists of dates that follow each other in order to finally get the data
    :param reduced_data: data that has a distance to the sun less than a given radius
    :return:
    """
    completed = False
    m, n = 0, 0
    list_of_indices = [[]]
    while not completed:
        if m == len(reduced_data.index) - 2:
            completed = True
        if reduced_data.index[m] == reduced_data.index[m + 1] - 1:
            list_of_indices[n].append(reduced_data.index[m])
            list_of_indices[n].append(reduced_data.index[m + 1])
        else:
            n = n + 1
            list_of_indices.append([])
        m += 1
    time_indices = []
    for n in range(len(list_of_indices)):
        start = min(list_of_indices[n])
        end = max(list_of_indices[n])
        time_indices.append([start, end])
    return time_indices


def get_dates(orbiter_times: pd.DataFrame, time_indices: list) -> list:
    """
    Function that finds the start and end dates of
    :param orbiter_times: data frame with the times available in the orbiter
    :param time_indices: start and end indices of different periods
    :return: start and end dates
    """
    all_dates = []
    for indices in time_indices:
        start_index = indices[0]
        end_index = indices[1]
        start = orbiter_times[start_index]
        end = orbiter_times[end_index]
        all_dates.append([start, end])
    return all_dates


def get_data(dates: list, probe: int = 2) -> List[ImportedData]:
    """
    Gets the data as ImportedData for the given start and end dates
    Be careful, especially for Helios 1  where a lot of data is missing
    :param dates: list of start and end dates when the spacecraft is at a location smaller than the given radius
    :param probe: 1 or 2 for Helios 1 or 2, can also be 'ulysses'
    :return: a list of ImportedData
    """
    imported_data = []
    for n in range(len(dates)):
        start = dates[n][0]
        end = dates[n][1]
        delta_t = end - start
        hours = np.int(delta_t.total_seconds() / 3600)
        start_date = start.strftime('%d/%m/%Y')
        try:
            if probe == 1 or probe == 2:
                imported_data.append(HeliosData(start_date=start_date, duration=hours, probe=probe))
            elif probe == 'ulysses':
                imported_data.append(UlyssesData(start_date=start_date, duration=hours))
            else:
                raise NotImplementedError('The data from this probe cannot be imported')
        except Exception:
            print('Previous method not working, switching to "day-to-day" method')
            hard_to_get_data = []
            interval = 24
            number_of_loops = np.int(hours/interval)
            for n in range(number_of_loops):
                try:
                    hard_to_get_data.append(HeliosData(start_date=start.strftime('%d/%m/%Y'), duration=interval, probe=probe))
                except Exception:
                    print('Not possible to download data between ' + str(start) + ' and ' +str(start+timedelta(hours=interval)))
                start = start + timedelta(hours=interval)

            for n in range(len(hard_to_get_data)):
                imported_data.append(hard_to_get_data[n])
    hours_to_analyse = 0
    for n in range(len(imported_data)):
        a = imported_data[n]
        hours_to_analyse = hours_to_analyse + len(a.data) * 40 / 3600  # only works for 40s measurements
    print(hours_to_analyse, ' hours to analyse')
    return imported_data


if __name__ == '__main__':
    orbiter = kernel_loader(2)
    times = orbit_times_generator('17/01/1976', '17/01/1979', 1)
    orbit_generator(orbiter, times)
    data = find_radii(orbiter, radius=0.3)
    time_indices = get_time_indices(data)
    dates = get_dates(orbiter.times, time_indices)
    imported_data_sets = get_data(dates)

# Helios 1 : December 10, 1974 to February 18, 1985
# Helios 2 : January 15, 1976 to December 23, 1979
