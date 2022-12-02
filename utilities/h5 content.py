# coding: utf-8

# This code take the building.csv file (output of development project script) and put it in the H5 file holder

import numpy as np
import pandas as pd

# read the latest building file
building = pd.read_csv(
    "C:/Users/blu/Box/Modeling and Surveys/Urban Modeling/Bay Area UrbanSim 1.5/H5 Contents/h5 contents/buildings_2020Mar20.1512.csv"
)

# read store
store = pd.HDFStore(
    "C:/Users/blu/Box/Modeling and Surveys/Urban Modeling/Bay Area UrbanSim 1.5/PBA50/Current PBA50 Large General Input Data/2020_03_17_bayarea_v5.h5"
)

# open the store
store.open()

# check if H5 has alread the building file

keys = store.keys()
if "/buildings" in keys:
    store.remove("buildings")
    store.put("buildings", building, format="table", append=False)
else:
    store.put("buildings", building, format="table", append=False)

# close the store
store.close()
