"""
PHASE 1 VERIFICATION - Data Types & Contracts

Verifies that core data structures work correctly.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.analytics.types import MetricSeries, MetricPoint, AnomalyResult, AggregatedAnomalyScore


class VerificationResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.errors = []

    def fail(self, error: str):
        self.errors.append(error)

    def success(self):
        self.passed = True

    def __str__(self):
        if self.passed:
            return f"✅ {self.name}"
        else:
            return f"❌ {self.name}\n   " + "\n   ".join(self.errors)


def test_metric_point() -> VerificationResult:
    """Test MetricPoint creation"""
    result = VerificationResult("MetricPoint Creation")

    try:
        now = datetime.utcnow()
        point = MetricPoint(timestamp=now, value=42.5)

        if point.timestamp != now:
            result.fail("Timestamp mismatch")
            return result

        if point.value != 42.5:
            result.fail("Value mismatch")
            return result

        result.success()
    except Exception as e:
        result.fail(str(e))

    return result


def test_metric_series() -> VerificationResult:
    """Test MetricSeries creation and validation"""
    result = VerificationResult("MetricSeries Creation & Validation")

    try:
        now = datetime.utcnow()
        timestamps = [now + timedelta(minutes=i) for i in range(10)]
        values = [float(50 + i) for i in range(10)]

        series = MetricSeries(
            tenant_id="test-tenant",
            cluster_id="test-cluster",
            node_id="node-001",
            metric_name="cpu_usage",
            timestamps=timestamps,
            values=values,
        )

        if series.length != 10:
            result.fail(f"Length should be 10, got {series.length}")
            return result

        if series.time_range != (timestamps[0], timestamps[-1]):
            result.fail("Time range mismatch")
            return result

        # Test validation: mismatched lengths
        try:
            bad_series = MetricSeries(
                tenant_id="test",
                cluster_id="test",
                node_id="test",
                metric_name="test",
                timestamps=timestamps,
                values=values[:-1],  # One less value
            )
            result.fail("Should reject mismatched lengths")
            return result
        except ValueError:
            pass  # Expected

        result.success()
    except Exception as e:
        result.fail(str(e))

    return result


def test_anomaly_result() -> VerificationResult:
    """Test AnomalyResult creation and validation"""
    result = VerificationResult("AnomalyResult Creation & Validation")

    try:
        now = datetime.utcnow()

        anomaly = AnomalyResult(
            tenant_id="test-tenant",
            cluster_id="test-cluster",
            node_id="node-001",
            metric_name="cpu_usage",
            window_start=now,
            window_end=now + timedelta(hours=1),
            anomaly_score=0.75,
            anomaly_label="spike",
        )

        if anomaly.anomaly_score != 0.75:
            result.fail("Score mismatch")
            return result

        if anomaly.anomaly_label != "spike":
            result.fail("Label mismatch")
            return result

        if not anomaly.is_anomaly:
            result.fail("is_anomaly should be True for spike")
            return result

        # Test score validation
        try:
            bad_anomaly = AnomalyResult(
                tenant_id="test",
                cluster_id="test",
                node_id="test",
                metric_name="test",
                window_start=now,
                window_end=now,
                anomaly_score=1.5,  # Out of range
                anomaly_label="spike",
            )
            result.fail("Should reject score > 1")
            return result
        except ValueError:
            pass  # Expected

        # Test label validation
        try:
            bad_anomaly = AnomalyResult(
                tenant_id="test",
                cluster_id="test",
                node_id="test",
                metric_name="test",
                window_start=now,
                window_end=now,
                anomaly_score=0.5,
                anomaly_label="invalid",
            )
            result.fail("Should reject invalid label")
            return result
        except ValueError:
            pass  # Expected

        result.success()
    except Exception as e:
        result.fail(str(e))

    return result


def test_aggregated_score() -> VerificationResult:
    """Test AggregatedAnomalyScore"""
    result = VerificationResult("AggregatedAnomalyScore Creation")

    try:
        score = AggregatedAnomalyScore(
            tenant_id="test-tenant",
            aggregate_score=0.6,
            cluster_id="test-cluster",
            node_id="node-001",
            num_metrics_analyzed=5,
            num_anomalies_detected=2,
        )

        if score.aggregate_score != 0.6:
            result.fail("Score mismatch")
            return result

        if score.num_metrics_analyzed != 5:
            result.fail("Metrics analyzed mismatch")
            return result

        result.success()
    except Exception as e:
        result.fail(str(e))

    return result


def main():
    """Run Phase 1 verification"""
    print("\n" + "=" * 80)
    print("PHASE 1: CORE DATA TYPES & CONTRACTS VERIFICATION".center(80))
    print("=" * 80 + "\n")

    tests = [
        test_metric_point(),
        test_metric_series(),
        test_anomaly_result(),
        test_aggregated_score(),
    ]

    for test in tests:
        print(test)

    all_passed = all(t.passed for t in tests)

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ PHASE 1 VERIFICATION COMPLETE - ALL TESTS PASSED".center(80))
        print("=" * 80 + "\n")
        return 0
    else:
        print("❌ PHASE 1 VERIFICATION FAILED".center(80))
        print("=" * 80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)