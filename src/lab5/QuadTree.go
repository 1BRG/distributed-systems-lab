package lab5

import (
	"math"
)

type Point struct {
	X float64
	Y float64
}

type QuadTreeNode struct {
	xd, yd, xu, yu float64
	count          int
	sumX, sumY     float64
	subTree        []*QuadTreeNode
	points         []Point
}

type QuadTree struct {
	maxDepth       int
	countThreshold int
	head           *QuadTreeNode
}

func NewQuadTree(xd float64, yd float64, xu float64, yu float64, maxDepth int, countThreshold int) *QuadTree {
	return &QuadTree{
		maxDepth:       maxDepth,
		countThreshold: countThreshold,
		head: &QuadTreeNode{
			xd: xd,
			yd: yd,
			xu: xu,
			yu: yu,
		},
	}
}

func (qt *QuadTreeNode) insideNodeTree(x float64, y float64, node *QuadTreeNode) bool {
	return x >= node.xd && x <= node.xu && y >= node.yd && y <= node.yu
}
func (qt *QuadTreeNode) nodeTreeEntirelyInsideQueryPointRadius(x float64, y float64, node *QuadTreeNode, radius float64) bool {
	radiusSq := radius * radius

	isPointInside := func(px float64, py float64) bool {
		dx := px - x
		dy := py - y
		return (dx*dx + dy*dy) <= radiusSq
	}

	return isPointInside(node.xd, node.yd) &&
		isPointInside(node.xu, node.yd) &&
		isPointInside(node.xd, node.yu) &&
		isPointInside(node.xu, node.yu)
}

func (qt *QuadTreeNode) nodeTreeEntirelyOutsideQueryPointRadius(x float64, y float64, node *QuadTreeNode, radius float64) bool {
	closestX := math.Max(node.xd, math.Min(x, node.xu))
	closestY := math.Max(node.yd, math.Min(y, node.yu))

	dx := closestX - x
	dy := closestY - y
	return (dx*dx + dy*dy) > radius*radius
}

func (qt *QuadTreeNode) pointInsideQueryPointRadius(x float64, y float64, pointX float64, pointY float64, radius float64) bool {
	radiusSq := radius * radius

	isPointInside := func(px float64, py float64) bool {
		dx := px - x
		dy := py - y
		return (dx*dx + dy*dy) <= radiusSq
	}

	return isPointInside(pointX, pointY)
}

func (qt *QuadTree) insert(x float64, y float64) {
	currNode := qt.head
	for depth := 0; depth < qt.maxDepth; depth++ {
		currNode.count++
		currNode.sumX += x
		currNode.sumY += y

		// if the current node has no children and exceeds the count threshold, split it into four quadrants
		if len(currNode.subTree) == 0 && currNode.count > qt.countThreshold && depth < qt.maxDepth-1 {
			midX := (currNode.xd + currNode.xu) / 2
			midY := (currNode.yd + currNode.yu) / 2
			currNode.subTree = []*QuadTreeNode{
				{xd: currNode.xd, yd: currNode.yd, xu: midX, yu: midY},
				{xd: midX, yd: currNode.yd, xu: currNode.xu, yu: midY},
				{xd: currNode.xd, yd: midY, xu: midX, yu: currNode.yu},
				{xd: midX, yd: midY, xu: currNode.xu, yu: currNode.yu},
			}

			//child redistribuition
			for _, point := range currNode.points {
				for _, child := range currNode.subTree {
					if currNode.insideNodeTree(point.X, point.Y, child) {
						child.points = append(child.points, point)
						child.count++
						child.sumX += point.X
						child.sumY += point.Y
						break
					}
				}
			}

			currNode.points = nil
			for _, child := range currNode.subTree {
				if currNode.insideNodeTree(x, y, child) {
					currNode = child
					break
				}
			}
		} else if len(currNode.subTree) == 0 {
			currNode.points = append(currNode.points, Point{X: x, Y: y})
			break
		} else {
			for _, child := range currNode.subTree {
				if currNode.insideNodeTree(x, y, child) {
					currNode = child
					break
				}
			}
		}
	}
}

func (qt *QuadTreeNode) query(x float64, y float64, radius float64) (int, float64, float64) {
	if qt.nodeTreeEntirelyInsideQueryPointRadius(x, y, qt, radius) {
		return qt.count, qt.sumX, qt.sumY
	}

	count := 0
	sumX := 0.0
	sumY := 0.0

	if qt.nodeTreeEntirelyOutsideQueryPointRadius(x, y, qt, radius) {
		return count, sumX, sumY
	}

	if len(qt.subTree) == 0 {
		for _, point := range qt.points {
			if qt.pointInsideQueryPointRadius(x, y, point.X, point.Y, radius) {
				count++
				sumX += point.X
				sumY += point.Y
			}
		}
		return count, sumX, sumY
	} else {

		for _, child := range qt.subTree {
			newCount, newSumX, newSumY := child.query(x, y, radius)
			count += newCount
			sumX += newSumX
			sumY += newSumY
		}
	}

	return count, sumX, sumY
}
