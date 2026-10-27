package main

import (
	"fmt"
	"math/rand"
	"time"
)

func generateRobot(name string, ch chan string) {
	time.Sleep(time.Duration(rand.Intn(1000)) * time.Millisecond)
	ch <- name
}
func exercise6() {
	ch1 := make(chan string)
	ch2 := make(chan string)

	go generateRobot("Robot 1", ch1)
	go generateRobot("Robot 2", ch2)

	select {
	case winner := <-ch1:
		fmt.Printf("%v won the race!\n", winner)
	case winner := <-ch2:
		fmt.Printf("%v won the race!\n", winner)
	}

}
