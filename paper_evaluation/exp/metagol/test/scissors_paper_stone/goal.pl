beats(1,paper,stone).
beats(1,scissors,paper).
beats(1,stone,scissors).
beats(2,paper,stone).
beats(2,scissors,paper).
beats(2,stone,scissors).
beats(3,paper,stone).
beats(3,scissors,paper).
beats(3,stone,scissors).
beats(4,paper,stone).
beats(4,scissors,paper).
beats(4,stone,scissors).
my_succ(1,0,1).
my_succ(1,1,2).
my_succ(1,2,3).
my_succ(2,0,1).
my_succ(2,1,2).
my_succ(2,2,3).
my_succ(3,0,1).
my_succ(3,1,2).
my_succ(3,2,3).
my_succ(4,0,1).
my_succ(4,1,2).
my_succ(4,2,3).
my_true_score(1,p1,0).
my_true_score(1,p2,3).
my_true_score(2,p1,2).
my_true_score(2,p2,0).
my_true_score(3,p1,0).
my_true_score(3,p2,0).
my_true_score(4,p1,0).
my_true_score(4,p2,0).
my_true_step(1,3).
my_true_step(2,3).
my_true_step(3,1).
my_true_step(4,3).
neg(goal(1,p1,1)).
neg(goal(1,p1,2)).
neg(goal(1,p1,3)).
neg(goal(1,p2,0)).
neg(goal(1,p2,1)).
neg(goal(1,p2,2)).
neg(goal(2,p1,0)).
neg(goal(2,p1,1)).
neg(goal(2,p1,3)).
neg(goal(2,p2,1)).
neg(goal(2,p2,2)).
neg(goal(2,p2,3)).
neg(goal(3,p1,1)).
neg(goal(3,p1,2)).
neg(goal(3,p1,3)).
neg(goal(3,p2,1)).
neg(goal(3,p2,2)).
neg(goal(3,p2,3)).
neg(goal(4,p1,1)).
neg(goal(4,p1,2)).
neg(goal(4,p1,3)).
neg(goal(4,p2,1)).
neg(goal(4,p2,2)).
neg(goal(4,p2,3)).
player(1,p1).
player(1,p2).
player(2,p1).
player(2,p2).
player(3,p1).
player(3,p2).
player(4,p1).
player(4,p2).
pos(goal(1,p1,0)).
pos(goal(1,p2,3)).
pos(goal(2,p1,2)).
pos(goal(2,p2,0)).
pos(goal(3,p1,0)).
pos(goal(3,p2,0)).
pos(goal(4,p1,0)).
pos(goal(4,p2,0)).