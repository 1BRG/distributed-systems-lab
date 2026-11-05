package lab5

import (
	"fmt"
	"sync"
)

func compressPoints(points []Point, eps float64) []Point {
	if len(points) <= 1 {
		return points
	}

	sh := NewSpatialHashing(eps, len(points))
	active := make([]Point, 0, len(points))

	for _, p := range points {
		if !sh.overlaps(p) {
			sh.insert(p)
			active = append(active, p)
		}
	}
	return active
}

func RendezvousQuadTree(nodes []Point, maxRounds int, maxDepth int, countThreshold int, radius float64) int {

	const eps = 1e-5

	for round := 0; round < maxRounds; round++ {
		if len(nodes) <= 1 {
			fmt.Println("Rendezvous achieved in round", round, "in node(", nodes[0].X, nodes[0].Y, ")")
			return 1
		}

		var maxX, maxY, minX, minY float64
		maxX = nodes[0].X
		minX = nodes[0].X
		maxY = nodes[0].Y
		minY = nodes[0].Y
		for _, node := range nodes {
			if node.X > maxX {
				maxX = node.X
			}
			if node.X < minX {
				minX = node.X
			}
			if node.Y > maxY {
				maxY = node.Y
			}
			if node.Y < minY {
				minY = node.Y
			}
		}

		qt := NewQuadTree(minX-1, minY-1, maxX+1, maxY+1, maxDepth, countThreshold)
		for _, node := range nodes {
			qt.insert(node.X, node.Y)
		}

		nextPositions := make([]Point, len(nodes))
		var wg sync.WaitGroup

		for i := range nodes {
			wg.Add(1)
			go func(idx int, node Point) {
				defer wg.Done()
				count, sumX, sumY := qt.head.query(node.X, node.Y, radius)

				nextPositions[idx] = Point{
					X: sumX / float64(count),
					Y: sumY / float64(count),
				}
			}(i, nodes[i])
		}

		wg.Wait()

		nodes = compressPoints(nextPositions, eps)
	}

	return len(nodes)
}

func RendezvousSpatialHashing(nodes []Point, maxRounds int, radius float64) int {

	const eps = 1e-5

	for round := 0; round < maxRounds; round++ {
		if len(nodes) <= 1 {
			fmt.Println("Rendezvous achieved in round", round, "in node(", nodes[0].X, nodes[0].Y, ")")
			return 1
		}

		sh := NewSpatialHashing(radius, len(nodes))
		for _, node := range nodes {
			sh.insert(node)
		}

		nextPositions := make([]Point, len(nodes))
		var wg sync.WaitGroup

		for i := range nodes {
			wg.Add(1)
			go func(idx int, node Point) {
				defer wg.Done()
				count, sumX, sumY := sh.query(node)

				nextPositions[idx] = Point{
					X: sumX / float64(count),
					Y: sumY / float64(count),
				}
			}(i, nodes[i])
		}

		wg.Wait()

		nodes = compressPoints(nextPositions, eps)
	}

	return len(nodes)
}
