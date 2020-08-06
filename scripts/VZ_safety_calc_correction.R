library(dplyr)
library(tidyr)
library(readxl)

# disable sci notation
options(scipen=999)

# path for 2015 run
Path_2015 = "M:/Application/Model One/RTP2021/IncrementalProgress/2015_TM152_IPA_16/"

# path for 2050 No project run
Path_2050_NP = "M:/Application/Model One/RTP2021/Blueprint/2050_TM152_DBP_NoProject_08/"

# path for 2050 BP run
Path_2050_BP = "M:/Application/Model One/RTP2021/Blueprint/2050_TM152_DBP_PlusCrossing_08/"

# assumptions
N_days_per_year = 300 # assume 300 days per year (outputs are for one day)
Obs_N_motorist_fatalities_15 = 301
Obs_N_ped_fatalities_15 = 127
Obs_N_bike_fatalities_15 = 27
Obs_N_motorist_injuries_15 = 1338
Obs_N_ped_injuries_15 = 379
Obs_N_bike_injuries_15 = 251
Obs_injuries_15 = 1968


collisionrates = read_excel("C:/Users/rmccoy/Box/Other Performance Projects/Research & Development/Safety Research/LookupTable/CollisionLookupFINAL.xlsx", sheet = "Lookup Table")%>%rename(
 serious_injury_rate = a, fatality_rate = k, ped_fatality = k_ped, motorist_fatality = k_motor, bike_fatality = k_bike)%>%select(
    at, ft, fatality_rate, serious_injury_rate,  motorist_fatality, ped_fatality, bike_fatality)  


# calculate for 2015
df_15 = read.csv(paste0(Path_2015,"OUTPUT/avgload5period.csv"))%>%mutate(ft_collision = ft, at_collision = at)

df_15$ft_collision[df_15$ft_collision==1] = 2 
df_15$ft_collision[df_15$ft_collision==8] = 2
df_15$ft_collision[df_15$ft_collision==6] = -1 # code says ignore ft 6 (dummy links) and lanes <= 0 by replacing the ft with -1, which won't match with anything
df_15$ft_collision[df_15$lanes<=0] = -1
df_15$ft_collision[df_15$ft_collision>4] = 4

df_15$at_collision[df_15$at_collision<3] = 3 
df_15$at_collision[df_15$at_collision>4] = 4 

df_15 = df_15%>%rename(at_original = at, ft_original = ft, at = at_collision, ft = ft_collision)

df_15_2 = left_join(df_15, collisionrates, by = c("ft", "at"))%>%mutate(annual_VMT = N_days_per_year * (volEA_tot+volAM_tot+volMD_tot+volPM_tot+volEV_tot)*distance,
                                                                        Avg_speed = (cspdEA + cspdAM+ cspdMD+ cspdPM+ cspdEV)/5,
                                                                        N_motorist_fatalities = annual_VMT/1000000 * motorist_fatality,
                                                                        N_ped_fatalities =  annual_VMT/1000000 * ped_fatality,
                                                                        N_bike_fatalities = annual_VMT/1000000 * bike_fatality,
                                                                        N_total_fatalities = N_motorist_fatalities + N_ped_fatalities + N_bike_fatalities,
                                                                        N_total_injuries =  annual_VMT/1000000 * serious_injury_rate)

df_15_3 = df_15_2%>%summarize(N_motorist_fatalities = sum(N_motorist_fatalities, na.rm=TRUE),
                              N_bike_fatalities = sum(N_bike_fatalities, na.rm=TRUE),
                              N_ped_fatalities = sum(N_ped_fatalities, na.rm=TRUE),
                              N_fatalities = sum(N_total_fatalities, na.rm=TRUE),
                              N_injuries = sum(N_total_injuries, na.rm=TRUE),
                              annual_VMT = sum(annual_VMT, na.rm=TRUE))

df_15_4 = df_15_3%>%mutate(N_motorist_fatalities_corrected = N_motorist_fatalities*(Obs_N_motorist_fatalities_15/df_15_3$N_motorist_fatalities),
         N_ped_fatalities_corrected = N_ped_fatalities*(Obs_N_ped_fatalities_15/df_15_3$N_ped_fatalities),
         N_bike_fatalities_corrected = N_bike_fatalities*(Obs_N_bike_fatalities_15/df_15_3$N_bike_fatalities),
         N_total_fatalities_corrected = N_motorist_fatalities_corrected + N_ped_fatalities_corrected + N_bike_fatalities_corrected,
         N_injuries_corrected = N_injuries*(Obs_injuries_15/df_15_3$N_injuries),
         N_motorist_fatalities_corrected_per_100M_VMT = N_motorist_fatalities_corrected/(annual_VMT/100000000),
         N_ped_fatalities_corrected_per_100M_VMT = N_ped_fatalities_corrected/(annual_VMT/100000000),
         N_bike_fatalities_corrected_per_100M_VMT = N_bike_fatalities_corrected/(annual_VMT/100000000),
         N_total_fatalities_corrected_per_100M_VMT = N_total_fatalities_corrected/(annual_VMT/100000000),
         N_injuries_corrected_per_100M_VMT = N_injuries_corrected/(annual_VMT/100000000))%>%
  select(-N_motorist_fatalities, -N_bike_fatalities, -N_ped_fatalities, -N_fatalities, -N_injuries)

df_15_5 = gather(df_15_4, index, value, annual_VMT:N_injuries_corrected_per_100M_VMT, factor_key = TRUE)%>%mutate(Year = 2015,
                                                                                                                          modelrunID = gsub('M:/Application/Model One/RTP2021/', '', Path_2015))

# read in no project
df_np = read.csv(paste0(Path_2050_NP,"OUTPUT/avgload5period.csv"))%>%mutate(
  Avg_speed_NP = (cspdEA + cspdAM+ cspdMD+ cspdPM+ cspdEV)/5)%>%select(
  a,b,Avg_speed_NP)
  
# read in project
# collision lookup table only has a few at and ft. at and ft not in the lookup table need to be mapped to their proxy (see OLD code staring at line 193) https://github.com/BayAreaMetro/travel-model-one/blob/master/utilities/RTP/metrics/hwynet.py
# new matches in the collisionlookupfinal excel under notes
df = read.csv(paste0(Path_2050_BP,"OUTPUT/avgload5period.csv"))%>%mutate(ft_collision = ft, at_collision = at)

df$ft_collision[df$ft_collision==1] = 2 
df$ft_collision[df$ft_collision==8] = 2
df$ft_collision[df$ft_collision==6] = -1 # code says ignore ft 6 (dummy links) and lanes <= 0 by replacing the ft with -1, which won't match with anything
df$ft_collision[df$lanes<=0] = -1
df$ft_collision[df$ft_collision>4] = 4

df$at_collision[df$at_collision<3] = 3 
df$at_collision[df$at_collision>4] = 4 


df = df%>%rename(at_original = at, ft_original = ft, at = at_collision, ft = ft_collision)

# calculate fatalities and injuries as they would be calculated without the speed reduction
df2 = left_join(df, collisionrates, by = c("ft", "at"))%>%mutate(annual_VMT = N_days_per_year *(volEA_tot+volAM_tot+volMD_tot+volPM_tot+volEV_tot)*distance,
                                                             Avg_speed = (cspdEA + cspdAM+ cspdMD+ cspdPM+ cspdEV)/5,
                                                             N_motorist_fatalities = annual_VMT/1000000 * motorist_fatality,
                                                             N_ped_fatalities = annual_VMT/1000000 * ped_fatality,
                                                             N_bike_fatalities = annual_VMT/1000000 * bike_fatality,
                                                             N_total_fatalities = N_motorist_fatalities + N_ped_fatalities + N_bike_fatalities,
                                                             N_total_injuries = annual_VMT/1000000 * serious_injury_rate)

# join average speed on each link in no project
df3 = left_join(df2, df_np, by=c("a", "b"))%>%select(a,, b, ft, at, annual_VMT, N_motorist_fatalities, N_ped_fatalities, N_bike_fatalities, 
                                  N_total_injuries, Avg_speed, Avg_speed_NP)


# add attributes for fatality reduction exponent based on ft
# exponents and methodology sourced from here: https://www.toi.no/getfile.php?mmfileid=13206 (table S1)
# methodology cited in this FHWA resource: https://www.fhwa.dot.gov/publications/research/safety/17098/003.cfm
df3$fatality_exponent = 0
df3$fatality_exponent[df3$ft%in%c(1,2,3,5,6,8)] = 4.6
df3$fatality_exponent[df3$ft%in%c(4,7)] = 3

df3$injury_exponent = 0
df3$injury_exponent[df3$ft%in%c(1,2,3,5,6,8)] = 3.5
df3$injury_exponent[df3$ft%in%c(4,7)] = 2

# adjust fatalities based on exponents and speed
df4 = df3%>%mutate(N_motorist_fatalities_after = ifelse(N_motorist_fatalities == 0,0,N_motorist_fatalities*(Avg_speed/Avg_speed_NP)^fatality_exponent),
                   N_ped_fatalities_after = ifelse(N_ped_fatalities == 0,0,N_ped_fatalities*(Avg_speed/Avg_speed_NP)^fatality_exponent),
                   N_bike_fatalities_after = ifelse(N_bike_fatalities == 0,0,N_bike_fatalities*(Avg_speed/Avg_speed_NP)^fatality_exponent),
                   N_fatalities = N_motorist_fatalities+ N_ped_fatalities+ N_bike_fatalities,
                   N_fatalities_after = N_motorist_fatalities_after+ N_ped_fatalities_after+ N_bike_fatalities_after,
                   N_injuries = N_total_injuries,
                   N_injuries_after = ifelse(N_injuries == 0,0,N_injuries*(Avg_speed/Avg_speed_NP)^injury_exponent))

# summarize
df5 = df4%>%summarize(N_motorist_fatalities = sum(N_motorist_fatalities, na.rm=TRUE),
                      N_motorist_fatalities_after = sum(N_motorist_fatalities_after, na.rm=TRUE),
                      N_bike_fatalities = sum(N_bike_fatalities, na.rm=TRUE),
                      N_bike_fatalities_after = sum(N_bike_fatalities_after, na.rm=TRUE),
                      N_ped_fatalities = sum(N_ped_fatalities, na.rm=TRUE),
                      N_ped_fatalities_after = sum(N_ped_fatalities_after, na.rm=TRUE),
                      N_fatalities = sum(N_fatalities, na.rm=TRUE),
                      N_fatalities_after = sum(N_fatalities_after, na.rm=TRUE),
                      N_injuries = sum(N_injuries, na.rm=TRUE),
                      N_injuries_after = sum(N_injuries_after, na.rm=TRUE),
                      annual_VMT = sum(annual_VMT, na.rm=TRUE))%>%select(-N_motorist_fatalities, -N_bike_fatalities, -N_ped_fatalities, -N_fatalities, -N_injuries)%>%rename(
                        N_motorist_fatalities = N_motorist_fatalities_after, N_bike_fatalities = N_bike_fatalities_after,  N_ped_fatalities = N_ped_fatalities_after, 
                        N_fatalities = N_fatalities_after, N_injuries = N_injuries_after
                      )

df6 = df5 %>%
  mutate(N_motorist_fatalities_corrected = N_motorist_fatalities*(Obs_N_motorist_fatalities_15/df_15_3$N_motorist_fatalities),
         N_ped_fatalities_corrected = N_ped_fatalities*(Obs_N_ped_fatalities_15/df_15_3$N_ped_fatalities),
         N_bike_fatalities_corrected = N_bike_fatalities*(Obs_N_bike_fatalities_15/df_15_3$N_bike_fatalities),
         N_total_fatalities_corrected = N_motorist_fatalities_corrected + N_ped_fatalities_corrected + N_bike_fatalities_corrected,
         N_injuries_corrected = N_injuries*(Obs_injuries_15/df_15_3$N_injuries),
         N_motorist_fatalities_corrected_per_100M_VMT = N_motorist_fatalities_corrected/(annual_VMT/100000000),
         N_ped_fatalities_corrected_per_100M_VMT = N_ped_fatalities_corrected/(annual_VMT/100000000),
         N_bike_fatalities_corrected_per_100M_VMT = N_bike_fatalities_corrected/(annual_VMT/100000000),
         N_total_fatalities_corrected_per_100M_VMT = N_total_fatalities_corrected/(annual_VMT/100000000),
         N_injuries_corrected_per_100M_VMT = N_injuries_corrected/(annual_VMT/100000000))%>%
  select(-N_motorist_fatalities, -N_bike_fatalities, -N_ped_fatalities, -N_fatalities, -N_injuries)

df7 = gather(df6, index, value, annual_VMT:N_injuries_corrected_per_100M_VMT, factor_key = TRUE)%>%mutate(Year = 2050,
  modelrunID = gsub('M:/Application/Model One/RTP2021/Blueprint', '', Path_2050_BP))

# calculate for 2050 no project
df_50np = read.csv(paste0(Path_2050_NP,"OUTPUT/avgload5period.csv"))%>%mutate(ft_collision = ft, at_collision = at)

df_50np$ft_collision[df_50np$ft_collision==1] = 2 
df_50np$ft_collision[df_50np$ft_collision==8] = 2
df_50np$ft_collision[df_50np$ft_collision==6] = -1 # code says ignore ft 6 (dummy links) and lanes <= 0 by replacing the ft with -1, which won't match with anything
df_50np$ft_collision[df_50np$lanes<=0] = -1
df_50np$ft_collision[df_50np$ft_collision>4] = 4

df_50np$at_collision[df_50np$at_collision<3] = 3 
df_50np$at_collision[df_50np$at_collision>4] = 4 

df_50np = df_50np%>%rename(at_original = at, ft_original = ft, at = at_collision, ft = ft_collision)

df_50np_2 = left_join(df_50np, collisionrates, by = c("ft", "at"))%>%mutate(annual_VMT = N_days_per_year *(volEA_tot+volAM_tot+volMD_tot+volPM_tot+volEV_tot)*distance,
                                                             Avg_speed = (cspdEA + cspdAM+ cspdMD+ cspdPM+ cspdEV)/5,
                                                             N_motorist_fatalities = annual_VMT/1000000 * motorist_fatality,
                                                             N_ped_fatalities = annual_VMT/1000000 * ped_fatality,
                                                             N_bike_fatalities =  annual_VMT/1000000 * bike_fatality,
                                                             N_total_fatalities = N_motorist_fatalities + N_ped_fatalities + N_bike_fatalities,
                                                             N_total_injuries = annual_VMT/1000000 * serious_injury_rate)

df_50np_3 = df_50np_2%>%summarize(N_motorist_fatalities = sum(N_motorist_fatalities, na.rm=TRUE),
                      N_bike_fatalities = sum(N_bike_fatalities, na.rm=TRUE),
                      N_ped_fatalities = sum(N_ped_fatalities, na.rm=TRUE),
                      N_fatalities = sum(N_total_fatalities, na.rm=TRUE),
                      N_injuries = sum(N_total_injuries, na.rm=TRUE),
                      annual_VMT = sum(annual_VMT, na.rm=TRUE))

df_50np_4 = df_50np_3%>%
  mutate(N_motorist_fatalities_corrected = N_motorist_fatalities*(Obs_N_motorist_fatalities_15/df_15_3$N_motorist_fatalities),
         N_ped_fatalities_corrected = N_ped_fatalities*(Obs_N_ped_fatalities_15/df_15_3$N_ped_fatalities),
         N_bike_fatalities_corrected = N_bike_fatalities*(Obs_N_bike_fatalities_15/df_15_3$N_bike_fatalities),
         N_total_fatalities_corrected = N_motorist_fatalities_corrected + N_ped_fatalities_corrected + N_bike_fatalities_corrected,
         N_injuries_corrected = N_injuries*(Obs_injuries_15/df_15_3$N_injuries),
         N_motorist_fatalities_corrected_per_100M_VMT = N_motorist_fatalities_corrected/(annual_VMT/100000000),
         N_ped_fatalities_corrected_per_100M_VMT = N_ped_fatalities_corrected/(annual_VMT/100000000),
         N_bike_fatalities_corrected_per_100M_VMT = N_bike_fatalities_corrected/(annual_VMT/100000000),
         N_total_fatalities_corrected_per_100M_VMT = N_total_fatalities_corrected/(annual_VMT/100000000),
         N_injuries_corrected_per_100M_VMT = N_injuries_corrected/(annual_VMT/100000000))%>%
  select(-N_motorist_fatalities, -N_bike_fatalities, -N_ped_fatalities, -N_fatalities, -N_injuries)

df_50np_5 = gather(df_50np_4, index, value, annual_VMT:N_injuries_corrected_per_100M_VMT, factor_key = TRUE)%>%mutate(Year = 2050,
                                                                                                    modelrunID = gsub('M:/Application/Model One/RTP2021/Blueprint', '', Path_2050_NP))


export = rbind(df_15_5,df7, df_50np_5)

# write csv
write.csv(export,"C:/Users/rmccoy/Box/Horizon and Plan Bay Area 2050/Equity and Performance/7_Analysis/Metrics/Healthy/fatalities_injuries_export.csv")

