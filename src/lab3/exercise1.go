package main

import (
	"fmt"
	"math/rand"
	"time"
)

// stocheaza deviatia fata de timpul real
type Clock struct {
	offset time.Duration
}

func (c *Clock) Now() time.Time {
	return time.Now().Add(c.offset)
}

// TODO:
// Calculeaza decalajul theta si round -trip -ul delta
func estimate(t1, t2, t3, t4 time.Time) (theta, delta time.Duration) {
	t2_minus_t1 := t2.Sub(t1)
	t3_minus_t4 := t3.Sub(t4)
	theta = (t2_minus_t1 + t3_minus_t4) / 2

	t4_minus_t1 := t4.Sub(t1)
	t3_minus_t2 := t3.Sub(t2)
	delta = t4_minus_t1 - t3_minus_t2

	return theta, delta
}

func measure(c_clock, s_clock *Clock) (theta, delta time.Duration) {
	// Request
	t1 := c_clock.Now()
	time.Sleep(3*time.Millisecond + time.Duration(rand.Intn(10))*time.Millisecond)
	t2 := s_clock.Now()

	// Procesare intre 5 si 20 ms
	time.Sleep(5*time.Millisecond + time.Duration(rand.Intn(20))*time.Millisecond)
	t3 := s_clock.Now()

	// Response
	time.Sleep(3*time.Millisecond + time.Duration(rand.Intn(10))*time.Millisecond)
	t4 := c_clock.Now()

	return estimate(t1, t2, t3, t4)
}

func simulate(c_clock *Clock, s_clock *Clock, iterations int) (best_theta, min_delta time.Duration) {
	best_theta = time.Duration(1<<63 - 1) // Set to maximum possible duration
	min_delta = time.Duration(1<<63 - 1)  // Set to maximum possible duration
	for i := 0; i < iterations; i++ {
		theta_i, delta_i := measure(c_clock, s_clock)
		fmt.Printf("Measure %v with theta: %v and delta: %v\n", i, theta_i, delta_i)
		if delta_i < min_delta {
			min_delta = delta_i
			best_theta = theta_i
		}
	}

	return best_theta, min_delta
}
