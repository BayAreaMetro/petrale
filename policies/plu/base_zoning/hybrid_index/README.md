### Intro
Hybrid index is used to build hybrid base zoning by selecting more reasonable allowed development type and intensity data from PBA40 versus BASIS. For each zoning attribute (allowable development or intensity), the index indicates if PBA40 data (denoted 0) or BASIS data (denoted 1) is used as BAUS base zoning input. 

**Allowable development types**: HS, HT, HM, OF, HO, SC, IL, IW, IH, RS, RB, MR, MT, ME

**Intensity**: MAX_DUA, MAX_FAR, MAX_HEIGHT

Two sets of indexes were created during the process: 
* **Interim indexes** - bring in BASIS data for one zoning attribute at a time (or in the case of intensity, all three intensity attributes together), in order to construct interim hybrid zoning, calculate and evaluate capacity discrepancies between PBA40 and the hybrid zoning at the jurisdiction level, and then decide if PBA40 or BASIS data should be used for this zoning attribute for each jurisdiction. 
* **Urbansim indexes** - combine the indexes of all zoning attributes.

### Process of building hybrid_urbansim
1. Create a set of [interim hybrid indexes](https://github.com/BayAreaMetro/petrale/tree/master/policies/plu/base_zoning/hybrid_index/interim) for zoning attributes. For example:
	* [idx_intensity_comp.csv](interim/idx_intensity_comp.csv): set the indexes of all intensity attributes as 1 and of all allowable development types as 0. The goal is to isolate and evaluate BASIS BOC intensity data.
	* [idx_HM_comp.csv](interim/idx_HM_comp.csv): set the indexes of HM as 1 and of all other allowable development types and intensities as 0. The goal is to isolate and evaluate BASIS BOC HM data.
	
2. Run [2_build_hybrid_zoning.py](../2_build_hybrid_zoning.py) with each interim hybrid index to create corresponding [interim hybrid zoning](https://mtcdrive.box.com/s/k7nt4b0vhl1k1b4kbjlwnbzegtvfqym8).

3. Run [hybrid_index_selection.ipynb](hybrid_index_selection.ipynb) to calculate capacity, compare capacity, select data source (0 as PBA40 OR 1 as BASIS) for each zoning attribute and each jurisdiction, and combine the indexes into one index file [index_urbansim_heuristics].

* Rules for intensity attributes: 

	For each jurisdiction:
	
		if abs(SQFT_pab40 - SQFT_hybird) / SQFT_pba40 <= 20%  THEN MAX_FAR_idx = 1 and MAX_HEIGHT_idx = 1
		
		else MAX_HEIGHT_idx = 0
	For each jurisdiction:
	
		if abs(UNITS_pab40 - UNITS_hybird) / UNITS_pba40 <= 20% THEN MAX_DUA_idx = 1
		
		else MAX_DUA_idx = 0

* Rule for MR (residential-commercial mixed-use):

	For each jurisdiction:

		if (abs(SQFT_pab40 - SQFT_hybird) / SQFT_pba40 <= 20%) & 
		   (abs(UNITS_pab40 - UNITS_hybird) / UNITS_pba40 <= 20%) THEN MR_idx = 1
		
		else MR_idx = 0

* Rule for residential-only development types:

	For each jurisdiction: 
		
		if abs(UNITS_pab40 - UNITS_hybird) / UNITS_pba40 <= 20% THEN devType_idx = 1
		
		else devType_idx = 0
	  
* Rule for non-residential-only development types:
	
	For each jurisdiction: 
		
		if abs(SQFT_pab40 - SQFT_hybird) / SQFT_pba40 <= 20% THEN devType_idx = 1
		
		else devType_idx = 0

4. Based on internal and external feedback, manually adjust *index_urbansim_heuristics.csv* to *index_urbansim.csv*.
