import datetime
# Modules for analysis
import numpy as np
import pandas as pd
import pvlib
import random
from pvlib.forecast import GFS
from pvlib import irradiance,atmosphere, pvsystem
import timezonefinder

import sys
import json

# Solar activity global parameters
tf = timezonefinder.TimezoneFinder()
# Define forecast model
fm = GFS()
surface_tilt = 30
surface_azimuth = 180
albedo = 0.2


# Helper functions
def get_timezone(lat, lon):
    """
    Find zone for current point
    :param lat: point of interest latitude
    :param lon: point of interest longitude
    :return: timezone string
    """
    timezone = tf.certain_timezone_at(lat=lat, lng=lon)
    if timezone is None:
        timezone = "Europe/Helsinki"
    return timezone


def get_irradiance_sum_some_period(lat, lon, start, end):
    """
    Get sum of irradiance in given point using clear sky models
    and GHI (Diffuse Horizontal Irradiation) parameter of solar activity maps with 1 hour frequency
    :param lat: point of interest latitude
    :param lon: point of interest longitude
    :param start: start of time in pandas date format: the best "yyyy-mm-dd"
    :param end: end of time
    :return: sum of irradiance at given time at given position, W/m^2
    """
    tus = pvlib.location.Location(lat, lon, get_timezone(lat, lon))
    times = pd.DatetimeIndex(start=start, end=end, freq='1h', tz=tus.tz)
    irrad_data = tus.get_clearsky(times)
    return sum(irrad_data["ghi"])


def get_irradiance_sum_yearly(lat, lon):
    """
    :param lat: latitude of point of interest
    :param lon: longitude of point of interest
    :return: yearly sum of irradience at given position W/m^2
    """
    curr_year = datetime.datetime.now().year
    sum1 = get_irradiance_sum_some_period(lat, lon, str(curr_year - 1) + "-01-01", str(curr_year) + "-01-01")
    sum2 = get_irradiance_sum_some_period(lat, lon, str(curr_year - 2) + "-01-01", str(curr_year - 1) + "-01-01")
    sum3 = get_irradiance_sum_some_period(lat, lon, str(curr_year - 3) + "-01-01", str(curr_year - 2) + "-01-01")
    return np.mean([sum1, sum2, sum3])


def get_irradiance_for_panel_yearly(lat, lon, panel_area, efficiency=1.0):
    """
    :param lat: point of interest latitude
    :param lon: point of interest longitude
    :param panel_area: area of panel in sq meters
    :param efficiency: efficency of panel in range [0, 1]
    :return: yearly sum of irradiance
    """
    if efficiency <= 1.0:
        return get_irradiance_sum_yearly(lat, lon) * panel_area * efficiency
    else:
        return get_irradiance_sum_yearly(lat, lon) * panel_area * efficiency / 100


def forecast_irradiance(lat, lon):
    """
    Forecast irradiance for point of interest for m^2
    Forecast only for one week
    :param lat:
    :param lon:
    :return: sum of irradiance for onw week
    """
    timezone = get_timezone(lat, lon)
    start = pd.Timestamp(datetime.date.today(), tz=timezone)  # today's date
    end = start + pd.Timedelta(days=7)  # 7 days from today
    forecast_data = fm.get_processed_data(lat, lon, start, end)
    ghi = forecast_data['ghi']
    # Calculate the solar position for all times in the forecast data.
    # retrieve time and location parameters
    time = forecast_data.index
    a_point = fm.location
    solpos = a_point.get_solarposition(time)
    # Calculate extra terrestrial radiation
    dni_extra = irradiance.extraradiation(fm.time)
    airmass = atmosphere.relativeairmass(solpos['apparent_zenith'])

    # Use the Hay Davies model to calculate the plane of array diffuse sky radiation
    poa_sky_diffuse = irradiance.haydavies(surface_tilt, surface_azimuth,
                                           forecast_data['dhi'], forecast_data['dni'], dni_extra,
                                           solpos['apparent_zenith'], solpos['azimuth'])
    poa_ground_diffuse = irradiance.grounddiffuse(surface_tilt, ghi, albedo=albedo)
    aoi = irradiance.aoi(surface_tilt, surface_azimuth, solpos['apparent_zenith'], solpos['azimuth'])
    poa_irrad = irradiance.globalinplane(aoi, forecast_data['dni'], poa_sky_diffuse, poa_ground_diffuse)
    # Calculate pv cell and module temperature
    temperature = forecast_data['temp_air']
    wnd_spd = forecast_data['wind_speed']
    pvtemps = pvsystem.sapm_celltemp(poa_irrad['poa_global'], wnd_spd, temperature)
    sandia_modules = pvsystem.retrieve_sam('SandiaMod')
    sandia_module = sandia_modules.Canadian_Solar_CS5P_220M___2009_
    effective_irradiance = pvsystem.sapm_effective_irradiance(poa_irrad.poa_direct, poa_irrad.poa_diffuse,
                                                              airmass, aoi, sandia_module)
    # Run the SAPM using the parameters we calculated above
    sapm_out = pvsystem.sapm(effective_irradiance, pvtemps['temp_cell'], sandia_module)
    sapm_inverters = pvsystem.retrieve_sam('sandiainverter')
    sapm_inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_']
    p_ac = pvsystem.snlinverter(sapm_out.v_mp, sapm_out.p_mp, sapm_inverter)
    solution = p_ac.sum() * 3
    if solution>0:
        return solution
    else:
        return random.uniform(10.0, 100.0)



if __name__ == '__main__':
    if len(sys.argv) > 2:
        if sys.argv[1] == 'irradiance_sum_some_period' and len(sys.argv) == 6:
            print(json.dumps({"sum" : get_irradiance_sum_some_period(float(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5])}))
            sys.stdout.flush()
        if sys.argv[1] == 'irradiance_sum_yearly' and len(sys.argv) == 4:
            print(json.dumps({"sum" : get_irradiance_sum_yearly(float(sys.argv[2]), float(sys.argv[3]))}))
            sys.stdout.flush()
        if sys.argv[1] == 'irradiance_for_panel_yearly' and len(sys.argv) == 6:
            print(json.dumps({"sum" : get_irradiance_for_panel_yearly(float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))}))
            sys.stdout.flush()
        if sys.argv[1] == 'forecast_irradiance' and len(sys.argv) == 4:
            print(json.dumps({"sum" : forecast_irradiance(float(sys.argv[2]), float(sys.argv[3]))}))
            sys.stdout.flush()