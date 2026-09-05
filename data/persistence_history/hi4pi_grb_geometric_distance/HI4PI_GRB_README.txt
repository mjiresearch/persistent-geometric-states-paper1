HI4PI GRB SIGHTLINE RETRIEVAL
==============================

Purpose
-------
Retrieve the public machine-readable H I 21-cm spectra needed to replace the
figure-digitized velocities in the GRB dust-distance / Galactic-rotation test.

Public source
-------------
HI4PI Collaboration (2016), CDS/VizieR catalog J/A+A/594/A116.
Archive root:
https://cdsarc.cds.unistra.fr/ftp/J/A+A/594/A116

The catalog contains Galactic spectral cubes in CUBES/GAL and an index named
cubes_gal.dat.  The included Python script reads the index first and resolves
the appropriate CAR cube for each target.

Targets
-------
GRB 221009A: l=52.96 deg,  b=+4.32 deg
GRB 160623A: l=84.17 deg, b=-2.69 deg
GRB 031203:  l=255.74 deg,b=-4.80 deg

Expected first two tiles:
GRB 221009A -> CAR_E03.fits
GRB 160623A -> CAR_E05.fits

The third tile is intentionally resolved from the official cubes_gal.dat table
rather than hard-coded.

Run
---
1. Install dependencies:
   python -m pip install numpy astropy

2. Resolve tiles without downloading the large cubes:
   python hi4pi_grb_fetch_extract.py --catalog-only

3. Download the selected cubes and extract spectra:
   python hi4pi_grb_fetch_extract.py --output hi4pi_grb_data

The downloads use HTTP Range requests, so interrupted transfers can resume.

Outputs
-------
Each GRB gets a CSV with:
  velocity_lsr_km_s
  brightness_temperature_K

Those CSVs are the inputs for the next stage: Gaussian component fitting,
matching the components to the X-ray dust layers, and recomputing the
rotation-curve residuals with uncertainties.
