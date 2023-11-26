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
#include <bitset>
#include <queue>
#include <unordered_set>

typedef int32_t CraftsmanID;

enum class ActionType
{
    MOVE,
    BUILD,
    DESTROY,
    STAY,
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
    STAY_STAY,
};

enum TileMask
{
    POND,
    CASTLE,
    T1_WALL,
    T2_WALL,
    T1_CRAFTSMAN,
    T2_CRAFTSMAN,
    T1_CLOSE_TERRITORY,
    T2_CLOSE_TERRITORY,
    T1_OPEN_TERRITORY,
    T2_OPEN_TERRITORY,
};

enum TileStatus : uint8_t
{
    NOT_VISITED,
    IS_TERRITORY,
    NOT_TERRITORY
};

inline int32_t subActionToX(SubActionType subActionType);
inline int32_t subActionToY(SubActionType subActionType);

struct GameOptions
{
    int32_t mapWidth;
    int32_t mapHeight;
    int32_t maxTurns;

    int32_t wallCoeff;
    int32_t castleCoeff;
    int32_t territoryCoeff;
};

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

struct MapState
{
public:
    std::vector<std::vector<uint32_t>> tiles;
    std::vector<std::vector<TileStatus>> tileStatusesT1;
    std::vector<std::vector<TileStatus>> tileStatusesT2;

    int32_t mapWidth;
    int32_t mapHeight;

    MapState(int32_t mapWidth, int32_t mapHeight);
    inline bool validPosition(int x, int y) const;
    inline void setTile(size_t x, size_t y, uint32_t mask);
    inline void setBit(size_t x, size_t y, TileMask mask);
    inline void clearBit(size_t x, size_t y, TileMask mask);
    inline bool isBitToggled(size_t x, size_t y, TileMask mask) const;
    inline bool isAnyOfMaskToggled(size_t x, size_t y, uint32_t mask) const;
    void clearMapBit(const TileMask mask);
    inline uint32_t getTile(uint64_t x, uint64_t y) const;
    std::string printMap() const;
    int calcPoints(const GameOptions &gameOptions, bool isT1) const;
    void checkCloseTerritory(const int32_t x, const int32_t y, const bool is_t1);
    void updateTerritory(const std::vector<DestroyAction> &&destroyActions,
                         const std::vector<BuildAction> &&buildActions);

    void clearTileStatuses();

private:
    void updateCloseTerritoryAndClearOpenTerritoryInside(const MapState &previousMap);
};

struct GameState
{
    MapState map;
    std::vector<GameAction> lastTurnActions;
    std::unordered_map<CraftsmanID, Craftsman> craftsmen;

    int turn;
    bool isT1Turn;

    GameState(MapState _map, std::unordered_map<CraftsmanID, Craftsman> craftsmen);
    GameState(MapState _map, std::unordered_map<CraftsmanID, Craftsman> craftsmen, int turn, bool isT1Turn);
    GameState applyActions(const std::vector<GameAction> &actions);
};

struct Game
{
private:
    std::vector<GameAction> actionBuffer;

public:
    GameOptions gameOptions;
    std::vector<GameState> allTurns;

    Game(const GameOptions game_options, std::vector<std::vector<uint32_t>> map, std::vector<Craftsman> craftsmen);
    void addAction(const GameAction action);
    void nextTurn();
    GameState getCurrentState() const;
    inline bool isT1Turn() const;
    inline bool isFinished() const;
};

#endif // GAME_INTERFACES_H
