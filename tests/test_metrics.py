import copy
import importlib.util
from pathlib import Path
import unittest

SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('metrics', SKILL / 'scripts/review_metrics.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture():
    return {
        'work_id': 'fixture-only', 'account': 'fixture-account', 'content_type': 'video',
        'published_at': '2026-10-01T10:00:00+08:00',
        'captured_at': '2026-10-02T10:05:00+08:00',
        'data_as_of': '2026-10-02T10:00:00+08:00',
        'duration_seconds': 100, 'traffic_basis': 'organic', 'measurement_scope': 'lifetime',
        'metrics': {
            'views': {'value': 1000, 'unit': 'count', 'exact': True, 'raw_name': 'views', 'source': 'fixture'},
            'avg_watch_seconds': {'value': 20, 'unit': 'seconds', 'raw_name': 'average seconds', 'source': 'fixture'},
            'bounce_2s_pct': {'value': 30, 'unit': 'percent', 'raw_name': '2 second bounce', 'source': 'fixture'},
        },
        'leads': {'confirmed_wechat': 5, 'qualified_wechat': 3, 'qualified_consultations': 2, 'paid_enrollments': 1, 'source': 'fixture'},
        'attribution': {'basis': 'confirmed_work', 'coverage': 'complete', 'same_cohort': True, 'view_window_aligned': True, 'window_mature': True},
    }


class MetricsTests(unittest.TestCase):
    def test_known_yield(self):
        r=mod.review_one(fixture())
        self.assertTrue(r['valid'])
        self.assertEqual(r['derived']['qualified_wechat_per_1000_views'], 3)
        self.assertEqual(r['derived']['avg_watch_pct_derived'], 20)
        self.assertEqual(r['metric_age_hours'], 24)

    def test_missing_is_not_zero(self):
        d=fixture(); d['leads']['qualified_wechat']=None
        r=mod.review_one(d)
        self.assertIsNone(r['lead_counts']['qualified_wechat'])
        self.assertIsNone(r['derived']['qualified_wechat_per_1000_views'])

    def test_real_zero_remains_zero(self):
        d=fixture(); d['leads'].update({k:0 for k in mod.LEADS})
        self.assertEqual(mod.review_one(d)['derived']['qualified_wechat_per_1000_views'], 0)

    def test_rounded_views_no_ratio(self):
        d=fixture(); d['metrics']['views']['exact']=False
        r=mod.review_one(d)
        self.assertIsNone(r['derived']['qualified_wechat_per_1000_views'])
        self.assertFalse(r['metric_context']['views']['exact'])
        self.assertEqual(r['metric_context']['views']['source'], 'fixture')

    def test_partial_attribution_no_ratio(self):
        d=fixture(); d['attribution']['coverage']='partial'
        self.assertIsNone(mod.review_one(d)['derived']['qualified_wechat_per_1000_views'])

    def test_no_three_second_interpolation(self):
        self.assertIsNone(mod.review_one(fixture())['observed_metrics']['retention_3s_pct'])

    def test_units_and_values_rejected(self):
        d=fixture(); d['metrics']['avg_watch_seconds']['unit']='percent'
        self.assertFalse(mod.review_one(d)['valid'])
        d=fixture(); d['metrics']['bounce_2s_pct']['value']=101
        self.assertFalse(mod.review_one(d)['valid'])

    def test_timezone_required(self):
        d=fixture(); d['captured_at']='2026-10-02T10:05:00'
        self.assertFalse(mod.review_one(d)['valid'])

    def test_cutoff_and_account_barriers(self):
        a=fixture(); b=copy.deepcopy(a); b['work_id']='other'; b['data_as_of']=None; b['account']='other'
        reasons=mod.review([a,b])['comparisons'][0]['basic_comparison_barriers']
        self.assertIn('account differs or unknown', reasons)
        self.assertIn('metric ages differ or unknown', reasons)

    def test_funnel_inversion(self):
        d=fixture(); d['leads']['qualified_wechat']=8
        self.assertFalse(mod.review_one(d)['valid'])

    def test_buyer_without_consultation(self):
        d=fixture(); d['leads']['qualified_consultations']=0
        self.assertTrue(mod.review_one(d)['valid'])

    def test_replay_not_clamped(self):
        d=fixture(); d['metrics']['avg_watch_seconds']['value']=120
        self.assertEqual(mod.review_one(d)['derived']['avg_watch_pct_derived'], 120)

    def test_invalid_container(self):
        self.assertFalse(mod.review(['not an object'])['valid'])
        self.assertFalse(mod.review([])['valid'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
