"""
PHASE 1 VERIFICATION SCRIPT

This script validates that all analytics modules can be imported
and their contracts are correctly defined.

Run this to verify Phase 1 completion.
"""

from datetime import datetime, timedelta

def verify_imports():
    """Verify all imports work"""
    print("=" * 60)
    print("PHASE 1 VERIFICATION - IMPORTS")
    print("=" * 60)
    
    try:
        # Import data types
        from backend.analytics.types import (
            MetricPoint,
            MetricSeries,
            AnomalyResult,
            AggregatedAnomalyScore,
        )
        print("✅ types.py - All data contracts imported")
        
        # Import engine
        from backend.analytics.engine import (
            AnomalyDetectionEngine,
            EngineRegistry,
        )
        print("✅ engine.py - Engine abstraction imported")
        
        # Import windows
        from backend.analytics.windows import (
            SlidingWindowExtractor,
            TimeBasedWindowExtractor,
            TimeWindow,
        )
        print("✅ windows.py - Window extraction imported")
        
        # Import aggregation
        from backend.analytics.aggregation import (
            AggregationStrategy,
            NodeAnomalyAggregator,
            ClusterAnomalyAggregator,
            TenantAnomalyAggregator,
            AggregationPipeline,
            AggregationConfig,
        )
        print("✅ aggregation.py - Aggregation pipeline imported")
        
        # Import explanation
        from backend.analytics.explain import (
            AnomalyType,
            AnomalyExplanation,
            ExplanationClassifier,
            ExplanationTemplateRegistry,
        )
        print("✅ explain.py - Explanation scaffold imported")
        
        # Import module-level
        import backend.analytics
        print("✅ __init__.py - Module initialization imported")
        
        print("\n" + "=" * 60)
        print("ALL IMPORTS SUCCESSFUL ✅")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"\n❌ IMPORT FAILED: {e}")
        return False


def verify_type_contracts():
    """Verify data type contracts"""
    print("\n" + "=" * 60)
    print("PHASE 1 VERIFICATION - TYPE CONTRACTS")
    print("=" * 60)
    
    from datetime import datetime
    from backend.analytics.types import MetricSeries, AnomalyResult
    
    try:
        # Test MetricSeries creation
        series = MetricSeries(
            tenant_id="test-tenant",
            cluster_id="test-cluster",
            node_id="test-node",
            metric_name="cpu_usage",
            timestamps=[
                datetime(2025, 1, 1, 0, 0, 0),
                datetime(2025, 1, 1, 0, 1, 0),
                datetime(2025, 1, 1, 0, 2, 0),
            ],
            values=[50.0, 55.0, 60.0],
        )
        assert series.length == 3
        print("✅ MetricSeries - Valid creation and properties")
        
        # Test AnomalyResult creation
        result = AnomalyResult(
            tenant_id="test-tenant",
            cluster_id="test-cluster",
            node_id="test-node",
            metric_name="cpu_usage",
            window_start=datetime(2025, 1, 1, 0, 0, 0),
            window_end=datetime(2025, 1, 1, 0, 2, 0),
            anomaly_score=0.85,
            anomaly_label="spike",
        )
        assert result.is_anomaly == True
        print("✅ AnomalyResult - Valid creation and properties")
        
        # Test validation (anomaly_label must be valid)
        try:
            bad_result = AnomalyResult(
                tenant_id="test-tenant",
                cluster_id="test-cluster",
                node_id="test-node",
                metric_name="cpu_usage",
                window_start=datetime(2025, 1, 1, 0, 0, 0),
                window_end=datetime(2025, 1, 1, 0, 2, 0),
                anomaly_score=0.85,
                anomaly_label="invalid_label",  # Should fail
            )
            print("❌ AnomalyResult - Validation FAILED (invalid label accepted)")
            return False
        except ValueError:
            print("✅ AnomalyResult - Validation works (invalid label rejected)")
        
        print("\n" + "=" * 60)
        print("ALL TYPE CONTRACTS VALID ✅")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ TYPE CONTRACT FAILED: {e}")
        return False


def verify_engine_interface():
    """Verify engine abstraction"""
    print("\n" + "=" * 60)
    print("PHASE 1 VERIFICATION - ENGINE INTERFACE")
    print("=" * 60)
    
    from backend.analytics.engine import AnomalyDetectionEngine
    
    try:
        # Verify abstract methods exist
        assert hasattr(AnomalyDetectionEngine, 'detect')
        print("✅ AnomalyDetectionEngine.detect() defined")
        
        assert hasattr(AnomalyDetectionEngine, 'explain')
        print("✅ AnomalyDetectionEngine.explain() defined")
        
        # Verify cannot instantiate abstract class directly
        try:
            engine = AnomalyDetectionEngine()
            print("❌ AnomalyDetectionEngine - Should be abstract!")
            return False
        except TypeError:
            print("✅ AnomalyDetectionEngine - Abstract (cannot instantiate)")
        
        print("\n" + "=" * 60)
        print("ENGINE INTERFACE VALID ✅")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ ENGINE INTERFACE FAILED: {e}")
        return False


def verify_window_extraction():
    """Verify sliding window logic"""
    print("\n" + "=" * 60)
    print("PHASE 1 VERIFICATION - WINDOW EXTRACTION")
    print("=" * 60)
    
    from datetime import datetime
    from backend.analytics.types import MetricSeries
    from backend.analytics.windows import SlidingWindowExtractor
    
    try:
        # Create test series
        series = MetricSeries(
            tenant_id="test",
            cluster_id="test",
            node_id="test",
            metric_name="test",
            timestamps=[datetime(2025, 1, 1, 0, 0, 0) + timedelta(minutes=i) for i in range(100)],
            values=[50.0 + i * 0.1 for i in range(100)],
        )
        
        # Extract windows
        extractor = SlidingWindowExtractor(window_size_points=10, stride_points=5)
        windows = extractor.extract(series)
        
        assert len(windows) > 0
        print(f"✅ Extracted {len(windows)} windows")
        
        # Verify window properties
        first_window = windows[0]
        assert first_window.size == 10
        print("✅ Window size properties correct")
        
        # Verify deterministic slicing
        windows2 = extractor.extract(series)
        assert len(windows) == len(windows2)
        print("✅ Deterministic slicing verified")
        
        print("\n" + "=" * 60)
        print("WINDOW EXTRACTION VALID ✅")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ WINDOW EXTRACTION FAILED: {e}")
        return False


def verify_aggregation():
    """Verify aggregation logic"""
    print("\n" + "=" * 60)
    print("PHASE 1 VERIFICATION - AGGREGATION")
    print("=" * 60)
    
    from datetime import datetime
    from backend.analytics.types import AnomalyResult
    from backend.analytics.aggregation import (
        AggregationStrategy,
        NodeAnomalyAggregator,
    )
    
    try:
        # Create test anomaly results
        results = [
            AnomalyResult(
                tenant_id="test",
                cluster_id="test",
                node_id="node-1",
                metric_name="cpu_usage",
                window_start=datetime(2025, 1, 1),
                window_end=datetime(2025, 1, 1),
                anomaly_score=0.8,
                anomaly_label="spike",
            ),
            AnomalyResult(
                tenant_id="test",
                cluster_id="test",
                node_id="node-1",
                metric_name="memory_used",
                window_start=datetime(2025, 1, 1),
                window_end=datetime(2025, 1, 1),
                anomaly_score=0.3,
                anomaly_label="normal",
            ),
        ]
        
        # Aggregate with MAX strategy
        aggregator = NodeAnomalyAggregator(strategy=AggregationStrategy.MAX)
        agg_score = aggregator.aggregate(results)
        
        assert agg_score.aggregate_score == 0.8  # MAX of 0.8 and 0.3
        print("✅ MAX aggregation strategy works")
        
        # Verify aggregation has correct counts
        assert agg_score.num_metrics_analyzed == 2
        assert agg_score.num_anomalies_detected == 1  # Only one is anomaly
        print("✅ Aggregation counts correct")
        
        print("\n" + "=" * 60)
        print("AGGREGATION LOGIC VALID ✅")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ AGGREGATION FAILED: {e}")
        return False


def main():
    """Run all verification tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║        PHASE 1 COMPLETION VERIFICATION SUITE           ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    results = [
        ("Imports", verify_imports()),
        ("Type Contracts", verify_type_contracts()),
        ("Engine Interface", verify_engine_interface()),
        ("Window Extraction", verify_window_extraction()),
        ("Aggregation Logic", verify_aggregation()),
    ]
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VERIFICATION TESTS PASSED ✅")
        print("PHASE 1 IS COMPLETE AND READY FOR PHASE 2")
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW ABOVE")
    print("=" * 60)
    print()
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
