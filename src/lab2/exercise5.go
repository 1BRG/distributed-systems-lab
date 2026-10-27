package main

import (
	"fmt"
)

func send(ch chan<- string) {
	ch <- "Message sent from send function"
}

func receive(in <-chan string, out chan<- string) {
	mesaj := <-in
	out <- mesaj
}

func exercise5() {
	ch1 := make(chan string)
	ch2 := make(chan string)

	go send(ch1)
	go receive(ch1, ch2)

	fmt.Println("Received in main: ", <-ch2)
}
