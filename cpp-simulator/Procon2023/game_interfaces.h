// game_interfaces.h

#ifndef GAME_INTERFACES_H
#define GAME_INTERFACES_H

#include <vector>
#include <iostream>
#include <ctype.h>
#include <assert.h>
#include <unordered_map>
#include <set>
#include <algorithm>

struct GameOptions
{
    int32_t mapWidth;
    int32_t mapHeight;
    int32_t maxTurns;

    int32_t wallCoeff;
    int32_t castleCoeff;
    int32_t territoryCoeff;
};

enum ActionType
{
    MOVE,
    BUILD,
    DESTROY,
    STAY
};

enum SubActionType
{
    MOVE_UP,
    MOVE_DOWN,
    MOVE_LEFT,
    MOVE_RIGHT,
    MOVE_UP_LEFT,
    MOVE_UP_RIGHT,
    MOVE_DOWN_LEFT,
    MOVE_DOWN_RIGHT,
    BUILD_UP,
    BUILD_DOWN,
    BUILD_LEFT,
    BUILD_RIGHT,
    DESTROY_UP,
    DESTROY_DOWN,
    DESTROY_LEFT,
    DESTROY_RIGHT,
};

enum TileMask
{
    CASTLE,
    POND,
    T1_WALL,
    T2_WALL,
    T1_CRAFTSMAN,
    T2_CRAFTSMAN,
    T1_CLOSE_TERRITORY,
    T2_CLOSE_TERRITORY,
    T1_OPEN_TERRITORY,
    T2_OPEN_TERRITORY,
};

int32_t subActionToX(SubActionType subActionType);
int32_t subActionToY(SubActionType subActionType);

typedef int CraftsmanID;
struct GameAction
{
    GameAction();
    GameAction(CraftsmanID craftsmanId, ActionType actionType, SubActionType subActionType);
    CraftsmanID craftsmanId;
    ActionType actionType;
    SubActionType subActionType;
};

struct DestroyAction
{
    int32_t x;
    int32_t y;
    bool isT1;
};

struct BuildAction
{
    int32_t x;
    int32_t y;
    bool isT1;
};

struct Craftsman
{
    Craftsman();
    Craftsman(int32_t id, int32_t x, int32_t y, bool isT1);
    int32_t id;
    int32_t x;
    int32_t y;
    bool isT1;
};

enum TileStatus : uint8_t
{
    NOT_VISITED,
    IS_TERRITORY,
    NOT_TERRITORY
};

struct MapState
{
public:
    std::vector<std::vector<uint32_t>> tiles;

    int32_t mapWidth;
    int32_t mapHeight;
    std::vector<std::vector<TileStatus>> tileStatusesT1;
    std::vector<std::vector<TileStatus>> tileStatusesT2;

    MapState(int32_t mapWidth, int32_t mapHeight);
    bool tileExists(int x, int y);
    void setTile(size_t x, size_t y, uint32_t mask);
    void setBit(size_t x, size_t y, TileMask mask);
    void clearBit(size_t x, size_t y, TileMask mask);
    bool isBitToggled(size_t x, size_t y, TileMask mask);
    bool isAnyOfMaskToggled(size_t x, size_t y, uint32_t mask);
    void clearMapBit(TileMask mask);
    uint32_t getTile(uint64_t x, uint64_t y);
    void printMap();
    int calcPoints(const GameOptions &gameOptions, bool isT1);
    TileStatus checkCloseTerritory(int32_t x, int32_t y, bool is_t1);
    void updateTerritory(std::vector<DestroyAction> destroyActions, std::vector<BuildAction> buildActions);

private:
    void updateCloseTerritoryAndClearOpenTerritoryInside();
};

struct GameState
{
    MapState map;
    std::unordered_map<CraftsmanID, GameAction> lastTurnActions;
    std::unordered_map<CraftsmanID, Craftsman> craftsmen;

    GameState(MapState _map, std::unordered_map<CraftsmanID, Craftsman> craftsmen);
    GameState applyActions(const std::unordered_map<CraftsmanID, GameAction> &actionByCraftsman);
};

struct Game
{
private:
    std::vector<GameAction> actionBuffer;

public:
    GameOptions gameOptions;
    std::vector<GameState> allTurns;

    Game(GameOptions game_options, std::vector<std::vector<uint32_t>> map, std::vector<Craftsman> craftsmen);
    void addAction(GameAction action);
    void nextTurn();
    GameState getCurrentState();
    bool isT1Turn();
    bool isFinished();
};

#endif // GAME_INTERFACES_H
