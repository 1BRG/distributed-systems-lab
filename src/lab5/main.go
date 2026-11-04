package lab5

import (
	"bufio"
	"fmt"
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

	nodes := make([]Point, 0, n)
	for scanner.Scan() {
		var x, y float64
		fmt.Sscan(scanner.Text(), &x, &y)
		nodes = append(nodes, Point{X: x, Y: y})
	}

	maxRounds := 100
	maxDepth := 10
	countThreshold := 4
	radius := 15.0

	remaining := RendezvousQuadTree(nodes, maxRounds, maxDepth, countThreshold, radius)
	fmt.Println("Number of remaining nodes:", remaining)
}
