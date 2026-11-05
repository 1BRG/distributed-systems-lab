import subprocess
import random
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

INPUT_FILE = "bench_input.txt"
BINARY_NAME = "rendezvous_bench.exe" if os.name == "nt" else "./rendezvous_bench"


def generate_data(num_points=8000, map_size=1000.0):
    rng = random.Random(42)
    points = []

    tight_centers = [(250.0, 250.0), (750.0, 250.0), (500.0, 750.0)]
    for _ in range(int(num_points * 0.60)):
        cx, cy = rng.choice(tight_centers)
        x = min(max(cx + rng.gauss(0, 18.0), 0.0), map_size)
        y = min(max(cy + rng.gauss(0, 18.0), 0.0), map_size)
        points.append((x, y))

    med_centers = [(250.0, 750.0), (750.0, 750.0), (500.0, 450.0)]
    for _ in range(num_points - len(points)):
        cx, cy = rng.choice(med_centers)
        x = min(max(cx + rng.gauss(0, 45.0), 0.0), map_size)
        y = min(max(cy + rng.gauss(0, 45.0), 0.0), map_size)
        points.append((x, y))

    rng.shuffle(points)

    with open(INPUT_FILE, "w") as f:
        f.write(f"{len(points)}\n")
        for x, y in points:
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


def run_go(depth, threshold, radius=35.0, rounds=5):
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
        if line.startswith("QT_ONLY_MS:"):
            return float(line.replace("QT_ONLY_MS:", ""))
        if line.startswith("BENCH_TIME_MS:"):
            ms_fallback = float(line.replace("BENCH_TIME_MS:", ""))
    return ms_fallback if "ms_fallback" in locals() else float("inf")


def trimmed_mean_and_se(samples, trim_count=1):
    s = sorted(samples)
    if len(s) > 2 * trim_count:
        s = s[trim_count:-trim_count]
    arr = np.array(s, dtype=float)
    mean = float(np.mean(arr))
    se = float(np.std(arr, ddof=1) / np.sqrt(len(arr))) if len(arr) > 1 else 0.0
    return mean, se


def main():
    compile_go()

    N = 8000
    MAP_SIZE = 1000.0
    RADIUS = 35.0
    ROUNDS = 5
    REPEATS = 5

    print(f"2. Generating {N} clustered points (Map={MAP_SIZE}x{MAP_SIZE}, Radius={RADIUS})...")
    generate_data(num_points=N, map_size=MAP_SIZE)

    depths = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    thresholds = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

    try:
        print("3. Warming up (CPU & OS cache stabilization)...")
        for _ in range(4):
            run_go(7, 32, radius=RADIUS, rounds=ROUNDS)

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

        best_yi, best_xi = np.unravel_index(np.argmin(Z_mean), Z_mean.shape)
        best_d = depths[best_yi]
        best_t = thresholds[best_xi]
        min_time = Z_mean[best_yi, best_xi]
        min_se = Z_se[best_yi, best_xi]

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

        print(f"\n==================================================================")
        print(f"REAL MEASURED GLOBAL MINIMUM:")
        print(f"  -> maxDepth       = {best_d}")
        print(f"  -> countThreshold = {best_t}")
        print(f"  -> Execution Time = {min_time:.2f} +/- {min_se:.2f} ms")
        print(f"==================================================================\n")

    finally:
        if os.path.exists(INPUT_FILE):
            os.remove(INPUT_FILE)

    X_idx, Y_idx = np.meshgrid(range(len(thresholds)), range(len(depths)))
    fig = plt.figure(figsize=(16, 6.5))

    ax3d = fig.add_subplot(1, 2, 1, projection="3d")
    surf = ax3d.plot_surface(
        X_idx, Y_idx, Z_mean, cmap="viridis_r", edgecolor="black", linewidth=0.4, alpha=0.88
    )
    ax3d.scatter(
        [best_xi], [best_yi], [min_time],
        color="red", s=130, zorder=10,
        label=f"Real Min: D={best_d}, T={best_t} ({min_time:.1f}ms)"
    )
    ax3d.set_xticks(range(len(thresholds)))
    ax3d.set_xticklabels(thresholds)
    ax3d.set_yticks(range(len(depths)))
    ax3d.set_yticklabels(depths)
    ax3d.set_xlabel("countThreshold (X)")
    ax3d.set_ylabel("maxDepth (Y)")
    ax3d.set_zlabel("Time (ms) (Z)")
    ax3d.set_title("3D QuadTree Performance on Clustered Data")
    ax3d.legend(loc="upper left")
    fig.colorbar(surf, ax=ax3d, shrink=0.5, aspect=10, label="Time (ms)")

    ax2d = fig.add_subplot(1, 2, 2)
    im = ax2d.imshow(Z_mean, cmap="viridis_r", aspect="auto", origin="lower")
    ax2d.plot(
        best_xi, best_yi, "ro", markersize=11, markeredgecolor="white", markeredgewidth=2,
        label=f"Real Min: D={best_d}, T={best_t} ({min_time:.1f}ms)"
    )
    ax2d.set_xticks(range(len(thresholds)))
    ax2d.set_xticklabels(thresholds)
    ax2d.set_yticks(range(len(depths)))
    ax2d.set_yticklabels(depths)
    ax2d.set_xlabel("countThreshold")
    ax2d.set_ylabel("maxDepth")
    ax2d.set_title("Top View (2D Heatmap - Clustered Data)")
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