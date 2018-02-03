import matplotlib.pyplot as plt
import seaborn as sns
sns.set(rc={'figure.figsize': (12, 6)})

# built in python modules
import datetime

# python add-ons
import numpy as np
import pandas as pd

import pvlib

# Clear sky models
tus = pvlib.location.Location(32.2, -111, 'US/Arizona', 700, 'Tucson')
times = pd.DatetimeIndex(start='2016-01-01', end='2017-01-01', freq='1h', tz=tus.tz)
ephem_data = tus.get_solarposition(times)
irrad_data = tus.get_clearsky(times)

print(irrad_data.head())
irrad_data.plot()
plt.ylabel('Irradiance $W/m^2$')
plt.title('Ineichen, climatological turbidity')

plt.show()