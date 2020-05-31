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
