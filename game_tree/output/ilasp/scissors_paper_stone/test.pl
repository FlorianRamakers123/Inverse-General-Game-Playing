%%%%%%% BACKGROUND KNOWLEDGE %%%%%%%
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
draws(P) :- does(P, A), does(Q, A), distinct_gdl(P, Q).
wins(P) :- does(P, A1), does(Q, A2), distinct_gdl(P, Q), beats(A1, A2).
loses(P) :- does(P, A1), does(Q, A2), distinct_gdl(P, Q), beats(A2, A1).
distinct_gdl(A,B) :- A \== B.
distinct_gdl(A,B):-A \== B.
%%%%%%% CONSTANTS %%%%%%%%
int(0).
int(1).
int(2).
int(3).
agent(p1).
agent(p2).
action(scissors).
action(paper).
action(stone).
%%%%%%% FALSE FACTS %%%%%%%
my_not(true_step(0)).
my_not(true_step(1)).
my_not(true_step(2)).
my_not(true_score(p1, 0)).
my_not(true_score(p1, 1)).
my_not(true_score(p1, 2)).
my_not(true_score(p1, 3)).
my_not(true_score(p2, 0)).
my_not(true_score(p2, 1)).
my_not(true_score(p2, 2)).
my_not(true_score(p2, 3)).
my_not(next_step(0)).
my_not(next_step(1)).
my_not(next_step(2)).
my_not(next_step(3)).
my_not(next_score(p1, 0)).
my_not(next_score(p1, 1)).
my_not(next_score(p1, 2)).
my_not(next_score(p1, 3)).
my_not(next_score(p2, 0)).
my_not(next_score(p2, 1)).
my_not(next_score(p2, 2)).
my_not(next_score(p2, 3)).
my_not(legal(p1, scissors)).
my_not(legal(p1, paper)).
my_not(legal(p1, stone)).
my_not(legal(p2, scissors)).
my_not(legal(p2, paper)).
my_not(legal(p2, stone)).
my_not(input(p1, scissors)).
my_not(input(p1, paper)).
my_not(input(p1, stone)).
my_not(input(p2, scissors)).
my_not(input(p2, paper)).
my_not(input(p2, stone)).
my_not(does(p1, scissors)).
my_not(does(p1, paper)).
my_not(does(p1, stone)).
my_not(does(p2, scissors)).
my_not(does(p2, paper)).
my_not(does(p2, stone)).
my_not(goal(p1, 0)).
my_not(goal(p1, 1)).
my_not(goal(p1, 2)).
my_not(goal(p1, 3)).
my_not(goal(p2, 0)).
my_not(goal(p2, 1)).
my_not(goal(p2, 2)).
my_not(goal(p2, 3)).
my_not(A) :- \+ A.

%%%%%%% FACTS %%%%%%%
does(A,B) :- fail.
true_step(3).
true_score(p1,0).
true_score(p2,0).

%%%%%%% HYPOTHESISES GOAL %%%%%%%
goal1(P, S) :- true_score(P, S).
goal2(V0, V1) :- true_score(V0, V1), agent(V0), int(V1).

%%%%%%% BASE TEST GOAL %%%%%%%
goal_base(A,B) :- goal1(A,B), goal2(A,B).

%%%%%%% POSITIVE TEST GOAL %%%%%%%
goal_pos(A,B) :- goal1(A,B), \+ goal2(A,B).

%%%%%%% NEGATIVE TEST GOAL %%%%%%%
goal_neg(A,B) :- goal2(A,B), \+ goal1(A,B).

%%%%%%% HYPOTHESISES LEGAL %%%%%%%
legal1(P, scissors) :- player(P).
legal1(P, paper) :- player(P).
legal1(P, stone) :- player(P).
legal2(V0, V1) :- agent(V0), action(V1).

%%%%%%% BASE TEST LEGAL %%%%%%%
legal_base(A,B) :- legal1(A,B), legal2(A,B).

%%%%%%% POSITIVE TEST LEGAL %%%%%%%
legal_pos(A,B) :- legal1(A,B), \+ legal2(A,B).

%%%%%%% NEGATIVE TEST LEGAL %%%%%%%
legal_neg(A,B) :- legal2(A,B), \+ legal1(A,B).

%%%%%%% HYPOTHESISES NEXT_SCORE %%%%%%%
next_score1(P, N) :- true_score(P, N), draws(P).
next_score1(P, N) :- true_score(P, N), loses(P).
next_score1(P, N) :- true_score(P, N2), succ1(N2, N), wins(P).
next_score2(V0, V1) :- succ1(V4, V1), beats(V8, V6), true_score(V0, V4), does(V0, V8), does(V5, V6), agent(V0), int(V1), int(V4), agent(V5), action(V6), action(V8).
next_score2(V0, V1) :- beats(V6, V7), true_score(V0, V1), does(V5, V6), does(V0, V7), agent(V0), int(V1), agent(V5), action(V6), action(V7).
next_score2(V0, V1) :- V5 = p1, V0 = p2, true_score(V0, V1), does(V0, V8), does(V5, V8), agent(V0), int(V1), agent(V5), action(V8).
next_score2(V0, V1) :- V5 = p2, V0 = p1, true_score(V0, V1), does(V5, V8), does(V0, V8), agent(V0), int(V1), agent(V5), action(V8).

%%%%%%% BASE TEST NEXT_SCORE %%%%%%%
next_score_base(A,B) :- next_score1(A,B), next_score2(A,B).

%%%%%%% POSITIVE TEST NEXT_SCORE %%%%%%%
next_score_pos(A,B) :- next_score1(A,B), \+ next_score2(A,B).

%%%%%%% NEGATIVE TEST NEXT_SCORE %%%%%%%
next_score_neg(A,B) :- next_score2(A,B), \+ next_score1(A,B).

%%%%%%% HYPOTHESISES NEXT_STEP %%%%%%%
next_step1(N) :- true_step(M), succ1(M, N).
next_step2(V0) :- succ1(V2, V0), true_step(V2), int(V0), int(V2).

%%%%%%% BASE TEST NEXT_STEP %%%%%%%
next_step_base(A) :- next_step1(A), next_step2(A).

%%%%%%% POSITIVE TEST NEXT_STEP %%%%%%%
next_step_pos(A) :- next_step1(A), \+ next_step2(A).

%%%%%%% NEGATIVE TEST NEXT_STEP %%%%%%%
next_step_neg(A) :- next_step2(A), \+ next_step1(A).

%%%%%%% HYPOTHESISES TERMINAL %%%%%%%
terminal1 :- true_step(3).
terminal2 :- V1 = 3, true_step(V1), int(V1).
