package main

import (
	"fmt"
)

func exercise2() {
	ch := make(chan string)
	done := make(chan bool)

	go func() {
		received := <-ch
		fmt.Println(received)
		done <- true
	}()

	ch <- "Salut"
	<-done
}
