# ACS PUMS 2014-2018 Jobs in the Bay Area, income & NAICS

suppressMessages(library(tidyverse))
wd <- "C:/Users/jhalpern/Documents/R/PBA2050/Outputs/Jobs-HousingFit"  # work directory
setwd(wd)

# Input person census files

PERSON_BA_RDATA = "M:/Data/Census/PUMS/PUMS 2014-18/pbayarea1418.Rdata"
HH__BA_RDATA     = "M:/Data/Census/PUMS/PUMS 2014-18/hbayarea1418.Rdata"
PERSON_CA_RDATA = "M:/Data/Census/PUMS/PUMS 2014-18/pcalif1418.Rdata"
HH__CA_RDATA     = "M:/Data/Census/PUMS/PUMS 2014-18/hcalif1418.Rdata"

load (PERSON_BA_RDATA)
load(HH__BA_RDATA) 
load (PERSON_CA_RDATA)
load(HH__CA_RDATA)

baypowpuma = c(100,1300,4100,5500,7500,8100,8500,9500,9700)

household <- hcalif1418 %>%  
  select(SERIALNO,HINCP,ADJINC) %>% 
  mutate(SERIALNO = as.character(SERIALNO))             # Imports as factor; fixing this

#Create short NAICS (2 number)
pums <- pcalif1418 %>% 
  filter(POWPUMA %in% baypowpuma)  %>%             #Filter responses with Place of Work in the Bay Area
  mutate(NAICSP_short = substr(NAICSP,0,2))

#See what distinct values look like
countingPOWPUMA <- pums %>% count(POWPUMA)
counting <- pums %>% count(NAICSP_short)
sapply(pums,NAICSP)  #NAICSP is a factor

#Many values are blank, see if true for NAICSP in general
sum(pums$NAICSP != "") #189639 not blank. Using PUMA instead of POWPUMA result 232844
sum(pums$NAICSP == "") #0 blank. Using PUMA instead of POWPUMA result 143213 (matches NAICSP_short)

sum(pums$WAGP!= "") #189639 not blank. Using PUMA instead of POWPUMA result 232844
sum(pums$WAGP == "") #0 blank. Using PUMA instead of POWPUMA result 143213 (matches NAICSP_short)


#Overall summary file
Sum_PUMS <- pums %>%
  mutate(SERIALNO = as.character(SERIALNO)) %>%         # Imports as factor; fixing this
  select(-ADJINC) %>%                                   # Remove this variable and use joined version
  left_join(.,household,by="SERIALNO") %>% 
  mutate(
    adjustedinc=HINCP*(ADJINC/1000000),
    incomeLW=case_when(
      adjustedinc <40000                         ~"1_less than 40k",
      adjustedinc >=40000 & adjustedinc <50000   ~"2_40k to 49,999",
      adjustedinc >=50000 & adjustedinc <80000   ~"3_50k to 79,999",
      adjustedinc >=80000 & adjustedinc <100000  ~"4_80k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"5_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"6_150k to 249,999",
      adjustedinc >= 250000                       ~"7_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    adjustedwage=WAGP*(ADJINC/1000000),
    earningsLW=case_when(
      adjustedwage <30000                         ~"1_less than 30k",
      adjustedwage >=30000 & adjustedwage <40000   ~"2_30k to 39,999",
      adjustedwage >=40000 & adjustedwage <50000   ~"3_40k to 49,999",
      adjustedwage >=50000 & adjustedwage <80000   ~"4_50k to 79,999",
      adjustedwage >=80000 & adjustedwage <100000  ~"5_80k to 99,999",
      adjustedwage >=100000 & adjustedwage <150000 ~"6_100k to 149,999",
      adjustedwage >=150000 & adjustedwage <250000 ~"7_150k to 249,999",
      adjustedwage >= 250000                       ~"8_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    County_Res=case_when(
      PUMA/100==1 ~"Alameda",PUMA/100==13 ~"Contra Costa",PUMA/100==41 ~"Marin",PUMA/100==55 ~"Napa",PUMA/100==75 ~"San Francisco",
      PUMA/100==81 ~"San Mateo",PUMA/100==85 ~"Santa Clara",PUMA/100==95 ~"Solano",PUMA/100==97 ~"Sonoma",TRUE  ~"Outside Bay Area"),
    County_Emp=case_when(
      POWPUMA/100==1 ~"Alameda",POWPUMA/100==13 ~"Contra Costa",POWPUMA/100==41 ~"Marin",POWPUMA/100==55 ~"Napa",POWPUMA/100==75 ~"San Francisco",
      POWPUMA/100==81 ~"San Mateo",POWPUMA/100==85 ~"Santa Clara",POWPUMA/100==95 ~"Solano",POWPUMA/100==97 ~"Sonoma",TRUE  ~"Outside Bay Area"),
    Industry=case_when(
      NAICSP_short==23|NAICSP_short==51|NAICSP_short==92|NAICSP_short==99 ~"OTHEMPN",NAICSP_short>=61 & NAICSP_short<=81 ~"HEREMPN",NAICSP_short>=52 & NAICSP_short<=56 ~"FPSEMPN",
      NAICSP_short==22|NAICSP_short>=31 & NAICSP_short<=33|NAICSP_short==42|NAICSP_short==48|NAICSP_short==49 ~"MWTEMPN",NAICSP_short==11| NAICSP_short==21  ~"AGREMPN",NAICSP_short==44| NAICSP_short==45 ~"RETEMPN",TRUE  ~"NA")
    
  )%>% 
  select(SERIALNO,SPORDER,Industry,PUMA,County_Res,POWPUMA,County_Emp,PWGTP,AGEP,JWTR,HINCP,adjustedinc,incomeLW,WAGP,adjustedwage,earningsLW,RELP) #if using calif instead of bayarea there is no PUMA_Name

income_Sum_Emp <- Sum_PUMS %>%                    #Summary of income bucket based on county employed in
  group_by(County_Emp,Industry,incomeLW) %>% 
  summarize(total=sum(PWGTP)) %>%                 #Summarize by person weights
  spread (., incomeLW, total, fill=0)

earning_Sum_Emp <- Sum_PUMS %>%                    #Summary of earnings bucket based on county employed in
  group_by(County_Emp,Industry,earningsLW) %>% 
  summarize(total=sum(PWGTP)) %>%                 #Summarize by person weights
  spread (., earningsLW, total, fill=0)

income_Sum_Res <- Sum_PUMS %>%                    #Summary of income bucket based on county residing in
  group_by(County_Res,Industry,incomeLW) %>% 
  summarize(total=sum(PWGTP)) %>% 
  spread (., incomeLW, total, fill=0)

write.csv(Sum_PUMS, "Summary PUMS2014-2018 Income Industry Age Race.csv", row.names = FALSE, quote = T)
write.csv(Sum_PUMS, "Summary PUMS2014-2018 Earnings Income Industry Age Race2.csv", row.names = FALSE, quote = T)
write.csv(income_Sum_Emp, "PUMS2014-2018 Income by Industry and Emp County.csv", row.names = FALSE, quote = T)
write.csv(earning_Sum_Emp, "PUMS2014-2018 Earnings by Industry and Emp County.csv", row.names = FALSE, quote = T)
write.csv(income_Sum_Res, "PUMS2014-2018 Income by Industry and Res County.csv", row.names = FALSE, quote = T)

#I don't know why the numbers are so different

# Extract retail employees and recode relevant variables, join with household file for income values

RETEMPN <- pums %>%
  mutate(SERIALNO = as.character(SERIALNO)) %>%         # Imports as factor; fixing this
  filter(NAICSP_short==44| NAICSP_short==45) %>%                                   # Extract only retail
  select(-ADJINC) %>%                                   # Remove this variable and use joined version
  left_join(.,household,by="SERIALNO") %>% 
  mutate(
    adjustedinc=HINCP*(ADJINC/1000000),
    incomerc=case_when(
      adjustedinc <25000                         ~"1_less to 25k",
      adjustedinc >=25000 & adjustedinc <35000   ~"2_25k to 34,999",
      adjustedinc >=35000 & adjustedinc <50000   ~"3_35k to 49,999",
      adjustedinc >=50000 & adjustedinc <75000   ~"4_50k to 74,999",
      adjustedinc >=75000 & adjustedinc <100000  ~"5_75k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"6_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"7_150k to 249,999",
      adjustedinc >= 250000                       ~"8_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    incomeLW=case_when(
      adjustedinc <40000                         ~"1_less than 40k",
      adjustedinc >=40000 & adjustedinc <50000   ~"2_40k to 49,999",
      adjustedinc >=50000 & adjustedinc <80000   ~"3_50k to 79,999",
      adjustedinc >=80000 & adjustedinc <100000  ~"4_80k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"5_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"6_150k to 249,999",
      adjustedinc >= 250000                       ~"7_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    racerc=case_when(
      HISP>1               ~"5_Hispanic",
      HISP==1 & RAC1P==1   ~"1_White",
      HISP==1 & RAC1P==2   ~"2_Black",
      HISP==1 & RAC1P==3   ~"4_Other",
      HISP==1 & RAC1P==4   ~"4_Other",
      HISP==1 & RAC1P==5   ~"4_Other",
      HISP==1 & RAC1P==6   ~"3_Asian",
      HISP==1 & RAC1P>=7   ~"4_Other",
      TRUE                 ~"Uncoded"),
    agerc=case_when(
      AGEP<20              ~"1_less_than_20",
      AGEP>=20 & AGEP<30   ~"2_between 20 and 30",
      AGEP>=30 & AGEP<40   ~"3_between 30 and 40",
      AGEP>=40 & AGEP<50   ~"4_between 40 and 50",
      AGEP>=50 & AGEP<60   ~"5_between 50 and 60",
      AGEP>=60 & AGEP<70   ~"6_between 60 and 70",
      AGEP>=70             ~"7_70+",
      TRUE                 ~"Uncoded"),
    County_Res=case_when(
      floor(PUMA/100)==1 ~"Alameda",floor(PUMA/100)==13 ~"Contra Costa",floor(PUMA/100)==41 ~"Marin",floor(PUMA/100)==55 ~"Napa",floor(PUMA/100)==75 ~"San Francisco",
      floor(PUMA/100)==81 ~"San Mateo",floor(PUMA/100)==85 ~"Santa Clara",floor(PUMA/100)==95 ~"Solano",floor(PUMA/100)==97 ~"Sonoma",TRUE  ~"Outside Bay Area"),
    County_Emp=case_when(
      floor(POWPUMA/100)==1 ~"Alameda",floor(POWPUMA/100)==13 ~"Contra Costa",floor(POWPUMA/100)==41 ~"Marin",floor(POWPUMA/100)==55 ~"Napa",floor(POWPUMA/100)==75 ~"San Francisco",
      floor(POWPUMA/100)==81 ~"San Mateo",floor(POWPUMA/100)==85 ~"Santa Clara",floor(POWPUMA/100)==95 ~"Solano",floor(POWPUMA/100)==97 ~"Sonoma",TRUE  ~"Error")
  )%>% 
  select(SERIALNO,SPORDER,PUMA,County_Res,POWPUMA,County_Emp,PWGTP,AGEP,JWTR,HINCP,adjustedinc,agerc,incomerc,incomeLW,racerc,RELP) #if using calif instead of bayarea there is no PUMA_Name

#Check
CountyE_check <- tapply(RETEMPN$PWGTP, RETEMPN$County_Emp, FUN=sum)
print(CountyE_check)
CountyR_check <- RETEMPN %>% count(County_Res)

# Summarize income

incomesum <- RETEMPN %>% 
  group_by(County_Res,incomeLW) %>% 
  summarize(total=sum(PWGTP)) %>% 
  spread (., incomeLW, total, fill=0)

# Summarize race

racesum <- RETEMPN %>% 
  group_by(County_Res,racerc) %>% 
  summarize(total=sum(PWGTP)) %>% 
  spread (., racerc, total, fill=0)

# Summarize age

agesum <- RETEMPN %>% 
  group_by(County_Res,agerc) %>% 
  summarize(total=sum(PWGTP)) %>% 
  spread (., agerc, total, fill=0)

write.csv(RETEMPN, "PUMS2014-2018 RETEMPN Summary v2.csv", row.names = FALSE, quote = T)
write.csv(incomesum, "PUMS2014-2018 RETEMPN by Income v2.csv", row.names = FALSE, quote = T)
write.csv(racesum, "PUMS2014-2018 RETEMPN by Race v2.csv", row.names = FALSE, quote = T)
write.csv(agesum, "PUMS2014-2018 RETEMPN by Age v2.csv ", row.names = FALSE, quote = T)

#Now repeat for all categories
AGREMPN <- pums %>%
  mutate(SERIALNO = as.character(SERIALNO)) %>%         # Imports as factor; fixing this
  filter(NAICSP_short==11| NAICSP_short==21) %>%                                   # Extract only retail
  select(-ADJINC) %>%                                   # Remove this variable and use joined version
  left_join(.,household,by="SERIALNO") %>% 
  mutate(
    adjustedinc=HINCP*(ADJINC/1000000),
    incomerc=case_when(
      adjustedinc <25000                         ~"1_less to 25k",
      adjustedinc >=25000 & adjustedinc <35000   ~"2_25k to 34,999",
      adjustedinc >=35000 & adjustedinc <50000   ~"3_35k to 49,999",
      adjustedinc >=50000 & adjustedinc <75000   ~"4_50k to 74,999",
      adjustedinc >=75000 & adjustedinc <100000  ~"5_75k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"6_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"7_150k to 249,999",
      adjustedinc >= 250000                       ~"8_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    incomeLW=case_when(
      adjustedinc <40000                         ~"1_less than 40k",
      adjustedinc >=40000 & adjustedinc <50000   ~"2_40k to 49,999",
      adjustedinc >=50000 & adjustedinc <80000   ~"3_50k to 79,999",
      adjustedinc >=80000 & adjustedinc <100000  ~"4_80k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"5_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"6_150k to 249,999",
      adjustedinc >= 250000                       ~"7_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    racerc=case_when(
      HISP>1               ~"5_Hispanic",
      HISP==1 & RAC1P==1   ~"1_White",
      HISP==1 & RAC1P==2   ~"2_Black",
      HISP==1 & RAC1P==3   ~"4_Other",
      HISP==1 & RAC1P==4   ~"4_Other",
      HISP==1 & RAC1P==5   ~"4_Other",
      HISP==1 & RAC1P==6   ~"3_Asian",
      HISP==1 & RAC1P>=7   ~"4_Other",
      TRUE                 ~"Uncoded"),
    agerc=case_when(
      AGEP<20              ~"1_less_than_20",
      AGEP>=20 & AGEP<30   ~"2_between 20 and 30",
      AGEP>=30 & AGEP<40   ~"3_between 30 and 40",
      AGEP>=40 & AGEP<50   ~"4_between 40 and 50",
      AGEP>=50 & AGEP<60   ~"5_between 50 and 60",
      AGEP>=60 & AGEP<70   ~"6_between 60 and 70",
      AGEP>=70             ~"7_70+",
      TRUE                 ~"Uncoded"),
    County_Res=case_when(
      floor(PUMA/100)==1 ~"Alameda",floor(PUMA/100)==13 ~"Contra Costa",floor(PUMA/100)==41 ~"Marin",floor(PUMA/100)==55 ~"Napa",floor(PUMA/100)==75 ~"San Francisco",
      floor(PUMA/100)==81 ~"San Mateo",floor(PUMA/100)==85 ~"Santa Clara",floor(PUMA/100)==95 ~"Solano",floor(PUMA/100)==97 ~"Sonoma",TRUE  ~"Outside Bay Area"),
    County_Emp=case_when(
      floor(POWPUMA/100)==1 ~"Alameda",floor(POWPUMA/100)==13 ~"Contra Costa",floor(POWPUMA/100)==41 ~"Marin",floor(POWPUMA/100)==55 ~"Napa",floor(POWPUMA/100)==75 ~"San Francisco",
      floor(POWPUMA/100)==81 ~"San Mateo",floor(POWPUMA/100)==85 ~"Santa Clara",floor(POWPUMA/100)==95 ~"Solano",floor(POWPUMA/100)==97 ~"Sonoma",TRUE  ~"Error")
  )%>% 
  select(SERIALNO,SPORDER,PUMA,County_Res,POWPUMA,County_Emp,PWGTP,AGEP,JWTR,HINCP,adjustedinc,agerc,incomerc,incomeLW,racerc,RELP) #if using calif instead of bayarea there is no PUMA_Name

MWTEMPN <- pums %>%
  mutate(SERIALNO = as.character(SERIALNO)) %>%         # Imports as factor; fixing this
  filter(NAICSP_short==22|NAICSP_short>=31 & NAICSP_short<=33|NAICSP_short==42|NAICSP_short==48|NAICSP_short==49) %>%                                   # Extract only retail
  select(-ADJINC) %>%                                   # Remove this variable and use joined version
  left_join(.,household,by="SERIALNO") %>% 
  mutate(
    adjustedinc=HINCP*(ADJINC/1000000),
    incomerc=case_when(
      adjustedinc <25000                         ~"1_less to 25k",
      adjustedinc >=25000 & adjustedinc <35000   ~"2_25k to 34,999",
      adjustedinc >=35000 & adjustedinc <50000   ~"3_35k to 49,999",
      adjustedinc >=50000 & adjustedinc <75000   ~"4_50k to 74,999",
      adjustedinc >=75000 & adjustedinc <100000  ~"5_75k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"6_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"7_150k to 249,999",
      adjustedinc >= 250000                       ~"8_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    incomeLW=case_when(
      adjustedinc <40000                         ~"1_less than 40k",
      adjustedinc >=40000 & adjustedinc <50000   ~"2_40k to 49,999",
      adjustedinc >=50000 & adjustedinc <80000   ~"3_50k to 79,999",
      adjustedinc >=80000 & adjustedinc <100000  ~"4_80k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"5_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"6_150k to 249,999",
      adjustedinc >= 250000                       ~"7_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    racerc=case_when(
      HISP>1               ~"5_Hispanic",
      HISP==1 & RAC1P==1   ~"1_White",
      HISP==1 & RAC1P==2   ~"2_Black",
      HISP==1 & RAC1P==3   ~"4_Other",
      HISP==1 & RAC1P==4   ~"4_Other",
      HISP==1 & RAC1P==5   ~"4_Other",
      HISP==1 & RAC1P==6   ~"3_Asian",
      HISP==1 & RAC1P>=7   ~"4_Other",
      TRUE                 ~"Uncoded"),
    agerc=case_when(
      AGEP<20              ~"1_less_than_20",
      AGEP>=20 & AGEP<30   ~"2_between 20 and 30",
      AGEP>=30 & AGEP<40   ~"3_between 30 and 40",
      AGEP>=40 & AGEP<50   ~"4_between 40 and 50",
      AGEP>=50 & AGEP<60   ~"5_between 50 and 60",
      AGEP>=60 & AGEP<70   ~"6_between 60 and 70",
      AGEP>=70             ~"7_70+",
      TRUE                 ~"Uncoded"),
    County_Res=case_when(
      floor(PUMA/100)==1 ~"Alameda",floor(PUMA/100)==13 ~"Contra Costa",floor(PUMA/100)==41 ~"Marin",floor(PUMA/100)==55 ~"Napa",floor(PUMA/100)==75 ~"San Francisco",
      floor(PUMA/100)==81 ~"San Mateo",floor(PUMA/100)==85 ~"Santa Clara",floor(PUMA/100)==95 ~"Solano",floor(PUMA/100)==97 ~"Sonoma",TRUE  ~"Outside Bay Area"),
    County_Emp=case_when(
      floor(POWPUMA/100)==1 ~"Alameda",floor(POWPUMA/100)==13 ~"Contra Costa",floor(POWPUMA/100)==41 ~"Marin",floor(POWPUMA/100)==55 ~"Napa",floor(POWPUMA/100)==75 ~"San Francisco",
      floor(POWPUMA/100)==81 ~"San Mateo",floor(POWPUMA/100)==85 ~"Santa Clara",floor(POWPUMA/100)==95 ~"Solano",floor(POWPUMA/100)==97 ~"Sonoma",TRUE  ~"Error")
  )%>% 
  select(SERIALNO,SPORDER,PUMA,County_Res,POWPUMA,County_Emp,PWGTP,AGEP,JWTR,HINCP,adjustedinc,agerc,incomerc,incomeLW,racerc,RELP) #if using calif instead of bayarea there is no PUMA_Name

FPSEMPN <- pums %>%
  mutate(SERIALNO = as.character(SERIALNO)) %>%         # Imports as factor; fixing this
  filter(NAICSP_short>=52 & NAICSP_short<=56) %>%                                   # Extract only retail
  select(-ADJINC) %>%                                   # Remove this variable and use joined version
  left_join(.,household,by="SERIALNO") %>% 
  mutate(
    adjustedinc=HINCP*(ADJINC/1000000),
    incomerc=case_when(
      adjustedinc <25000                         ~"1_less to 25k",
      adjustedinc >=25000 & adjustedinc <35000   ~"2_25k to 34,999",
      adjustedinc >=35000 & adjustedinc <50000   ~"3_35k to 49,999",
      adjustedinc >=50000 & adjustedinc <75000   ~"4_50k to 74,999",
      adjustedinc >=75000 & adjustedinc <100000  ~"5_75k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"6_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"7_150k to 249,999",
      adjustedinc >= 250000                       ~"8_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    incomeLW=case_when(
      adjustedinc <40000                         ~"1_less than 40k",
      adjustedinc >=40000 & adjustedinc <50000   ~"2_40k to 49,999",
      adjustedinc >=50000 & adjustedinc <80000   ~"3_50k to 79,999",
      adjustedinc >=80000 & adjustedinc <100000  ~"4_80k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"5_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"6_150k to 249,999",
      adjustedinc >= 250000                       ~"7_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    racerc=case_when(
      HISP>1               ~"5_Hispanic",
      HISP==1 & RAC1P==1   ~"1_White",
      HISP==1 & RAC1P==2   ~"2_Black",
      HISP==1 & RAC1P==3   ~"4_Other",
      HISP==1 & RAC1P==4   ~"4_Other",
      HISP==1 & RAC1P==5   ~"4_Other",
      HISP==1 & RAC1P==6   ~"3_Asian",
      HISP==1 & RAC1P>=7   ~"4_Other",
      TRUE                 ~"Uncoded"),
    agerc=case_when(
      AGEP<20              ~"1_less_than_20",
      AGEP>=20 & AGEP<30   ~"2_between 20 and 30",
      AGEP>=30 & AGEP<40   ~"3_between 30 and 40",
      AGEP>=40 & AGEP<50   ~"4_between 40 and 50",
      AGEP>=50 & AGEP<60   ~"5_between 50 and 60",
      AGEP>=60 & AGEP<70   ~"6_between 60 and 70",
      AGEP>=70             ~"7_70+",
      TRUE                 ~"Uncoded"),
    County_Res=case_when(
      floor(PUMA/100)==1 ~"Alameda",floor(PUMA/100)==13 ~"Contra Costa",floor(PUMA/100)==41 ~"Marin",floor(PUMA/100)==55 ~"Napa",floor(PUMA/100)==75 ~"San Francisco",
      floor(PUMA/100)==81 ~"San Mateo",floor(PUMA/100)==85 ~"Santa Clara",floor(PUMA/100)==95 ~"Solano",floor(PUMA/100)==97 ~"Sonoma",TRUE  ~"Outside Bay Area"),
    County_Emp=case_when(
      floor(POWPUMA/100)==1 ~"Alameda",floor(POWPUMA/100)==13 ~"Contra Costa",floor(POWPUMA/100)==41 ~"Marin",floor(POWPUMA/100)==55 ~"Napa",floor(POWPUMA/100)==75 ~"San Francisco",
      floor(POWPUMA/100)==81 ~"San Mateo",floor(POWPUMA/100)==85 ~"Santa Clara",floor(POWPUMA/100)==95 ~"Solano",floor(POWPUMA/100)==97 ~"Sonoma",TRUE  ~"Error")
  )%>% 
  select(SERIALNO,SPORDER,PUMA,County_Res,POWPUMA,County_Emp,PWGTP,AGEP,JWTR,HINCP,adjustedinc,agerc,incomerc,incomeLW,racerc,RELP) #if using calif instead of bayarea there is no PUMA_Name

HEREMPN <- pums %>%
  mutate(SERIALNO = as.character(SERIALNO)) %>%         # Imports as factor; fixing this
  filter(NAICSP_short>=61 & NAICSP_short<=81) %>%                                   # Extract only retail
  select(-ADJINC) %>%                                   # Remove this variable and use joined version
  left_join(.,household,by="SERIALNO") %>% 
  mutate(
    adjustedinc=HINCP*(ADJINC/1000000),
    incomerc=case_when(
      adjustedinc <25000                         ~"1_less to 25k",
      adjustedinc >=25000 & adjustedinc <35000   ~"2_25k to 34,999",
      adjustedinc >=35000 & adjustedinc <50000   ~"3_35k to 49,999",
      adjustedinc >=50000 & adjustedinc <75000   ~"4_50k to 74,999",
      adjustedinc >=75000 & adjustedinc <100000  ~"5_75k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"6_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"7_150k to 249,999",
      adjustedinc >= 250000                       ~"8_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    incomeLW=case_when(
      adjustedinc <40000                         ~"1_less than 40k",
      adjustedinc >=40000 & adjustedinc <50000   ~"2_40k to 49,999",
      adjustedinc >=50000 & adjustedinc <80000   ~"3_50k to 79,999",
      adjustedinc >=80000 & adjustedinc <100000  ~"4_80k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"5_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"6_150k to 249,999",
      adjustedinc >= 250000                       ~"7_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    racerc=case_when(
      HISP>1               ~"5_Hispanic",
      HISP==1 & RAC1P==1   ~"1_White",
      HISP==1 & RAC1P==2   ~"2_Black",
      HISP==1 & RAC1P==3   ~"4_Other",
      HISP==1 & RAC1P==4   ~"4_Other",
      HISP==1 & RAC1P==5   ~"4_Other",
      HISP==1 & RAC1P==6   ~"3_Asian",
      HISP==1 & RAC1P>=7   ~"4_Other",
      TRUE                 ~"Uncoded"),
    agerc=case_when(
      AGEP<20              ~"1_less_than_20",
      AGEP>=20 & AGEP<30   ~"2_between 20 and 30",
      AGEP>=30 & AGEP<40   ~"3_between 30 and 40",
      AGEP>=40 & AGEP<50   ~"4_between 40 and 50",
      AGEP>=50 & AGEP<60   ~"5_between 50 and 60",
      AGEP>=60 & AGEP<70   ~"6_between 60 and 70",
      AGEP>=70             ~"7_70+",
      TRUE                 ~"Uncoded"),
    County_Res=case_when(
      floor(PUMA/100)==1 ~"Alameda",floor(PUMA/100)==13 ~"Contra Costa",floor(PUMA/100)==41 ~"Marin",floor(PUMA/100)==55 ~"Napa",floor(PUMA/100)==75 ~"San Francisco",
      floor(PUMA/100)==81 ~"San Mateo",floor(PUMA/100)==85 ~"Santa Clara",floor(PUMA/100)==95 ~"Solano",floor(PUMA/100)==97 ~"Sonoma",TRUE  ~"Outside Bay Area"),
    County_Emp=case_when(
      floor(POWPUMA/100)==1 ~"Alameda",floor(POWPUMA/100)==13 ~"Contra Costa",floor(POWPUMA/100)==41 ~"Marin",floor(POWPUMA/100)==55 ~"Napa",floor(POWPUMA/100)==75 ~"San Francisco",
      floor(POWPUMA/100)==81 ~"San Mateo",floor(POWPUMA/100)==85 ~"Santa Clara",floor(POWPUMA/100)==95 ~"Solano",floor(POWPUMA/100)==97 ~"Sonoma",TRUE  ~"Error")
  )%>% 
  select(SERIALNO,SPORDER,PUMA,County_Res,POWPUMA,County_Emp,PWGTP,AGEP,JWTR,HINCP,adjustedinc,agerc,incomerc,incomeLW,racerc,RELP) #if using calif instead of bayarea there is no PUMA_Name

OTHEMPN <- pums %>%
  mutate(SERIALNO = as.character(SERIALNO)) %>%         # Imports as factor; fixing this
  filter(NAICSP_short==23|NAICSP_short==51|NAICSP_short==92|NAICSP_short==99) %>%                                   # Extract only retail
  select(-ADJINC) %>%                                   # Remove this variable and use joined version
  left_join(.,household,by="SERIALNO") %>% 
  mutate(
    adjustedinc=HINCP*(ADJINC/1000000),
    incomerc=case_when(
      adjustedinc <25000                         ~"1_less to 25k",
      adjustedinc >=25000 & adjustedinc <35000   ~"2_25k to 34,999",
      adjustedinc >=35000 & adjustedinc <50000   ~"3_35k to 49,999",
      adjustedinc >=50000 & adjustedinc <75000   ~"4_50k to 74,999",
      adjustedinc >=75000 & adjustedinc <100000  ~"5_75k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"6_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"7_150k to 249,999",
      adjustedinc >= 250000                       ~"8_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    incomeLW=case_when(
      adjustedinc <40000                         ~"1_less than 40k",
      adjustedinc >=40000 & adjustedinc <50000   ~"2_40k to 49,999",
      adjustedinc >=50000 & adjustedinc <80000   ~"3_50k to 79,999",
      adjustedinc >=80000 & adjustedinc <100000  ~"4_80k to 99,999",
      adjustedinc >=100000 & adjustedinc <150000 ~"5_100k to 149,999",
      adjustedinc >=150000 & adjustedinc <250000 ~"6_150k to 249,999",
      adjustedinc >= 250000                       ~"7_250k+",
      TRUE                                       ~"Uncoded, group quarters"),
    racerc=case_when(
      HISP>1               ~"5_Hispanic",
      HISP==1 & RAC1P==1   ~"1_White",
      HISP==1 & RAC1P==2   ~"2_Black",
      HISP==1 & RAC1P==3   ~"4_Other",
      HISP==1 & RAC1P==4   ~"4_Other",
      HISP==1 & RAC1P==5   ~"4_Other",
      HISP==1 & RAC1P==6   ~"3_Asian",
      HISP==1 & RAC1P>=7   ~"4_Other",
      TRUE                 ~"Uncoded"),
    agerc=case_when(
      AGEP<20              ~"1_less_than_20",
      AGEP>=20 & AGEP<30   ~"2_between 20 and 30",
      AGEP>=30 & AGEP<40   ~"3_between 30 and 40",
      AGEP>=40 & AGEP<50   ~"4_between 40 and 50",
      AGEP>=50 & AGEP<60   ~"5_between 50 and 60",
      AGEP>=60 & AGEP<70   ~"6_between 60 and 70",
      AGEP>=70             ~"7_70+",
      TRUE                 ~"Uncoded"),
    County_Res=case_when(
      floor(PUMA/100)==1 ~"Alameda",floor(PUMA/100)==13 ~"Contra Costa",floor(PUMA/100)==41 ~"Marin",floor(PUMA/100)==55 ~"Napa",floor(PUMA/100)==75 ~"San Francisco",
      floor(PUMA/100)==81 ~"San Mateo",floor(PUMA/100)==85 ~"Santa Clara",floor(PUMA/100)==95 ~"Solano",floor(PUMA/100)==97 ~"Sonoma",TRUE  ~"Outside Bay Area"),
    County_Emp=case_when(
      floor(POWPUMA/100)==1 ~"Alameda",floor(POWPUMA/100)==13 ~"Contra Costa",floor(POWPUMA/100)==41 ~"Marin",floor(POWPUMA/100)==55 ~"Napa",floor(POWPUMA/100)==75 ~"San Francisco",
      floor(POWPUMA/100)==81 ~"San Mateo",floor(POWPUMA/100)==85 ~"Santa Clara",floor(POWPUMA/100)==95 ~"Solano",floor(POWPUMA/100)==97 ~"Sonoma",TRUE  ~"Error")
  )%>% 
  select(SERIALNO,SPORDER,PUMA,County_Res,POWPUMA,County_Emp,PWGTP,AGEP,JWTR,HINCP,adjustedinc,agerc,incomerc,incomeLW,racerc,RELP) #if using calif instead of bayarea there is no PUMA_Name


write.csv(AGREMPN, "PUMS2014-2018 AGREMPN Summary v2.csv", row.names = FALSE, quote = T)
write.csv(MWTEMPN, "PUMS2014-2018 MWTEMPN Summary v2.csv", row.names = FALSE, quote = T)
write.csv(FPSEMPN, "PUMS2014-2018 FPSEMPN Summary v2.csv", row.names = FALSE, quote = T)
write.csv(HEREMPN, "PUMS2014-2018 HEREMPN Summary v2.csv", row.names = FALSE, quote = T)
write.csv(OTHEMPN, "PUMS2014-2018 OTHEMPN Summary v2.csv", row.names = FALSE, quote = T)

