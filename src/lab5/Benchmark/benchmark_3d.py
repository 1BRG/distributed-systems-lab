import subprocess
import random
import os
import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

INPUT_FILE = "bench_input.txt"
BINARY_NAME = "rendezvous_bench.exe" if os.name == "nt" else "./rendezvous_bench"


def generate_data(num_points=8000, map_size=1000.0):
    """Generates uniformly distributed points with a fixed seed for reproducibility."""
    rng = random.Random(42)
    with open(INPUT_FILE, "w") as f:
        f.write(f"{num_points}\n")
        for _ in range(num_points):
            x = rng.uniform(0, map_size)
            y = rng.uniform(0, map_size)
            f.write(f"{x:.6f} {y:.6f}\n")


def compile_go():
    print("1. Compiling Go project with optimizations...")
    res = subprocess.run(
        ["go", "build", "-ldflags=-s -w", "-o", BINARY_NAME, "."],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print("Compilation error:\n", res.stderr)
        exit(1)


def run_go(depth, threshold, radius=120.0, rounds=5):
    exec_path = f".\\{BINARY_NAME}" if os.name == "nt" else BINARY_NAME
    cmd = [
        exec_path,
        "-file", INPUT_FILE,
        "-depth", str(depth),
        "-threshold", str(threshold),
        "-radius", str(radius),
        "-rounds", str(rounds),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if line.startswith("BENCH_TIME_MS:"):
            return float(line.replace("BENCH_TIME_MS:", ""))
    return float("inf")


def trimmed_mean_and_se(samples, trim_count=1):
    """
    Computes the trimmed mean and standard error (SE) to eliminate outliers
    caused by the Go Garbage Collector and OS context switches.
    """
    s = sorted(samples)
    if len(s) > 2 * trim_count:
        s = s[trim_count:-trim_count]
    arr = np.array(s, dtype=float)
    mean = float(np.mean(arr))
    se = float(np.std(arr, ddof=1) / np.sqrt(len(arr))) if len(arr) > 1 else 0.0
    return mean, se


def find_true_mathematical_optimum(depths, thresholds, Z_mean, Z_se, N):
    """
    Finds the true mathematical optimum (d*, T*) by enforcing strict structural
    non-degeneracy and pooling across the equivalent L-shaped plateau:
    
    1. For any depth d, average leaf capacity is m(d) = N / 4^(d-1).
       - If T >> m(d), parent nodes already have <= T points, so depth d is NEVER reached.
       - If T << m(d), depth limit stops subdivision first, so T is inactive.
       Therefore, for each depth d, the ONLY mathematically valid (non-degenerate)
       canonical threshold is the grid value T closest to N / 4^(d-1).
       
    2. Because all cells in the L-elbow around (d, T_canonical) execute the exact
       same QuadTree structure, we pool the neighborhood along the active arms
       to cancel out random 1-2 ms OS scheduling fluctuations.
    """
    candidates = []

    for i, d in enumerate(depths):
        theo_leaf_density = N / (4.0 ** (d - 1))

        # Ignore depths where a full tree has < 1 point per cell (pure over-partitioning)
        if theo_leaf_density < 1.0:
            continue

        # Find the canonical threshold T in the grid closest in log2-space to N / 4^(d-1)
        best_j = min(
            range(len(thresholds)),
            key=lambda j: abs(math.log2(thresholds[j]) - math.log2(theo_leaf_density)),
        )
        t_canon = thresholds[best_j]

        # Enforce strict mathematical coupling: T must be within 1 grid step of N / 4^(d-1)
        if abs(math.log2(t_canon) - math.log2(theo_leaf_density)) > 1.1:
            continue

        # Pool measurements across the structurally equivalent L-elbow:
        # - Horizontal arm: same depth d, thresholds <= t_canon (depth-limited equivalent trees)
        # - Vertical arm: same threshold t_canon, depths >= d (threshold-limited equivalent trees)
        # - Immediate neighbors around the elbow
        elbow_vals = []
        elbow_weights = []

        for ii in range(len(depths)):
            for jj in range(len(thresholds)):
                if ii == i and jj == best_j:
                    elbow_vals.append(Z_mean[ii, jj])
                    elbow_weights.append(3.0)
                elif ii == i and jj < best_j and (best_j - jj) <= 2:
                    # Horizontal equivalent arm (same tree stopped by maxDepth = d)
                    elbow_vals.append(Z_mean[ii, jj])
                    elbow_weights.append(1.5)
                elif jj == best_j and ii > i and (ii - i) <= 2:
                    # Vertical equivalent arm (same tree stopped by countThreshold = t_canon)
                    elbow_vals.append(Z_mean[ii, jj])
                    elbow_weights.append(1.5)
                elif abs(ii - i) <= 1 and abs(jj - best_j) <= 1:
                    elbow_vals.append(Z_mean[ii, jj])
                    elbow_weights.append(1.0)

        pooled_time = float(np.average(elbow_vals, weights=elbow_weights))
        candidates.append((pooled_time, i, best_j))

    # Select the canonical (d*, T*) pair that minimizes the pooled structural execution time
    candidates.sort(key=lambda x: x[0])
    _, best_i, best_j = candidates[0]
    return best_i, best_j


def main():
    compile_go()

    N = 8000
    MAP_SIZE = 1000.0
    RADIUS = 120.0
    ROUNDS = 5
    REPEATS = 7  # 7 interleaved runs per pair (min and max dropped -> mean over 5 runs)

    print(f"2. Generating {N} test points (Map={MAP_SIZE}x{MAP_SIZE}, Radius={RADIUS})...")
    generate_data(num_points=N, map_size=MAP_SIZE)

    depths = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    thresholds = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

    try:
        # 3. Warm-up to stabilize CPU clock frequency and OS file cache
        print("3. Warming up (CPU & OS cache stabilization)...")
        for _ in range(5):
            run_go(5, 32, radius=RADIUS, rounds=ROUNDS)

        # 4. Collect data in randomized interleaved order (prevents thermal throttling bias)
        print(f"4. Running benchmark ({REPEATS} randomized passes across the full grid)...")
        raw_samples = {(i, j): [] for i in range(len(depths)) for j in range(len(thresholds))}
        grid_pairs = [(i, j) for i in range(len(depths)) for j in range(len(thresholds))]

        rng = random.Random(123)
        for r in range(REPEATS):
            rng.shuffle(grid_pairs)
            print(f"   -> Pass {r + 1}/{REPEATS} in progress...")
            for i, j in grid_pairs:
                ms = run_go(depths[i], thresholds[j], radius=RADIUS, rounds=ROUNDS)
                raw_samples[(i, j)].append(ms)

        Z_mean = np.zeros((len(depths), len(thresholds)))
        Z_se = np.zeros((len(depths), len(thresholds)))

        for i in range(len(depths)):
            for j in range(len(thresholds)):
                mean_val, se_val = trimmed_mean_and_se(raw_samples[(i, j)], trim_count=1)
                Z_mean[i, j] = mean_val
                Z_se[i, j] = se_val

        best_yi, best_xi = find_true_mathematical_optimum(depths, thresholds, Z_mean, Z_se, N)
        best_d = depths[best_yi]
        best_t = thresholds[best_xi]
        min_time = Z_mean[best_yi, best_xi]
        min_se = Z_se[best_yi, best_xi]

        # Print table with outlier-filtered trimmed mean values
        print("\n5. Benchmark Results (Trimmed Mean in ms):\n")
        header = f"{'Depth \\ Thresh':>14} | " + " | ".join(f"{t:>6}" for t in thresholds)
        print(header)
        print("-" * len(header))
        for i, d in enumerate(depths):
            row_vals = []
            for j, t in enumerate(thresholds):
                marker = "*" if (i == best_yi and j == best_xi) else " "
                row_vals.append(f"{Z_mean[i, j]:>5.1f}{marker}")
            print(f"{d:>14} | " + " | ".join(row_vals))
        print("-" * len(header))

        theo_leaf_points = N / (4 ** (best_d - 1))
        print(f"\n==================================================================")
        print(f"TRUE MATHEMATICAL OPTIMUM FOUND:")
        print(f"  -> maxDepth       = {best_d}")
        print(f"  -> countThreshold = {best_t}")
        print(f"  -> Execution Time = {min_time:.2f} ± {min_se:.2f} ms")
        print(f"  -> Theoretical check: N / 4^(d-1) = {theo_leaf_points:.1f} points/cell (chosen T={best_t})")
        print(f"==================================================================\n")

    finally:
        # Clean up input file BEFORE opening the blocking GUI window
        if os.path.exists(INPUT_FILE):
            os.remove(INPUT_FILE)

    # 6. Plot 3D Surface + 2D Heatmap with theoretical coupling curve
    X_idx, Y_idx = np.meshgrid(range(len(thresholds)), range(len(depths)))
    fig = plt.figure(figsize=(16, 6.5))

    # Subplot 1: 3D Performance Surface + Optimal Point
    ax3d = fig.add_subplot(1, 2, 1, projection="3d")
    surf = ax3d.plot_surface(
        X_idx, Y_idx, Z_mean, cmap="viridis_r", edgecolor="black", linewidth=0.4, alpha=0.88
    )
    ax3d.scatter(
        [best_xi], [best_yi], [min_time],
        color="red", s=130, zorder=10,
        label=f"Math Optimum: D={best_d}, T={best_t} ({min_time:.1f}±{min_se:.1f}ms)"
    )
    ax3d.set_xticks(range(len(thresholds)))
    ax3d.set_xticklabels(thresholds)
    ax3d.set_yticks(range(len(depths)))
    ax3d.set_yticklabels(depths)
    ax3d.set_xlabel("countThreshold (X)")
    ax3d.set_ylabel("maxDepth (Y)")
    ax3d.set_zlabel("Time (ms) (Z)")
    ax3d.set_title("3D QuadTree Performance Surface (Trimmed Mean)")
    ax3d.legend(loc="upper left")
    fig.colorbar(surf, ax=ax3d, shrink=0.5, aspect=10, label="Time (ms)")

    # Subplot 2: 2D Heatmap + Theoretical Boundary T = N / 4^(d-1)
    ax2d = fig.add_subplot(1, 2, 2)
    im = ax2d.imshow(Z_mean, cmap="viridis_r", aspect="auto", origin="lower")
    ax2d.plot(
        best_xi, best_yi, "ro", markersize=11, markeredgecolor="white", markeredgewidth=2,
        label=f"Optimum: D={best_d}, T={best_t} ({min_time:.1f}ms)"
    )

    # Plot theoretical balance curve: d = 1 + log4(N / T)
    theo_x = np.linspace(0, len(thresholds) - 1, 100)
    theo_t_vals = [2 ** x for x in theo_x]
    theo_d_vals = [1.0 + math.log(N / t, 4) for t in theo_t_vals]
    theo_y = np.interp(theo_d_vals, depths, range(len(depths)))
    ax2d.plot(
        theo_x, theo_y, "w--", linewidth=2.0,
        label=r"Theoretical Curve: $T = N / 4^{d-1}$"
    )

    ax2d.set_xticks(range(len(thresholds)))
    ax2d.set_xticklabels(thresholds)
    ax2d.set_yticks(range(len(depths)))
    ax2d.set_yticklabels(depths)
    ax2d.set_xlabel("countThreshold")
    ax2d.set_ylabel("maxDepth")
    ax2d.set_title("2D Heatmap & Mathematical Coupling Curve")
    ax2d.legend(loc="upper right")
    fig.colorbar(im, ax=ax2d, label="Time (ms)")

    plt.tight_layout()
    plt.savefig("quadtree_3d_benchmark.png", dpi=150)
    print("3D plot saved to 'quadtree_3d_benchmark.png'. Opening interactive window...")

    try:
        plt.show()
    except KeyboardInterrupt:
        print("\nPlot window closed by user.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user.")
        if os.path.exists(INPUT_FILE):
            os.remove(INPUT_FILE)