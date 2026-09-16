"""
MW potential: Sormani et al. (2022) analytic approximation of the Portail et al. (2017)
M2M barred model, as distributed in AGAMA's example_mw_bar_potential.py.

This is the potential adopted by Khoperskov et al. 2025 (A&A 700, A89), Sect. 2.2.

Two variants are provided:
  'portail17'  -- the Sormani+22 bar model exactly as in AGAMA's example script.
                  This is what the papers cite.
  'hunter24'   -- same bar, but retuned to reproduce dynamical constraints across the
                  whole Galaxy (Hunter et al. 2024). See CAVEAT in README.

Units: kpc, Msun, km/s.  Bar rotates CLOCKWISE, so Omega is NEGATIVE.
"""
import os
import numpy as np
import agama
import numpy as _np
_np.seterr(all="ignore")

OMEGA_BAR = -37.5
BAR_ANGLE = 27.0
R_SUN = 8.12
Z_SUN = 0.0208
V_SUN = (-9.5, 250.7, 8.56)


def _makeDisk(**p):
    sd, sr, sh = p['surfaceDensity'], p['scaleRadius'], p['scaleHeight']
    icr, si, vsi = p['innerCutoffRadius'], p['sersicIndex'], p['verticalSersicIndex']
    def density(xyz):
        R = (xyz[:, 0]**2 + xyz[:, 1]**2)**0.5
        return (sd / (4 * sh) * np.exp(-(R / sr)**si - icr / (R + 1e-100)) /
                np.cosh((abs(xyz[:, 2]) / sh)**vsi))
    return agama.Density(density, symmetry='a')


def _makeXBar(**p):
    dn, x0, y0, z0 = p['densityNorm'], p['x0'], p['y0'], p['z0']
    xc, yc, c, alpha = p['xc'], p['yc'], p['c'], p['alpha']
    cpar, cperp, m, n = p['cpar'], p['cperp'], p['m'], p['n']
    ocr = p['outerCutoffRadius']
    def density(xyz):
        r = np.sum(xyz**2, axis=1)**0.5
        a = (((abs(xyz[:, 0]) / x0)**cperp + (abs(xyz[:, 1]) / y0)**cperp)**(cpar / cperp)
             + (abs(xyz[:, 2]) / z0)**cpar)**(1 / cpar)
        ap = (((xyz[:, 0] + c * xyz[:, 2]) / xc)**2 + (xyz[:, 1] / yc)**2)**0.5
        am = (((xyz[:, 0] - c * xyz[:, 2]) / xc)**2 + (xyz[:, 1] / yc)**2)**0.5
        return (dn / np.cosh(a**m) * np.exp(-(r / ocr)**2) *
                (1 + alpha * (np.exp(-ap**n) + np.exp(-am**n))))
    return density


def _makeLongBar(**p):
    dn, x0, y0 = p['densityNorm'], p['x0'], p['y0']
    cpar, cperp, sh = p['cpar'], p['cperp'], p['scaleHeight']
    icr, ocr = p['innerCutoffRadius'], p['outerCutoffRadius']
    ics, ocs = p['innerCutoffStrength'], p['outerCutoffStrength']
    def density(xyz):
        R = (xyz[:, 0]**2 + xyz[:, 1]**2)**0.5
        a = ((abs(xyz[:, 0]) / x0)**cperp + (abs(xyz[:, 1]) / y0)**cperp)**(1 / cperp)
        return dn / np.cosh(xyz[:, 2] / sh)**2 * np.exp(
            -a**cpar - (R / ocr)**ocs - (icr / R)**ics)
    return density


def _makeCMC(mass, scaleRadius, scaleHeight, axisRatioY):
    norm = mass / (4 * np.pi * scaleRadius**2 * scaleHeight * axisRatioY)
    def density(xyz):
        return norm * np.exp(-(xyz[:, 0]**2 + (xyz[:, 1] / axisRatioY)**2)**0.5 / scaleRadius
                             - abs(xyz[:, 2]) / scaleHeight)
    return agama.Density(density, symmetry='a')


def _makeBarDensity():
    p = np.array([
        3.16273226e+09, 4.90209137e-01, 3.92017253e-01, 2.29482096e-01,
        1.99110223e+00, 2.23179266e+00, 8.73227940e-01, 4.36983774e+00,
        6.25670015e-01, 1.34152138e+00, 1.94025114e+00, 7.50504078e-01,
        4.68875471e-01, 4.95381575e+08, 5.36363324e+00, 9.58522229e-01,
        6.10542494e-01, 9.69645220e-01, 3.05125124e+00, 3.19043585e+00,
        5.58255674e-01, 1.67310332e+01, 3.19575493e+00, 1.74304936e+13,
        4.77961423e-01, 2.66853061e-01, 2.51516920e-01, 1.87882599e+00,
        9.80136710e-01, 2.20415408e+00, 7.60708626e+00, -2.72907665e+01,
        1.62966434e+00])
    xbar = _makeXBar(densityNorm=p[0], x0=p[1], y0=p[2], z0=p[3], cpar=p[4],
                     cperp=p[5], m=p[6], outerCutoffRadius=p[7], alpha=p[8],
                     c=p[9], n=p[10], xc=p[11], yc=p[12])
    lb1 = _makeLongBar(densityNorm=p[13], x0=p[14], y0=p[15], scaleHeight=p[16],
                       cperp=p[17], cpar=p[18], outerCutoffRadius=p[19],
                       innerCutoffRadius=p[20], outerCutoffStrength=p[21],
                       innerCutoffStrength=p[22])
    lb2 = _makeLongBar(densityNorm=p[23], x0=p[24], y0=p[25], scaleHeight=p[26],
                       cperp=p[27], cpar=p[28], outerCutoffRadius=p[29],
                       innerCutoffRadius=p[30], outerCutoffStrength=p[31],
                       innerCutoffStrength=p[32])
    return agama.Density(lambda x: xbar(x) + lb1(x) + lb2(x), symmetry='t')


def stellar_density():
    pd = [1.03063359e+09, 4.75409497e+00, 4.68804907e+00, 1.51100601e-01,
          1.53608780e+00, 7.15915848e-01]
    disk = _makeDisk(surfaceDensity=pd[0], scaleRadius=pd[1],
                     innerCutoffRadius=pd[2], scaleHeight=pd[3],
                     sersicIndex=pd[4], verticalSersicIndex=pd[5])
    return agama.Density(_makeBarDensity(), disk, _makeCMC(0.2e10, 0.25, 0.05, 0.5))


def hunter24_stellar_density():
    params_nsc = dict(type='Spheroid', mass=6.1e7, gamma=0.71, beta=4, alpha=1,
                      axisRatioZ=0.73, scaleRadius=0.0059, outerCutoffRadius=0.1)
    params_nsd = [
        dict(type='Spheroid', densityNorm=2.00583e12, gamma=0, beta=0, alpha=1,
             axisRatioZ=0.37, outerCutoffRadius=0.00506, cutoffStrength=0.72),
        dict(type='Spheroid', densityNorm=1.53e12, gamma=0, beta=0, alpha=1,
             axisRatioZ=0.37, outerCutoffRadius=0.0246, cutoffStrength=0.79),
    ]
    params_disk = [
        dict(type='Disk', surfaceDensity=1.332e9, scaleRadius=2.0,
             scaleHeight=0.3, innerCutoffRadius=2.7, sersicIndex=1),
        dict(type='Disk', surfaceDensity=8.97e8, scaleRadius=2.8,
             scaleHeight=0.9, innerCutoffRadius=2.7, sersicIndex=1),
    ]
    return agama.Density(_makeBarDensity(), *params_disk, params_nsc, *params_nsd)


def _make_portail17_potential(include_dark=True, mmax=12, gridsize=25):
    pot_bary = agama.Potential(type='CylSpline', density=stellar_density(), mmax=mmax,
        gridsizeR=gridsize, gridsizez=gridsize, Rmin=0.1, Rmax=40, zmin=0.05, zmax=20)
    if not include_dark:
        return agama.Potential(pot_bary)
    pot_dark = agama.Potential(type='Multipole', density='Spheroid', axisratioz=0.8,
        gamma=0, beta=0, outerCutoffRadius=1.84, cutoffStrength=0.74,
        densityNorm=0.0263e10, gridsizer=26, rmin=0.01, rmax=1000, lmax=8)
    return agama.Potential(pot_bary, pot_dark)


def _make_hunter24_potential(include_dark=True):
    params_bh = dict(type='Plummer', mass=4.1e6, scaleRadius=1e-3)
    params_nsc = dict(type='Spheroid', mass=6.1e7, gamma=0.71, beta=4, alpha=1,
                      axisRatioZ=0.73, scaleRadius=0.0059, outerCutoffRadius=0.1)
    params_nsd = [
        dict(type='Spheroid', densityNorm=2.00583e12, gamma=0, beta=0, alpha=1,
             axisRatioZ=0.37, outerCutoffRadius=0.00506, cutoffStrength=0.72),
        dict(type='Spheroid', densityNorm=1.53e12, gamma=0, beta=0, alpha=1,
             axisRatioZ=0.37, outerCutoffRadius=0.0246, cutoffStrength=0.79),
    ]
    params_disk = [
        dict(type='Disk', surfaceDensity=1.332e9, scaleRadius=2.0, scaleHeight=0.3,
             innerCutoffRadius=2.7, sersicIndex=1),
        dict(type='Disk', surfaceDensity=8.97e8, scaleRadius=2.8, scaleHeight=0.9,
             innerCutoffRadius=2.7, sersicIndex=1),
    ]
    params_gas = [
        dict(type='Disk', surfaceDensity=5.81e7, scaleRadius=7, scaleHeight=-0.085,
             innerCutoffRadius=4, sersicIndex=1),
        dict(type='Disk', surfaceDensity=2.68e9, scaleRadius=1.5, scaleHeight=-0.045,
             innerCutoffRadius=12, sersicIndex=1),
    ]
    params_dark = dict(type='Spheroid', densitynorm=2.774e11, gamma=0, beta=0,
                       alpha=1, outerCutoffRadius=8.682e-6, cutoffStrength=0.1704)
    spheroids = [params_bh, params_nsc, *params_nsd]
    if include_dark:
        spheroids.insert(0, params_dark)
    pot_mul = agama.Potential(type='Multipole', density=agama.Density(*spheroids),
                              lmax=12, gridSizeR=36, rmin=1e-4, rmax=1000)
    pot_cyl = agama.Potential(type='CylSpline', density=agama.Density(
        _makeBarDensity(), *(params_disk + params_gas)), mmax=8, gridSizeR=30,
        gridSizez=32, Rmin=0.1, Rmax=200, zmin=0.05, zmax=200)
    return agama.Potential(pot_mul, pot_cyl)


def target_stellar_density(model='portail17'):
    model = model.lower()
    if model == 'portail17':
        return stellar_density()
    if model == 'hunter24':
        return hunter24_stellar_density()
    raise ValueError("unknown target density model %r" % model)


def make_potential(model='portail17', include_dark=True, mmax=12, gridsize=25,
                   cache=None):
    agama.setUnits(length=1, mass=1, velocity=1)
    model = model.lower()
    if model not in ('portail17', 'hunter24'):
        raise ValueError("model must be 'portail17' or 'hunter24'")
    if cache and os.path.exists(cache):
        tag = ('dark' if include_dark else 'baryons').lower()
        base = os.path.basename(cache).lower()
        if model in base and tag in base:
            return agama.Potential(cache)
        if model == 'portail17' and include_dark and base == 'portail17.ini':
            return agama.Potential(cache)
    np.seterr(all='ignore')
    if model == 'portail17':
        pot = _make_portail17_potential(include_dark, mmax=mmax, gridsize=gridsize)
    else:
        pot = _make_hunter24_potential(include_dark)
    if cache:
        pot.export(cache)
    return pot


if __name__ == '__main__':
    import time
    for model in ('portail17', 'hunter24'):
        for include_dark in (True, False):
            t0 = time.time()
            name = '%s_%s' % (model, 'dark' if include_dark else 'baryons')
            pot = make_potential(model=model, include_dark=include_dark,
                                 cache=name + '.ini')
            r = np.array([2., 4., 8.12, 12., 15.])
            xyz = np.column_stack((r, r * 0, r * 0))
            vc = np.sqrt(np.maximum(-r * pot.force(xyz)[:, 0], 0.0))
            print('%s built in %.1f s' % (name, time.time() - t0))
            print('  vc:', ' '.join('R=%.2f:%.1f' % x for x in zip(r, vc)))
