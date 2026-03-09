"""
PHASE 3 VERIFICATION - STRICT VERSION

Tests complete end-to-end anomaly detection with proper error handling.
Returns non-zero exit code on ANY failure.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.simulator.generator import MetricSimulator, SimulatorConfig, AnomalyInjector
from backend.ingestion.collector import MetricCollector, SimulatorSource
from backend.ingestion.validator import MetricValidator
from backend.storage.interface import configure_storage
from backend.storage.memory_storage import InMemoryStorage
from backend.analytics.merlion_engine import MerlionAnomalyEngine
from backend.analytics.detection_pipeline import AnomalyDetectionPipeline
from backend.analytics.explain import ExplanationClassifier


class VerificationResult:
    """Track verification results"""

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


def step_1_simulator() -> VerificationResult:
    """STEP 1: Generate metrics with anomalies"""
    result = VerificationResult("STEP 1: Metric Generation")

    try:
        config = SimulatorConfig(
            baseline_mean=60.0,
            baseline_std=10.0,
            inject_spikes=True,
            spike_probability=0.05,
        )

        sim = MetricSimulator(config)
        series = sim.generate(
            tenant_id="acme-corp",
            cluster_id="prod-cluster",
            node_id="node-001",
            metric_name="cpu_usage",
            num_points=500,
        )

        # Inject spike
        series, spike_info = AnomalyInjector.inject_spike(
            series, spike_index=250, magnitude=3.0, duration=5
        )

        # Validate
        if len(series.values) != 500:
            result.fail(f"Expected 500 points, got {len(series.values)}")
            return result

        if series.metric_name != "cpu_usage":
            result.fail(f"Metric name mismatch")
            return result

        result.success()
        return series, result

    except Exception as e:
        result.fail(str(e))
        return None, result


def step_2_ingestion(series) -> tuple:
    """STEP 2: Validate and store metrics"""
    result = VerificationResult("STEP 2: Ingestion & Validation")

    try:
        # Validate
        validator = MetricValidator()
        validation = validator.validate(series)

        if not validation.is_valid:
            for error in validation.errors:
                result.fail(error)
            return None, result

        # Store
        storage = InMemoryStorage()
        configure_storage(storage)
        storage.store_metric(series)

        # Verify stored
        try:
            retrieved = storage.get_metric_series(
                tenant_id=series.tenant_id,
                cluster_id=series.cluster_id,
                node_id=series.node_id,
                metric_name=series.metric_name,
                start_time=series.timestamps[0],
                end_time=series.timestamps[-1],
            )
            if len(retrieved.values) != len(series.values):
                result.fail(f"Storage mismatch: stored {len(series.values)}, retrieved {len(retrieved.values)}")
                return None, result
        except Exception as e:
            result.fail(f"Retrieval failed: {e}")
            return None, result

        result.success()
        return storage, result

    except Exception as e:
        result.fail(str(e))
        return None, result


def step_3_detection(storage, series) -> tuple:
    """STEP 3: Run anomaly detection"""
    result = VerificationResult("STEP 3: Anomaly Detection")

    try:
        engine = MerlionAnomalyEngine(config={
            'contamination': 0.05,
            'window_size': 100,
        })

        results = engine.detect(series)

        if not isinstance(results, list):
            result.fail(f"Detection should return list, got {type(results)}")
            return None, result

        if len(results) == 0:
            result.fail("No anomalies detected (expected at least some)")
            return None, result

        # Validate each result
        for i, r in enumerate(results):
            if not hasattr(r, 'anomaly_score'):
                result.fail(f"Result {i} missing anomaly_score")
                return None, result
            if not (0 <= r.anomaly_score <= 1):
                result.fail(f"Result {i} score out of range: {r.anomaly_score}")
                return None, result
            if r.anomaly_label not in ['spike', 'trend', 'seasonal', 'normal']:
                result.fail(f"Result {i} invalid label: {r.anomaly_label}")
                return None, result

        result.success()
        return results, result

    except Exception as e:
        result.fail(str(e))
        import traceback
        result.fail(traceback.format_exc())
        return None, result


def step_4_storage_query(storage, results) -> tuple:
    """STEP 4: Store and query anomalies"""
    result = VerificationResult("STEP 4: Storage & Query")

    try:
        # Store results
        for r in results:
            storage.store_anomaly_result(
                tenant_id=r.tenant_id,
                cluster_id=r.cluster_id,
                node_id=r.node_id,
                metric_name=r.metric_name,
                result=r,
            )

        # Query back
        queried = storage.query_anomalies(
            tenant_id="acme-corp",
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1),
            min_score=0.0,
        )

        if not isinstance(queried, list):
            result.fail(f"Query should return list, got {type(queried)}")
            return None, result

        if len(queried) == 0:
            result.fail("Query returned no anomalies (expected some)")
            return None, result

        # Validate query result format
        for q in queried:
            required = ['tenant_id', 'anomaly_score', 'window_start', 'window_end']
            for field in required:
                if field not in q:
                    result.fail(f"Query result missing {field}")
                    return None, result

        result.success()
        return queried, result

    except Exception as e:
        result.fail(str(e))
        import traceback
        result.fail(traceback.format_exc())
        return None, result


def step_5_pipeline(storage, series) -> tuple:
    """STEP 5: End-to-end pipeline"""
    result = VerificationResult("STEP 5: End-to-End Pipeline")

    try:
        engine = MerlionAnomalyEngine()
        pipeline = AnomalyDetectionPipeline(
            engine=engine,
            classifier=ExplanationClassifier(),
            storage_backend=storage,
        )

        results, explanations, stats = pipeline.detect_metric(series)

        if stats.has_critical_errors():
            for error in stats.errors:
                result.fail(error)
            return None, result

        if len(results) == 0:
            result.fail("Pipeline returned no anomalies")
            return None, result

        result.success()
        return results, result

    except Exception as e:
        result.fail(str(e))
        import traceback
        result.fail(traceback.format_exc())
        return None, result


def step_6_integration() -> VerificationResult:
    """STEP 6: Full integration test"""
    result = VerificationResult("STEP 6: Full Integration Test")

    try:
        # Fresh setup
        storage = InMemoryStorage()
        configure_storage(storage)

        # Generate
        sim = MetricSimulator(SimulatorConfig(baseline_mean=50, inject_spikes=True))
        series = sim.generate(
            tenant_id="test-tenant",
            cluster_id="test-cluster",
            node_id="test-node",
            metric_name="memory_used",
            num_points=300,
        )

        # Store
        storage.store_metric(series)

        # Detect
        engine = MerlionAnomalyEngine()
        pipeline = AnomalyDetectionPipeline(engine=engine, storage_backend=storage)
        results, explanations, stats = pipeline.detect_metric(series)

        if stats.has_critical_errors():
            for error in stats.errors:
                result.fail(error)
            return result

        # Verify output format
        for r in results:
            if not hasattr(r, 'explanation') or r.explanation is None:
                result.fail(f"Result missing explanation")
                return result

        result.success()
        return result

    except Exception as e:
        result.fail(str(e))
        import traceback
        result.fail(traceback.format_exc())
        return result


def main():
    """Run all verification steps"""
    print("\n" + "=" * 80)
    print("PHASE 3: REAL ANOMALY DETECTION - STRICT VERIFICATION".center(80))
    print("=" * 80 + "\n")

    all_passed = True

    # Step 1
    series, r1 = step_1_simulator()
    print(r1)
    if not r1.passed:
        all_passed = False

    # Step 2
    if series:
        storage, r2 = step_2_ingestion(series)
        print(r2)
        if not r2.passed:
            all_passed = False
    else:
        all_passed = False

    # Step 3
    if storage and series:
        results, r3 = step_3_detection(storage, series)
        print(r3)
        if not r3.passed:
            all_passed = False
    else:
        all_passed = False

    # Step 4
    if storage and results:
        queried, r4 = step_4_storage_query(storage, results)
        print(r4)
        if not r4.passed:
            all_passed = False
    else:
        all_passed = False

    # Step 5
    if storage and series:
        _, r5 = step_5_pipeline(storage, series)
        print(r5)
        if not r5.passed:
            all_passed = False
    else:
        all_passed = False

    # Step 6
    r6 = step_6_integration()
    print(r6)
    if not r6.passed:
        all_passed = False

    # Final result
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ PHASE 3 VERIFICATION COMPLETE - ALL TESTS PASSED".center(80))
        print("=" * 80)
        return 0
    else:
        print("❌ PHASE 3 VERIFICATION FAILED - SEE ERRORS ABOVE".center(80))
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)