#!/usr/bin/env python3
import csv
import math
import os
import random
import re
import statistics
import subprocess
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("[WARN] matplotlib is not installed. Only the CSV file will be generated (run 'pip install matplotlib' for plots).")

# ==============================================================================
# BENCHMARK CONFIGURATION
# ==============================================================================
SEED = 26
REPEATS = 3               # Number of runs per test (median is taken)
TEMP_INPUT = "bench_input_tmp.txt"
CSV_OUTPUT = "benchmark_results.csv"
PLOT_OUTPUT = "benchmark_plots.png"
BINARY_NAME = "rendezvous_bench.exe" if os.name == "nt" else "./rendezvous_bench"


# ==============================================================================
# 1. POINT DISTRIBUTION GENERATORS
# ==============================================================================
def generate_uniform(n: int, box_size: float = 10000.0) -> list[tuple[float, float]]:
    """Uniform distribution over a large square [0, box_size] x [0, box_size].
    Favors Spatial Hashing (sparsely populated cells, O(1) per query).
    """
    return [(random.uniform(0.0, box_size), random.uniform(0.0, box_size)) for _ in range(n)]


def generate_multi_cluster(n: int, num_clusters: int = 15, box_size: float = 5000.0, cluster_std: float = 3.0) -> list[tuple[float, float]]:
    """Multiple dense Gaussian clusters (std=3.0 < radius=15.0).
    Favors QuadTree (inner quadrants are aggregated in O(1)).
    """
    centers = [(random.uniform(0.0, box_size), random.uniform(0.0, box_size)) for _ in range(num_clusters)]
    points = []
    for i in range(n):
        cx, cy = centers[i % num_clusters]
        px = random.gauss(cx, cluster_std)
        py = random.gauss(cy, cluster_std)
        points.append((px, py))
    return points


def generate_super_cluster(n: int, box_size: float = 20.0) -> list[tuple[float, float]]:
    """A single extremely dense cluster inside a 20x20 square (for radius=15.0).
    Worst-case O(N^2) for Spatial Hashing; QuadTree remains fast if maxDepth is sufficient.
    """
    points = []
    # Use a small jitter so points are not initially within distance < 1e-5
    grid_side = int(math.ceil(math.sqrt(n)))
    step = box_size / max(grid_side, 1)
    for i in range(n):
        gx = (i % grid_side) * step + random.uniform(0.0, step * 0.4)
        gy = (i // grid_side) * step + random.uniform(0.0, step * 0.4)
        points.append((gx, gy))
    return points


def generate_core_halo(n: int, core_ratio: float = 0.8, core_size: float = 25.0, halo_size: float = 10000.0) -> list[tuple[float, float]]:
    """80% of points in a dense core (25x25) and 20% scattered across 10000x10000.
    Tests QuadTree adaptability to non-uniform densities.
    """
    n_core = int(n * core_ratio)
    n_halo = n - n_core
    cx, cy = halo_size / 2.0, halo_size / 2.0

    points = [
        (cx + random.uniform(-core_size / 2, core_size / 2),
         cy + random.uniform(-core_size / 2, core_size / 2))
        for _ in range(n_core)
    ]
    points.extend(
        (random.uniform(0.0, halo_size), random.uniform(0.0, halo_size))
        for _ in range(n_halo)
    )
    return points


def write_points_to_file(points: list[tuple[float, float]], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{len(points)}\n")
        for x, y in points:
            f.write(f"{x:.6f} {y:.6f}\n")


# ==============================================================================
# 2. GO COMPILATION AND EXECUTION
# ==============================================================================
def compile_go_binary() -> str:
    """Attempts to compile the Go project into a native executable for benchmarking."""
    print("[INFO] Compiling Go project...")
    # Case 1: main.go is inside cmd/ or in the current directory
    candidates = [
        ["go", "build", "-o", BINARY_NAME, "./cmd"],
        ["go", "build", "-o", BINARY_NAME, "main.go"],
        ["go", "build", "-o", BINARY_NAME, "."],
    ]
    for cmd in candidates:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(BINARY_NAME.lstrip("./")):
            print(f"[OK] Compiled successfully using: {' '.join(cmd)}")
            return BINARY_NAME
    print("[WARN] Automatic compilation with `go build` failed. Falling back to `go run main.go`.")
    return ""


def run_single_test(binary: str, algo: str, filepath: str, rounds: int, depth: int, threshold: int, radius: float) -> tuple[float, int]:
    """Runs the algorithm REPEATS times and returns (median_time_ms, remaining_nodes)."""
    times = []
    remaining_nodes = -1

    for _ in range(REPEATS):
        if binary:
            cmd = [binary]
        else:
            cmd = ["go", "run", "main.go"]

        cmd += [
            "-file", filepath,
            "-algo", algo,
            "-rounds", str(rounds),
            "-depth", str(depth),
            "-threshold", str(threshold),
            "-radius", str(radius),
        ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Error running {' '.join(cmd)}:\n{res.stderr}")

        out = res.stdout
        m_time = re.search(r"BENCH_TIME_MS:([0-9.]+)", out)
        m_rem = re.search(r"Number of remaining nodes:\s*(\d+)", out)

        if not m_time:
            raise RuntimeError(f"BENCH_TIME_MS not found in output:\n{out}")

        times.append(float(m_time.group(1)))
        if m_rem:
            remaining_nodes = int(m_rem.group(1))

    return statistics.median(times), remaining_nodes


# ==============================================================================
# 3. BENCHMARK SUITE
# ==============================================================================
def run_all_benchmarks(binary: str) -> list[dict]:
    random.seed(SEED)
    results = []

    distributions = {
        "uniform": generate_uniform,
        "multi_cluster": generate_multi_cluster,
        "super_cluster": generate_super_cluster,
        "core_halo": generate_core_halo,
    }

    # --------------------------------------------------------------------------
    # EXPERIMENT 1: Scaling with N (1 single round -> isolates build + query)
    # --------------------------------------------------------------------------
    n_values_round1 = [1000, 3000, 7000, 15000, 30000]
    print("\n=== EXPERIMENT 1: Scaling with N (rounds = 1, radius = 15, depth = 12, threshold = 8) ===")
    for dist_name, gen_fn in distributions.items():
        for n in n_values_round1:
            pts = gen_fn(n)
            write_points_to_file(pts, TEMP_INPUT)

            qt_ms, qt_rem = run_single_test(binary, "quadtree", TEMP_INPUT, rounds=1, depth=12, threshold=8, radius=15.0)
            sh_ms, sh_rem = run_single_test(binary, "spatial", TEMP_INPUT, rounds=1, depth=12, threshold=8, radius=15.0)

            match_str = "OK" if qt_rem == sh_rem else f"MISMATCH ({qt_rem} vs {sh_rem})"
            speedup = sh_ms / qt_ms if qt_ms > 0 else 0.0
            print(f"[{dist_name:13s} | N={n:6d} | R=1] QT: {qt_ms:8.2f} ms | SH: {sh_ms:8.2f} ms | Speedup QT vs SH: {speedup:5.2f}x | Nodes: {match_str}")

            results.append({
                "experiment": "scale_N_round1",
                "distribution": dist_name,
                "N": n,
                "rounds": 1,
                "radius": 15.0,
                "depth": 12,
                "threshold": 8,
                "qt_ms": qt_ms,
                "sh_ms": sh_ms,
                "qt_remaining": qt_rem,
                "sh_remaining": sh_rem,
            })

    # --------------------------------------------------------------------------
    # EXPERIMENT 2: Multi-round simulation (rounds = 50)
    # --------------------------------------------------------------------------
    n_values_multi = [1000, 5000, 10000, 20000]
    print("\n=== EXPERIMENT 2: Full Simulation (rounds = 50, radius = 15, depth = 12, threshold = 8) ===")
    for dist_name in ["uniform", "multi_cluster", "core_halo"]:
        gen_fn = distributions[dist_name]
        for n in n_values_multi:
            pts = gen_fn(n)
            write_points_to_file(pts, TEMP_INPUT)

            qt_ms, qt_rem = run_single_test(binary, "quadtree", TEMP_INPUT, rounds=50, depth=12, threshold=8, radius=15.0)
            sh_ms, sh_rem = run_single_test(binary, "spatial", TEMP_INPUT, rounds=50, depth=12, threshold=8, radius=15.0)

            speedup = sh_ms / qt_ms if qt_ms > 0 else 0.0
            print(f"[{dist_name:13s} | N={n:6d} | R=50] QT: {qt_ms:8.2f} ms | SH: {sh_ms:8.2f} ms | Speedup QT vs SH: {speedup:5.2f}x | Rem: {qt_rem}")

            results.append({
                "experiment": "scale_N_multi_round",
                "distribution": dist_name,
                "N": n,
                "rounds": 50,
                "radius": 15.0,
                "depth": 12,
                "threshold": 8,
                "qt_ms": qt_ms,
                "sh_ms": sh_ms,
                "qt_remaining": qt_rem,
                "sh_remaining": sh_rem,
            })

    # --------------------------------------------------------------------------
    # EXPERIMENT 3: Varying communication radius (N = 15000, rounds = 1)
    # --------------------------------------------------------------------------
    radii = [5.0, 15.0, 40.0, 100.0, 250.0]
    print("\n=== EXPERIMENT 3: Radius Impact (N = 15000, rounds = 1, multi_cluster) ===")
    pts = generate_multi_cluster(15000, num_clusters=15, box_size=2000.0, cluster_std=10.0)
    write_points_to_file(pts, TEMP_INPUT)
    for r in radii:
        qt_ms, qt_rem = run_single_test(binary, "quadtree", TEMP_INPUT, rounds=1, depth=12, threshold=8, radius=r)
        sh_ms, sh_rem = run_single_test(binary, "spatial", TEMP_INPUT, rounds=1, depth=12, threshold=8, radius=r)
        speedup = sh_ms / qt_ms if qt_ms > 0 else 0.0
        print(f"[radius={r:6.1f} | N=15000] QT: {qt_ms:8.2f} ms | SH: {sh_ms:8.2f} ms | Speedup QT vs SH: {speedup:5.2f}x")

        results.append({
            "experiment": "vary_radius",
            "distribution": "multi_cluster",
            "N": 15000,
            "rounds": 1,
            "radius": r,
            "depth": 12,
            "threshold": 8,
            "qt_ms": qt_ms,
            "sh_ms": sh_ms,
            "qt_remaining": qt_rem,
            "sh_remaining": sh_rem,
        })

    # --------------------------------------------------------------------------
    # EXPERIMENT 4: QuadTree Tuning (vary maxDepth -> U-shaped curve / parabola)
    # --------------------------------------------------------------------------
    depths = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12]
    print("\n=== EXPERIMENT 4: QuadTree maxDepth Impact on Dense Clusters (N = 15000, rounds = 1) ===")
    # Using Gaussian clusters on box_size=500 with radius=25 and threshold=2
    # so that maxDepth genuinely controls splitting from depth 2 up to 12:
    # - At depth 2..4: quadrants (250..62.5) > radius (25) -> under-splitting (slow)
    # - At depth 6..7: quadrants (15.6..7.8) < radius (25) -> optimal O(1) aggregation (minimum!)
    # - At depth 9..12: quadrants (1.9..0.24) << radius (25) -> over-splitting overhead (slow again)
    pts = generate_multi_cluster(15000, num_clusters=8, box_size=500.0, cluster_std=12.0)
    write_points_to_file(pts, TEMP_INPUT)
    sh_ms, sh_rem = run_single_test(binary, "spatial", TEMP_INPUT, rounds=1, depth=7, threshold=2, radius=25.0)
    for d in depths:
        qt_ms, qt_rem = run_single_test(binary, "quadtree", TEMP_INPUT, rounds=1, depth=d, threshold=2, radius=25.0)
        print(f"[depth={d:2d} | threshold=2] QT: {qt_ms:8.2f} ms (vs SH: {sh_ms:8.2f} ms)")
        results.append({
            "experiment": "vary_depth",
            "distribution": "dense_clusters",
            "N": 15000,
            "rounds": 1,
            "radius": 25.0,
            "depth": d,
            "threshold": 2,
            "qt_ms": qt_ms,
            "sh_ms": sh_ms,
            "qt_remaining": qt_rem,
            "sh_remaining": sh_rem,
        })

    if os.path.exists(TEMP_INPUT):
        os.remove(TEMP_INPUT)

    return results


# ==============================================================================
# 4. CSV EXPORT AND PLOT GENERATION
# ==============================================================================
def save_csv(results: list[dict], filename: str) -> None:
    if not results:
        return
    fieldnames = list(results[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] Results saved to '{filename}'.")


def plot_results(results: list[dict], filename: str) -> None:
    if not HAS_MATPLOTLIB or not results:
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Benchmark: QuadTree vs. Spatial Hashing (Rendezvous)", fontsize=15, fontweight="bold")

    # Plot 1: Uniform Distribution (1 Round)
    ax = axes[0, 0]
    sub = [r for r in results if r["experiment"] == "scale_N_round1" and r["distribution"] == "uniform"]
    ax.plot([r["N"] for r in sub], [r["qt_ms"] for r in sub], "o-", label="QuadTree", linewidth=2)
    ax.plot([r["N"] for r in sub], [r["sh_ms"] for r in sub], "s--", label="Spatial Hashing", linewidth=2)
    ax.set_title("1. Uniform Distribution (1 Round) - Spatial Hashing Wins")
    ax.set_xlabel("Number of Points (N)")
    ax.set_ylabel("Time (ms)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Plot 2: Multi-Cluster & Super-Cluster (1 Round)
    ax = axes[0, 1]
    for dist, style in [("multi_cluster", "-"), ("super_cluster", ":")]:
        sub = [r for r in results if r["experiment"] == "scale_N_round1" and r["distribution"] == dist]
        ax.plot([r["N"] for r in sub], [r["qt_ms"] for r in sub], f"o{style}", label=f"QuadTree ({dist})", linewidth=2)
        ax.plot([r["N"] for r in sub], [r["sh_ms"] for r in sub], f"s{style}", label=f"Spatial Hash ({dist})", linewidth=2)
    ax.set_title("2. Dense Clusters (1 Round) - QuadTree Wins (O(N^2) for Hash)")
    ax.set_xlabel("Number of Points (N)")
    ax.set_ylabel("Time (ms)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Plot 3: Varying Radius (N = 15000)
    ax = axes[1, 0]
    sub = [r for r in results if r["experiment"] == "vary_radius"]
    ax.plot([r["radius"] for r in sub], [r["qt_ms"] for r in sub], "o-", label="QuadTree", linewidth=2)
    ax.plot([r["radius"] for r in sub], [r["sh_ms"] for r in sub], "s--", label="Spatial Hashing", linewidth=2)
    ax.set_title("3. Communication Radius Impact (N=15000, Multi-Cluster)")
    ax.set_xlabel("Radius")
    ax.set_ylabel("Time (ms)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Plot 4: maxDepth Impact on Super-Cluster
    ax = axes[1, 1]
    sub = [r for r in results if r["experiment"] == "vary_depth"]
    ax.plot([r["depth"] for r in sub], [r["qt_ms"] for r in sub], "o-", color="tab:blue", label="QuadTree (varying depth)", linewidth=2)
    if sub:
        ax.axhline(sub[0]["sh_ms"], color="tab:orange", linestyle="--", linewidth=2, label="Spatial Hashing (baseline)")
    ax.set_title("4. maxDepth Impact on Super-Cluster (N=15000)")
    ax.set_xlabel("QuadTree maxDepth")
    ax.set_ylabel("Time (ms)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    plt.savefig(filename, dpi=150)
    print(f"[OK] Plots saved to '{filename}'.")


if __name__ == "__main__":
    binary_path = compile_go_binary()
    all_results = run_all_benchmarks(binary_path)
    save_csv(all_results, CSV_OUTPUT)
    plot_results(all_results, PLOT_OUTPUT)