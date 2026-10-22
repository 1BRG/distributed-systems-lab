package main
import ("fmt"; "os"; "bufio";"strings"
)

func isPrime(n int) bool {
    if(n <= 1 || (n % 2 == 0 && n != 2)){
        return false
    }

    if(n == 2){
        return true;
    }

    for i := 3; i * i <= n; i += 2{
        if(n % i == 0){
            return false
        }
    }
    return true
}

func exercise1()  {
    var number int
    fmt.Print("Enter a number: ")
    scanner := bufio.NewScanner(os.Stdin)
    scanner.Scan()
    fmt.Sscan(scanner.Text(), &number)

    if(isPrime(number)) {
        fmt.Println("The number is prime.")
    } else {
        fmt.Println("The number is not prime.")
    }
}

func exercise2(){
    var numbers [5] int32 = [5]int32{6, 2, 1, 4, 5}
    var ok bool = true

    for ok{
        ok = false;
        for i := 0; i < len(numbers) - 1; i++{
            if(numbers[i] > numbers[i + 1]){
                numbers[i], numbers[i + 1] = numbers[i + 1], numbers[i]
                ok = true
                }
        }
    }

    for i := 0; i < len(numbers); i++{
        fmt.Print(numbers[i], " ")
    }
    fmt.Println()
}

func exercise3(){
    numbers := []int32{1, 2, 3, 4, 5}
    evenNumbers := []int32{}
    for i := 0; i < len(numbers); i++ {
        if(numbers[i]%2 == 0) {
            evenNumbers = append(evenNumbers, numbers[i])
        }
    }
    for i := 0; i < len(evenNumbers); i++ {
        fmt.Print(evenNumbers[i], " ")
    }
    fmt.Println()
}

func exercise4(){
    slice := []float32{1.2, 2.4, 3.1, 4.3, 5.5}
    var index int
    fmt.Print("Enter the index of the element to remove: ")
    scanner := bufio.NewScanner(os.Stdin)
    scanner.Scan()
    fmt.Sscan(scanner.Text(), &index)

    withoutIdx := append(slice[0:index], slice[index+1:]...)
    fmt.Println("Slice after removing element at index", index, ":", withoutIdx)
}

func exercise5(){
    slice := []string{"Laboratorul", "de", "sisteme", "distribuite"}
    for i := 0; i < len(slice) / 2; i++ {
        slice[i], slice[len(slice)-1-i] = slice[len(slice)-1-i], slice[i]
    }
    for i := 0; i < len(slice); i++ {
        fmt.Print(slice[i], " ")
    }

    fmt.Println()

}

func exercise6(){
    studentsAndHeights := map[string]int{
        "Andrei": 190,
        "Maria": 165,
        "Ion": 182,
        "Elena": 172,
        "George": 178,
        "Ana": 165,
    }

    var names []string
    var heights []int


    for name, height := range studentsAndHeights {
        names = append(names, name)
        heights = append(heights, height)
    }

    ok := true
    for ok {
        ok = false
        for i := 0; i < len(heights)-1; i++ {
            if(heights[i] < heights[i+1]) {
                heights[i], heights[i+1] = heights[i+1], heights[i]
                
                names[i], names[i+1] = names[i+1], names[i]  
                ok = true
            }
        }
    }

    for i := 0; i < len(names); i++ {
        fmt.Printf("%v: %v\n", names[i], heights[i])
    }
}

func exercise7(){
    file , err := os.Open("file.txt")
    if err != nil {
        fmt.Println(err)
    }

    defer file.Close ()
    scanner := bufio.NewScanner(file)
    
    wordsAndCounts := make(map[string]int)
    for scanner.Scan() {
        line := scanner.Text()
        words := strings.Fields(line)
        for _, word := range words {
            wordsAndCounts[word]++
        }
    }

    for word, count := range wordsAndCounts {
        fmt.Printf("%v: %v\n", word, count)
    }
}

func exercise8(){
    employeesAndDepartmentsId := map[string]int{
        "Ana Popescu": 1,
        "Mihai Ionescu": 2,
        "Bogdan Radu": 1,
        "Elena Dumitrescu": 3,
        "Cristian Vasile": 2,
        "Ioana Enache": 1,
    }

    departmentsAndEmployees := make(map[int][]string)
    for employee, departmentId := range employeesAndDepartmentsId {
        departmentsAndEmployees[departmentId] = append(departmentsAndEmployees[departmentId], employee)
    }

    for departmentId, employees := range departmentsAndEmployees {
        fmt.Printf("Department %v: %v\n", departmentId, employees)
    }
}

func exercise9(){
    var numbers [5] int32 = [5]int32{2, 7, 11, 8, 4}
    seen := make(map[int32]int)

    fmt.Print("Enter a target number: ")
    var target int32
    scanner := bufio.NewScanner(os.Stdin)
    scanner.Scan()
    fmt.Sscan(scanner.Text(), &target)

    for i, num := range numbers {
        complement := target - num

        complementIndex, found := seen[complement]
        if(found) {
            fmt.Printf("Found numbers: %v and %v at indices %v and %v\n", complement, num, complementIndex, i)
        }
        
        seen[num] = i
    }
}

func main(){
    fmt.Println("Lab 1 - Go")
    fmt.Println("\nExercise 1: Check if a number is prime")
    exercise1()
    fmt.Println("\nExercise 2: Sort an array of integers")
    exercise2()
    fmt.Println("\nExercise 3: Filter even numbers from a slice")
    exercise3()
    fmt.Println("\nExercise 4: Remove an element from a slice by index")
    exercise4()
    fmt.Println("\nExercise 5: Reverse a slice of strings")
    exercise5()
    fmt.Println("\nExercise 6: Display students and their heights")
    exercise6()
    fmt.Println("\nExercise 7: Count words in a file")
    exercise7()
    fmt.Println("\nExercise 8: Group employees by department")
    exercise8()
    fmt.Println("\nExercise 9: Find two numbers that add up to a target")
    exercise9()
}