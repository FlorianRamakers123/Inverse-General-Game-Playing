index(1).
index(2).
index(3).
role(white).
role(black).
init_cell(1, 1, b).
init_cell(1, 2, b).
init_cell(1, 3, b).
init_cell(2, 1, b).
init_cell(2, 2, b).
init_cell(2, 3, b).
init_cell(3, 1, b).
init_cell(3, 2, b).
init_cell(3, 3, b).
base_control(white).
base_control(black).
init_control(white).
line(X) :- row(M, X).
line(X) :- diagonal(X).
line(X) :- column(M, X).
input(R, noop) :- role(R).
open :- true_cell(M, N, b).
base_cell(M, N, x) :- index(M), index(N).
base_cell(M, N, o) :- index(M), index(N).
base_cell(M, N, b) :- index(M), index(N).
input_mark(R, M, N) :- role(R), index(M), index(N).
row(M, X) :- true_cell(M, 1, X), true_cell(M, 2, X), true_cell(M, 3, X).
diagonal(X) :- true_cell(1, 1, X), true_cell(2, 2, X), true_cell(3, 3, X).
diagonal(X) :- true_cell(1, 3, X), true_cell(2, 2, X), true_cell(3, 1, X).
column(N, X) :- true_cell(1, N, X), true_cell(2, N, X), true_cell(3, N, X).
%%%%%%%%%%%%% GAME RULES %%%%%%%%%%%%%.
goal(white, 100) :- line(x), not(line(o)).
goal(white, 50) :- not(line(x)), not(line(o)).
goal(white, 0) :- not(line(x)), line(o).
goal(black, 100) :- not(line(x)), line(o).
goal(black, 50) :- not(line(x)), not(line(o)).
goal(black, 0) :- line(x), not(line(o)).
legal_mark(W, X, Y) :- true_cell(X, Y, b), true_control(W).
legal(white, noop) :- true_control(black).
legal(black, noop) :- true_control(white).
next_cell(M, N, x) :- does_mark(white, M, N), true_cell(M, N, b).
next_cell(M, N, o) :- does_mark(black, M, N), true_cell(M, N, b).
next_cell(M, N, W) :- true_cell(M, N, W), distinct(W, b).
next_cell(M, N, b) :- does_mark(W, J, K), true_cell(M, N, b), distinct(M, J).
next_cell(M, N, b) :- does_mark(W, J, K), true_cell(M, N, b), distinct(N, K).
next_control(white) :- true_control(black).
next_control(black) :- true_control(white).
terminal :- line(x).
terminal :- line(o).
terminal :- not(open).