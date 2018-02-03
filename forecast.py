import datetime

# scientific python add-ons
import pandas as pd

import matplotlib.pyplot as plt
# seaborn makes your plots look better
import seaborn as sns
sns.set(rc={"figure.figsize": (12, 6)})
sns.set_color_codes()

# finally, we import the pvlib library
from pvlib import solarposition,irradiance,atmosphere,pvsystem
from pvlib.forecast import GFS, RAP, HRRR, HRRR_ESRL
import timezonefinder

# Define global parameters
tf = timezonefinder.TimezoneFinder()
surface_tilt = 30
surface_azimuth = 180 # pvlib uses 0=North, 90=East, 180=South, 270=West convention
albedo = 0.2
# Define forecast model
fm = GFS()


# Calculate mean irradiance per hour by meter^2 in some period of time
def mean_AC_power_per_hour_some_period(lat, lon, start, end):
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
    return p_ac.mean()


def total_AC_power_some_period(lat, lon, start, end):
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
    return p_ac.sum() * 3


def mean_AC_power_yearly(lat, lon):
    # Get current timezone
    timezone = tf.certain_timezone_at(lat=lat, lng=lon)
    if timezone is None:
        timezone = "Europe/Helsinki"
    # Get mean power in last 5 years
    curr_year = datetime.datetime.now().year
    start = pd.Timestamp(str(curr_year - 5) + "-01-01", tz=timezone)
    end = pd.Timestamp(datetime.date.today(), tz=timezone)
    return mean_AC_power_per_hour_some_period(lat, lon, start, end)


def total_AC_power_yearly(lat, lon):
    # Get current timezone
    timezone = tf.certain_timezone_at(lat=lat, lng=lon)
    if timezone is None:
        timezone = "Europe/Helsinki"
    # Get mean power in last 5 years
    curr_year = datetime.datetime.now().year
    start = pd.Timestamp(datetime.datetime.today(), tz=timezone) - pd.Timedelta(days=365)
    end = pd.Timestamp(datetime.datetime.today(), tz=timezone)
    data = fm.get_data(lat, lon, start, end)
    print(len(data))
    return 1


# Choose a location.
# Tucson, AZ
latitude = 32.2
longitude = -110.9
tz = 'US/Mountain'

# Get time for forecasting
start = pd.Timestamp(datetime.date.today(), tz=tz) # today's date
end = start + pd.Timedelta(days=7) # 7 days from today

print("Mean:", mean_AC_power_per_hour_some_period(latitude, longitude, start, end))
#print("Mean yeary:", mean_AC_power_yearly(latitude, longitude))
print("Total:", total_AC_power_some_period(latitude, longitude, start, end))
print("Total yearly:", total_AC_power_yearly(latitude, longitude))
















