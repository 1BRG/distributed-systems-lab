package main

import (
	"sync"
)

type Msg struct {
	Value int
	Done  bool
}

func node(id int, in <-chan Msg, out chan<- Msg, leader *int, wg *sync.WaitGroup) {
	defer wg.Done()
	for received := range in {
		if received.Done {
			out <- received
			return
		}
		if received.Value > id {
			out <- received
		} else if received.Value == id {
			*leader = id
			out <- Msg{Value: id, Done: true}
		}
	}
}

func RingFlooding(ids []int) int {
	var wg sync.WaitGroup
	channels := make([]chan Msg, len(ids))
	for i := range ids {
		channels[i] = make(chan Msg, 1)
	}

	var leader int
	for i := 0; i < len(ids); i++ {
		id := ids[i]

		in := channels[i]

		right_out := channels[(i+1)%len(ids)]
		right_out <- Msg{Value: id, Done: false}

		wg.Add(1)
		go node(id, in, right_out, &leader, &wg)

	}
	wg.Wait()

	return leader
}
