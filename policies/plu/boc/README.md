## This script aims to:
* evaluate the BASIS BOC data (zoning data collected through BASIS) by comparing the build-out-capacity of the Bay Area land under BASIS BOC scheme versus PBA40 planned land use scheme
* analyze the build-out-capacity of certain types of parcels, e.g., vacant parcels, parcels with a investment to land ratio (ILR), etc. 
* analyze the build-out-capacity of various zoningmod scenarios

## Key components and steps:
### BASIS BOC data evaluation
* merge p10 (parcel data used in PBA40) with PLU10 (planned land use data used in PBA40)
* merge p10 data with BASIS BOC (build-out-capacity data collected in the BASIS process, to be used as planned land use in PBA50)
* merge the data with b10 (building data used in PBA40) to assign parcel characteristics, e.g. vacancy, ILR, etc.
* calculate the build-out-capacity for all parcels as well as various parcel groups at the county and jurisdiction levels
### PBA50 Zoningmod scenario evaluation
* merge the hybrid parcel data (Blueprint Option 2) with BASIS BOC data
* merge the data with PBA zoningmod data
* merge the data with BASIS building data
* calculate the build-out-capacity for each zoningmod scenarios at the county and jurisdiction levels
