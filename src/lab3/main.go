package main

import (
	"fmt"
	"sort"
	"sync"
	"time"
)

func main() {
	fmt.Println("Exercise 1:")
	s_clock := &Clock{offset: 0}
	c_clock := &Clock{offset: 100 * time.Millisecond}

	theta, delta := measure(c_clock, s_clock)
	fmt.Printf("Theta: %v, Delta: %v\n", theta, delta)

	best_theta, min_delta := simulate(c_clock, s_clock, 10)
	fmt.Printf("Best Theta: %v, Min Delta: %v\n", best_theta, min_delta)

	fmt.Println("\nExercise 2:")

	ch12 := make(chan Message, 1)
	ch23 := make(chan Message, 1)
	ch31 := make(chan Message, 1)

	eventsChan := make(chan Event, 20)
	var wg sync.WaitGroup

	runProcess := func(id int, in <-chan Message, out chan<- Message) {
		defer wg.Done()
		clock := &LamportClock{counter: 0}

		clock.Tick()
		eventsChan <- Event{process: id, internal_counter: clock.counter, kind: "internal"}

		ts := clock.Send()
		out <- Message{sender: id, ts: ts}
		eventsChan <- Event{process: id, internal_counter: clock.counter, kind: "send"}

		msg := <-in
		clock.Receive(msg.ts)
		eventsChan <- Event{process: id, internal_counter: clock.counter, kind: "recv"}
	}

	wg.Add(3)
	go runProcess(1, ch31, ch12)
	go runProcess(2, ch12, ch23)
	go runProcess(3, ch23, ch31)

	wg.Wait()
	close(eventsChan)

	var allEvents []Event
	for e := range eventsChan {
		allEvents = append(allEvents, e)
	}

	sort.Slice(allEvents, func(i, j int) bool {
		return less(allEvents[i], allEvents[j])
	})

	for _, e := range allEvents {
		fmt.Printf("Process: %d | Internal Counter: %2d | Kind: %s\n", e.process, e.internal_counter, e.kind)
	}
}
