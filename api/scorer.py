"""
Core scoring engine — loads model artifacts and scores applicants.

Scoring pipeline:
  Raw features → bin assignment → WOE lookup → LR log-odds → score transformation → risk grade
"""
import os
import sys
import numpy as np
import joblib
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'artifacts')

# Module-level cache (loaded once at import)
_bin_boundaries = None
_woe_maps = None
_lr_model = None
_params = None
_feature_order = None
_risk_grades = None
_metrics = None
_loaded = False

FEATURE_KEYS = ['fico_score', 'inq_6m', 'dti', 'revol_util', 'delinq_2yrs', 'credit_age', 'annual_inc']


def load_artifacts():
    """Load all model artifacts. Called once at startup."""
    global _bin_boundaries, _woe_maps, _lr_model, _params, _feature_order, _risk_grades, _metrics, _loaded

    if _loaded:
        return True

    try:
        _bin_boundaries = joblib.load(os.path.join(ARTIFACTS_DIR, 'bin_boundaries.joblib'))
        _woe_maps = joblib.load(os.path.join(ARTIFACTS_DIR, 'woe_maps.joblib'))
        _lr_model = joblib.load(os.path.join(ARTIFACTS_DIR, 'lr_model.joblib'))
        _params = joblib.load(os.path.join(ARTIFACTS_DIR, 'scorecard_params.joblib'))
        _feature_order = joblib.load(os.path.join(ARTIFACTS_DIR, 'feature_order.joblib'))
        _risk_grades = joblib.load(os.path.join(ARTIFACTS_DIR, 'risk_grades.joblib'))

        import json
        with open(os.path.join(ARTIFACTS_DIR, 'model_metrics.json'), 'r', encoding='utf-8') as f:
            _metrics = json.load(f)

        _loaded = True
        return True
    except Exception as e:
        print(f"[Scorer] Failed to load artifacts: {e}")
        return False


def get_artifacts_status():
    """Return which artifacts are available"""
    files = [
        'bin_boundaries.joblib', 'woe_maps.joblib', 'lr_model.joblib',
        'scorecard_params.joblib', 'feature_order.joblib', 'risk_grades.joblib',
        'model_metrics.json'
    ]
    available = [f for f in files if os.path.exists(os.path.join(ARTIFACTS_DIR, f))]
    return available


def raw_to_bin(value, boundaries):
    """
    Assign a raw feature value to a bin label using boundary edges.

    boundaries = [-inf, edge1, edge2, ..., inf]
    np.digitize with internal edges gives bin index, then label = f'Bin_{idx}'
    """
    if boundaries is None or len(boundaries) < 2:
        return 'Bin_0'

    if np.isnan(value):
        return 'Missing'

    # Use internal edges (exclude -inf at [0] and inf at [-1])
    internal_edges = boundaries[1:-1]
    if len(internal_edges) == 0:
        return 'Bin_0'

    bin_idx = int(np.digitize(value, internal_edges))
    return f'Bin_{bin_idx}'


def score_applicant(features: dict) -> dict:
    """
    Score a single applicant.

    Args:
        features: dict with keys matching FEATURE_KEYS

    Returns:
        dict with score, grade, points breakdown, etc.
    """
    if not _loaded:
        load_artifacts()

    factor = _params['factor']
    intercept = _params['intercept']
    offset = _params['offset']
    coefficients = _params['coefficients']
    base_points = _params['base_points']

    total_score = base_points
    feature_points = {}

    for feat in FEATURE_KEYS:
        raw_val = features.get(feat)
        if raw_val is None:
            woe_val = 0.0
        else:
            boundaries = _bin_boundaries.get(feat)
            woe_map = _woe_maps.get(feat, {})
            bin_label = raw_to_bin(raw_val, boundaries)
            woe_val = woe_map.get(bin_label, 0.0)

        woe_feat_name = feat + '_woe'
        coef = coefficients.get(woe_feat_name, 0)
        pts = -factor * coef * woe_val
        feature_points[feat] = round(float(pts), 2)
        total_score += pts

    score = int(round(np.clip(total_score, 300, 850)))

    # Map to risk grade
    grade = 'E'
    grade_desc = 'High Risk'
    expected_dr = 0.30
    for g, (lo, hi, desc, dr) in _risk_grades.items():
        if lo <= score < hi or (g == 'A' and score >= hi):
            grade = g
            grade_desc = desc
            expected_dr = dr
            break

    # Probability of bad from LR model
    woe_values = []
    for feat in FEATURE_KEYS:
        raw_val = features.get(feat)
        if raw_val is None:
            woe_values.append(0.0)
        else:
            boundaries = _bin_boundaries.get(feat)
            woe_map = _woe_maps.get(feat, {})
            bin_label = raw_to_bin(raw_val, boundaries)
            woe_values.append(woe_map.get(bin_label, 0.0))

    log_odds_bad = intercept + sum(c * w for c, w in zip(
        [coefficients.get(f + '_woe', 0) for f in FEATURE_KEYS], woe_values
    ))
    prob_bad = round(float(1 / (1 + np.exp(-log_odds_bad))), 4)

    tz = timezone(timedelta(hours=8))
    return {
        'score': score,
        'grade': grade,
        'grade_description': grade_desc,
        'expected_default_rate': round(expected_dr, 4),
        'probability_bad': prob_bad,
        'points_breakdown': {
            'base_points': round(base_points, 2),
            'features': feature_points,
            'total': round(float(total_score), 2),
        },
        'model_version': _params.get('model_version', 'v1.0'),
        'timestamp': datetime.now(tz).strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    }


# Auto-load on import
load_artifacts()
