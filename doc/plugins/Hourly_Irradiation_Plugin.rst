Hourly_Irradiation_Plugin
=========================

The hourly irradiation model calculates the plane-of-array irradiation and resulting solar power density for three configurations:

- fixed tilt (no tracking),
- horizontal single-axis tracking,
- dual-axis tracking.


Equations
---------

If the module tilt is not specified, it defaults to the absolute latitude:

.. math::

   \beta = |\phi|

The solar declination angle is calculated as:

.. math::

   \delta_d
   =
   23.45^\circ
   \sin\left(
   \frac{2\pi}{365}(d - 81)
   \right)

The solar hour angle is:

.. math::

   \omega_h
   =
   15^\circ
   (t_h - 12)
   +
   \lambda

The solar altitude angle is:

.. math::

   \alpha_h
   =
   \arcsin
   \left(
   \sin(\delta_d)\sin(\phi)
   +
   \cos(\delta_d)\cos(\phi)\cos(\omega_h)
   \right)

The solar azimuth angle is:

.. math::

   \gamma_h
   =
   \arccos
   \left(
   \frac{
   \sin(\delta_d)\cos(\phi)
   -
   \cos(\delta_d)\sin(\phi)\cos(\omega_h)
   }{
   \cos(\alpha_h)
   }
   \right)
   \cdot
   \mathrm{sign}(\omega_h)

For the fixed-tilt configuration, the direct normal irradiance projection factor is:

.. math::

   f_{\mathrm{DNI},h}
   =
   \cos(\alpha_h)\sin(\beta)\cos(\gamma_{\mathrm{arr}} - \gamma_h)
   +
   \sin(\alpha_h)\cos(\beta)

Negative values are clipped to zero.

The direct plane-of-array irradiation is:

.. math::

   G_{\mathrm{dir},h}
   =
   G_{\mathrm{DNI},h}
   \cdot
   f_{\mathrm{DNI},h}

The diffuse plane-of-array irradiation is:

.. math::

   G_{\mathrm{diff},h}
   =
   G_{\mathrm{DHI},h}
   \cdot
   \frac{180^\circ - \beta}{180^\circ}

The total plane-of-array irradiation is:

.. math::

   G_{\mathrm{POA},h}
   =
   G_{\mathrm{dir},h}
   +
   G_{\mathrm{diff},h}

The cell temperature is estimated from the nominal operating temperature:

.. math::

   T_{\mathrm{cell},h}
   =
   T_{\mathrm{amb},h}
   +
   \left(
   T_{\mathrm{NOCT}} - 20^\circ\mathrm{C}
   \right)
   \frac{
   G_{\mathrm{POA},h}
   }{
   800
   }

The temperature derating factor is:

.. math::

   f_{\mathrm{temp},h}
   =
   1
   +
   \alpha_T
   \left(
   T_{\mathrm{cell},h} - 25^\circ\mathrm{C}
   \right)

The resulting hourly power density for the fixed-tilt configuration is:

.. math::

   P_h
   =
   f_{\mathrm{temp},h}
   \cdot
   f_{\mathrm{mismatch}}
   \cdot
   f_{\mathrm{dirt}}
   \cdot
   G_{\mathrm{POA},h}

This corresponds to:

``Hourly Irradiation > No tracking > Value``


Horizontal single-axis tracking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For horizontal single-axis tracking, the tracking azimuth is:

.. math::

   \gamma_{\mathrm{SAT},h}
   =
   \mathrm{sign}(\gamma_h)
   \frac{\pi}{2}

The tracking tilt angle is:

.. math::

   \beta_{\mathrm{SAT},h}
   =
   \arctan
   \left(
   \frac{
   \cos(\gamma_{\mathrm{SAT},h} - \gamma_h)
   }{
   \tan(\alpha_h)
   }
   \right)

The corresponding irradiation projection factor is:

.. math::

   f_{\mathrm{SAT},h}
   =
   \cos(\alpha_h)\sin(\beta_{\mathrm{SAT},h})
   \cos(\gamma_{\mathrm{SAT},h} - \gamma_h)
   +
   \sin(\alpha_h)\cos(\beta_{\mathrm{SAT},h})

Negative values are clipped to zero.

The single-axis tracking power density is:

.. math::

   P_{\mathrm{SAT},h}
   =
   f_{\mathrm{temp},h}
   \cdot
   f_{\mathrm{mismatch}}
   \cdot
   f_{\mathrm{dirt}}
   \cdot
   G_{\mathrm{POA,SAT},h}

This corresponds to:

``Hourly Irradiation > Horizontal single axis tracking > Value``


Dual-axis tracking
~~~~~~~~~~~~~~~~~~

For dual-axis tracking, the model assumes direct normal irradiance is always normal to the module surface:

.. math::

   P_{\mathrm{DAT},h}
   =
   G_{\mathrm{DNI},h}
   \cdot
   f_{\mathrm{temp},h}
   \cdot
   f_{\mathrm{mismatch}}
   \cdot
   f_{\mathrm{dirt}}



Yearly averaged power densities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The yearly averaged power densities are calculated as:

.. math::

   \overline{P}
   =
   \frac{
   \sum_h P_h
   }{
   365 \times 24
   }

.. math::

   \overline{P}_{\mathrm{SAT}}
   =
   \frac{
   \sum_h P_{\mathrm{SAT},h}
   }{
   365 \times 24
   }

.. math::

   \overline{P}_{\mathrm{DAT}}
   =
   \frac{
   \sum_h P_{\mathrm{DAT},h}
   }{
   365 \times 24
   }


Notation
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 45 30

   * - Symbol
     - Description
     - Dimension

   * - :math:`\phi`
     - Latitude
     - angle

   * - :math:`\lambda`
     - Longitude
     - angle

   * - :math:`\beta`
     - Module tilt
     - angle

   * - :math:`\gamma_{\mathrm{arr}}`
     - Array azimuth
     - angle

   * - :math:`T_{\mathrm{NOCT}}`
     - Nominal operating temperature
     - absolute temperature

   * - :math:`f_{\mathrm{mismatch}}`
     - Mismatch derating factor
     - dimensionless

   * - :math:`f_{\mathrm{dirt}}`
     - Dirt derating factor
     - dimensionless

   * - :math:`\alpha_T`
     - Temperature coefficient
     - 1 / temperature difference

   * - :math:`\delta_d`
     - Solar declination angle
     - angle

   * - :math:`\omega_h`
     - Solar hour angle
     - angle

   * - :math:`\alpha_h`
     - Solar altitude angle
     - angle

   * - :math:`\gamma_h`
     - Solar azimuth angle
     - angle

   * - :math:`G_{\mathrm{DNI},h}`
     - Direct normal irradiance
     - power / area

   * - :math:`G_{\mathrm{DHI},h}`
     - Diffuse horizontal irradiance
     - power / area

   * - :math:`G_{\mathrm{POA},h}`
     - Plane-of-array irradiance
     - power / area

   * - :math:`T_{\mathrm{amb},h}`
     - Ambient temperature
     - absolute temperature

   * - :math:`T_{\mathrm{cell},h}`
     - Solar cell temperature
     - absolute temperature

   * - :math:`f_{\mathrm{temp},h}`
     - Temperature derating factor
     - dimensionless

   * - :math:`P_h`
     - Hourly power density without tracking
     - power / area

   * - :math:`P_{\mathrm{SAT},h}`
     - Hourly power density with horizontal single-axis tracking
     - power / area

   * - :math:`P_{\mathrm{DAT},h}`
     - Hourly power density with dual-axis tracking
     - power / area

   * - :math:`\overline{P}`
     - Mean solar input without tracking
     - power / area

   * - :math:`\overline{P}_{\mathrm{SAT}}`
     - Mean solar input with horizontal single-axis tracking
     - power / area

   * - :math:`\overline{P}_{\mathrm{DAT}}`
     - Mean solar input with dual-axis tracking
     - power / area

Implementation
--------------

.. automodule:: pyH2A.Plugins.Hourly_Irradiation_Plugin
    :members: