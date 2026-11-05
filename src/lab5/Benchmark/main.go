package main

import (
	"bufio"
	"flag"
	"fmt"
	"lab5"
	"os"
	"time"
)

func main() {
	filePath := flag.String("file", "input.txt", "Input file path")
	algo := flag.String("algo", "quadtree", "Algorithm to run: 'quadtree' or 'spatial'")
	maxRounds := flag.Int("rounds", 100, "Maximum number of rounds")
	maxDepth := flag.Int("depth", 10, "Maximum depth of QuadTree")
	countThreshold := flag.Int("threshold", 4, "Point threshold per node")
	radius := flag.Float64("radius", 15.0, "Communication radius")
	flag.Parse()

	file, err := os.Open(*filePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error opening file: %v\n", err)
		os.Exit(1)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	var n int
	if scanner.Scan() {
		fmt.Sscan(scanner.Text(), &n)
	}

	nodes := make([]lab5.Point, 0, n)
	for scanner.Scan() {
		var x, y float64
		if _, err := fmt.Sscan(scanner.Text(), &x, &y); err == nil {
			nodes = append(nodes, lab5.Point{X: x, Y: y})
		}
	}

	start := time.Now()
	var remaining int
	switch *algo {
	case "quadtree":
		remaining = lab5.RendezvousQuadTree(nodes, *maxRounds, *maxDepth, *countThreshold, *radius)
	case "spatial":
		remaining = lab5.RendezvousSpatialHashing(nodes, *maxRounds, *radius)
	default:
		fmt.Fprintf(os.Stderr, "Unknown algorithm: %s (use 'quadtree' or 'spatial')\n", *algo)
		os.Exit(1)
	}
	elapsedMs := float64(time.Since(start).Microseconds()) / 1000.0

	fmt.Println("Number of remaining nodes:", remaining)
	fmt.Printf("BENCH_TIME_MS:%.3f\n", elapsedMs)
}
