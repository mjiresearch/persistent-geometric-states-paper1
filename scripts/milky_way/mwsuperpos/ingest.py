"""
Build the input star sample for the orbit superposition.

Reproduces the selection of Khoperskov et al. 2025 (A&A 700, A89), Sect. 2.1.

The public DistMass DR17 VAC has used more than one column-naming convention.
For the current v1.6.1 file the relevant fields are WEIGHTED_DIST,
WEIGHTED_DIST_ERR, AGE_UNCOR_SS and AGE_ERR.  The uncorrected-Sharma age scale
is the default because Stone-Martinez et al. state that Imig et al. (2023) used
that model, and Khoperskov et al. cite the Imig analysis when motivating their
DistMass age choice.  All four names remain explicitly overrideable.
"""
import numpy as np
from astropy.table import Table, join

LOGG_MAX = 2.2
RV_ERR_MAX = 2.0
DIST_FRAC_ERR_MAX = 0.20
PM_FRAC_ERR_MAX = 0.10
AGE_ERR_MAX = 2.0


def load_allstar(path, columns=None):
    if columns is None:
        columns = ['APOGEE_ID', 'RA', 'DEC', 'LOGG', 'TEFF',
                   'VHELIO_AVG', 'VERR', 'FE_H', 'FE_H_ERR',
                   'MG_FE', 'MG_FE_ERR', 'ASPCAPFLAG', 'EXTRATARG', 'SNREV',
                   'GAIAEDR3_SOURCE_ID', 'GAIAEDR3_PMRA', 'GAIAEDR3_PMDEC',
                   'GAIAEDR3_PMRA_ERROR', 'GAIAEDR3_PMDEC_ERROR']
    t = Table.read(path, hdu=1)
    keep = [c for c in columns if c in t.colnames]
    missing = set(columns) - set(keep)
    if missing:
        print('WARNING: columns absent from allStar: %s' % sorted(missing))
    return t[keep]


def _resolve_column(t, requested, candidates, label):
    """Return an available column name, preferring an explicit request."""
    if requested is not None:
        if requested not in t.colnames:
            raise KeyError('requested %s column %r absent; available: %s'
                           % (label, requested, t.colnames))
        return requested
    for name in candidates:
        if name in t.colnames:
            return name
    raise KeyError('no recognised %s column; tried %s; available: %s'
                   % (label, candidates, t.colnames))


def load_distmass(path, dist_col=None, dist_err_col=None,
                  age_col=None, age_err_col=None):
    """Read DistMass and normalize distance/age columns.

    Defaults target the public DR17 v1.6.1 VAC while accepting earlier aliases.
    Distances are converted from pc to kpc when their median scale indicates pc.
    """
    t = Table.read(path, hdu=1)
    dist_col = _resolve_column(
        t, dist_col,
        ('WEIGHTED_DIST', 'DISTANCE_WEIGHTED', 'DISTANCE', 'DIST'),
        'distance')
    dist_err_col = _resolve_column(
        t, dist_err_col,
        ('WEIGHTED_DIST_ERR', 'DISTANCE_WEIGHTED_ERR', 'DISTANCE_ERR', 'DIST_ERR'),
        'distance-error')
    age_col = _resolve_column(
        t, age_col,
        ('AGE_UNCOR_SS', 'AGE_COR_SS', 'AGE_COR_MO', 'AGE_UNCOR_MO',
         'AGE_COR_TW', 'AGE_UNCOR_TW', 'AGE'),
        'age')
    age_err_col = _resolve_column(t, age_err_col, ('AGE_ERR',), 'age-error')

    print('DistMass columns: distance=%s, distance_err=%s, age=%s, age_err=%s'
          % (dist_col, dist_err_col, age_col, age_err_col))

    out = Table()
    out['APOGEE_ID'] = t['APOGEE_ID']
    for src, dst in ((dist_col, 'dist'), (dist_err_col, 'dist_err'),
                     (age_col, 'age'), (age_err_col, 'age_err')):
        out[dst] = np.asarray(t[src], dtype=float)

    finite_dist = np.asarray(out['dist'], float)
    finite_dist = finite_dist[np.isfinite(finite_dist) & (finite_dist > 0)]
    if len(finite_dist) and np.nanmedian(finite_dist) > 100:
        print('NOTE: DistMass distances are in pc; converting to kpc')
        out['dist'] /= 1000.0
        out['dist_err'] /= 1000.0
    return out


def apply_selection(t, verbose=True):
    def rep(name, mask, prev):
        if verbose:
            print('  %-28s %7d kept (%+d)' % (name, mask.sum(), mask.sum() - prev))
        return mask.sum()
    n = len(t)
    if verbose:
        print('starting from %d rows' % n)
    finite = np.isfinite(t['LOGG']) & np.isfinite(t['FE_H']) & np.isfinite(t['MG_FE'])
    m = finite
    prev = rep('finite logg/[Fe/H]/[Mg/Fe]', m, n)
    m &= t['ASPCAPFLAG'] == 0
    prev = rep('ASPCAPFLAG == 0', m, prev)
    m &= t['EXTRATARG'] == 0
    prev = rep('EXTRATARG == 0', m, prev)
    m &= t['LOGG'] < LOGG_MAX
    prev = rep('log g < %.1f' % LOGG_MAX, m, prev)
    m &= np.isfinite(t['VERR']) & (t['VERR'] < RV_ERR_MAX)
    prev = rep('RV err < %.0f km/s' % RV_ERR_MAX, m, prev)
    pm = np.hypot(t['GAIAEDR3_PMRA'], t['GAIAEDR3_PMDEC'])
    pmerr = np.hypot(t['GAIAEDR3_PMRA_ERROR'], t['GAIAEDR3_PMDEC_ERROR'])
    with np.errstate(invalid='ignore', divide='ignore'):
        m &= np.isfinite(pm) & (pm > 0) & (pmerr / pm < PM_FRAC_ERR_MAX)
    prev = rep('PM err < %.0f%%' % (100 * PM_FRAC_ERR_MAX), m, prev)
    with np.errstate(invalid='ignore', divide='ignore'):
        m &= np.isfinite(t['dist']) & (t['dist'] > 0)
        m &= np.isfinite(t['dist_err']) & (t['dist_err'] >= 0)
        m &= (t['dist_err'] / t['dist']) < DIST_FRAC_ERR_MAX
    prev = rep('dist err < %.0f%%' % (100 * DIST_FRAC_ERR_MAX), m, prev)
    m &= np.isfinite(t['age']) & (t['age'] > 0)
    m &= np.isfinite(t['age_err']) & (t['age_err'] >= 0) & (t['age_err'] < AGE_ERR_MAX)
    rep('sigma_age < %.0f Gyr' % AGE_ERR_MAX, m, prev)
    return t[m]


def build_sample(allstar_path, distmass_path, out_path='sample.fits', verbose=True,
                 **distmass_columns):
    a = load_allstar(allstar_path)
    d = load_distmass(distmass_path, **distmass_columns)
    if 'SNREV' in a.colnames:
        a.sort('SNREV'); a.reverse()
        _, idx = np.unique(np.asarray(a['APOGEE_ID']), return_index=True)
        a = a[np.sort(idx)]
    t = join(a, d, keys='APOGEE_ID', join_type='inner')
    if verbose:
        print('joined allStar x distmass: %d rows' % len(t))
    t = apply_selection(t, verbose=verbose)
    if verbose:
        print('final sample: %d stars (paper reports ~80 000)' % len(t))
    if out_path:
        t.write(out_path, overwrite=True)
    return t


def to_initial_conditions(t):
    from orbits import icrs_to_galactocentric, to_bar_frame
    xv = icrs_to_galactocentric(
        np.asarray(t['RA'], float), np.asarray(t['DEC'], float),
        np.asarray(t['dist'], float), np.asarray(t['GAIAEDR3_PMRA'], float),
        np.asarray(t['GAIAEDR3_PMDEC'], float), np.asarray(t['VHELIO_AVG'], float))
    ic = to_bar_frame(xv)
    meta = Table()
    meta['APOGEE_ID'] = t['APOGEE_ID']
    meta['GAIA_SOURCE_ID'] = t['GAIAEDR3_SOURCE_ID']
    for c in ('FE_H', 'FE_H_ERR', 'MG_FE', 'MG_FE_ERR', 'age', 'age_err'):
        if c in t.colnames:
            meta[c] = t[c]
    meta['x'], meta['y'], meta['z'] = ic[:, 0], ic[:, 1], ic[:, 2]
    meta['vx'], meta['vy'], meta['vz'] = ic[:, 3], ic[:, 4], ic[:, 5]
    return ic, meta


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('allstar'); p.add_argument('distmass')
    p.add_argument('-o', '--out', default='sample.fits')
    p.add_argument('--dist-col')
    p.add_argument('--dist-err-col')
    p.add_argument('--age-col')
    p.add_argument('--age-err-col')
    args = p.parse_args()
    build_sample(args.allstar, args.distmass, args.out,
                 dist_col=args.dist_col, dist_err_col=args.dist_err_col,
                 age_col=args.age_col, age_err_col=args.age_err_col)
