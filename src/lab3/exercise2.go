package main

type LamportClock struct{ counter int }

// incrementeaza contorul
func (l *LamportClock) Tick() {
	l.counter++
}

func (l *LamportClock) Send() int {
	l.counter++
	return l.counter
}

func (l *LamportClock) Receive(ts int) {
	if ts > l.counter {
		l.counter = ts
	}
	l.counter++
}

type Message struct{ sender, ts int }

type Event struct {
	process          int
	internal_counter int
	kind             string // "internal", "send", "recv"
}

// TODO: retuneaza true daca a precede b
func less(a, b Event) bool {
	return a.internal_counter < b.internal_counter
}
