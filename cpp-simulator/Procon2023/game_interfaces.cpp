#include "game_interfaces.h"

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
}

GameState::GameState(MapState _map, std::unordered_map<CraftsmanID, Craftsman> _craftsmen, int _turn, bool _isT1Turn)
    : map(_map), craftsmen(_craftsmen), turn(_turn), isT1Turn(_isT1Turn)
{
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
    for (int i = 0; i < 10; i++)
    {
        for (int j = 0; j < 2; j++)
        {
            if (i % 2 == 0)
                game.addAction(GameAction(j, ActionType::BUILD, SubActionType::BUILD_RIGHT));
            else
                game.addAction(GameAction(j, ActionType::MOVE, SubActionType::MOVE_RIGHT));
        }
        game.nextTurn();
    }

    for (int i = 0; i < 10; i++)
    {
        for (int j = 0; j < 2; j++)
        {
            if (i % 2 == 0)
                game.addAction(GameAction(j, ActionType::BUILD, SubActionType::BUILD_DOWN));
            else
                game.addAction(GameAction(j, ActionType::MOVE, SubActionType::MOVE_DOWN));
        }
        game.nextTurn();
    }

    for (int i = 0; i < 10; i++)
    {
        for (int j = 0; j < 2; j++)
        {
            if (i % 2 == 0)
                game.addAction(GameAction(j, ActionType::BUILD, SubActionType::BUILD_LEFT));
            else
                game.addAction(GameAction(j, ActionType::MOVE, SubActionType::MOVE_LEFT));
        }
        game.nextTurn();
    }

    for (int i = 0; i < 10; i++)
    {
        for (int j = 0; j < 2; j++)
        {
            if (i % 2 == 0)
                game.addAction(GameAction(j, ActionType::BUILD, SubActionType::BUILD_UP));
            else
                game.addAction(GameAction(j, ActionType::MOVE, SubActionType::MOVE_UP));
        }
        game.nextTurn();
    }

    game.addAction(GameAction(1, ActionType::DESTROY, SubActionType::DESTROY_LEFT));
    game.nextTurn();
    game.addAction(GameAction(1, ActionType::MOVE, SubActionType::MOVE_RIGHT));
    game.nextTurn();
    game.addAction(GameAction(1, ActionType::DESTROY, SubActionType::DESTROY_LEFT));
    game.nextTurn();
    game.addAction(GameAction(1, ActionType::MOVE, SubActionType::MOVE_DOWN));
    game.nextTurn();
    game.addAction(GameAction(1, ActionType::DESTROY, SubActionType::DESTROY_LEFT));
    game.nextTurn();
    game.addAction(GameAction(1, ActionType::BUILD, SubActionType::BUILD_RIGHT));
    game.nextTurn();
    game.addAction(GameAction(1, ActionType::BUILD, SubActionType::BUILD_LEFT));
    game.nextTurn();

    game.getCurrentState().map.printMap();

    return 0;
}