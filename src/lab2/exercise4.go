package main

import (
	"fmt"
	"time"
)

func exercise4() {
	done := make(chan bool)

	go func() {
		fmt.Println("Goroutine started")
		time.Sleep(1 * time.Second)
		fmt.Println("Goroutine finished")
		done <- true
	}()

	<-done
	fmt.Println("Finished")
}
