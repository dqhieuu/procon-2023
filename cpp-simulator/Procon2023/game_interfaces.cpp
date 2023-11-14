#include "game_interfaces.h"

int32_t subActionToX(SubActionType subActionType)
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

int32_t subActionToY(SubActionType subActionType)
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

MapState::MapState(int32_t mapWidth, int32_t mapHeight)
{
    assert(mapHeight <= 25 && mapWidth <= 25 && mapHeight >= 0 && mapWidth >= 0);
    this->mapWidth = mapWidth;
    this->mapHeight = mapHeight;
    tiles = std::vector<std::vector<uint32_t>>(25, std::vector<uint32_t>(25, 0));

    tileStatusesT1 = std::vector<std::vector<TileStatus>>(25, std::vector<TileStatus>(25, NOT_VISITED));
    tileStatusesT2 = std::vector<std::vector<TileStatus>>(25, std::vector<TileStatus>(25, NOT_VISITED));

    // if mapWidth or mapHeight < 25, set POND bit of outer tiles to POND
    for (auto y = mapHeight; y < 25; ++y)
        for (auto x = mapWidth; x < 25; ++x)
            setBit(x, y, TileMask::POND);
}

GameAction::GameAction() : craftsmanId(-1), actionType(ActionType::MOVE), subActionType(SubActionType::MOVE_DOWN)
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

bool MapState::tileExists(int x, int y)
{
    return x >= 0 && x < mapWidth && y >= 0 && y < mapHeight;
}

void MapState::setTile(size_t x, size_t y, uint32_t mask)
{
    tiles[y][x] = mask;
}

void MapState::setBit(size_t x, size_t y, TileMask mask)
{
    tiles[y][x] |= (1 << mask);
}

void MapState::clearBit(size_t x, size_t y, TileMask mask)
{
    tiles[y][x] &= ~(1 << mask);
}

bool MapState::isBitToggled(size_t x, size_t y, TileMask mask)
{
    return tiles[y][x] & (1 << mask);
}

bool MapState::isAnyOfMaskToggled(size_t x, size_t y, uint32_t mask)
{
    return tiles[y][x] & mask;
}

void MapState::clearMapBit(TileMask mask)
{
    for (int y = 0; y < mapHeight; y++)
    {
        for (int x = 0; x < mapWidth; x++)
        {
            clearBit(x, y, mask);
        }
    }
}

uint32_t MapState::getTile(uint64_t x, uint64_t y)
{
    return tiles[y][x];
}

void MapState::printMap()
{
    for (int i = 0; i < tiles.size(); i++)
    {
        for (int j = 0; j < tiles[i].size(); j++)
        {
            std::cout << tiles[i][j] << " ";
        }
        std::cout << std::endl;
    }
}

int MapState::calcPoints(const GameOptions &gameOptions, bool isT1)
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

TileStatus MapState::checkCloseTerritory(int32_t x, int32_t y, bool is_t1)
{
    if (x < 0 || x >= mapWidth || y < 0 || y >= mapHeight)
    {
        return NOT_TERRITORY;
    }

    auto &tileStatuses = is_t1 ? tileStatusesT1 : tileStatusesT2;
    const auto wallMask = is_t1 ? TileMask::T1_WALL : TileMask::T2_WALL;

    if (tileStatuses[y][x] != TileStatus::NOT_VISITED)
    {
        return tileStatuses[y][x];
    }

    // check 4 direction
    if (tiles[y][x - 1] != wallMask)
    {
        if (checkCloseTerritory(x - 1, y, is_t1) == NOT_TERRITORY)
            return tileStatuses[y][x] = NOT_TERRITORY;
    }
    if (tiles[y][x + 1] != wallMask)
    {
        if (checkCloseTerritory(x + 1, y, is_t1) == NOT_TERRITORY)
            return tileStatuses[y][x] = NOT_TERRITORY;
    }
    if (tiles[y - 1][x] != wallMask)
    {
        if (checkCloseTerritory(x, y - 1, is_t1) == NOT_TERRITORY)
            return tileStatuses[y][x] = NOT_TERRITORY;
    }
    if (tiles[y + 1][x] != wallMask)
    {
        if (checkCloseTerritory(x, y + 1, is_t1) == NOT_TERRITORY)
            return tileStatuses[y][x] = NOT_TERRITORY;
    }
    return tileStatuses[y][x] = IS_TERRITORY;
}

void MapState::updateTerritory(std::vector<DestroyAction> destroyActions, std::vector<BuildAction> buildActions)
{
    clearMapBit(TileMask::T1_CLOSE_TERRITORY);
    clearMapBit(TileMask::T2_CLOSE_TERRITORY);

    // apply actions
    for (const DestroyAction &action : destroyActions)
    {
        if (!(isBitToggled(action.x, action.y, TileMask::T1_WALL) || isBitToggled(action.x, action.y, TileMask::T2_WALL)))
            continue;

        clearBit(action.x, action.y, action.isT1 ? TileMask::T1_WALL : TileMask::T2_WALL);
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

    updateCloseTerritoryAndClearOpenTerritoryInside();
}

void MapState::updateCloseTerritoryAndClearOpenTerritoryInside()
{
    MapState previousMap = *this;

    for (int y = 0; y < mapHeight; y++)
        for (int x = 0; x < mapWidth; x++)
        {
            if (tileStatusesT1[y][x] == NOT_VISITED)
            {
                tileStatusesT1[y][x] = checkCloseTerritory(x, y, true);
            }

            if (tileStatusesT1[y][x] == IS_TERRITORY)
            {
                setBit(x, y, TileMask::T1_CLOSE_TERRITORY);
                clearBit(x, y, TileMask::T1_OPEN_TERRITORY);
                clearBit(x, y, TileMask::T2_OPEN_TERRITORY);
            }

            if (tileStatusesT2[y][x] == NOT_VISITED)
            {
                tileStatusesT2[y][x] = checkCloseTerritory(x, y, false);
            }
            if (tileStatusesT2[y][x] == IS_TERRITORY)
            {
                setBit(x, y, TileMask::T2_CLOSE_TERRITORY);
                clearBit(x, y, TileMask::T1_OPEN_TERRITORY);
                clearBit(x, y, TileMask::T2_OPEN_TERRITORY);
            }
        }

    for (int y = 0; y < mapHeight; y++)
        for (int x = 0; x < mapWidth; x++)
        {
            if (previousMap.tileStatusesT1[y][x] == IS_TERRITORY &&
                tileStatusesT1[y][x] == NOT_TERRITORY && tileStatusesT2[y][x] == NOT_TERRITORY)
            {
                setBit(y, x, TileMask::T1_OPEN_TERRITORY);
            }
            else if (previousMap.tileStatusesT2[y][x] == IS_TERRITORY &&
                     tileStatusesT1[y][x] == NOT_TERRITORY && tileStatusesT2[y][x] == NOT_TERRITORY)
            {
                setBit(y, x, TileMask::T2_OPEN_TERRITORY);
            }
        }
}

GameState::GameState(MapState _map, std::unordered_map<CraftsmanID, Craftsman> craftsmen)
    : map(_map.mapWidth, _map.mapHeight), craftsmen(craftsmen)
{
}

GameState GameState::applyActions(const std::unordered_map<CraftsmanID, GameAction> &actionByCraftsman)
{
    auto nextGameState = *this;
    nextGameState.lastTurnActions = actionByCraftsman;

    std::vector<DestroyAction> destroyActions;
    std::vector<BuildAction> buildActions;
    std::vector<GameAction> moveActions;

    std::set<std::pair<int32_t, int32_t>> moveForbiddenPositions;

    for (const auto &[craftsmanId, action] : actionByCraftsman)
    {
        const auto &craftsman = craftsmen[craftsmanId];
        auto nextX = craftsman.x + subActionToX(action.subActionType);
        auto nextY = craftsman.y + subActionToY(action.subActionType);

        if (!map.tileExists(nextX, nextY))
            continue;

        if (action.actionType == ActionType::MOVE)
            moveActions.emplace_back(action);
        else if (action.actionType == ActionType::BUILD)
            buildActions.push_back({nextX, nextY, craftsman.isT1});
        else if (action.actionType == ActionType::DESTROY)
            destroyActions.push_back({nextX, nextY, craftsman.isT1});
    }

    auto nextMap = map;
    nextMap.updateTerritory(destroyActions, buildActions);

    for (const auto [_, craftsman] : craftsmen)
    {
        moveForbiddenPositions.insert({craftsman.x, craftsman.y});
    }

    for (const auto &action : moveActions)
    {
        const auto &craftsman = craftsmen[action.craftsmanId];
        auto nextX = craftsman.x + subActionToX(action.subActionType);
        auto nextY = craftsman.y + subActionToY(action.subActionType);

        if (moveForbiddenPositions.find({nextX, nextY}) != moveForbiddenPositions.end())
            continue;

        if (nextMap.isBitToggled(nextX, nextY, craftsman.isT1 ? TileMask::T2_WALL : TileMask::T1_WALL) ||
            nextMap.isBitToggled(nextX, nextY, TileMask::POND))
            continue;

        nextGameState.craftsmen[action.craftsmanId].x = nextX;
        nextGameState.craftsmen[action.craftsmanId].y = nextY;

        nextMap.clearBit(craftsman.x, craftsman.y, craftsman.isT1 ? TileMask::T1_CRAFTSMAN : TileMask::T2_CRAFTSMAN);
        nextMap.setBit(nextX, nextY, craftsman.isT1 ? TileMask::T1_CRAFTSMAN : TileMask::T2_CRAFTSMAN);
        moveForbiddenPositions.insert({nextX, nextY});
    }

    nextGameState.map = nextMap;
    return nextGameState;
}

Game::Game(GameOptions game_options, std::vector<std::vector<uint32_t>> map, std::vector<Craftsman> craftsmen)
{
    // load game options
    this->gameOptions = game_options;

    // load map
    auto initialMap = MapState(game_options.mapWidth, game_options.mapHeight);
    for (size_t i = 0; i < map.size(); i++)
    {
        for (size_t j = 0; j < map[i].size(); j++)
        {
            initialMap.setTile(i, j, map[i][j]);
        }
    }

    // load craftsmen
    std::unordered_map<CraftsmanID, Craftsman> initialCraftsmen;
    for (const Craftsman &craftsman : craftsmen)
    {
        initialCraftsmen[craftsman.id] = craftsman;
    }

    // load initial state
    auto initialState = GameState(initialMap, initialCraftsmen);

    allTurns.push_back(initialState);
}

void Game::addAction(GameAction action)
{
    actionBuffer.push_back(action);
}

void Game::nextTurn()
{
    if (allTurns.size() >= gameOptions.maxTurns)
        return;

    // apply actions in buffer to current state
    GameState &currentState = allTurns.back();

    std::unordered_map<CraftsmanID, GameAction> actionByCraftsman;
    for (const GameAction &action : actionBuffer)
    {
        actionByCraftsman[action.craftsmanId] = action;
    }

    GameState nextState = currentState.applyActions(actionByCraftsman);

    // push new state to allTurns
    allTurns.push_back(nextState);

    // clear action buffer
    actionBuffer.clear();
}

bool Game::isFinished()
{
    return allTurns.size() >= gameOptions.maxTurns;
}

bool Game::isT1Turn()
{
    return allTurns.size() % 2 == 0;
}

GameState Game::getCurrentState()
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
    for (int i = 0; i < 10; i++)
    {
        craftsmen.push_back(Craftsman(i, i + 1, i + 1, true));
    }

    Game game = Game(gameOptions, map, craftsmen);
    for (int i = 0; i < 10; i++)
    {
        game.addAction(GameAction(0, ActionType::MOVE, SubActionType::MOVE_DOWN));
        game.nextTurn();
    }
    cout << game.getCurrentState().map.tiles[0][0];

    return 0;
}