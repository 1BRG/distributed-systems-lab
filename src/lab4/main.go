package main

import (
	"fmt"
)

func prepExercise1() {
	nodes := []int{1, 2, 6, 4, 2, 9, 3}
	leader := RingFlooding(nodes)
	fmt.Printf("Leader is: %d\n", leader)
}

func prepExercise2() {
	graphNodes := []GraphNode{
		{id: 1, neighbors: []int{2, 4, 6}},
		{id: 2, neighbors: []int{3, 5}},
		{id: 3, neighbors: []int{4, 6, 1}},
		{id: 4, neighbors: []int{5, 7, 2}},
		{id: 5, neighbors: []int{6, 1}},
		{id: 6, neighbors: []int{7, 2, 4}},
		{id: 7, neighbors: []int{1, 3}},
	}

	graphLeader := GraphFlooding(graphNodes)
	fmt.Printf("Graph Leader is: %d\n", graphLeader)
}

func prepExercise3() {
	graphNodes := []GraphNodeVote{
		{id: 1, initialVote: 1.0, neighbors: []int{2, 4}},
		{id: 2, initialVote: 1.0, neighbors: []int{1, 3}},
		{id: 3, initialVote: 1.0, neighbors: []int{2, 4}},
		{id: 4, initialVote: 0.0, neighbors: []int{3, 1}},
	}

	fmt.Println("Starting majority voting (simulating 30 rounds of convergence)...")
	AverageFlooding(graphNodes, 30)
}
func main() {
	fmt.Println("Exercise 1:")
	prepExercise1()

	fmt.Println("\nExercise 2:")
	prepExercise2()

	fmt.Println("\nExercise 3:")
	prepExercise3()

}
