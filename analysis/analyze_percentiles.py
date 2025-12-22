"""
Analyze player stats distributions and compute percentiles for role threshold tuning.

Usage:
    python analysis/analyze_percentiles.py [csv_file]
    
Example:
    python analysis/analyze_percentiles.py analysis/player_stats_all.csv
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path


def analyze_distributions(csv_file: str):
    """
    Analyze distributions of key stats and compute percentiles.
    
    Args:
        csv_file: Path to CSV file with player stats
    """
    print("=" * 80)
    print("📊 WvW Analytics - Role Threshold Analysis")
    print("=" * 80)
    print()
    
    # Load data
    print(f"📁 Loading data from: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"   Total records: {len(df)}")
    print()
    
    # Filter out records with very low activity (likely AFKs or very short fights)
    # Keep only players with at least some meaningful activity
    active_df = df[(df['dps'] > 0) | (df['cleanses'] > 0) | (df['strips_out'] > 0)]
    print(f"   Active players (DPS > 0 or support stats > 0): {len(active_df)}")
    print()
    
    # Define key metrics for role detection
    metrics = {
        "DPS": "dps",
        "Cleanses": "cleanses",
        "Strips": "strips_out",
        "Quickness %": "quickness_uptime",
        "Alacrity %": "alacrity_uptime",
        "Resistance %": "resistance_uptime",
        "Might avg": "might_uptime"
    }
    
    percentiles = [50, 70, 80, 90, 95]
    
    print("=" * 80)
    print("📈 Distribution Analysis")
    print("=" * 80)
    print()
    
    results = {}
    
    for metric_name, column in metrics.items():
        print(f"🔍 {metric_name} ({column})")
        print("-" * 80)
        
        data = active_df[column].dropna()
        
        # Basic stats
        print(f"   Count:  {len(data)}")
        print(f"   Mean:   {data.mean():.2f}")
        print(f"   Median: {data.median():.2f}")
        print(f"   Std:    {data.std():.2f}")
        print()
        
        # Percentiles
        print("   Percentiles:")
        percentile_values = {}
        for p in percentiles:
            value = np.percentile(data, p)
            percentile_values[p] = value
            print(f"      P{p:2d}: {value:8.2f}")
        
        results[column] = percentile_values
        print()
    
    # Analyze current role distribution
    print("=" * 80)
    print("🎭 Current Role Distribution")
    print("=" * 80)
    print()
    
    role_counts = df['detected_role'].value_counts()
    total = len(df)
    
    for role, count in role_counts.items():
        percentage = (count / total) * 100
        print(f"   {role:20s}: {count:5d} ({percentage:5.2f}%)")
    print()
    
    # Propose thresholds based on percentiles
    print("=" * 80)
    print("💡 Proposed Threshold Updates")
    print("=" * 80)
    print()
    print("Based on the data distribution, here are suggested threshold values:")
    print()
    
    # Healer/Support: high cleanses (P80-P90), low DPS
    print("# Healer/Support thresholds")
    print(f"HEALER_MIN_CLEANSES = {int(results['cleanses'][80])}  # P80 of cleanses")
    print(f"HEALER_MAX_DPS = 800  # Keep low to ensure pure support builds")
    print()
    
    # Stripper: high strips (P80), low cleanses
    print("# Stripper thresholds")
    print(f"STRIPPER_MIN_STRIPS = {int(results['strips_out'][80])}  # P80 of strips")
    print(f"STRIPPER_MAX_CLEANSES = {int(results['cleanses'][50])}  # P50 of cleanses (to exclude healers)")
    print(f"STRIPPER_STRIP_TO_CLEANSE_RATIO = 1.5  # Strips should dominate over cleanses")
    print()
    
    # DPS: high DPS (P70), low support
    print("# DPS thresholds")
    print(f"DPS_MIN_DPS = {int(results['dps'][70])}  # P70 of DPS")
    print(f"DPS_MAX_CLEANSES = {int(results['cleanses'][50])}  # P50 of cleanses")
    print(f"DPS_MAX_STRIPS = {int(results['strips_out'][50])}  # P50 of strips")
    print("# Note: Removed quickness_uptime constraint since it's received, not given")
    print()
    
    # Boon Support: high boon uptime (P70-P80), moderate cleanses
    print("# Boon Support thresholds")
    print(f"BOON_MIN_UPTIME = {results['quickness_uptime'][70]:.1f}  # P70 of quickness (or alacrity/resistance)")
    print(f"BOON_MIN_CLEANSES = {int(results['cleanses'][50])}  # P50 of cleanses (some support activity)")
    print(f"BOON_MAX_DPS = {int(results['dps'][80])}  # P80 of DPS (allow some boon DPS builds)")
    print(f"# Note: In WvW, Resistance is as important as Quickness for support detection")
    print()
    
    # Additional insights
    print("=" * 80)
    print("📝 Additional Insights")
    print("=" * 80)
    print()
    print("Key observations:")
    print(f"  • {len(active_df)} players with meaningful activity out of {len(df)} total")
    print(f"  • Median DPS: {results['dps'][50]:.0f}")
    print(f"  • Median cleanses: {results['cleanses'][50]:.0f}")
    print(f"  • Median strips: {results['strips_out'][50]:.0f}")
    print()
    print("Recommendations:")
    print("  1. Remove quickness_uptime constraint from DPS detection")
    print("     (players receive boons, doesn't mean they're support)")
    print("  2. Use P70-P80 percentiles for role-defining stats")
    print("  3. Keep hybrid as catch-all for mixed/unclear builds")
    print()


def main():
    """Main entry point for analysis script."""
    # Default CSV file
    default_csv = "analysis/player_stats_all.csv"
    
    # Get CSV file from command line or use default
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = default_csv
    
    # Check if file exists
    if not Path(csv_file).exists():
        print(f"❌ Error: File not found: {csv_file}")
        print()
        print("Please run the export script first:")
        print("  python -m app.scripts.export_player_stats")
        sys.exit(1)
    
    analyze_distributions(csv_file)


if __name__ == "__main__":
    main()
