# ACS 2013-2017 create 2015 MAZ data for households by income.R
# Create "2015" MAZ data from ACS 2013-2017 
# SI

# Notes

"

1. ACS households by income data here are downloaded for the 2013-2017 5-year dataset. The end year can
   be updated by changing the *ACS_year* variable. 

2. 2010 decennial census household data at the block level were used to develop the share of households by
   maz to block group. That share was then applied to each household income category. Data were then totaled, 
   rounded, with the largest income column (i.e., column with the most hhs) adjusted so subtotals equal totals. 
   
"
# Import Libraries

suppressMessages(library(tidyverse))
library(tidycensus)

# Set up directories, import TAZ/census block equivalence, install census key, set ACS year

censuskey            <- readLines("M:/Data/Census/API/api-key.txt")
census_api_key(censuskey, install = TRUE, overwrite = TRUE)
baycounties          <- c("01","13","41","55","75","81","85","95","97")


ACS_year <- 2017
ACS_product="5"
state_code ="06"

# Set input path locations and working directory

USERPROFILE     <- gsub("\\\\","/", Sys.getenv("USERPROFILE"))
wd <- paste0(USERPROFILE,"/Box/Modeling and Surveys/Development/Travel Model Two Development/Model Inputs/Land Use")
setwd(wd)

# Bring in maz to blockgroup share file

maz_to_bg_in    <- file.path(USERPROFILE,"Documents","GitHub","travel-model-two","maz_taz","crosswalks","Census 2010 hhs maz share of blockgroups_ACS2017.csv")

maz_to_bg       <- read.csv(maz_to_bg_in,header = T)
              
# ACS household income variables
# Make ACS API call, rename variables, and select estimates to remove margin-of-error values
# Change "bg" class type for easy merging
# Note that "E" on the end of each variable is appended by tidycensus package to denote "estimate"

hh_income_vars <-   c("B19001_002E",        # Household income 0 to $10k 
                           "B19001_003E",		# Household income $10 to $15k
                           "B19001_004E",		# Household income $15 to $20k
                           "B19001_005E",		# Household income $20 to $25k
                           "B19001_006E",		# Household income $25 to $30k
                           "B19001_007E",		# Household income $30 to $35k
                           "B19001_008E",		# Household income $35 to $40k
                           "B19001_009E",		# Household income $40 to $45k
                           "B19001_010E",		# Household income $45 to $50k
                           "B19001_011E",		# Household income 50 to $60k
                           "B19001_012E",		# Household income 60 to $75k
                           "B19001_013E",		# Household income 75 to $100k
                           "B19001_014E",		# Household income $100 to $1$25k
                           "B19001_015E",		# Household income $1$25 to $150k
                           "B19001_016E",		# Household income $150 to $200k
                           "B19001_017E")		# Household income $200k+
  
acs_income <- get_acs(geography = "block group", variables = hh_income_vars,
          state = state_code, county=baycounties,
          year=ACS_year,
          output="wide",
          survey = "acs5",
          key = censuskey) %>% 
  select(GEOID,NAME,hhinc0_10E = B19001_002E,    # Income categories 
                    hhinc10_15E = B19001_003E,
                    hhinc15_20E = B19001_004E,
                    hhinc20_25E = B19001_005E,
                    hhinc25_30E = B19001_006E,
                    hhinc30_35E = B19001_007E,
                    hhinc35_40E = B19001_008E,
                    hhinc40_45E = B19001_009E,
                    hhinc45_50E = B19001_010E,
                    hhinc50_60E = B19001_011E,
                    hhinc60_75E = B19001_012E,
                    hhinc75_100E = B19001_013E,
                    hhinc100_125E = B19001_014E,
                    hhinc125_150E = B19001_015E,
                    hhinc150_200E = B19001_016E,
                    hhinc200pE = B19001_017E) %>% 
  mutate(blockgroup=as.numeric(GEOID))

# Income table - Guidelines for HH income values used from ACS
# Use CPI values from 2017 and 2010 to get inflation values right

"

CPI_current <- 274.92                             # CPI value for 2017
CPI_current <- 227.47                             # CPI value for 2010
CPI_ratio2010 <- CPI_current/CPI_reference = 1.208599 # 2017 CPI/2010 CPI

    2010 income breaks 2017 CPI equivalent   Nearest 2017 ACS breakpoint
    ------------------ -------------------   ---------------------------
    $30,000            $36,258               $35,000
    $60,000            $72,516               $75,000 
    $100,000           $120,860              $125,000
    ------------------ -------------------   ---------------------------

Household Income Category Equivalency, 2010$ and 2017$

          Year      Lower Bound     Upper Bound
          ----      ------------    -----------
HHINCQ1   2010      $-inf           $29,999
          2017      $-inf           $34,999
HHINCQ2   2010      $30,000         $59,999
          2017      $35,000         $74,999
HHINCQ3   2010      $60,000         $99,999
          2017      $75,000         $124,999
HHINCQ4   2010      $100,000        $inf
          2017      $125,000        $inf
          ----      -------------   -----------

"

# Join 2013-2017 ACS block group and maz to block group shares files
# Combine and collapse ACS categories to get appropriate TM2 categories
# Apply shares of 2013-2017 ACS variables from maz to block group file

workingdata <- left_join(maz_to_bg,acs_income, by="blockgroup") %>% 
  mutate(
  HHINCQ1=(hhinc0_10E+
             hhinc10_15E+
             hhinc15_20E+
             hhinc20_25E+
             hhinc25_30E+
             hhinc30_35E)*maz_share,
  HHINCQ2=(hhinc35_40E+
             hhinc40_45E+
             hhinc45_50E+
             hhinc50_60E+
             hhinc60_75E)*maz_share,
  HHINCQ3=(hhinc75_100E+                
             hhinc100_125E)*maz_share,
  HHINCQ4=(hhinc125_150E+
             hhinc150_200E+
             hhinc200pE)*maz_share)

# Summarize data by MAZ
# Now set up dataset to round and adjust column values such that subtotals match totals

hh_columns <- c("HHINCQ1","HHINCQ2","HHINCQ3","HHINCQ4")

final <- workingdata %>%
  group_by(maz) %>%
  summarize(  HHINCQ1=sum(HHINCQ1),
              HHINCQ2=sum(HHINCQ2),
              HHINCQ3=sum(HHINCQ3),
              HHINCQ4=sum(HHINCQ4)) %>%
  ungroup() %>% 
  mutate(hh_total=rowSums(select(.,all_of(hh_columns)))) %>%                       # Sum rows before rounding to get best total
  mutate_at(c(all_of(hh_columns),"hh_total"),~round(.,digits = 0)) %>%             # Round columns
  mutate(hh_subtotal=rowSums(select(.,all_of(hh_columns))),                        # Sum rows after rounding to ensure subtotals match totals
         max_hh = hh_columns[max.col(select(.,hh_columns), ties.method="first")],  # Find max column for adjustment
         hh_diff = hh_total - hh_subtotal)                                         # Calculate subtotal and total difference

for (col in hh_columns) {
  final[col] <- if_else(final$max_hh==col, 
                                     final[[col]] + final[["hh_diff"]],
                                     final[[col]])                                # Adjust largest column to resolve total/subtotal discrepancy
}

# Clean up file and export relevant variables
# Remove "0" MAZ

final <- final %>% 
  select(MAZ=maz,HHINCQ1,HHINCQ2,HHINCQ3,HHINCQ4) %>% 
  filter (MAZ !=0)

write.csv(final,"ACS 2013-2017 MAZ Households by Income for 2015.csv",row.names = F)
