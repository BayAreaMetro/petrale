library(dplyr)
library(stringr)
options(scipen = 999) # disables scientific notation

############### INPUTS TO UPDATE ############### 
# folder name
folder = "Blueprint Plus Crossing (s23)/v1.7.1- FINAL DRAFT BLUEPRINT/"

# create variable for model run number
modelrun = "98"

# set working directory for UrbanSim model run
setwd(paste0("C:/Users/rmccoy/Box/Modeling and Surveys/Urban Modeling/Bay Area UrbanSim 1.5/PBA50/Draft Blueprint runs/",folder))

############### H2-3 Annual acres of greenfield development ############### 
# note: urban_footprint_0 = greenfield sites
# define function to calculate avg annual greenfield development between any two model run years
greenfield = function(startyear, endyear){
  startdf = read.csv(paste0("run",modelrun,"_urban_footprint_summary_",toString(startyear),".csv"))%>%filter(X == "acres")%>%select(urban_footprint_0)
  enddf = read.csv(paste0("run",modelrun,"_urban_footprint_summary_",toString(endyear),".csv"))%>%filter(X == "acres")%>%select(urban_footprint_0)
  
  df = data.frame((enddf - startdf)/(endyear-startyear))%>%mutate(
    metric = "H2-3", 
    name = "annual_acres_greenfield_dev", 
    year = endyear)%>%rename(value = urban_footprint_0)
}

# run function for period 2010-2015 (baseline) and 2015-2050 (performance)
ann_greenfield_2010_2015 = greenfield(2010, 2015)
ann_greenfield_2015_2050 = greenfield(2015, 2050)

# adjust 2015 greenfield to match observed data (correcting for many development projecs being forced between 2010 and 2015)
greenfield_observed_2015 = 6642/2
ann_greenfield_2010_20152 = ann_greenfield_2010_2015%>%mutate(value = value*(greenfield_observed_2015/value))

setwd("C:/Users/rmccoy/Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/Healthy")
greenfield_export = rbind(ann_greenfield_2010_20152,ann_greenfield_2015_2050)%>%mutate(modelrunID = folder)
write.csv(greenfield_export,"greenfield_development_export.csv")