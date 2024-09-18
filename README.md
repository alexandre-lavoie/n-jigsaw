# 🧩 n-jigsaw

Solver for https://www.youtube.com/watch?v=b5nElEbbnfU

```
Initial
                                                                
       0  +0 -0     1  +2 -2     2  +4 -4     3  +4 -4     4    
      +1           +3           +5           -3           +4    

      -1           -3           -5           +3           -4    
       5  +3 -3     6  +5 -5     7  +3 -3     8  +5 -5     9    
      -4           -3           +6           -5           +2    

      +4           +3           -6           +5           -2    
      10  -5 +5    11  +3 -3    12  +3 -3    13  +5 -5    14    
      +1           -5           -3           +7           +4    

      -1           +5           +3           -7           -4    
      15  -5 +5    16  +3 -3    17  -5 +5    18  +3 -3    19    
      -2           +3           +5           +5           +2    

      +2           -3           -5           -5           -2    
      20  -4 +4    21  -0 +0    22  -2 +2    23  -2 +2    24

Final
                                                                
       0  +0 -0    21  +4 -4    19  +2 -2    14  +4 -4     4    
      +1           -3           -3           -5           +4    

      -1           +3           +3           +5           -4    
      15  -5 +5    11  +3 -3    17  -5 +5    16  +3 -3     3    
      -2           -5           +5           +3           +4    

      +2           +5           -5           -3           -4    
       1  +3 -3    13  +5 -5     7  +3 -3     6  +5 -5     9    
      -0           +7           +6           -3           +2    

      +0           -7           -6           +3           -2    
      22  -5 +5    18  +3 -3    12  +3 -3     8  +5 -5    23    
      -2           +5           -3           -5           +2    

      +2           -5           +3           +5           -2    
      20  -4 +4    10  +1 -1     5  -4 +4     2  -2 +2    24
```

## 🔍 Overview

A greedy search algorithm to find jigsaws with exactly 2 solutions. It uses a [wavefunction collapse](https://robertheaton.com/2018/12/17/wavefunction-collapse-algorithm/)-like solution to "grow" the solution from a set of permutations.

It feels similar to going from one state to another on a Rubik's cube. There's edges, corners, and center pieces. This is in 2D though.

Different sizes can be provided. `7x7` worked without issues on my end.

## 📦 Requirements

`Python 3.12`

## 🖥️ Usage

```
python solve.py [-h] [--width WIDTH] [--height HEIGHT]

options:
  -h, --help       show this help message and exit
  --width WIDTH    Number of jigsaw pieces on the X-axis
  --height HEIGHT  Number of jigsaw pieces on the Y-axis
```

## 📊 Statistics

Using the following time estimate cli:

```
python -m timeit -n 1 -r 100 -s 'import os' 'os.system("python solve.py --width 5 --height 5")'
```

I get the following run statistics:

```
1 loop, best of 100: 79.5 msec per loop
```

This tends to vary between 50 milliseconds and 200 milliseconds (given `random` is used to find solutions).


## 🔣 Algorithm

Start with an initial state.

```
A B C D

E F G H

I J K L

M N O P
```

Create the edges between the pieces. Do not worry about the knob/socket yet.

```
A-B-C-D
| | | |
E-F-G-H
| | | | 
I-J-K-L
| | | |
M-N-O-P
```

Apply permutations on graph to get to the desired/random final state.

```
A-O-I-D
| | | |
E-F-G-H
| | | | 
C-K-J-L
| | | |
M-N-B-P
```

Compare the edges between the initial state and final state. Keep track of the edges that overlap.

```
-B-          -O-
 | <-- == --> |
```

Label the edges that overlap with a unique identifier/number.

```
A-01-B-03-C-04-D
|    |    |    |
05   02   06  07
|    |    |    |
E-08-F-09-G-10-H
|    |    |    |
04   11   12  13
|    |    |    |
I-06-J-14-K-15-L
|    |    |    |
03   16   02  17
|    |    |    |
M-18-N-03-O-01-P
```

Go through the edges and assign knots/slots. Note that edges with the same ID should automatically propagate to the other edge.

```
A>01>B>03>C>04>D
V    V    V    V
05   02   06  07
V    V    V    V
E-08-F-09-G-10-H
^    V    V    V
04   11   12  13
^    V    V    V
I>06>J>14>K>15>L
^    ^    ^    V
03   16   02  17
^    ^    ^    V
M<18<N<03<O<01<P
```

Voila, a solution with the most possible edges. This said, the puzzle might not have only 2 solution. Compare the pieces to see if any of them match (the ID and the knot/slot matters).

```
    ^                  ^  
    06                 06 
    ^                  ^
<03<C<04<    ==    <03<I<04<

    03                 01
    ^                  ^
    M<18     !=        A>05
```

Given `I` and `V` have the same edges, this puzzle has more than 2 solutions.

Repeat this algorithm until a puzzle that only has 2 solutions is found.
