"""
Orbit integration for the superposition library.

Khoperskov et al. 2025 (Paper II, Sect. 2.2):
  "we integrated the orbits of the APOGEE stars in a rigid, rotating 3D X-shaped
   barred galactic potential over 5 Gyr. The output of the orbit integration
   incorporates 500 data points (positions and velocities) per orbit for each star."

Everything here happens in the BAR-COROTATING frame.
"""
import numpy as np
import agama

from potential import OMEGA_BAR, BAR_ANGLE, R_SUN, Z_SUN, V_SUN

T_INTEGRATE = 5.0
N_POINTS = 500


def icrs_to_galactocentric(ra, dec, dist, pmra, pmdec, rv,
                           R_sun=R_SUN, z_sun=Z_SUN, v_sun=V_SUN):
    import astropy.units as u
    from astropy.coordinates import SkyCoord, Galactocentric, CartesianDifferential
    vR, vphi, vz = v_sun
    galcen_v = CartesianDifferential([-vR, vphi, vz] * u.km / u.s)
    frame = Galactocentric(galcen_distance=R_sun * u.kpc,
                           z_sun=z_sun * u.kpc,
                           galcen_v_sun=galcen_v)
    c = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, distance=dist * u.kpc,
                 pm_ra_cosdec=pmra * u.mas / u.yr, pm_dec=pmdec * u.mas / u.yr,
                 radial_velocity=rv * u.km / u.s)
    g = c.transform_to(frame)
    return np.column_stack([
        g.x.to(u.kpc).value, g.y.to(u.kpc).value, g.z.to(u.kpc).value,
        g.v_x.to(u.km / u.s).value, g.v_y.to(u.km / u.s).value,
        g.v_z.to(u.km / u.s).value])


def to_bar_frame(xv, bar_angle=BAR_ANGLE):
    a = np.radians(bar_angle)
    c, s = np.cos(a), np.sin(a)
    out = xv.copy()
    out[:, 0] = c * xv[:, 0] + s * xv[:, 1]
    out[:, 1] = -s * xv[:, 0] + c * xv[:, 1]
    out[:, 3] = c * xv[:, 3] + s * xv[:, 4]
    out[:, 4] = -s * xv[:, 3] + c * xv[:, 4]
    return out


def integrate_library(ic, potential, time=T_INTEGRATE, trajsize=N_POINTS,
                      omega=OMEGA_BAR, dtype=np.float32, verbose=True):
    n = len(ic)
    _, trajs = agama.orbit(potential=potential, ic=ic, time=time,
                           trajsize=trajsize, Omega=omega, separateTime=True)
    out = np.ascontiguousarray(trajs, dtype=dtype)
    if verbose:
        print('integrated %d orbits, %d points each, T=%.1f Gyr, Omega=%.1f km/s/kpc'
              % (n, trajsize, time, omega))
    return out


MIRRORS = np.array([
    [1, 1, 1], [-1, 1, 1], [1, -1, 1], [1, 1, -1],
    [-1, -1, 1], [-1, 1, -1], [1, -1, -1], [-1, -1, -1]], dtype=np.int8)


def mirror_positions(xyz):
    return (xyz[None, :, :] * MIRRORS[:, None, :]).reshape(-1, 3)
