package main

import (
	"fmt"
)

func exercise3() {
	ch := make(chan string)

	go func() {
		ch <- "mesaj1"
		ch <- "mesaj2"
	}()

	fmt.Println(<-ch)
	fmt.Println(<-ch)
}
