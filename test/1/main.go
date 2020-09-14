package main

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
)

const (
	maxn = int(1e5 + 50)
	mod  = int(1e9 + 7)
	eps  = 1e-8
	inf  = int(0x3f3f3f3f)
)

type Pair struct {
	key int
	value int
}

func main() {
	var a, b int
	scanInt(&a)
	scanInt(&b)
	printlnInts(a + b)
	out.Flush()
}

/*********************** I/O ***********************/

var channelType chan string
var in *bufio.Scanner
var out = bufio.NewWriter(os.Stdout)
var oWg *sync.WaitGroup

// string and slice are the return value
func init() {
	in = bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1024), int(1e+9))
	in.Split(bufio.ScanWords)
	channelType = make(chan string, 16)
	oWg = &sync.WaitGroup{}
	oWg.Add(1)
	writer := bufio.NewWriter(os.Stdout)
	go func() {
		defer oWg.Done()
		defer writer.Flush()

		for line := range channelType {
			writer.WriteString(line + "\n")
		}
	}()
}
func scanString() string { in.Scan(); return in.Text() }
func scanInt(a *int)     { *a, _ = strconv.Atoi(scanString()) }
func scanInts(a ...*int) {
	for i := range a {
		*a[i], _ = strconv.Atoi(scanString())
	}
}
func scanInt64(a *int64) { *a, _ = strconv.ParseInt(scanString(), 10, 64) }
func scanInt64s(a ...*int64) {
	for i := range a {
		*a[i], _ = strconv.ParseInt(scanString(), 10, 64)
	}
}
func scanStringSlice(n int) []string {
	s := make([]string, n)
	for i := 0; i < n; i++ {
		s[i] = scanString()
	}
	return s
}
func scanIntSlice(n int) []int {
	arr := make([]int, n)
	for i := 0; i < n; i++ {
		scanInt(&arr[i])
	}
	return arr
}
func scanInt64Slice(n int) []int64 {
	arr := make([]int64, n)
	for i := 0; i < n; i++ {
		scanInt64(&arr[i])
	}
	return arr
}
func printlnInts(args ...int) {
	for _, x := range args {
		fmt.Fprint(out, x, " ")
	}
	fmt.Fprintln(out)
}
func printlnInt64s(args ...int64) {
	for _, x := range args {
		fmt.Fprint(out, x, " ")
	}
	fmt.Fprintln(out)
}
func printIntSlice(a []int, flag bool) {
	for _, x := range a {
		fmt.Fprint(out, x, " ")
	}
	if flag { fmt.Fprintln(out) }
}
func printInt64Slice(a []int64, flag bool) {
	for _, x := range a {
		fmt.Fprint(out, x, " ")
	}
	if flag { fmt.Fprintln(out) }
}
func printRuneSlice(a []rune, flag bool) {
	for _, x := range a {
		fmt.Fprintf(out, "%c", x)
	}
	if flag { fmt.Fprintln(out) }
}
func putchar(a ...rune) {
	for _, x := range a {
		fmt.Fprintf(out, "%c", x)
	}
}
func printString(s string) { fmt.Fprintln(out, s) }

/*********************** Utils ***********************/

func stringEquivalent(v interface{}) string { return fmt.Sprintf("%v", v) }
func spaceSeperatedStringFromArray(a []int) string {
	sb := strings.Builder{}
	sb.Grow(len(a) * 9)
	for i := range a {
		sb.WriteString(strconv.Itoa(a[i]) + " ")
	}
	return sb.String()
}
func spaceSeperatedStringFromArray64(a []int64) string {
	sb := strings.Builder{}
	sb.Grow(len(a) * 9)
	for i := range a {
		sb.WriteString(strconv.FormatInt(a[i], 10) + " ")
	}
	return sb.String()
}
func minMaxFromArray(args ...int64) (int64, int64) {
	minVal, maxVal := int64(math.MaxInt64), int64(math.MinInt64)
	for _, v := range args {
		if v < minVal {
			minVal = v
		}
		if v > maxVal {
			maxVal = v
		}
	}
	return minVal, maxVal
}
func minElementFromArray(args ...int64) int64 { mn, _ := minMaxFromArray(args...); return mn }
func maxElementFromArray(args ...int64) int64 { _, mx := minMaxFromArray(args...); return mx }
func lcmCalculation(a, b int64) int64         { return a / gcdCalculation(a, b) * b }
func gcdCalculation(a, b int64) int64 {
	if a == 0 {
		return b
	}
	return gcdCalculation(b%a, a)
}
func sortInt64Slice(a []int64) { sort.Slice(a, func(i, j int) bool { return a[i] < a[j] }) }
func absoluteValue(x int64) int64 {
	if x < 0 {
		return -x
	}
	return x
}
func min(args ...int) int { mn, _ := minMaxFinder(args...); return mn }
func max(args ...int) int { _, mx := minMaxFinder(args...); return mx }
func minMaxFinder(args ...int) (int, int) {
	minVal, maxVal := int(math.MaxInt32), int(math.MinInt32)
	for _, v := range args {
		if v < minVal {
			minVal = v
		}
		if v > maxVal {
			maxVal = v
		}
	}
	return minVal, maxVal
}
func same(x, y double) bool { return math.Abs(float64(x-y)) < eps }
func popcount(x int) (res int) {
	for i := 0; i < 32; i++ {
		if 1 == (1 & (x >> uint(i))) {
			res++
		}
	}
	return
}
func qp(a, n int64) (res int64) {
	for ; n > 0; n >>= 1 {
		if (n & 1) == 1 {
			res = res * a % int64(mod)
		}
		a = a * a % int64(mod)
	}
	return
}
func divUp(a, b int64) int64 {
	if a % b == 0 { return a / b } else { return a / b + 1 }
}
// [l, r)
func reverse(a *[]rune, l, r int) {
	for i, j := l, r - 1; i < j; i, j = i + 1, j - 1 {
		(*a)[i], (*a)[j] = (*a)[j], (*a)[i]
	}
}

/*********************** Structs ***********************/
type pair struct{ X, Y int }
type double float64
type pairSlice []pair

func (p pairSlice) Len() int { return len(p) }
func (p pairSlice) Less(i, j int) bool {
	if p[i].X != p[j].X {
		return p[i].X < p[j].X
	} else {
		return p[i].Y < p[j].Y
	}
}
func (p pairSlice) Swap(i, j int) { p[i], p[j] = p[j], p[i] }