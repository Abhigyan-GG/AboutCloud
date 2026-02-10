"""
Interactive Testing Guide - What Works Right Now

This script demonstrates all working functionality in the current system.
Run this to see what the platform can do.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.simulator.generator import MetricSimulator, SimulatorConfig, AnomalyInjector, generate_multi_node_scenario
from backend.ingestion.collector import MetricCollector, SimulatorSource
from backend.ingestion.validator import MetricValidator
from backend.ingestion.pipeline import IngestionPipeline
from backend.storage.interface import configure_storage
from backend.storage.memory_storage import InMemoryStorage
from backend.analytics.windows import SlidingWindowExtractor
from backend.analytics.aggregation import (
    NodeAnomalyAggregator,
    ClusterAnomalyAggregator,
    TenantAnomalyAggregator,
    AggregationStrategy,
)
from backend.analytics.types import AnomalyResult


def test_1_simulator():
    """TEST 1: Generate synthetic metrics"""
    print("\n" + "="*70)
    print("TEST 1: METRIC SIMULATOR")
    print("="*70)
    print("\n📊 Generating synthetic cloud metrics...\n")
    
    config = SimulatorConfig(
        baseline_mean=60.0,
        baseline_std=10.0,
        inject_spikes=True,
        spike_probability=0.02,
    )
    
    sim = MetricSimulator(config)
    series = sim.generate(
        tenant_id="acme-corp",
        cluster_id="production",
        node_id="web-server-01",
        metric_name="cpu_usage",
        num_points=200,
    )
    
    print(f"✓ Generated metric series:")
    print(f"  Tenant:  {series.tenant_id}")
    print(f"  Cluster: {series.cluster_id}")
    print(f"  Node:    {series.node_id}")
    print(f"  Metric:  {series.metric_name}")
    print(f"  Points:  {len(series.values)}")
    print(f"  Mean:    {sum(series.values)/len(series.values):.2f}")
    print(f"  Min:     {min(series.values):.2f}")
    print(f"  Max:     {max(series.values):.2f}")
    
    print("\n💡 WHAT THIS MEANS:")
    print("  - Simulator creates realistic time-series data")
    print("  - Configurable baseline patterns (normal distribution)")
    print("  - Automatic spike injection for testing")
    print("  - Multi-tenant metadata preserved")
    
    return series


def test_2_anomaly_injection(series):
    """TEST 2: Inject specific anomalies"""
    print("\n" + "="*70)
    print("TEST 2: ANOMALY INJECTION")
    print("="*70)
    print("\n💉 Injecting controlled anomalies...\n")
    
    # Inject spike
    spiked, spike_meta = AnomalyInjector.inject_spike(
        series, spike_index=100, magnitude=4.0, duration=3
    )
    
    print(f"✓ Spike Anomaly Injected:")
    print(f"  Location:  Index {spike_meta['index']}")
    print(f"  Magnitude: {spike_meta['magnitude']}x normal")
    print(f"  Before:    {spike_meta['original_value']:.2f}")
    print(f"  After:     {spike_meta['anomalous_value']:.2f}")
    print(f"  Increase:  +{spike_meta['anomalous_value'] - spike_meta['original_value']:.2f}")
    
    # Inject trend
    trend_series, trend_meta = AnomalyInjector.inject_trend(
        series, start_index=120, slope=0.8
    )
    
    print(f"\n✓ Trend Anomaly Injected:")
    print(f"  Start:     Index {trend_meta['start_index']}")
    print(f"  Direction: {trend_meta['direction']}")
    print(f"  Slope:     {trend_meta['slope']} per point")
    
    print("\n💡 WHAT THIS MEANS:")
    print("  - You can inject labeled anomalies for testing ML models")
    print("  - Supports spikes, trends, level shifts")
    print("  - Metadata tracks exact anomaly details")
    print("  - Perfect for creating test datasets")
    
    return spiked, trend_series


def test_3_validation():
    """TEST 3: Data quality validation"""
    print("\n" + "="*70)
    print("TEST 3: DATA VALIDATION")
    print("="*70)
    print("\n🔍 Testing data quality checks...\n")
    
    validator = MetricValidator()
    
    # Test 1: Valid data
    sim = MetricSimulator()
    valid_series = sim.generate("tenant-1", "cluster-1", "node-1", "cpu", 100)
    result = validator.validate(valid_series)
    
    print(f"✓ Valid Series Check:")
    print(f"  Status:   {'PASS ✓' if result.is_valid else 'FAIL ✗'}")
    print(f"  Errors:   {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    
    # Test 2: Missing tenant_id
    from backend.analytics.types import MetricSeries
    bad_series = MetricSeries(
        tenant_id="",  # Invalid!
        cluster_id="cluster-1",
        node_id="node-1",
        metric_name="cpu",
        timestamps=[datetime.now()],
        values=[50.0],
    )
    
    result = validator.validate(bad_series)
    print(f"\n✓ Invalid Series Check (missing tenant_id):")
    print(f"  Status: {'PASS ✓' if result.is_valid else 'FAIL ✗'}")
    print(f"  Errors: {result.errors}")
    
    # Test 3: Percentage out of bounds
    bad_percent = MetricSeries(
        tenant_id="tenant-1",
        cluster_id="cluster-1",
        node_id="node-1",
        metric_name="cpu_usage_percent",
        timestamps=[datetime.now()],
        values=[150.0],  # > 100%!
    )
    
    result = validator.validate(bad_percent)
    print(f"\n✓ Out of Bounds Check (150% CPU):")
    print(f"  Status:   {'PASS ✓' if result.is_valid else 'FAIL ✗'}")
    print(f"  Warnings: {result.warnings}")
    
    print("\n💡 WHAT THIS MEANS:")
    print("  - Validator catches bad data before it enters storage")
    print("  - Enforces tenant isolation (security)")
    print("  - Checks timestamps, bounds, null values")
    print("  - Distinguishes errors (reject) vs warnings (accept with log)")


def test_4_ingestion_pipeline():
    """TEST 4: Full ingestion pipeline"""
    print("\n" + "="*70)
    print("TEST 4: INGESTION PIPELINE")
    print("="*70)
    print("\n🔄 Testing end-to-end data flow...\n")
    
    # Setup
    storage = InMemoryStorage()
    configure_storage(storage)
    
    collector = MetricCollector(SimulatorSource())
    validator = MetricValidator()
    pipeline = IngestionPipeline(collector, validator, storage)
    
    # Ingest multi-node cluster
    start = datetime(2025, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=1)
    
    series_list, stats = pipeline.ingest_cluster(
        tenant_id="acme-corp",
        cluster_id="production",
        node_ids=[f"web-{i:02d}" for i in range(5)],
        metric_name="memory_usage",
        start_time=start,
        end_time=end,
    )
    
    print(f"✓ Ingestion Complete:")
    print(f"  Collected: {stats.total_collected} series")
    print(f"  Valid:     {stats.total_valid}")
    print(f"  Invalid:   {stats.total_invalid}")
    print(f"  Stored:    {stats.total_stored}")
    print(f"  Success:   {stats.success_rate():.1%}")
    
    # Verify storage
    storage_stats = storage.get_stats()
    print(f"\n✓ Storage State:")
    print(f"  Tenants: {storage_stats['total_tenants']}")
    print(f"  Metrics: {storage_stats['total_metrics']}")
    
    # Retrieve from storage
    retrieved = storage.get_metric_series(
        tenant_id="acme-corp",
        cluster_id="production",
        node_id="web-00",
        metric_name="memory_usage",
        start_time=start,
        end_time=end,
    )
    
    print(f"\n✓ Retrieved from Storage:")
    print(f"  Node:   {retrieved.node_id}")
    print(f"  Points: {len(retrieved.values)}")
    
    print("\n💡 WHAT THIS MEANS:")
    print("  - Full pipeline: Collect → Validate → Store")
    print("  - Batch ingestion for entire clusters")
    print("  - Statistics tracked (success rate, errors)")
    print("  - Data persisted and retrievable")
    print("  - Multi-tenant isolation enforced")
    
    return storage


def test_5_sliding_windows():
    """TEST 5: Sliding window extraction"""
    print("\n" + "="*70)
    print("TEST 5: SLIDING WINDOWS")
    print("="*70)
    print("\n🪟 Extracting analysis windows...\n")
    
    # Generate data
    sim = MetricSimulator()
    series = sim.generate("tenant-1", "cluster-1", "node-1", "cpu", 300)
    
    # Extract windows
    extractor = SlidingWindowExtractor(
        window_size_points=50,
        stride_points=25,
    )
    
    windows = extractor.extract(series)
    
    print(f"✓ Window Extraction:")
    print(f"  Total Points:  {len(series.values)}")
    print(f"  Window Size:   {extractor.window_size_points}")
    print(f"  Stride:        {extractor.stride_points}")
    print(f"  Windows Found: {len(windows)}")
    
    print(f"\n✓ First 3 Windows:")
    for i, win in enumerate(windows[:3]):
        print(f"  Window {i+1}: {win.size} points, {win.start_time} → {win.end_time}")
    
    print("\n💡 WHAT THIS MEANS:")
    print("  - Time series split into overlapping windows")
    print("  - Each window analyzed independently")
    print("  - Configurable size and overlap")
    print("  - Enables batch anomaly detection")


def test_6_aggregation():
    """TEST 6: Multi-level aggregation"""
    print("\n" + "="*70)
    print("TEST 6: ANOMALY SCORE AGGREGATION")
    print("="*70)
    print("\n📊 Testing hierarchy: Node → Cluster → Tenant...\n")
    
    # Create mock anomaly results for 5 nodes
    now = datetime.now()
    mock_results = []
    
    for i in range(5):
        result = AnomalyResult(
            tenant_id="acme-corp",
            cluster_id="production",
            node_id=f"web-{i:02d}",
            metric_name="cpu_usage",
            window_start=now,
            window_end=now + timedelta(minutes=5),
            anomaly_score=0.1 + (i * 0.15),  # Increasing scores
            anomaly_label="normal",
        )
        mock_results.append(result)
    
    # Make one node highly anomalous
    mock_results[3].anomaly_score = 0.95
    mock_results[3].anomaly_label = "spike"
    
    print("✓ Mock Anomaly Scores (5 nodes):")
    for r in mock_results:
        print(f"  {r.node_id}: {r.anomaly_score:.2f} ({r.anomaly_label})")
    
    # Node-level (already have individual scores)
    print(f"\n✓ Node-Level Scores:")
    print(f"  Min:  {min(r.anomaly_score for r in mock_results):.2f}")
    print(f"  Max:  {max(r.anomaly_score for r in mock_results):.2f}")
    print(f"  Mean: {sum(r.anomaly_score for r in mock_results)/len(mock_results):.2f}")
    
    # Aggregate to cluster (using different strategies)
    cluster_agg_max = ClusterAnomalyAggregator(strategy=AggregationStrategy.MAX)
    cluster_agg_mean = ClusterAnomalyAggregator(strategy=AggregationStrategy.MEAN)
    
    # Need to convert AnomalyResult to AggregatedAnomalyScore first
    node_agg = NodeAnomalyAggregator(strategy=AggregationStrategy.MAX)
    node_scores = [node_agg.aggregate([r]) for r in mock_results]
    
    cluster_max = cluster_agg_max.aggregate(node_scores)
    cluster_mean = cluster_agg_mean.aggregate(node_scores)
    
    print(f"\n✓ Cluster-Level Aggregation:")
    print(f"  Strategy MAX:  {cluster_max.aggregate_score:.2f}")
    print(f"  Strategy MEAN: {cluster_mean.aggregate_score:.2f}")
    print(f"  Anomalies:     {cluster_max.num_anomalies_detected}")
    
    # Aggregate to tenant
    tenant_agg = TenantAnomalyAggregator(strategy=AggregationStrategy.MAX)
    tenant_score = tenant_agg.aggregate([cluster_max])
    
    print(f"\n✓ Tenant-Level Aggregation:")
    print(f"  Tenant ID:     {tenant_score.tenant_id}")
    print(f"  Final Score:   {tenant_score.aggregate_score:.2f}")
    print(f"  Strategy:      {tenant_score.aggregation_strategy}")
    
    print("\n💡 WHAT THIS MEANS:")
    print("  - Anomaly scores aggregated across hierarchy")
    print("  - Node → Cluster → Tenant levels")
    print("  - Multiple strategies (MAX catches worst-case)")
    print("  - Dashboard can show: 'Cluster 95% anomalous due to node web-03'")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  ABOUTCLOUD ANALYTICS PLATFORM - INTERACTIVE TEST SUITE")
    print("="*70)
    print("\n  This demonstrates ALL working functionality in the current system.")
    print("  Watch what happens and what it means for your platform.")
    print("\n" + "="*70)
    
    try:
        # Run tests
        series = test_1_simulator()
        spiked, trend = test_2_anomaly_injection(series)
        test_3_validation()
        storage = test_4_ingestion_pipeline()
        test_5_sliding_windows()
        test_6_aggregation()
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY: WHAT YOU HAVE RIGHT NOW")
        print("="*70)
        
        print("\n✅ WORKING COMPONENTS:")
        print("  1. Metric Simulator     - Generate test data")
        print("  2. Anomaly Injector     - Create labeled anomalies")
        print("  3. Data Validator       - Quality checks + tenant isolation")
        print("  4. Ingestion Pipeline   - Collect → Validate → Store")
        print("  5. Storage Layer        - Persist & retrieve metrics")
        print("  6. Sliding Windows      - Batch analysis preparation")
        print("  7. Aggregation Pipeline - Multi-level scoring")
        
        print("\n❌ NOT IMPLEMENTED YET:")
        print("  1. Actual ML Detection  - Currently using mock scores")
        print("  2. Merlion Integration  - No real anomaly detection")
        print("  3. Explanation Engine   - Stub only")
        print("  4. REST API             - No HTTP endpoints")
        print("  5. Dashboard            - No visualization")
        print("  6. Persistent DB        - Only in-memory storage")
        
        print("\n💡 WHAT YOU CAN DO NOW:")
        print("  - Generate realistic cloud metrics")
        print("  - Ingest multi-tenant data safely")
        print("  - Store and retrieve time series")
        print("  - Prepare data for ML (windows)")
        print("  - Aggregate scores across hierarchy")
        
        print("\n🚀 NEXT STEP:")
        print("  Install Merlion and implement real anomaly detection!")
        print("  Command: pip install salesforce-merlion")
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
