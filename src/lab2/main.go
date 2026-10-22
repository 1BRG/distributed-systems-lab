package main
import ("fmt";
)

type Student struct {
	name string
	age int
}

func(s Student) printStudent() {
	fmt.Println("Name: ", s.name)
	fmt.Println("Age: ", s.age)
}
func main(){
	Student1 := Student{name: "John", age: 20}
	Student1.printStudent()
}