package main

import (
	"bufio"
	"fmt"
	"lab5"
	"os"
)

func main() {
	file, _ := os.Open("input.txt")
	defer file.Close()

	scanner := bufio.NewScanner(file)

	var n int
	if scanner.Scan() {
		fmt.Sscan(scanner.Text(), &n)
	}

	nodes := make([]lab5.Point, 0, n)
	for scanner.Scan() {
		var x, y float64
		fmt.Sscan(scanner.Text(), &x, &y)
		nodes = append(nodes, lab5.Point{X: x, Y: y})
	}

	maxRounds := 100
	maxDepth := 10
	countThreshold := 4
	radius := 15.0

	remaining := lab5.RendezvousQuadTree(nodes, maxRounds, maxDepth, countThreshold, radius)
	fmt.Println("Number of remaining nodes:", remaining)

	remainingSh := lab5.RendezvousSpatialHashing(nodes, maxRounds, radius)
	fmt.Println("Number of remaining nodes:", remainingSh)
}
