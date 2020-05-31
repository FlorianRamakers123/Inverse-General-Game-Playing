%%%%%%% BACKGROUND KNOWLEDGE %%%%%%%
base(p).
base(q).
base(r).
base(1).
base(2).
base(3).
base(4).
base(5).
base(6).
base(7).
init(1).
role(robot).
input(robot,a).
input(robot,b).
input(robot,c).
successor(1,2).
successor(2,3).
successor(3,4).
successor(4,5).
successor(5,6).
successor(6,7).
legal_gdl(robot,a).
legal_gdl(robot,b).
legal_gdl(robot,c).
distinct_gdl(A,B):-A \== B.
%%%%%%% CONSTANTS %%%%%%%%
prop(p).
prop(q).
prop(r).
prop(1).
prop(2).
prop(3).
prop(4).
prop(5).
prop(6).
prop(7).
agent(robot).
action(a).
action(b).
action(c).
int(0).
int(100).
%%%%%%% FALSE FACTS %%%%%%%
my_not(true(p)).
my_not(true(q)).
my_not(true(r)).
my_not(true(1)).
my_not(true(2)).
my_not(true(3)).
my_not(true(4)).
my_not(true(5)).
my_not(true(6)).
my_not(next(p)).
my_not(next(q)).
my_not(next(r)).
my_not(next(1)).
my_not(next(2)).
my_not(next(3)).
my_not(next(4)).
my_not(next(5)).
my_not(next(6)).
my_not(next(7)).
my_not(legal(robot, a)).
my_not(legal(robot, b)).
my_not(legal(robot, c)).
my_not(does(robot, a)).
my_not(does(robot, b)).
my_not(does(robot, c)).
my_not(goal(robot, 0)).
my_not(goal(robot, 100)).
my_not(A) :- \+ A.

%%%%%%% FACTS %%%%%%%
does(A,B) :- fail.
true(7).

%%%%%%% HYPOTHESISES GOAL %%%%%%%
goal1(robot,100) :- true(p), true(q), true(r).
goal1(robot,0) :- my_not(true(p)).
goal1(robot,0) :- my_not(true(q)).
goal1(robot,0) :- my_not(true(r)).
goal2(V0, V1) :- V13 = q, V12 = r, V1 = 100, true(V12), true(V13), agent(V0), int(V1), prop(V12), prop(V13).
goal2(V0, V1) :- V14 = r, V1 = 0, my_not(true(V14)), agent(V0), int(V1), prop(V14).
goal2(V0, V1) :- V14 = p, V1 = 0, my_not(true(V14)), agent(V0), int(V1), prop(V14).
goal2(V0, V1) :- V14 = q, V1 = 0, my_not(true(V14)), agent(V0), int(V1), prop(V14).

%%%%%%% BASE TEST GOAL %%%%%%%
goal_base(A,B) :- goal1(A,B), goal2(A,B).

%%%%%%% POSITIVE TEST GOAL %%%%%%%
goal_pos(A,B) :- goal1(A,B), \+ goal2(A,B).

%%%%%%% NEGATIVE TEST GOAL %%%%%%%
goal_neg(A,B) :- goal2(A,B), \+ goal1(A,B).

%%%%%%% HYPOTHESISES LEGAL %%%%%%%
legal1(robot,A) :- legal_gdl(robot,A).
legal2(V0, V1) :- agent(V0), action(V1).

%%%%%%% BASE TEST LEGAL %%%%%%%
legal_base(A,B) :- legal1(A,B), legal2(A,B).

%%%%%%% POSITIVE TEST LEGAL %%%%%%%
legal_pos(A,B) :- legal1(A,B), \+ legal2(A,B).

%%%%%%% NEGATIVE TEST LEGAL %%%%%%%
legal_neg(A,B) :- legal2(A,B), \+ legal1(A,B).

%%%%%%% HYPOTHESISES NEXT %%%%%%%
next1(p) :- does(robot, a), my_not(true(p)).
next1(p) :- does(robot, b), true(q).
next1(p) :- does(robot, c), true(p).
next1(q) :- does(robot, a), true(q).
next1(q) :- does(robot, b), true(p).
next1(q) :- does(robot, c), true(r).
next1(r) :- does(robot, a), true(r).
next1(r) :- does(robot, b), true(r).
next1(r) :- does(robot, c), true(q).
next1(Y) :- true(X), successor(X,Y).
next2(V0) :- V11 = a, V0 = p, does(V8, V11), my_not(true(V0)), prop(V0), agent(V8), action(V11).
next2(V0) :- successor(V3, V0), true(V3), prop(V0), prop(V3).
next2(V0) :- V12 = q, V10 = b, V0 = p, true(V12), does(V8, V10), prop(V0), agent(V8), action(V10), prop(V12).
next2(V0) :- V11 = a, V0 = q, true(V0), does(V8, V11), prop(V0), agent(V8), action(V11).
next2(V0) :- V9 = c, V0 = p, true(V0), does(V8, V9), prop(V0), agent(V8), action(V9).
next2(V0) :- V13 = p, V10 = b, V0 = q, true(V13), does(V8, V10), prop(V0), agent(V8), action(V10), prop(V13).
next2(V0) :- V11 = a, V0 = r, true(V0), does(V8, V11), prop(V0), agent(V8), action(V11).
next2(V0) :- V10 = b, V0 = r, true(V0), does(V8, V10), prop(V0), agent(V8), action(V10).
next2(V0) :- V12 = r, V9 = c, V0 = q, true(V12), does(V8, V9), prop(V0), agent(V8), action(V9), prop(V12).
next2(V0) :- V12 = q, V9 = c, V0 = r, true(V12), does(V8, V9), prop(V0), agent(V8), action(V9), prop(V12).

%%%%%%% BASE TEST NEXT %%%%%%%
next_base(A) :- next1(A), next2(A).

%%%%%%% POSITIVE TEST NEXT %%%%%%%
next_pos(A) :- next1(A), \+ next2(A).

%%%%%%% NEGATIVE TEST NEXT %%%%%%%
next_neg(A) :- next2(A), \+ next1(A).

%%%%%%% HYPOTHESISES TERMINAL %%%%%%%
terminal1 :- true(p), true(q), true(r).
terminal1 :- true(7).
terminal2 :- V1 = 7, true(V1), prop(V1).
