import subprocess
import random
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

INPUT_FILE = "bench_input.txt"
BINARY_NAME = "rendezvous_bench.exe" if os.name == "nt" else "./rendezvous_bench"

def generate_data(num_points=1500, map_size=1000.0):
    random.seed(42)
    points = []
    centers = [(random.uniform(100, map_size - 100), random.uniform(100, map_size - 100)) for _ in range(8)]
    for _ in range(num_points):
        cx, cy = random.choice(centers)
        x = cx + random.gauss(0, 25.0)
        y = cy + random.gauss(0, 25.0)
        points.append((x, y))

    with open(INPUT_FILE, "w") as f:
        f.write(f"{len(points)}\n")
        for x, y in points:
            f.write(f"{x:.6f} {y:.6f}\n")

def compile_go():
    print("1. Compiling Go project...")
    res = subprocess.run(["go", "build", "-o", BINARY_NAME, "."], capture_output=True, text=True)
    if res.returncode != 0:
        print("Compilation error:\n", res.stderr)
        exit(1)

def run_go(depth, threshold, radius=60.0, rounds=8):
    exec_path = f".\\{BINARY_NAME}" if os.name == "nt" else BINARY_NAME
    cmd = [
        exec_path,
        "-file", INPUT_FILE,
        "-depth", str(depth),
        "-threshold", str(threshold),
        "-radius", str(radius),
        "-rounds", str(rounds)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if line.startswith("BENCH_TIME_MS:"):
            return float(line.replace("BENCH_TIME_MS:", ""))
    return 0.0

def main():
    compile_go()

    N = 1500
    print(f"2. Generating {N} test points...")
    generate_data(num_points=N)

    depths = list(range(2, 21, 2))
    thresholds = list(range(1, 22, 2))

    Z = np.zeros((len(depths), len(thresholds)))

    min_time = float("inf")
    best_d, best_t = None, None

    print("\n3. Running benchmark for 3D surface...\n")
    header = f"{'Depth \\ Thresh':>14} | " + " | ".join(f"{t:>6}" for t in thresholds)
    print(header)
    print("-" * len(header))

    for i, d in enumerate(depths):
        row_vals = []
        for j, t in enumerate(thresholds):
            ms = (run_go(d, t) + run_go(d, t)) / 2.0
            Z[i, j] = ms
            row_vals.append(f"{ms:>6.1f}")
            if ms < min_time:
                min_time = ms
                best_d, best_t = d, t
        print(f"{d:>14} | " + " | ".join(row_vals))

    print("-" * len(header))
    print(f"\nGLOBAL MINIMUM FOUND: maxDepth = {best_d}, countThreshold = {best_t} -> Time: {min_time:.2f} ms\n")

    X, Y = np.meshgrid(thresholds, depths)

    fig = plt.figure(figsize=(15, 6))

    ax3d = fig.add_subplot(1, 2, 1, projection='3d')
    surf = ax3d.plot_surface(X, Y, Z, cmap='viridis_r', edgecolor='black', linewidth=0.3, alpha=0.85)
    ax3d.scatter([best_t], [best_d], [min_time], color='red', s=120, label=f'Min: D={best_d}, T={best_t} ({min_time:.1f}ms)', zorder=10)

    ax3d.set_xlabel('countThreshold (X)')
    ax3d.set_ylabel('maxDepth (Y)')
    ax3d.set_zlabel('Time (ms) (Z)')
    ax3d.set_title('3D QuadTree Performance Surface')
    ax3d.legend()
    fig.colorbar(surf, ax=ax3d, shrink=0.5, aspect=10, label='Time (ms)')

    ax2d = fig.add_subplot(1, 2, 2)
    im = ax2d.imshow(Z, cmap='viridis_r', aspect='auto', origin='lower')
    ax2d.set_xticks(range(len(thresholds)))
    ax2d.set_xticklabels(thresholds)
    ax2d.set_yticks(range(len(depths)))
    ax2d.set_yticklabels(depths)
    ax2d.set_xlabel('countThreshold')
    ax2d.set_ylabel('maxDepth')
    ax2d.set_title('Top View (2D Heatmap)')
    fig.colorbar(im, ax=ax2d, label='Time (ms)')

    plt.tight_layout()
    plt.savefig("quadtree_3d_benchmark.png", dpi=150)
    print("3D plot saved to 'quadtree_3d_benchmark.png'. Opening interactive window...")
    plt.show()

    if os.path.exists(INPUT_FILE):
        os.remove(INPUT_FILE)

if __name__ == "__main__":
    main()