package main

import (
	"fmt"
	"math/rand"
)

func generateRobot1(name string, in chan string, out chan string, observer chan bool) {
	x := 0
	y := 0
	for i := 0; i < 5; i++ {
		x += rand.Intn(3) - 1
		y += rand.Intn(3) - 1
		out <- name + ":" + "Im at position (" + fmt.Sprint(x) + ", " + fmt.Sprint(y) + ")"
	}
	close(out)

	for message := range in {
		fmt.Println(message)
	}

	observer <- true
}
func exercise7() {

	ch1 := make(chan string, 5)
	ch2 := make(chan string, 5)
	observer := make(chan bool)

	go generateRobot1("Robot 1", ch1, ch2, observer)
	go generateRobot1("Robot 2", ch2, ch1, observer)

	<-observer
	<-observer
	fmt.Println("Both robots finished!")
}
