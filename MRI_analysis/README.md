# Ouputs from the MRI experiment

This folder includes: 
- The exact event files that were entered into the GLM analysis to define onset times - **sub-#_run-#_Events**
- The raw cluster tables outputted from the within subject fixed effects analysis - **Back-Contrast_Clusters** + **View-Contrast_Clusters** + **Person-Contrast_Clusters**
- All scanning parameters of the functional and anatomical scans - **Scanning_Parameters**

The event TSV files lack headers and so are defined here:

**Event files:**
First column - stimulus onset time in seconds
Second column - Duration of stimulus
Third column - Amplitude weighting value used by FSL (All set to 1 for an equal weighting)
