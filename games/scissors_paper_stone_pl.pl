succ1(0, 1).
succ1(1, 2).
succ1(2, 3).
player(p1).
player(p2).
init_step(0).
init_score(p1, 0).
init_score(p2, 0).
beats(paper, stone).
beats(scissors, paper).
beats(stone, scissors).
draws(P) :- does(P, A), does(Q, A), distinct(P, Q).
wins(P) :- does(P, A1), does(Q, A2), distinct(P, Q), beats(A1, A2).
loses(P) :- does(P, A1), does(Q, A2), distinct(P, Q), beats(A2, A1).
distinct(A,B) :- A \== B.
%%%%%%%%%%%%% GAME RULES %%%%%%%%%%%%%.
goal(P, S) :- true_score(P, S).
legal(P, scissors) :- player(P).
legal(P, paper) :- player(P).
legal(P, stone) :- player(P).
next_step(N) :- true_step(M), succ1(M, N).
next_score(P, N) :- true_score(P, N), draws(P).
next_score(P, N) :- true_score(P, N), loses(P).
next_score(P, N) :- true_score(P, N2), succ1(N2, N), wins(P).
terminal :- true_step(3).
