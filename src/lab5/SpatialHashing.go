package lab5

import (
	"math"
)

type gridCell struct {
	cx, cy int
}

type SpatialHashing struct {
	grid   map[gridCell][]Point
	radius float64
}

func NewSpatialHashing(radius float64, estimateSize int) *SpatialHashing {
	return &SpatialHashing{
		grid:   make(map[gridCell][]Point, estimateSize),
		radius: radius,
	}
}

func (sh *SpatialHashing) insert(p Point) {
	cell := gridCell{
		cx: int(math.Floor(p.X / sh.radius)),
		cy: int(math.Floor(p.Y / sh.radius)),
	}
	sh.grid[cell] = append(sh.grid[cell], p)
}

func (sh *SpatialHashing) overlaps(p Point) bool {
	cell := gridCell{
		cx: int(math.Floor(p.X / sh.radius)),
		cy: int(math.Floor(p.Y / sh.radius)),
	}

	for dx := -1; dx <= 1; dx++ {
		for dy := -1; dy <= 1; dy++ {
			neighborCell := gridCell{cx: cell.cx + dx, cy: cell.cy + dy}
			for _, a := range sh.grid[neighborCell] {
				distX := p.X - a.X
				distY := p.Y - a.Y
				if distX*distX+distY*distY <= sh.radius*sh.radius {
					return true
				}
			}
		}
	}

	return false
}

func (sh *SpatialHashing) query(p Point) (int, float64, float64) {
	cell := gridCell{
		cx: int(math.Floor(p.X / sh.radius)),
		cy: int(math.Floor(p.Y / sh.radius)),
	}

	sumX := 0.0
	sumY := 0.0
	count := 0

	for dx := -1; dx <= 1; dx++ {
		for dy := -1; dy <= 1; dy++ {
			neighborCell := gridCell{cx: cell.cx + dx, cy: cell.cy + dy}
			for _, a := range sh.grid[neighborCell] {
				distX := p.X - a.X
				distY := p.Y - a.Y
				if distX*distX+distY*distY <= sh.radius*sh.radius {
					sumX += a.X
					sumY += a.Y
					count++
				}
			}
		}
	}

	return count, sumX, sumY
}
