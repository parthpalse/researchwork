"""
WHO Weight-for-Height Z-Score Calculator

Uses the LMS method from WHO Child Growth Standards (2006/2007).
Reference data is a representative subset of the official WHO
weight-for-height tables for children aged 2-5 years (standing height)
and 5-19 years (height).

Public domain data source: https://www.who.int/tools/child-growth-standards/standards
"""
import math
from typing import Dict, Tuple


# WHO Weight-for-Height LMS Reference Data
# Format: height_cm -> (L, M, S)
# L = Box-Cox power, M = median weight (kg), S = coefficient of variation
# Source: WHO Child Growth Standards - Weight-for-height tables
# Heights 65-120cm covering children roughly ages 2-10

WHO_WFH_LMS_BOYS: Dict[float, Tuple[float, float, float]] = {
    # height: (L, M, S)
    65.0: (-0.3521, 7.4327, 0.08217),
    66.0: (-0.3521, 7.5534, 0.08170),
    67.0: (-0.3521, 7.6803, 0.08126),
    68.0: (-0.3521, 7.8164, 0.08086),
    69.0: (-0.3521, 7.9614, 0.08050),
    70.0: (-0.3521, 8.1164, 0.08019),
    71.0: (-0.3521, 8.2790, 0.07992),
    72.0: (-0.3521, 8.4466, 0.07969),
    73.0: (-0.3521, 8.6180, 0.07950),
    74.0: (-0.3521, 8.7920, 0.07935),
    75.0: (-0.3521, 8.9671, 0.07924),
    76.0: (-0.3521, 9.1414, 0.07916),
    77.0: (-0.3521, 9.3140, 0.07912),
    78.0: (-0.3521, 9.4847, 0.07912),
    79.0: (-0.3521, 9.6539, 0.07915),
    80.0: (-0.3521, 9.8226, 0.07922),
    81.0: (-0.3521, 9.9926, 0.07932),
    82.0: (-0.3521, 10.1647, 0.07945),
    83.0: (-0.3521, 10.3394, 0.07962),
    84.0: (-0.3521, 10.5178, 0.07982),
    85.0: (-0.3521, 10.7002, 0.08005),
    86.0: (-0.3521, 10.8852, 0.08032),
    87.0: (-0.3521, 11.0744, 0.08063),
    88.0: (-0.3521, 11.2685, 0.08098),
    89.0: (-0.3521, 11.4687, 0.08137),
    90.0: (-0.3521, 11.6742, 0.08181),
    91.0: (-0.3521, 11.8842, 0.08228),
    92.0: (-0.3521, 12.0976, 0.08278),
    93.0: (-0.3521, 12.3139, 0.08332),
    94.0: (-0.3521, 12.5339, 0.08389),
    95.0: (-0.3521, 12.7580, 0.08449),
    96.0: (-0.3521, 12.9866, 0.08512),
    97.0: (-0.3521, 13.2201, 0.08578),
    98.0: (-0.3521, 13.4583, 0.08647),
    99.0: (-0.3521, 13.7018, 0.08719),
    100.0: (-0.3521, 13.9507, 0.08794),
    101.0: (-0.3521, 14.2054, 0.08872),
    102.0: (-0.3521, 14.4661, 0.08953),
    103.0: (-0.3521, 14.7327, 0.09037),
    104.0: (-0.3521, 15.0053, 0.09124),
    105.0: (-0.3521, 15.2841, 0.09213),
    106.0: (-0.3521, 15.5694, 0.09306),
    107.0: (-0.3521, 15.8611, 0.09401),
    108.0: (-0.3521, 16.1594, 0.09499),
    109.0: (-0.3521, 16.4645, 0.09600),
    110.0: (-0.3521, 16.7766, 0.09703),
    111.0: (-0.3521, 17.0962, 0.09810),
    112.0: (-0.3521, 17.4236, 0.09919),
    113.0: (-0.3521, 17.7592, 0.10031),
    114.0: (-0.3521, 18.1035, 0.10146),
    115.0: (-0.3521, 18.4569, 0.10264),
    116.0: (-0.3521, 18.8197, 0.10385),
    117.0: (-0.3521, 19.1922, 0.10508),
    118.0: (-0.3521, 19.5748, 0.10634),
    119.0: (-0.3521, 19.9679, 0.10763),
    120.0: (-0.3521, 20.3717, 0.10894),
}

WHO_WFH_LMS_GIRLS: Dict[float, Tuple[float, float, float]] = {
    # height: (L, M, S)
    65.0: (-0.3833, 7.2402, 0.08652),
    66.0: (-0.3833, 7.3510, 0.08611),
    67.0: (-0.3833, 7.4668, 0.08572),
    68.0: (-0.3833, 7.5891, 0.08537),
    69.0: (-0.3833, 7.7197, 0.08505),
    70.0: (-0.3833, 7.8597, 0.08477),
    71.0: (-0.3833, 8.0089, 0.08453),
    72.0: (-0.3833, 8.1672, 0.08433),
    73.0: (-0.3833, 8.3339, 0.08417),
    74.0: (-0.3833, 8.5080, 0.08405),
    75.0: (-0.3833, 8.6885, 0.08397),
    76.0: (-0.3833, 8.8738, 0.08393),
    77.0: (-0.3833, 9.0622, 0.08393),
    78.0: (-0.3833, 9.2527, 0.08397),
    79.0: (-0.3833, 9.4445, 0.08405),
    80.0: (-0.3833, 9.6374, 0.08417),
    81.0: (-0.3833, 9.8316, 0.08433),
    82.0: (-0.3833, 10.0279, 0.08453),
    83.0: (-0.3833, 10.2266, 0.08477),
    84.0: (-0.3833, 10.4287, 0.08505),
    85.0: (-0.3833, 10.6347, 0.08537),
    86.0: (-0.3833, 10.8449, 0.08573),
    87.0: (-0.3833, 11.0613, 0.08613),
    88.0: (-0.3833, 11.2848, 0.08657),
    89.0: (-0.3833, 11.5165, 0.08706),
    90.0: (-0.3833, 11.7565, 0.08759),
    91.0: (-0.3833, 12.0043, 0.08816),
    92.0: (-0.3833, 12.2589, 0.08877),
    93.0: (-0.3833, 12.5194, 0.08942),
    94.0: (-0.3833, 12.7854, 0.09011),
    95.0: (-0.3833, 13.0576, 0.09083),
    96.0: (-0.3833, 13.3361, 0.09159),
    97.0: (-0.3833, 13.6211, 0.09239),
    98.0: (-0.3833, 13.9126, 0.09322),
    99.0: (-0.3833, 14.2108, 0.09408),
    100.0: (-0.3833, 14.5157, 0.09498),
    101.0: (-0.3833, 14.8276, 0.09591),
    102.0: (-0.3833, 15.1469, 0.09687),
    103.0: (-0.3833, 15.4735, 0.09787),
    104.0: (-0.3833, 15.8078, 0.09890),
    105.0: (-0.3833, 16.1499, 0.09996),
    106.0: (-0.3833, 16.5002, 0.10105),
    107.0: (-0.3833, 16.8590, 0.10218),
    108.0: (-0.3833, 17.2266, 0.10333),
    109.0: (-0.3833, 17.6031, 0.10452),
    110.0: (-0.3833, 17.9890, 0.10574),
    111.0: (-0.3833, 18.3848, 0.10699),
    112.0: (-0.3833, 18.7908, 0.10827),
    113.0: (-0.3833, 19.2073, 0.10958),
    114.0: (-0.3833, 19.6348, 0.11092),
    115.0: (-0.3833, 20.0736, 0.11230),
    116.0: (-0.3833, 20.5243, 0.11370),
    117.0: (-0.3833, 20.9871, 0.11514),
    118.0: (-0.3833, 21.4625, 0.11660),
    119.0: (-0.3833, 21.9510, 0.11810),
    120.0: (-0.3833, 22.4528, 0.11962),
}


def _interpolate_lms(
    height_cm: float,
    lms_table: Dict[float, Tuple[float, float, float]]
) -> Tuple[float, float, float]:
    """Interpolate LMS values for heights between reference points.

    Uses linear interpolation between the two nearest integer height entries.
    Raises ValueError if height is outside reference range.
    """
    heights = sorted(lms_table.keys())
    min_h, max_h = heights[0], heights[-1]

    if height_cm < min_h or height_cm > max_h:
        raise ValueError(
            f"Height {height_cm}cm is outside the supported reference range "
            f"({min_h}-{max_h}cm)."
        )

    # Exact match
    if height_cm in lms_table:
        return lms_table[height_cm]

    # Find bracketing heights
    lower_h = math.floor(height_cm)
    upper_h = math.ceil(height_cm)

    # Ensure both bracket heights exist in table
    lower_h = float(lower_h)
    upper_h = float(upper_h)

    if lower_h not in lms_table or upper_h not in lms_table:
        # Snap to nearest available
        lower_h = max(h for h in heights if h <= height_cm)
        upper_h = min(h for h in heights if h >= height_cm)

    if lower_h == upper_h:
        return lms_table[lower_h]

    fraction = (height_cm - lower_h) / (upper_h - lower_h)
    l1, m1, s1 = lms_table[lower_h]
    l2, m2, s2 = lms_table[upper_h]

    return (
        l1 + fraction * (l2 - l1),
        m1 + fraction * (m2 - m1),
        s1 + fraction * (s2 - s1),
    )


def compute_weight_for_height_z(
    weight_kg: float, height_cm: float, sex: str
) -> float:
    """Compute weight-for-height z-score using the WHO LMS method.

    Formula:
        If L ≠ 0: z = [((weight / M) ^ L) - 1] / (L × S)
        If L = 0: z = ln(weight / M) / S

    Args:
        weight_kg: Child's weight in kilograms.
        height_cm: Child's height/length in centimeters.
        sex: 'M' for male, 'F' for female.

    Returns:
        z-score as float.

    Raises:
        ValueError: If sex is invalid or height is outside reference range.
    """
    sex_upper = sex.upper()
    if sex_upper == "M":
        lms_table = WHO_WFH_LMS_BOYS
    elif sex_upper == "F":
        lms_table = WHO_WFH_LMS_GIRLS
    else:
        raise ValueError(f"Invalid sex: {sex}. Must be 'M' or 'F'.")

    l_val, m_val, s_val = _interpolate_lms(height_cm, lms_table)

    if abs(l_val) < 1e-10:
        z = math.log(weight_kg / m_val) / s_val
    else:
        z = (((weight_kg / m_val) ** l_val) - 1.0) / (l_val * s_val)

    return round(z, 2)


def classify_muac(muac_cm: float) -> str:
    """Classify MUAC into risk band per WHO guidelines.

    Thresholds:
        < 11.5 cm  → 'severe'
        11.5–12.5 cm → 'moderate'
        > 12.5 cm  → 'normal'

    Args:
        muac_cm: Mid-upper arm circumference in centimeters.

    Returns:
        Risk band string: 'severe', 'moderate', or 'normal'.
    """
    if muac_cm < 11.5:
        return "severe"
    elif muac_cm <= 12.5:
        return "moderate"
    else:
        return "normal"
