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
%%%%%%%%%%%%% GAME RULES %%%%%%%%%%%%%.
goal(robot,100) :- true(p), true(q), true(r).
goal(robot,0) :- not(true(p)).
goal(robot,0) :- not(true(q)).
goal(robot,0) :- not(true(r)).
legal(robot,A) :- legal_gdl(robot,A).
next(p) :- does(robot, a), not(true(p)).
next(p) :- does(robot, b), true(q).
next(p) :- does(robot, c), true(p).
next(q) :- does(robot, a), true(q).
next(q) :- does(robot, b), true(p).
next(q) :- does(robot, c), true(r).
next(r) :- does(robot, a), true(r).
next(r) :- does(robot, b), true(r).
next(r) :- does(robot, c), true(q).
next(Y) :- true(X), successor(X,Y).
terminal :- true(p), true(q), true(r).
terminal :- true(7).


