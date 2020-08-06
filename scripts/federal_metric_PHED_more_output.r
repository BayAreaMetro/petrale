########################################################################################

# R code to calculate Peak Hour Excessive Delay(PHED)
# i.e. Annual Hours of Peak Hour Excessive Delay (PHED) Per Capita

# Background:
# -----------
# Webinar providing key definitions here: https://www.fhwa.dot.gov/tpm/rule.cfm (see June 1 webinar, around 30 minutes in, slide 35)
# Slides from the webinar here (no longer available online): M:\Application\Model One\TIP2019\Excessive_delay\170601pm3.pdf
# Additional info here: https://www.fhwa.dot.gov/tpm/rule/pm3/phed.pdf

# Key definitions:
# ----------------
# "Threshold": Travel Time at 20mph OR at 60% of the posted speed limit

# "Peak hours": They define "peak travel hours" as 6-10 a.m. on weekday mornings; and the weekday afternoon period is 3-7 p.m. or 4-8 p.m. (State DOTs and MPOs can choose one that suits them).
# In our travel model we have AM as 6-10 am) and PM as 3-7 pm). So these are the two time periods that we need to analysis (not all five time periods).

# Excessive delay is calculated for three modes - car (drive alone, shared by two, and shared by 3+), trucks (small and medium, and heavy vehicles), and buses.

########################################################################################

library(foreign)
library(dplyr)
library(tidyr)

##################################
# set file paths
##################################

Scenario <- "M:/Application/Model One/RTP2021/IncrementalProgress/2015_TM152_IPA_16"
PHED_output_file <- "C:/Users/rmccoy/Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/Connected/PHED_2015.csv"

SFOakUAlinks_txt <-"M:/Application/Model One/TIP2019/Excessive_delay/LinksInSFOakUA_2020n2022.txt"
SJUAlinks_txt <-"M:/Application/Model One/TIP2019/Excessive_delay/LinksInSJUA_2020n2022.txt"

SFOakUAtaz_txt <-"M:/Application/Model One/TIP2019/Excessive_delay/SFOakUA_706TAZ.txt"
SJUAtaz_txt <- "M:/Application/Model One/TIP2019/Excessive_delay/SJUA_336TAZ.txt"

bp = "PlusCrossing"
year = 2050

##################################
# Calculations for cars and trucks
##################################

phed_calc = function(Scenario, bp, year){
  
  # read the standard output avgload5period_vehclasses.csv from a scenario
  file_cars_n_trucks <- paste0(Scenario, "/OUTPUT/avgload5period_vehclasses.csv")
  RoadwayData <- read.csv(file=file_cars_n_trucks, header=TRUE, sep=",")
  
  # check number of rows in the dataset
  nrow(RoadwayData)
  
  # keep cases where facility type does not equal to 6
  RoadwayData <- subset(RoadwayData, ft!=6)
  nrow(RoadwayData)
  
  # add a column to show 60 percent of posted speed
  RoadwayData$ffs60pc <- RoadwayData$ffs*0.6
  
  # determine threshold speed
  RoadwayData$threshold_speed <- pmax(RoadwayData$ffs60pc, 20)
  
  # determine threshold time (in minutes)
  RoadwayData$threshold_time <- RoadwayData$distance/RoadwayData$threshold_speed*60
  
  #------
  # analysis by time period
  #------
  
  # determine if the link is below threshold in a certain time period
  RoadwayData$below_thresholdAM <- ifelse(RoadwayData$cspdAM<RoadwayData$threshold_speed, 1, 0)
  RoadwayData$below_thresholdPM <- ifelse(RoadwayData$cspdPM<RoadwayData$threshold_speed, 1, 0)
  
  # congested travel time (ctim) - threshold_time
  RoadwayData$timediffAM <- RoadwayData$ctimAM - RoadwayData$threshold_time
  RoadwayData$timediffPM <- RoadwayData$ctimPM - RoadwayData$threshold_time
  
  # excessive delay by link in minutes
  RoadwayData$delayAM = RoadwayData$below_thresholdAM * RoadwayData$timediffAM
  RoadwayData$delayPM = RoadwayData$below_thresholdPM * RoadwayData$timediffPM
  
  # excessive delay taking volume into account
  RoadwayData$delayXvolAM = RoadwayData$delayAM * (RoadwayData$volAM_da * 1 + RoadwayData$volAM_s2 * 2 + RoadwayData$volAM_s3 * 3 + RoadwayData$volAM_sm * 1 + RoadwayData$volAM_hv * 1
  			+ RoadwayData$volAM_dat * 1 + RoadwayData$volAM_s2t * 2 + RoadwayData$volAM_s3t * 3 + RoadwayData$volAM_smt * 1 + RoadwayData$volAM_hvt * 1)
  
  RoadwayData$delayXvolPM = RoadwayData$delayPM * (RoadwayData$volPM_da * 1 + RoadwayData$volPM_s2 * 2 + RoadwayData$volPM_s3 * 3 + RoadwayData$volPM_sm * 1 + RoadwayData$volPM_hv * 1
  			+ RoadwayData$volPM_dat * 1 + RoadwayData$volPM_s2t * 2 + RoadwayData$volPM_s3t * 3 + RoadwayData$volPM_smt * 1 + RoadwayData$volPM_hvt * 1)
  
  # total excessive delay in hours - cars and trucks
  sum(RoadwayData$delayXvolAM)/60
  sum(RoadwayData$delayXvolPM)/60
  
  ##################################
  # Calculate for delay on buses
  ##################################
  
  
  # initiate a vector to store the 15 file paths
  file_busesAM <- vector()
  file_busesPM <- vector()
  
  dbfAM = read.dbf(paste0(Scenario, "/OUTPUT/trn/trnlinkAM_ALLMSA.dbf"))
  dbfPM = read.dbf(paste0(Scenario, "/OUTPUT/trn/trnlinkPM_ALLMSA.dbf"))
  
  # we only want bus lines
  # i.e. MODE >= 10 and MODE<100
  # according to this: https://github.com/BayAreaMetro/travel-model-one/blob/master/utilities/PBA40/metrics/bus_opcost.py
  # NewList1 <- filter(BusDataAM1, (MODE>=10 & MODE<100))
  # NewList2 <- filter(BusDataAM2, (MODE>=10 & MODE<100))
  # keep only 4 variables (A, B, MODE and AB_VOL)
  
  dbf_busonlyAM = dbfAM%>%filter((MODE>=10 & MODE <100))%>%select(A, B, MODE, AB_VOL)%>%group_by(A, B)%>%summarise(bus_vol = sum(AB_VOL))
  dbf_busonlyPM = dbfPM%>%filter((MODE>=10 & MODE <100))%>%select(A, B, MODE, AB_VOL)%>%group_by(A, B)%>%summarise(bus_vol = sum(AB_VOL))
  
  
  # write out a file to check
  # write.csv(BusData15FilesAM, file="M:/Application/Model One/TIP2019/Excessive_delay/temp_outfile_am.csv")
  # write.csv(BusData15FilesAM, file="M:/Application/Model One/TIP2019/Excessive_delay/temp_outfile_pm.csv")
  
  # -------
  # merge the bus volume to the RoadwayFile
  # ------
  RoadwayBusDataAM <- left_join(RoadwayData, dbf_busonlyAM, by = c("a" = "A", "b" = "B"))
  RoadwayBusDataPM <- left_join(RoadwayData, dbf_busonlyPM, by = c("a" = "A", "b" = "B"))
  
  # fill in the NAs after the left join
  RoadwayBusDataAM$bus_vol[is.na(RoadwayBusDataAM$bus_vol)] <- 0
  RoadwayBusDataPM$bus_vol[is.na(RoadwayBusDataPM$bus_vol)] <- 0
  
  RoadwayBusDataAM$delayXbus_vol <- RoadwayBusDataAM$delayAM * RoadwayBusDataAM$bus_vol
  RoadwayBusDataPM$delayXbus_vol <- RoadwayBusDataPM$delayPM * RoadwayBusDataPM$bus_vol
  
  # total excessive delay in hours - bus only
  sum(RoadwayBusDataAM$delayXbus_vol)/60
  sum(RoadwayBusDataPM$delayXbus_vol)/60
  
  # total excessive delay in hours - car, bus, and trucks
  (sum(RoadwayBusDataAM$delayXvolAM) + sum(RoadwayBusDataAM$delayXbus_vol))/60
  (sum(RoadwayBusDataPM$delayXvolPM) + sum(RoadwayBusDataPM$delayXbus_vol))/60
  
  # read the VMT file to get total population
  file_population <- paste(Scenario, "/OUTPUT/core_summaries/AutoTripsVMT_personsHomeWork.csv", sep="")
  VMTData <- read.csv(file=file_population, header=TRUE, sep=",")
  totpop_BayArea <- sum(VMTData$freq)
  totpop_BayArea
  
  
  # total excessive delay *per person* in hours - car, bus, and trucks (per day)
  PHED_AM <-(sum(RoadwayBusDataAM$delayXvolAM) + sum(RoadwayBusDataAM$delayXbus_vol))/60/totpop_BayArea
  PHED_PM <-(sum(RoadwayBusDataPM$delayXvolPM) + sum(RoadwayBusDataPM$delayXbus_vol))/60/totpop_BayArea
  
  PHED_annual = (PHED_AM+PHED_PM)*300
  
  
  ##################################
  # Add geographic definitions
  ##################################
  
  # Read the geographic defintions
  SFOakUA_links <- read.csv(file=SFOakUAlinks_txt, header=TRUE, sep=",")
  SJUA_links <- read.csv(file=SJUAlinks_txt, header=TRUE, sep=",")
  
  SFOakUA_links <- select(SFOakUA_links, A, B, DISTANCE)
  SJUA_links <- select(SJUA_links, A, B, DISTANCE)
  
  # merge files indicating links that lie within the two urbanized areas respectively
  SFOakUA_RoadwayBusDataAM <- left_join(RoadwayBusDataAM, SFOakUA_links, by = c("a" = "A", "b" = "B"))
  SFOakUA_RoadwayBusDataPM <- left_join(RoadwayBusDataPM, SFOakUA_links, by = c("a" = "A", "b" = "B"))
  
  SJUA_RoadwayBusDataAM <- left_join(RoadwayBusDataAM, SJUA_links, by = c("a" = "A", "b" = "B"))
  SJUA_RoadwayBusDataPM <- left_join(RoadwayBusDataPM, SJUA_links, by = c("a" = "A", "b" = "B"))
  
  # filter out the irrelevant links
  SFOakUA_RoadwayBusDataAM <- filter(SFOakUA_RoadwayBusDataAM, !is.na(DISTANCE))
  SFOakUA_RoadwayBusDataPM <- filter(SFOakUA_RoadwayBusDataPM, !is.na(DISTANCE))
  
  SJUA_RoadwayBusDataAM <- filter(SJUA_RoadwayBusDataAM, !is.na(DISTANCE))
  SJUA_RoadwayBusDataPM <- filter(SJUA_RoadwayBusDataPM, !is.na(DISTANCE))
  
  ##################################
  # Calculate population
  ##################################
  
  # read files indicating tazs that lie within the two urbanized areas respectively
  SFOakUA_TAZ <- read.csv(file=SFOakUAtaz_txt, header=TRUE, sep=",")
  SJUA_TAZ <- read.csv(file=SJUAtaz_txt, header=TRUE, sep=",")
  
  # merge the files
  VMTData_SFOakUA <- left_join(VMTData,SFOakUA_TAZ, by = c("taz" = "TAZ1454"))
  VMTData_SJUA <- left_join(VMTData,SJUA_TAZ, by = c("taz" = "TAZ1454"))
  
  # filter out the irrelevant zones
  VMTData_SFOakUA <- filter(VMTData_SFOakUA, !is.na(FID))
  VMTData_SJUA <- filter(VMTData_SJUA, !is.na(FID))
  
  # calculate total population by UA
  SFOakUA_totpop <- sum(VMTData_SFOakUA$freq)
  SJUA_totpop <- sum(VMTData_SJUA$freq)
  
  # display total population by UA
  SFOakUA_totpop
  SJUA_totpop
  
  # display excessive delay by UA and by time period (in minutes)
  SFOakUA_carstrucks_AM_minutes <- sum(SFOakUA_RoadwayBusDataAM$delayXvolAM)
  SFOakUA_carstrucks_AM_minutes
  
  SFOakUA_buses_AM_minutes <-sum(SFOakUA_RoadwayBusDataAM$delayXbus_vol)
  SFOakUA_buses_AM_minutes
  
  SFOakUA_carstrucks_PM_minutes <-sum(SFOakUA_RoadwayBusDataPM$delayXvolPM)
  SFOakUA_carstrucks_PM_minutes
  
  SFOakUA_buses_PM_minutes <- sum(SFOakUA_RoadwayBusDataPM$delayXbus_vol)
  SFOakUA_buses_PM_minutes
  
  SJUA_carstrucks_AM_minutes <-sum(SJUA_RoadwayBusDataAM$delayXvolAM)
  SJUA_carstrucks_AM_minutes
  
  SJUA_buses_AM_minutes <- sum(SJUA_RoadwayBusDataAM$delayXbus_vol)
  SJUA_buses_AM_minutes
  
  SJUA_carstrucks_PM_minutes <-sum(SJUA_RoadwayBusDataPM$delayXvolPM)
  SJUA_carstrucks_PM_minutes
  
  SJUA_buses_PM_minutes <- sum(SJUA_RoadwayBusDataPM$delayXbus_vol)
  SJUA_buses_PM_minutes
  
  # total excessive delay *per person* in hours - car, bus, and trucks (per day)
  SFOakUA_AM <-sum(SFOakUA_RoadwayBusDataAM$delayXvolAM + SFOakUA_RoadwayBusDataAM$delayXbus_vol)/60/SFOakUA_totpop
  SFOakUA_PM <-sum(SFOakUA_RoadwayBusDataPM$delayXvolPM + SFOakUA_RoadwayBusDataPM$delayXbus_vol)/60/SFOakUA_totpop
  
  SJUA_AM <- sum(SJUA_RoadwayBusDataAM$delayXvolAM + SJUA_RoadwayBusDataAM$delayXbus_vol)/60/SJUA_totpop
  SJUA_PM <- sum(SJUA_RoadwayBusDataPM$delayXvolPM + SJUA_RoadwayBusDataPM$delayXbus_vol)/60/SJUA_totpop
  
  
  
  ##################################
  # Annualize the results
  ##################################
  # assume 260 days RM: update to 300
  # 52 weeks * 5 weekdays per week = 260 days RM: update to 300
  # although 52*7 = 364 and the maximum number of days in a year is 366, so the max number of weekday in a year can be 262
  
  # total excessive delay *per person* in hours - car, bus, and trucks - annualized
  PHED_SFOakUA <- (SFOakUA_AM + SFOakUA_PM)* 300
  PHED_SJUA <- (SJUA_AM + SJUA_PM)* 300
  
  PHED_SFOakUA
  PHED_SJUA
  
  PHED <- data.frame(PHED_SFOakUA, PHED_SJUA, PHED_annual)
  
  PHED_export = gather(PHED, index, value, PHED_SFOakUA:PHED_annual, factor_key = TRUE)%>%mutate(Year = year,
                                                                                                 modelrunID = gsub('M:/Application/Model One/RTP2021/', '', Scenario),
                                                                                                 Blueprint = bp)

}

phed_2015 = phed_calc("M:/Application/Model One/RTP2021/IncrementalProgress/2015_TM152_IPA_16", "2015", 2015)
phed_2050_np = phed_calc("M:/Application/Model One/RTP2021/Blueprint/2050_TM152_DBP_NoProject_08", "No Project", 2050)
phed_2050_bp = phed_calc("M:/Application/Model One/RTP2021/Blueprint/2050_TM152_DBP_PlusCrossing_08", "PlusCrossing", 2050)

phed_export = rbind(phed_2015, phed_2050_np, phed_2050_bp)

# adjust so that 2015 matches 2017 observed data
SFOakUA_adjust_factor = 31.3/phed_2015[1,2]
SJUA_adjust_factor = 27.5/phed_2015[2,2]
region_adjust_factor = mean(SFOakUA_adjust_factor, SJUA_adjust_factor)

phed_export_adjust = phed_export%>%mutate(adjust_factor = 0)
phed_export_adjust$adjust_factor[phed_export_adjust$index == "PHED_SFOakUA"] = SFOakUA_adjust_factor
phed_export_adjust$adjust_factor[phed_export_adjust$index == "PHED_SJUA"] = SJUA_adjust_factor
phed_export_adjust$adjust_factor[phed_export_adjust$index == "PHED_annual"] = region_adjust_factor


phed_export_adjust = phed_export_adjust%>%mutate(value_adjusted = value * adjust_factor)

# write out the results
# Annual Hours of Peak Hour Excessive Delay (PHED) Per Capita
write.csv(phed_export_adjust, "C:/Users/rmccoy/Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/Connected/phed.csv")


### calculate PM2.5 from vmt_vht_metrics.csv
# path for 2015 run
Path_2015 = "M:/Application/Model One/RTP2021/IncrementalProgress/2015_TM152_IPA_16/"

# path for 2050 No project run
Path_2050_NP = "M:/Application/Model One/RTP2021/Blueprint/2050_TM152_DBP_NoProject_08/"

# path for 2050 BP run
Path_2050_BP = "M:/Application/Model One/RTP2021/Blueprint/2050_TM152_DBP_PlusCrossing_08/"

PM25_calc = function(path, year, bp){
  df = read.csv(paste0(path, "OUTPUT/metrics/vmt_vht_metrics.csv"))%>%
    mutate(PM25_total_annual = 300*(Diesel_PM2.5+Gas_PM2.5+PM2.5_wear))%>%
    summarize(PM25_total_annual = sum(PM25_total_annual))%>%
    mutate(Year = year,
           Blueprint = bp,
           modelrunID = gsub("/OUTPUT.*$", "", gsub('M:/Application/Model One/RTP2021/', '', path)))%>%
    select(PM25_total_annual, Year, Blueprint, modelrunID)
}

pm25_15 = PM25_calc(Path_2015, 2015, "2015")
pm25_50_np = PM25_calc(Path_2050_NP, 2050, "No Project")
pm25_50_bp = PM25_calc(Path_2050_BP, 2050, "PlusCrossing")

pm25_export = rbind(pm25_15, pm25_50_np, pm25_50_bp)

# write csv
write.csv(pm25_export, "C:/Users/rmccoy/Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/Healthy/pm25_annual.csv")
