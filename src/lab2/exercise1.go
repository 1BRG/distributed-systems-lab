package main

import (
	"fmt"
)

func exercise1() {
	ch := make(chan string)

	go func() {
		ch <- "Salut"
	}()

	received := <-ch
	fmt.Println(received)
}
