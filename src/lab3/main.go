package main

import (
	"fmt"
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

}
