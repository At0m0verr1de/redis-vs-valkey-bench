#!/usr/bin/env python3
"""Print the phase-B RATE: 60% of the lowest workers=400 phase-A median across summaries.

Usage:  python3 -I rate.py results/summary_A.csv [results-lan/summary_A.csv ...]
"""
import csv
import sys

WORKERS = "400"
SHARE = 0.6

low = min(float(row["rps_median"])
          for path in sys.argv[1:]
          for row in csv.DictReader(open(path))
          if row["workers"] == WORKERS)
print(int(low * SHARE))
