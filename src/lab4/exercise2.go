package main

import (
	"sync"
)

type GraphNode struct {
	id        int
	neighbors []int
}

type GraphMsg struct {
	id    int
	round int
}

func graphNode(id int, in <-chan GraphMsg, out []chan<- GraphMsg, inDegree int, leader *int, wg *sync.WaitGroup, rounds int) {
	defer wg.Done()

	maxId := id
	expectedMsgs := inDegree

	var pendingMsgs []GraphMsg

	for round := 0; round < rounds; round++ {
		for _, out_neighbor := range out {
			out_neighbor <- GraphMsg{id: maxId, round: round}
		}

		received_count := 0
		var newPendingMsgs []GraphMsg
		for _, msg := range pendingMsgs {
			if msg.round == round {
				received_count++
				if msg.id > maxId {
					maxId = msg.id
				}
			} else {
				newPendingMsgs = append(newPendingMsgs, msg)
			}
		}

		pendingMsgs = newPendingMsgs
		for received_count < expectedMsgs {
			msg := <-in
			if msg.round == round {
				received_count++
				if msg.id > maxId {
					maxId = msg.id
				}
			} else {
				pendingMsgs = append(pendingMsgs, msg)
			}
		}
	}
	if maxId == id {
		*leader = id
	}

}

func GraphFlooding(nodes []GraphNode) int {
	var wg sync.WaitGroup
	channels := make([]chan GraphMsg, len(nodes))
	idToPositionMap := make(map[int]int)

	rounds := len(nodes)
	var leader int

	inDegree := make(map[int]int)

	for i := 0; i < len(nodes); i++ {
		idToPositionMap[nodes[i].id] = i
		for _, nei := range nodes[i].neighbors {
			inDegree[nei]++
		}
	}
	for i := 0; i < len(nodes); i++ {
		channels[i] = make(chan GraphMsg, inDegree[nodes[i].id]*rounds)
	}

	for i := 0; i < len(nodes); i++ {
		var out_channels []chan<- GraphMsg

		for _, nei := range nodes[i].neighbors {
			out_channels = append(out_channels, channels[idToPositionMap[nei]])
		}
		wg.Add(1)

		go graphNode(nodes[i].id, channels[i], out_channels, inDegree[nodes[i].id], &leader, &wg, rounds)
	}
	wg.Wait()

	return leader
}
