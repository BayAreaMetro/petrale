# Summarize_BusinessData_by_MAZ_Industry.R
# Sum ESRI Business Analyst data to MAZ level for several employment taxonomy schemes
# Input data year should be set - e.g., Sys.setenv(BIZDATA_YEAR="2020")

suppressMessages(library(tidyverse))
library(sf)

# Data locations
BIZDATA_DIR             <- "M:/Data/BusinessData"
BIZDATA_YEAR            <- Sys.getenv("BIZDATA_YEAR")
stopifnot(BIZDATA_YEAR %in% c("2015", "2017", "2019", "2020") )
bizdata_location        <- file.path(BIZDATA_DIR, paste0("Businesses_",BIZDATA_YEAR,"_BayArea_wcountyTAZ.csv"))      

# MAZ geography location
f_tm2_maz_shp_path      <- "M:/Data/GIS layers/TM2_maz_taz_v2.2/mazs_TM2_v2_2.shp"

# Bring in regional totals, using 
SCENARIO_NUM            <- 24 # final blueprint
reg_total_location      <- paste0("X:/regional_forecast/to_baus/s",SCENARIO_NUM,"/employment_controls_s",SCENARIO_NUM,".csv")
regional_totals         <- read_csv(reg_total_location) %>%
  mutate(TOTEMP=AGREMPN + MWTEMPN + RETEMPN + FPSEMPN + HEREMPN + OTHEMPN)

regional_2015 <- regional_totals %>% filter(year==2015) %>% .$TOTEMP
regional_2020 <- regional_totals %>% filter(year==2020) %>% .$TOTEMP
regional_2017 <- regional_2015
regional_2019 <- regional_2020

# Bring in industry crosswalk
userprofile          <- gsub("\\\\","/", Sys.getenv("USERPROFILE"))
github               <- file.path(userprofile,"Documents","GitHub")
crosswalk_dir        <- file.path(github,"petrale","economy","2020_naics_recode.csv")
crosswalk            <- read.csv(crosswalk_dir)

# output files
output_location           <- file.path(github,"petrale","basemap","imputation_and_siting","employment","2015")
output_maz_industry_file  <- paste0("BusinessData_",BIZDATA_YEAR,"_MAZ_industry.csv")

# Bring in business data and MAZ shapefile and match MAZ geography to file
# Create a version of MAZ shapefile without geometry for later index matching
# Start by matching employment within MAZ shapes, then (for poor matches, due to MAZ delineation) select closest MAZ 
# Concatenate "good" and "bad" datasets, remove geography field - leaving a dataframe

bizdata <- read_csv(bizdata_location) %>% mutate(naicssix=as.integer(substr(NAICS,0,6)))
bizdata <- st_as_sf(bizdata, coords = c("POINT_X", "POINT_Y"), crs = 4326)
bizdata <- st_transform(bizdata, crs = 2230)

tm2_maz_shp <- st_read(f_tm2_maz_shp_path) %>%
  select(TM2_MAZ = maz)

tm2_maz <- tm2_maz_shp
st_geometry(tm2_maz)<-NULL
   
tm2_maz_shp <- st_transform(tm2_maz_shp, 2230)

bizdata_maz <- bizdata %>%
  st_join(tm2_maz_shp, join = st_within)

bizdata_maz_good <- bizdata_maz %>% filter(!is.na(TM2_MAZ))

bizdata_maz_bad <- bizdata_maz %>% filter(is.na(TM2_MAZ)) 

bizdata_maz_bad <- bizdata_maz_bad %>% 
  mutate(TM2_MAZ_index=st_nearest_feature(bizdata_maz_bad,tm2_maz_shp))

bizdata_maz_bad <- bizdata_maz_bad %>% 
  mutate(TM2_MAZ=tm2_maz[.$TM2_MAZ_index,"TM2_MAZ"]) %>% 
  select(-TM2_MAZ_index)

bizdata_maz <- rbind(bizdata_maz_good,bizdata_maz_bad)

st_geometry(bizdata_maz) <- NULL

# Join employment data to crosswalk and create codes for missing crosswalk cells
# The crosswalk is current for 2020 (so no missing crosswalk values should appear now), but will need updating for later years
# Missing crosswalk cells are indicated by "-999" for numeric taxonomies and "unclassified" for text-based
# Rename category from "sixcat" to "abag6" for later summaries

bizdata_joined <- left_join(bizdata_maz,crosswalk,by="naicssix") %>% 
  mutate(steelhead   =if_else(is.na(steelhead),"Unclassified",steelhead),
         naics2      =if_else(is.na(naics2),-999L,naics2),
         remi70      =if_else(is.na(remi70),-999L,remi70),
         US2detailed =if_else(is.na(US2detailed),"Unclassified",US2detailed),
         sixcat      =if_else(is.na(sixcat),"Unclassified",sixcat)) %>% 
  rename(abag6=sixcat)

# Sum total employment for later joining

bizdata_maz_total <- bizdata_joined %>% 
  group_by(TM2_MAZ)%>% 
  summarize(Total=sum(EMPNUM)) 
                           
# Summarize by steelhead categories, create dummy maz file to rbind for full maz coverage, spread to matrix format, delete dummy variable

bizdata_maz_steelhead <- bizdata_joined %>% 
  group_by(TM2_MAZ,steelhead) %>% 
  summarize(employment=sum(EMPNUM)) 

tm2_maz_dummy <- tm2_maz_shp %>% 
  mutate(steelhead="dummy",employment=-999)
st_geometry(tm2_maz_dummy) <- NULL                                        

bizdata_maz_steelhead <- rbind(bizdata_maz_steelhead,tm2_maz_dummy) %>%
  spread(steelhead,employment,fill=0) 

bizdata_maz_steelhead <- bizdata_maz_steelhead %>% 
  select(-dummy)

# Now do the same summary for naics2 categories, adding "emp_sec" to the front of category names

bizdata_maz_naics2 <- bizdata_joined %>% 
  group_by(TM2_MAZ,naics2) %>% 
  summarize(employment=sum(EMPNUM)) %>% 
  mutate(naics2=paste0("emp_sec",naics2))

tm2_maz_dummy <- tm2_maz_dummy %>% 
  rename(naics2=steelhead) 

bizdata_maz_naics2 <- rbind(bizdata_maz_naics2,tm2_maz_dummy) %>%
  spread(naics2,employment,fill=0) 

bizdata_maz_naics2 <- bizdata_maz_naics2 %>% 
  select(-dummy)

# Now the summary for ABAG6, appending Total employment (changing NA values to zero) for final dataset output

bizdata_maz_abag6 <- bizdata_joined %>% 
  group_by(TM2_MAZ,abag6) %>% 
  summarize(employment=sum(EMPNUM)) 

tm2_maz_dummy <- tm2_maz_dummy %>% 
  rename(abag6=naics2) 

bizdata_maz_abag6 <- rbind(bizdata_maz_abag6,tm2_maz_dummy) %>%
  spread(abag6,employment,fill=0) %>% 
  left_join(.,bizdata_maz_total,by="TM2_MAZ") 

bizdata_maz_abag6 <- bizdata_maz_abag6 %>% 
  mutate(Total=if_else(is.na(Total),0,Total)) %>% 
  select(-dummy)

# Now join all three into a single dataframe

bizdata_maz_all <- left_join(bizdata_maz_steelhead,bizdata_maz_naics2,by="TM2_MAZ") %>% 
  left_join(.,bizdata_maz_abag6, by="TM2_MAZ")

# Output file

write.csv(bizdata_maz_all, file.path(output_location,output_maz_industry_file), row.names = FALSE, quote = T)



