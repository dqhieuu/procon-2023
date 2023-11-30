# Game PROCON 2023

## Tham số Petting Zoo
| Param             | Value                                                      |
|-------------------|------------------------------------------------------------|
| Actions           | Discrete                                                   |
| Parallel API      | ???                                                        |
| Manual Control    | ???                                                        |
| Agents            | `['player_1_craftsman_index', 'player_2_craftsman_index']` |
| Agents            | 2 * số agent mỗi team                                      |
| Action Shape      | Discrete(17)                                               |
| Action Values     |                                                            |
| Observation Shape | MultiBinary([h,w,10])                                      |
| Observation Value |                                                            |


# Encode ô cờ (Observation space)
```
0 = t1 craftsman
1 = t2 craftsman
2 = t1 wall
3 = t2 wall
4 = castle
5 = pond
6 = t1 closed teritory
7 = t2 closed teritory
8 = t1 open teritory
9 = t2 open teritory
10 = is t2 turn
11 = craftsman of team <turn_team> has done action
```

# Encode nước đi (Action space)
```
0 = stay
1 = move up
2 = move down
3 = move left
4 = move right
5 = move up left
6 = move up right
7 = move down left
8 = move down right
9 = build wall up
10 = build wall down
11 = build wall left
12 = build wall right
13 = destroy wall up
14 = destroy wall down
15 = destroy wall left
16 = destroy wall right
```

# Reward
| Thắng | Thua | Hoà |
|-------|------|-----|
| +1    | -1   | 0   |