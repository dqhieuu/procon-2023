#include "game_interfaces.h"
#include <stdio.h>

std::vector<std::vector<std::vector<std::vector<std::vector<int>>>>> minCostMap;
std::vector<std::vector<std::vector<std::vector<std::vector<std::pair<int,int>>>>>> prev_bfs;

inline int32_t subActionToX(SubActionType subActionType)
{
    switch (subActionType)
    {
    case MOVE_LEFT:
    case MOVE_UP_LEFT:
    case MOVE_DOWN_LEFT:
    case BUILD_LEFT:
    case DESTROY_LEFT:
        return -1;
    case MOVE_RIGHT:
    case MOVE_UP_RIGHT:
    case MOVE_DOWN_RIGHT:
    case BUILD_RIGHT:
    case DESTROY_RIGHT:
        return 1;
    default:
        return 0;
    }
}

inline int32_t subActionToY(SubActionType subActionType)
{
    switch (subActionType)
    {
    case MOVE_UP:
    case MOVE_UP_LEFT:
    case MOVE_UP_RIGHT:
    case BUILD_UP:
    case DESTROY_UP:
        return -1;
    case MOVE_DOWN:
    case MOVE_DOWN_LEFT:
    case MOVE_DOWN_RIGHT:
    case BUILD_DOWN:
    case DESTROY_DOWN:
        return 1;
    default:
        return 0;
    }
}

MapState::MapState(int32_t mapWidth, int32_t mapHeight)
{
    assert(mapHeight <= 25 && mapWidth <= 25 && mapHeight >= 10 && mapWidth >= 10);
    this->mapWidth = mapWidth;
    this->mapHeight = mapHeight;
    // all tiles are ponds by default
    tiles = std::vector<std::vector<uint32_t>>(25, std::vector<uint32_t>(25, 1 << TileMask::POND));

    tileStatusesT1 = std::vector<std::vector<TileStatus>>(25, std::vector<TileStatus>(25, NOT_VISITED));
    tileStatusesT2 = std::vector<std::vector<TileStatus>>(25, std::vector<TileStatus>(25, NOT_VISITED));

    // remove ponds to make tiles movable
    for (auto y = 0; y < mapHeight; ++y)
        for (auto x = 0; x < mapWidth; ++x)
            clearBit(x, y, TileMask::POND);
}

GameAction::GameAction() : craftsmanId(-1), actionType(ActionType::MOVE), subActionType(SubActionType::MOVE_UP)
{
}

GameAction::GameAction(CraftsmanID _craftsmanId, ActionType _actionType, SubActionType _subActionType) : craftsmanId(_craftsmanId), actionType(_actionType), subActionType(_subActionType)
{
}

Craftsman::Craftsman() : id(-1), x(-1), y(-1), isT1(true)
{
}

Craftsman::Craftsman(int32_t id, int32_t x, int32_t y, bool isT1) : id(id), x(x), y(y), isT1(isT1)
{
}

inline bool MapState::validPosition(int x, int y) const
{
    return x >= 0 && x < mapWidth && y >= 0 && y < mapHeight;
}

inline void MapState::setTile(size_t x, size_t y, uint32_t bit)
{
    tiles[y][x] = bit;
}

inline void MapState::setBit(size_t x, size_t y, TileMask bit)
{
    tiles[y][x] |= (1 << bit);
}

inline void MapState::clearBit(size_t x, size_t y, TileMask bit)
{
    tiles[y][x] &= ~(1 << bit);
}

inline bool MapState::isBitToggled(size_t x, size_t y, TileMask bit) const
{
    return tiles[y][x] & (1 << bit);
}

inline bool MapState::isAnyOfMaskToggled(size_t x, size_t y, uint32_t mask) const
{
    return tiles[y][x] & mask;
}

void MapState::clearMapBit(TileMask bit)
{
    for (int y = 0; y < mapHeight; y++)
    {
        for (int x = 0; x < mapWidth; x++)
        {
            clearBit(x, y, bit);
        }
    }
}

inline uint32_t MapState::getTile(uint64_t x, uint64_t y) const
{
    return tiles[y][x];
}

std::string MapState::printMap() const
{
    std::string res;
    for (int i = 0; i < tiles.size(); i++)
    {
        for (int j = 0; j < tiles[i].size(); j++)
        {
            // convert to bitmask of 10 bits
            uint32_t tile = tiles[i][j];
            std::string tileStr = std::bitset<10>(tile).to_string();

            res += tileStr + " ";
        }
        res += "\n";
    }
    return res;
}

int MapState::calcPoints(const GameOptions &gameOptions, bool isT1) const
{
    int points = 0;
    auto teamCloseTerritoryMask = isT1 ? TileMask::T1_CLOSE_TERRITORY : TileMask::T2_CLOSE_TERRITORY;
    auto teamOpenTerritoryMask = isT1 ? TileMask::T1_OPEN_TERRITORY : TileMask::T2_OPEN_TERRITORY;
    auto wallMask = isT1 ? TileMask::T1_WALL : TileMask::T2_WALL;

    for (int y = 0; y < mapHeight; ++y)
    {
        for (int x = 0; x < mapWidth; ++x)
        {
            if (isBitToggled(x, y, teamCloseTerritoryMask) || isBitToggled(x, y, teamOpenTerritoryMask))
            {
                points += gameOptions.territoryCoeff;
                if (isBitToggled(x, y, TileMask::CASTLE))
                {
                    points += gameOptions.castleCoeff;
                }
            }
            else if (isBitToggled(x, y, wallMask))
            {
                points += gameOptions.wallCoeff;
            }
        }
    }

    return points;
}

void MapState::checkCloseTerritory(const int32_t _x, const int32_t _y, const bool is_t1)
{
    auto &tileStatuses = is_t1 ? tileStatusesT1 : tileStatusesT2;

    std::set<std::pair<int32_t, int32_t>> positions;
    bool enclosed = true;

    std::queue<std::pair<int32_t, int32_t>> q;
    q.push({_x, _y});

    while (!q.empty())
    {
        auto [x, y] = q.front();
        q.pop();

        if (!validPosition(x, y))
        {
            enclosed = false;
            continue;
        }

        if (isBitToggled(x, y, is_t1 ? TileMask::T1_WALL : TileMask::T2_WALL) || positions.find({x, y}) != positions.end())
        {
            continue;
        }

        positions.insert({x, y});

        if (positions.find({x + 1, y}) == positions.end())
            q.push({x + 1, y});
        if (positions.find({x - 1, y}) == positions.end())
            q.push({x - 1, y});
        if (positions.find({x, y + 1}) == positions.end())
            q.push({x, y + 1});
        if (positions.find({x, y - 1}) == positions.end())
            q.push({x, y - 1});
    }

    for (const auto &[x, y] : positions)
    {
        tileStatuses[y][x] = enclosed ? TileStatus::IS_TERRITORY : TileStatus::NOT_TERRITORY;
    }
}

void MapState::updateTerritory(const std::vector<DestroyAction> &&destroyActions,
                               const std::vector<BuildAction> &&buildActions)
{
    const MapState previousMap = *this;

    clearMapBit(TileMask::T1_CLOSE_TERRITORY);
    clearMapBit(TileMask::T2_CLOSE_TERRITORY);
    clearTileStatuses();

    // apply actions
    for (const DestroyAction &action : destroyActions)
    {
        if (!(isBitToggled(action.x, action.y, TileMask::T1_WALL) || isBitToggled(action.x, action.y, TileMask::T2_WALL)))
            continue;

        clearBit(action.x, action.y, TileMask::T1_WALL);
        clearBit(action.x, action.y, TileMask::T2_WALL);
    }

    for (const BuildAction &action : buildActions)
    {
        const auto cantBuildMask = (1 << TileMask::T1_WALL) |
                                   (1 << TileMask::T2_WALL) |
                                   (1 << TileMask::CASTLE) |
                                   (1 << TileMask::POND) |
                                   (1 << TileMask::T1_CRAFTSMAN) |
                                   (1 << TileMask::T2_CRAFTSMAN);
        if (isAnyOfMaskToggled(action.x, action.y, cantBuildMask))
            continue;

        setBit(action.x, action.y, action.isT1 ? TileMask::T1_WALL : TileMask::T2_WALL);
    }

    updateCloseTerritoryAndClearOpenTerritoryInside(previousMap);
}

void MapState::updateCloseTerritoryAndClearOpenTerritoryInside(const MapState &previousMap)
{
    for (int y = 0; y < mapHeight; y++)
        for (int x = 0; x < mapWidth; x++)
        {
            if (isBitToggled(x, y, TileMask::T1_WALL) || isBitToggled(x, y, TileMask::T2_WALL))
            {
                clearBit(x, y, TileMask::T1_OPEN_TERRITORY);
                clearBit(x, y, TileMask::T2_OPEN_TERRITORY);
            }

            if (!isBitToggled(x, y, TileMask::T1_WALL))
            {
                if (tileStatusesT1[y][x] == NOT_VISITED)
                    checkCloseTerritory(x, y, true);

                if (tileStatusesT1[y][x] == IS_TERRITORY)
                {
                    setBit(x, y, TileMask::T1_CLOSE_TERRITORY);
                    clearBit(x, y, TileMask::T1_OPEN_TERRITORY);
                    clearBit(x, y, TileMask::T2_OPEN_TERRITORY);
                }
            }

            if (!isBitToggled(x, y, TileMask::T2_WALL))
            {
                if (tileStatusesT2[y][x] == NOT_VISITED)
                    checkCloseTerritory(x, y, false);

                if (tileStatusesT2[y][x] == IS_TERRITORY)
                {
                    setBit(x, y, TileMask::T2_CLOSE_TERRITORY);
                    clearBit(x, y, TileMask::T1_OPEN_TERRITORY);
                    clearBit(x, y, TileMask::T2_OPEN_TERRITORY);
                }
            }
        }

    for (int y = 0; y < mapHeight; y++)
        for (int x = 0; x < mapWidth; x++)
        {
            if (isBitToggled(x, y, TileMask::T1_WALL) || isBitToggled(x, y, TileMask::T2_WALL))
                continue;

            if ((previousMap.isBitToggled(x, y, TileMask::T1_CLOSE_TERRITORY) || previousMap.isBitToggled(x, y, TileMask::T1_OPEN_TERRITORY)) &&
                tileStatusesT1[y][x] == NOT_TERRITORY && tileStatusesT2[y][x] == NOT_TERRITORY)
            {
                setBit(x, y, TileMask::T1_OPEN_TERRITORY);
            }
            else if ((previousMap.isBitToggled(x, y, TileMask::T2_CLOSE_TERRITORY) || previousMap.isBitToggled(x, y, TileMask::T2_OPEN_TERRITORY)) &&
                     tileStatusesT1[y][x] == NOT_TERRITORY && tileStatusesT2[y][x] == NOT_TERRITORY)
            {
                setBit(x, y, TileMask::T2_OPEN_TERRITORY);
            }
        }
}

void MapState::clearTileStatuses()
{
    for (int y = 0; y < mapHeight; y++)
        for (int x = 0; x < mapWidth; x++)
        {
            tileStatusesT1[y][x] = NOT_VISITED;
            tileStatusesT2[y][x] = NOT_VISITED;
        }
}

GameState::GameState(MapState _map, std::unordered_map<CraftsmanID, Craftsman> _craftsmen)
    : map(_map), craftsmen(_craftsmen), turn(1), isT1Turn(true)
{
    initMinCostMap(_map);
}

GameState::GameState(MapState _map, std::unordered_map<CraftsmanID, Craftsman> _craftsmen, int _turn, bool _isT1Turn)
    : map(_map), craftsmen(_craftsmen), turn(_turn), isT1Turn(_isT1Turn)
{
    initMinCostMap(_map);
}

int GameState::findCraftsmanIdByPos(int x, int y) const
{
    for (const auto &[craftsmanId, craftsman] : craftsmen)
    {
        if (craftsman.x == x && craftsman.y == y)
            return craftsmanId;
    }
    return -1;
}

GameState GameState::applyActions(const std::vector<GameAction> &actionBuffer)
{
    std::vector<GameAction> actionByCraftsman;

    { // deduplicate actions by craftsman
        std::unordered_set<int32_t> craftsmanIdVisited;

        for (auto it = actionBuffer.rbegin(); it != actionBuffer.rend(); ++it)
        {
            if (craftsmen[it->craftsmanId].isT1 != isT1Turn)
                continue;

            if (craftsmanIdVisited.find(it->craftsmanId) != craftsmanIdVisited.end())
                continue;

            craftsmanIdVisited.insert(it->craftsmanId);

            actionByCraftsman.push_back(*it);
        }

        reverse(actionByCraftsman.begin(), actionByCraftsman.end());
    }

    auto nextGameState = *this;
    nextGameState.lastTurnActions = actionByCraftsman;
    nextGameState.turn++;
    nextGameState.isT1Turn = !nextGameState.isT1Turn;

    auto nextMap = map;

    std::vector<DestroyAction> destroyActions;
    std::vector<BuildAction> buildActions;
    std::vector<GameAction> moveActions;

    std::set<std::pair<int32_t, int32_t>> moveForbiddenPositions;
    for (const auto &[craftsmanId, craftsman] : craftsmen)
    {
        moveForbiddenPositions.insert({craftsman.x, craftsman.y});
    }

    // Categorize actions by type
    for (const auto &action : actionByCraftsman)
    {
        const auto &craftsman = craftsmen[action.craftsmanId];
        auto nextX = craftsman.x + subActionToX(action.subActionType);
        auto nextY = craftsman.y + subActionToY(action.subActionType);

        if (!map.validPosition(nextX, nextY))
            continue;

        if (action.actionType == ActionType::MOVE)
            moveActions.emplace_back(action);
        else if (action.actionType == ActionType::BUILD)
            buildActions.push_back({nextX, nextY, craftsman.isT1});
        else if (action.actionType == ActionType::DESTROY)
            destroyActions.push_back({nextX, nextY, craftsman.isT1});
    }

    // Apply destroy and build actions
    nextMap.updateTerritory(std::move(destroyActions), std::move(buildActions));

    // Apply move actions
    for (const auto &action : moveActions)
    {
        const auto &craftsman = craftsmen[action.craftsmanId];
        auto nextX = craftsman.x + subActionToX(action.subActionType);
        auto nextY = craftsman.y + subActionToY(action.subActionType);

        if (moveForbiddenPositions.find({nextX, nextY}) != moveForbiddenPositions.end() ||
            nextMap.isBitToggled(nextX, nextY, craftsman.isT1 ? TileMask::T2_WALL : TileMask::T1_WALL) ||
            nextMap.isBitToggled(nextX, nextY, TileMask::POND))
            continue;

        nextGameState.craftsmen[action.craftsmanId].x = nextX;
        nextGameState.craftsmen[action.craftsmanId].y = nextY;

        nextMap.clearBit(craftsman.x, craftsman.y, craftsman.isT1 ? TileMask::T1_CRAFTSMAN : TileMask::T2_CRAFTSMAN);
        nextMap.setBit(nextX, nextY, craftsman.isT1 ? TileMask::T1_CRAFTSMAN : TileMask::T2_CRAFTSMAN);

        moveForbiddenPositions.insert({nextX, nextY});
    }

    nextGameState.map = std::move(nextMap);
    return nextGameState;
}
void GameState::initMinCostMap(MapState _map)
{    
    minCostMap = std::vector<std::vector<std::vector<std::vector<std::vector<int>>>>>(
        25,
        std::vector<std::vector<std::vector<std::vector<int>>>>(
            25,
            std::vector<std::vector<std::vector<int>>>(
                25,
                std::vector<std::vector<int>>(
                    25,
                    std::vector<int>(2, 100000)))));
    prev_bfs = std::vector<std::vector<std::vector<std::vector<std::vector<std::pair<int, int>>>>>>(
        25,
        std::vector<std::vector<std::vector<std::vector<std::pair<int, int>>>>>(
            25,
            std::vector<std::vector<std::vector<std::pair<int, int>>>>(
                25,
                std::vector<std::vector<std::pair<int, int>>>(
                    25,
                    std::vector<std::pair<int, int>>(2, {-1, -1})))));
    for (int i = 0; i < 25; i++)
        for (int j = 0; j < 25; j++)
        {
            if (_map.getTile(i, j) & (1 << TileMask::POND))
                continue;
            bfs(i, j, true);
            bfs(i, j, false);
        }
}
void GameState::bfs(int x, int y, bool isT1)
{
    std::queue<std::pair<int, int>> q;
    // direction 0: left, 1: up, 2: right, 3: down, 4: left-up, 5: right-up, 6: left-down, 7: right-down
    std::vector<std::pair<int, int>> direction = {{-1, 0}, {0, -1}, {1, 0}, {0, 1}, {-1, -1}, {1, -1}, {-1, 1}, {1, 1}};
    q.push({x, y});
    minCostMap[x][y][x][y][isT1] = 0;
    while (!q.empty())
    {
        auto [cur_x, cur_y] = q.front();
        q.pop();
        for (int i = 0; i < 8; i++)
        {
            if (cur_x + direction[i].first < 0 || cur_x + direction[i].first >= 25 || cur_y + direction[i].second < 0 || cur_y + direction[i].second >= 25)
                continue;
            if (map.getTile(cur_x + direction[i].first, cur_y + direction[i].second) & (1 << TileMask::POND))
                continue;
            int new_x = cur_x + direction[i].first;
            int new_y = cur_y + direction[i].second;
            if (i > 3 && map.getTile(new_x, new_y) & (1 << TileMask::T1_WALL) && !isT1)
                continue;
            if (i > 3 && map.getTile(new_x, new_y) & (1 << TileMask::T2_WALL) && isT1)
                continue;
            int new_cost = minCostMap[x][y][cur_x][cur_y][isT1] + 1;
            if (map.getTile(new_x, new_y) & (1 << TileMask::T1_WALL) && !isT1)
                new_cost += 1;
            if (map.getTile(new_x, new_y) & (1 << TileMask::T2_WALL) && isT1)
                new_cost += 1;
            if (new_cost < minCostMap[x][y][new_x][new_y][isT1])
            {
                minCostMap[x][y][new_x][new_y][isT1] = new_cost;
                prev_bfs[x][y][new_x][new_y][isT1] = {cur_x, cur_y};
                q.push({new_x, new_y});
            }
        }
    }
}
std::pair<int, GameAction> GameState::findWayToBuild(int x, int y, bool isT1, std::vector<std::pair<int, int>> buildAbleCells)
{
    std::vector<std::vector<std::vector<int>>> cost(
        4,
        std::vector<std::vector<int>>(
            12,
            std::vector<int>((1 << 12), 10000)));
    std::vector<std::vector<std::vector<std::pair<int, int>>>> prev(
        4,
        std::vector<std::vector<std::pair<int, int>>>(
            12,
            std::vector<std::pair<int, int>>((1 << 12), {-1, -1})));
    // create array Direction 0: left, 1: up, 2: right, 3: down
    std::vector<std::pair<int, int>> direction = {{-1, 0}, {0, -1}, {1, 0}, {0, 1}};
    int size = buildAbleCells.size();

    std::cout<<"Test 1"<<'\n';
    for (int i = 0; i < size; i++)
    {
        for (int k = 0; k < 4; k++)
        {
            if (buildAbleCells[i].first + direction[k].first < 0 || buildAbleCells[i].first + direction[k].first >= 25 || buildAbleCells[i].second + direction[k].second < 0 || buildAbleCells[i].second + direction[k].second >= 25)
                continue;
            if (map.getTile(buildAbleCells[i].first + direction[k].first, buildAbleCells[i].second + direction[k].second) & (1 << TileMask::POND))
                continue;
            int new_x = buildAbleCells[i].first + direction[k].first;
            int new_y = buildAbleCells[i].second + direction[k].second;
            cost[k][i][1 << i] = minCostMap[x][y][new_x][new_y][isT1];
        }
    }
        std::cout<<"Test 2"<<'\n';

    for (int i = 1; i < (1 << size); i++)
    {
        for (int j = 0; j < size; j++)
        {
            if (i & (1 << j))
            {
                int real_x = buildAbleCells[j].first;
                int real_y = buildAbleCells[j].second;
                for (int k = 0; k < 4; k++)
                {
                    if (real_x + direction[k].first < 0 || real_x + direction[k].first >= 25 || real_y + direction[k].second < 0 || real_y + direction[k].second >= 25)
                        continue;
                    if (map.getTile(real_x + direction[k].first, real_y + direction[k].second) & (1 << TileMask::POND))
                        continue;
                    int new_x = real_x + direction[k].first;
                    int new_y = real_y + direction[k].second;
                    for (int z = 0; z < size; z++)
                    {
                        // if bit z is toggle continue
                        if (i & (1 << z))
                            continue;

                        int new_x2 = buildAbleCells[z].first;
                        int new_y2 = buildAbleCells[z].second;
                        for (int l = 0; l < 4; l++)
                        {
                            if (new_x2 + direction[l].first < 0 || new_x2 + direction[l].first >= 25 || new_y2 + direction[l].second < 0 || new_y2 + direction[l].second >= 25)
                                continue;
                            if (map.getTile(new_x2 + direction[l].first, new_y2 + direction[l].second) & (1 << TileMask::POND))
                                continue;
                            int new_x3 = new_x2 + direction[l].first;
                            int new_y3 = new_y2 + direction[l].second;
                            if (cost[k][j][i] + minCostMap[new_x][new_y][new_x3][new_y3][isT1] < cost[l][z][i | (1 << z)])
                            {
                                cost[l][z][i | (1 << z)] = cost[k][j][i] + minCostMap[new_x][new_y][new_x3][new_y3][isT1];
                                prev[l][z][i | (1 << z)] = {k, j};
                            }
                        }
                    }
                }
            }
            else
                continue;
        }
    }
        std::cout<<"Test 2"<<'\n';

    int craftman_id = findCraftsmanIdByPos(x, y);
    int min_cost = 200;
    std::pair<int, int> direction_and_cell = {-1, -1};
    for (int i = 0; i < size; i++)
    {
        for (int j = 0; j < 4; j++)
        {
            if (cost[j][i][(1 << size) - 1] < min_cost)
            {
                min_cost = cost[j][i][(1 << size) - 1];
                direction_and_cell = {j, i};
            }
        }
    }
    if (direction_and_cell.first == -1)
        return {-1, GameAction()};
        std::cout<<"Test 3"<<'\n';
    std::cout << direction_and_cell.first << ' ' << direction_and_cell.second << '\n';
    std::cout << buildAbleCells[direction_and_cell.second].first << ' ' << buildAbleCells[direction_and_cell.second].second << '\n';
    std::cout << x << ' ' << y << '\n';
    // check if x and y next to buildable cell return build
    if (buildAbleCells[direction_and_cell.second].first + direction[direction_and_cell.first].first == x && buildAbleCells[direction_and_cell.second].second + direction[direction_and_cell.first].second == y)
    {
        if (direction_and_cell.first == 0)
            return {min_cost, GameAction(craftman_id, ActionType::BUILD, SubActionType::BUILD_RIGHT)};
        else if (direction_and_cell.first == 1)
            return {min_cost, GameAction(craftman_id, ActionType::BUILD, SubActionType::BUILD_DOWN)};
        else if (direction_and_cell.first == 2)
            return {min_cost, GameAction(craftman_id, ActionType::BUILD, SubActionType::BUILD_LEFT)};
        else if (direction_and_cell.first == 3)
            return {min_cost, GameAction(craftman_id, ActionType::BUILD, SubActionType::BUILD_UP)};
    }

    int cur_mask = (1 << size) - 1;
    while (prev[direction_and_cell.first][direction_and_cell.second][cur_mask] != std::pair{-1, -1})
    {
        auto [new_direction, new_cell] = prev[direction_and_cell.first][direction_and_cell.second][cur_mask];
        cur_mask ^= (1 << direction_and_cell.second);
        direction_and_cell = {new_direction, new_cell};
    }
        if (buildAbleCells[direction_and_cell.second].first + direction[direction_and_cell.first].first == x && buildAbleCells[direction_and_cell.second].second + direction[direction_and_cell.first].second == y)
    {
        if (direction_and_cell.first == 0)
            return {min_cost, GameAction(craftman_id, ActionType::BUILD, SubActionType::BUILD_RIGHT)};
        else if (direction_and_cell.first == 1)
            return {min_cost, GameAction(craftman_id, ActionType::BUILD, SubActionType::BUILD_DOWN)};
        else if (direction_and_cell.first == 2)
            return {min_cost, GameAction(craftman_id, ActionType::BUILD, SubActionType::BUILD_LEFT)};
        else if (direction_and_cell.first == 3)
            return {min_cost, GameAction(craftman_id, ActionType::BUILD, SubActionType::BUILD_UP)};
    }
        std::cout<<"Test 4"<<'\n';

    std::pair<int, int> cell_need_to_build = buildAbleCells[direction_and_cell.second];
    std::cout<<cell_need_to_build.first<<' '<<cell_need_to_build.second<<'\n';
    std::pair<int, int> cell_need_to_move_in = {cell_need_to_build.first + direction[direction_and_cell.first].first, cell_need_to_build.second + direction[direction_and_cell.first].second};
    std::cout<<cell_need_to_move_in.first<<' '<<cell_need_to_move_in.second<<   '\n';
    std::cout<<x<<" "<<y<<'\n';
    std::cout<<prev_bfs[x][y][cell_need_to_move_in.first][cell_need_to_move_in.second][isT1].first<<' '<<prev_bfs[x][y][cell_need_to_move_in.first][cell_need_to_move_in.second][isT1].second<<'\n';
    std::cout<<"====================\n";
    for(int i=0;i<25;i++)
    {
        for(int j=0;j<25;j++)
        {
            std::cout<<minCostMap[x][y][i][j][isT1]<<' ';
        }
        std::cout<<'\n';
    }
    std::cout<<"====================\n";
    std::cout<<"====================\n";
    for(int i=0;i<25;i++)
    {
        for(int j=0;j<25;j++)
        {
            printf("(%2d,%2d) ",prev_bfs[x][y][i][j][isT1].first,prev_bfs[x][y][i][j][isT1].second);
        }
        std::cout<<'\n';
    }
    std::cout<<"====================\n";
    while (prev_bfs[x][y][cell_need_to_move_in.first][cell_need_to_move_in.second][isT1] != std::pair{x, y})
    {
        auto [new_x, new_y] = prev_bfs[x][y][cell_need_to_move_in.first][cell_need_to_move_in.second][isT1];
        cell_need_to_move_in = {new_x, new_y};
    }
    std::cout<<"Test 5"<<'\n';

    if (cell_need_to_move_in.first == x - 1 && cell_need_to_move_in.second == y - 1)
        return {min_cost, GameAction(craftman_id, ActionType::MOVE, SubActionType::MOVE_UP_LEFT)};
    else if (cell_need_to_move_in.first == x + 1 && cell_need_to_move_in.second == y - 1)
        return {min_cost, GameAction(craftman_id, ActionType::MOVE, SubActionType::MOVE_UP_RIGHT)};
    else if (cell_need_to_move_in.first == x - 1 && cell_need_to_move_in.second == y + 1)
        return {min_cost, GameAction(craftman_id, ActionType::MOVE, SubActionType::MOVE_DOWN_LEFT)};
    else if (cell_need_to_move_in.first == x + 1 && cell_need_to_move_in.second == y + 1)
        return {min_cost, GameAction(craftman_id, ActionType::MOVE, SubActionType::MOVE_DOWN_RIGHT)};
    else if (cell_need_to_move_in.first == x - 1)
        return {min_cost, GameAction(craftman_id, ActionType::MOVE, SubActionType::MOVE_LEFT)};
    else if (cell_need_to_move_in.first == x + 1)
        return {min_cost, GameAction(craftman_id, ActionType::MOVE, SubActionType::MOVE_RIGHT)};
    else if (cell_need_to_move_in.second == y - 1)
        return {min_cost, GameAction(craftman_id, ActionType::MOVE, SubActionType::MOVE_UP)};
    else 
        return {min_cost, GameAction(craftman_id, ActionType::MOVE, SubActionType::MOVE_DOWN)};
}

Game::Game(const GameOptions game_options, std::vector<std::vector<uint32_t>> map, std::vector<Craftsman> craftsmen)
{

    // load game options
    this->gameOptions = game_options;

    // load map
    auto initialMap = MapState(game_options.mapWidth, game_options.mapHeight);
    for (size_t y = 0; y < map.size(); y++)
    {
        for (size_t x = 0; x < map[y].size(); x++)
        {
            initialMap.setTile(x, y, map[y][x]);
        }
    }

    // load craftsmen
    std::unordered_map<CraftsmanID, Craftsman> initialCraftsmen;
    for (const Craftsman &craftsman : craftsmen)
    {
        initialCraftsmen[craftsman.id] = craftsman;
        initialMap.setBit(craftsman.x, craftsman.y, craftsman.isT1 ? TileMask::T1_CRAFTSMAN : TileMask::T2_CRAFTSMAN);
    }

    // load initial state
    auto turn1 = GameState(initialMap, initialCraftsmen);

    allTurns.push_back(turn1);
}

void Game::addAction(const GameAction action)
{
    actionBuffer.emplace_back(action);
}

void Game::nextTurn()
{
    if (allTurns.size() >= gameOptions.maxTurns)
        return;

    // apply actions in buffer to current state
    GameState &currentState = allTurns.back();

    GameState nextState = currentState.applyActions(actionBuffer);

    // push new state to allTurns
    allTurns.push_back(nextState);

    // clear action buffer
    actionBuffer.clear();
}

inline bool Game::isFinished() const
{
    return getCurrentState().turn >= gameOptions.maxTurns;
}

inline bool Game::isT1Turn() const
{
    return getCurrentState().isT1Turn;
}

GameState Game::getCurrentState() const
{
    return allTurns.back();
}

using namespace std;

int main(void)
{
    GameOptions gameOptions;
    gameOptions.mapWidth = 10;
    gameOptions.mapHeight = 10;
    gameOptions.maxTurns = 100;
    gameOptions.territoryCoeff = 10;
    gameOptions.castleCoeff = 100;
    gameOptions.wallCoeff = 1;

    vector<vector<uint32_t>> map;
    for (int i = 0; i < gameOptions.mapHeight; i++)
    {
        vector<uint32_t> row;
        for (int j = 0; j < gameOptions.mapWidth; j++)
        {
            row.push_back(0);
        }
        map.push_back(row);
    }

    vector<Craftsman> craftsmen;
    for (int i = 0; i < 2; i++)
    {
        craftsmen.push_back(Craftsman(i, i, i, true));
    }

    Game game = Game(gameOptions, map, craftsmen);
    GameState current_state = game.getCurrentState();
    pair<int, GameAction> res = current_state.findWayToBuild(0, 0, true, {{1, 0}, {0, 1}});
    cout << res.first;

    // Game game = Game(gameOptions, map, craftsmen);
    // for (int i = 0; i < 10; i++)
    // {
    //     for (int j = 0; j < 2; j++)
    //     {
    //         if (i % 2 == 0)
    //             game.addAction(GameAction(j, ActionType::BUILD, SubActionType::BUILD_RIGHT));
    //         else
    //             game.addAction(GameAction(j, ActionType::MOVE, SubActionType::MOVE_RIGHT));
    //     }
    //     game.nextTurn();
    // }

    // for (int i = 0; i < 10; i++)
    // {
    //     for (int j = 0; j < 2; j++)
    //     {
    //         if (i % 2 == 0)
    //             game.addAction(GameAction(j, ActionType::BUILD, SubActionType::BUILD_DOWN));
    //         else
    //             game.addAction(GameAction(j, ActionType::MOVE, SubActionType::MOVE_DOWN));
    //     }
    //     game.nextTurn();
    // }

    // for (int i = 0; i < 10; i++)
    // {
    //     for (int j = 0; j < 2; j++)
    //     {
    //         if (i % 2 == 0)
    //             game.addAction(GameAction(j, ActionType::BUILD, SubActionType::BUILD_LEFT));
    //         else
    //             game.addAction(GameAction(j, ActionType::MOVE, SubActionType::MOVE_LEFT));
    //     }
    //     game.nextTurn();
    // }

    // for (int i = 0; i < 10; i++)
    // {
    //     for (int j = 0; j < 2; j++)
    //     {
    //         if (i % 2 == 0)
    //             game.addAction(GameAction(j, ActionType::BUILD, SubActionType::BUILD_UP));
    //         else
    //             game.addAction(GameAction(j, ActionType::MOVE, SubActionType::MOVE_UP));
    //     }
    //     game.nextTurn();
    // }

    // game.addAction(GameAction(1, ActionType::DESTROY, SubActionType::DESTROY_LEFT));
    // game.nextTurn();
    // game.addAction(GameAction(1, ActionType::MOVE, SubActionType::MOVE_RIGHT));
    // game.nextTurn();
    // game.addAction(GameAction(1, ActionType::DESTROY, SubActionType::DESTROY_LEFT));
    // game.nextTurn();
    // game.addAction(GameAction(1, ActionType::MOVE, SubActionType::MOVE_DOWN));
    // game.nextTurn();
    // game.addAction(GameAction(1, ActionType::DESTROY, SubActionType::DESTROY_LEFT));
    // game.nextTurn();
    // game.addAction(GameAction(1, ActionType::BUILD, SubActionType::BUILD_RIGHT));
    // game.nextTurn();
    // game.addAction(GameAction(1, ActionType::BUILD, SubActionType::BUILD_LEFT));
    // game.nextTurn();

    // game.getCurrentState().map.printMap();

    return 0;
}