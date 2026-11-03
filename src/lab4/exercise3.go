package main

import (
	"fmt"
	"sync"
)

type MsgVote struct {
	round int
	val   float64
}

type GraphNodeVote struct {
	id          int
	initialVote float64
	neighbors   []int
}

func voteNode(id int, initialVote float64, in <-chan MsgVote, out []chan<- MsgVote, expectedIn int, rounds int, wg *sync.WaitGroup) {
	defer wg.Done()

	xi := initialVote
	var pending []MsgVote

	for round := 0; round < rounds; round++ {

		for _, ch := range out {
			ch <- MsgVote{round: round, val: xi}
		}

		sum := xi
		receivedCount := 0

		var newPendingMsgs []MsgVote
		for _, msg := range pending {
			if msg.round == round {
				sum += msg.val
				receivedCount++
			} else {
				newPendingMsgs = append(newPendingMsgs, msg)
			}
		}
		pending = newPendingMsgs

		for receivedCount < expectedIn {
			m := <-in
			if m.round == round {
				sum += m.val
				receivedCount++
			} else {
				pending = append(pending, m)
			}
		}

		xi = sum / float64(expectedIn+1)
	}

	votFinal := 0
	if xi > 0.5 {
		votFinal = 1
	}
	fmt.Printf("Node %d | Value convergence: %.4f | Final vote: %d\n", id, xi, votFinal)
}

func AverageFlooding(nodes []GraphNodeVote, rounds int) {
	var wg sync.WaitGroup

	channels := make([]chan MsgVote, len(nodes))
	idToPositionMap := make(map[int]int)

	inDegree := make(map[int]int)

	for i, node := range nodes {
		idToPositionMap[node.id] = i
		for _, outNeighbor := range node.neighbors {
			inDegree[outNeighbor]++
		}
	}

	for i := 0; i < len(nodes); i++ {
		channels[i] = make(chan MsgVote, inDegree[nodes[i].id]*rounds+1)
	}

	for i := 0; i < len(nodes); i++ {
		var out_channels []chan<- MsgVote
		for _, neiID := range nodes[i].neighbors {
			out_channels = append(out_channels, channels[idToPositionMap[neiID]])
		}

		expectedIn := inDegree[nodes[i].id]

		wg.Add(1)
		go voteNode(nodes[i].id, nodes[i].initialVote, channels[i], out_channels, expectedIn, rounds, &wg)
	}

	wg.Wait()
}
