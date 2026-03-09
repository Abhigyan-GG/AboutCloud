"""
PHASE 2 VERIFICATION - Storage & Ingestion Pipeline

Verifies that storage, validation, and ingestion work correctly.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.simulator.generator import MetricSimulator, SimulatorConfig
from backend.ingestion.validator import MetricValidator
from backend.ingestion.pipeline import IngestionPipeline
from backend.ingestion.collector import MetricCollector, SimulatorSource
from backend.storage.interface import configure_storage
from backend.storage.memory_storage import InMemoryStorage


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


def test_metric_validator() -> VerificationResult:
    """Test MetricValidator"""
    result = VerificationResult("MetricValidator")

    try:
        validator = MetricValidator()

        # Generate valid series
        sim = MetricSimulator()
        series = sim.generate(
            tenant_id="test",
            cluster_id="test",
            node_id="test",
            metric_name="cpu",
            num_points=100,
        )

        validation = validator.validate(series)

        if not validation.is_valid:
            result.fail(f"Valid series rejected: {validation.errors}")
            return result

        # Test invalid series (empty)
        from backend.analytics.types import MetricSeries
        try:
            bad_series = MetricSeries(
                tenant_id="",  # Empty tenant
                cluster_id="test",
                node_id="test",
                metric_name="test",
                timestamps=[],
                values=[],
            )
            result.fail("Should reject empty timestamp list")
            return result
        except ValueError:
            pass  # Expected

        result.success()
    except Exception as e:
        result.fail(str(e))

    return result


def test_storage_backend() -> VerificationResult:
    """Test InMemoryStorage"""
    result = VerificationResult("InMemoryStorage")

    try:
        storage = InMemoryStorage()

        # Generate and store
        sim = MetricSimulator()
        series = sim.generate(
            tenant_id="acme",
            cluster_id="prod",
            node_id="node-1",
            metric_name="cpu_usage",
            num_points=100,
        )

        storage.store_metric(series)

        # Retrieve
        retrieved = storage.get_metric_series(
            tenant_id="acme",
            cluster_id="prod",
            node_id="node-1",
            metric_name="cpu_usage",
            start_time=series.timestamps[0],
            end_time=series.timestamps[-1],
        )

        if len(retrieved.values) != len(series.values):
            result.fail(f"Length mismatch: stored {len(series.values)}, retrieved {len(retrieved.values)}")
            return result

        # Test non-existent metric
        try:
            missing = storage.get_metric_series(
                tenant_id="acme",
                cluster_id="prod",
                node_id="node-999",
                metric_name="missing",
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
            )
            result.fail("Should raise ValueError for missing metric")
            return result
        except ValueError:
            pass  # Expected

        # Test stats
        stats = storage.get_stats()
        if stats['total_metrics'] != 1:
            result.fail(f"Stats: expected 1 metric, got {stats['total_metrics']}")
            return result

        result.success()
    except Exception as e:
        result.fail(str(e))
        import traceback
        result.fail(traceback.format_exc())

    return result


def test_ingestion_pipeline() -> VerificationResult:
    """Test IngestionPipeline"""
    result = VerificationResult("IngestionPipeline")

    try:
        storage = InMemoryStorage()
        configure_storage(storage)

        collector = MetricCollector(SimulatorSource())
        validator = MetricValidator()
        pipeline = IngestionPipeline(collector, validator, storage)

        # Ingest single metric
        series, stats = pipeline.ingest_metric(
            tenant_id="test",
            cluster_id="test",
            node_id="test",
            metric_name="cpu",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
        )

        if stats.total_valid != 1:
            result.fail(f"Expected 1 valid metric, got {stats.total_valid}")
            return result

        if stats.success_rate() != 1.0:
            result.fail(f"Expected 100% success rate, got {stats.success_rate()}")
            return result

        result.success()
    except Exception as e:
        result.fail(str(e))
        import traceback
        result.fail(traceback.format_exc())

    return result


def test_multi_tenant_isolation() -> VerificationResult:
    """Test multi-tenant isolation"""
    result = VerificationResult("Multi-Tenant Isolation")

    try:
        storage = InMemoryStorage()

        sim = MetricSimulator()

        # Store for tenant A
        series_a = sim.generate(
            tenant_id="tenant-a",
            cluster_id="cluster-1",
            node_id="node-1",
            metric_name="cpu",
            num_points=10,
        )
        storage.store_metric(series_a)

        # Store for tenant B
        series_b = sim.generate(
            tenant_id="tenant-b",
            cluster_id="cluster-1",
            node_id="node-1",
            metric_name="cpu",
            num_points=10,
        )
        storage.store_metric(series_b)

        # Retrieve tenant A data
        retrieved_a = storage.get_metric_series(
            tenant_id="tenant-a",
            cluster_id="cluster-1",
            node_id="node-1",
            metric_name="cpu",
            start_time=series_a.timestamps[0],
            end_time=series_a.timestamps[-1],
        )

        # Verify isolation
        if retrieved_a.tenant_id != "tenant-a":
            result.fail("Tenant isolation broken")
            return result

        result.success()
    except Exception as e:
        result.fail(str(e))

    return result


def main():
    """Run Phase 2 verification"""
    print("\n" + "=" * 80)
    print("PHASE 2: STORAGE & INGESTION PIPELINE VERIFICATION".center(80))
    print("=" * 80 + "\n")

    tests = [
        test_metric_validator(),
        test_storage_backend(),
        test_ingestion_pipeline(),
        test_multi_tenant_isolation(),
    ]

    for test in tests:
        print(test)

    all_passed = all(t.passed for t in tests)

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ PHASE 2 VERIFICATION COMPLETE - ALL TESTS PASSED".center(80))
        print("=" * 80 + "\n")
        return 0
    else:
        print("❌ PHASE 2 VERIFICATION FAILED".center(80))
        print("=" * 80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)