### Intro
Hybrid index is used to build hybrid base zoning by selecting more reasonable allowed development type and intensity data from PBA40 versus BASIS.

For each zoning attribute (allowable development or intensity), the index indicates if PBA40 data (denoted 0) or BASIS data (denoted 1) is used as BAUS base zoning input. The index is then used in [2_build_hybrid_zoning.py](../2_build_hybrid_zoning.py) to construct hybrid base zoning through an iterative process. The end result is 'hybrid_urbansim'.

Allowable development types: HS, HT, HM, OF, HO, SC, IL, IW, IH, RS, RB, MR, MT, ME

Intensity: MAX_DUA, MAX_FAR, MAX_HEIGHT

### Process of building hybrid_urbansim
1. Create [idx_intensity_comp.csv](): set the indexes of all intensity attributes as 1 and of all allowable development types as 0. The goal is to isolate and evaluate BASIS BOC intensity data.
2. Run [2_build_hybrid_zoning.py](../2_build_hybrid_zoning.py) and [3_dev_capacity_calculation.py](../3_dev_capacity_calculation.py) with *idx_intensity_comp.csv* as the input. 
3. Compare the development capacity of PBA40 and hybrid, and use the following rules to generate hybrid index (0 or 1) for each intensity attribute: 
	1. For each jurisdiciont:
	
		if abs(SQFT_pab40 - SQFT_hybird)   <= SQFT_pba40 * **20%**  THEN MAX_FAR_idx = 1 and MAX_HEIGHT_idx = 1
		
		if abs(SQFT_pab40 - SQFT_hybird)   >  SQFT_pba40 * **20%**  THEN MAX_FAR_idx = 0 and MAX_HEIGHT_idx = 0
	2. For each jurisdiction:
	
		if abs(UNITS_pab40 - UNITS_hybird) <= UNITS_pba40 * **20%** THEN MAX_DUA_idx = 1
		
		if abs(UNITS_pab40 - UNITS_hybird) >  UNITS_pba40 * **20%** THEN MAX_DUA_idx = 0

4. For each of the development types, e.g. HM, create [idx_HM_comp.csv](): set the index of HM as 1 and of all the other zoning attributes as 0.
5. Run [2_build_hybrid_zoning.py](../2_build_hybrid_zoning.py) and [3_dev_capacity_calculation.py](../3_dev_capacity_calculation.py) with each of the development type comparison index files as input, then repeat Step 3 to generate the hybrid index for each development type.
6. Merge the indexes for all zoning attributes to generate [index_urbansim.csv]()
