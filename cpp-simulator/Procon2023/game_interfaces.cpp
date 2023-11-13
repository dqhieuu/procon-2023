#include "game_interfaces.h"
#include <vector>
#include <iostream>
#include <ctype.h>
#include <assert.h>
#include <unordered_map>

using namespace std;

int add(int i, int j)
{
    return i + j;
}

enum TileMask
{
    CASTLE,
    RIVER,
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

// Game -> GameState: current turn -> MapState -> Tile
// apply actions to GameState -> next GameState


struct MapState
{
    vector<vector<uint16_t>> tiles;

    int max_width;
    int max_height;
    MapState(int mapWidth, int mapHeight)
    {
        assert(mapHeight <= 25 && mapWidth <= 25 && mapHeight >= 0 && mapWidth >= 0);
        this->max_width = mapWidth;
        this->max_height = mapHeight;
        // fill tiles with size of 25x25 of CASTLE
        tiles = vector<vector<uint16_t>>(25, vector<uint16_t>(25, 0));

        tileStatuses1 = vector<vector<TileStatus>>(25, vector<TileStatus>(25, NOT_VISITED));
        tileStatuses2 = vector<vector<TileStatus>>(25, vector<TileStatus>(25, NOT_VISITED));

        // if mapWidth or mapHeight < 25, set RIVER bit of outer tiles to RIVER
        for (int i = mapHeight; i < 25; i++)
        {
            for (int j = mapWidth; j < 25; ++j)
            {
                if (i >= mapHeight || j >= mapWidth)
                {
                    setBit(i, j, TileMask::RIVER);
                }
            }
        }
    }

    void setTile(int x, int y, uint16_t mask)
    {
        tiles[x][y] = mask;
    }

    void setBit(int x, int y, TileMask mask)
    {
        tiles[x][y] |= (1 << mask);
    }

    bool checkBitExist(int x, int y, TileMask mask)
    {
        return tiles[x][y] & (1 << mask);
    }

    void clearBit(int x, int y, TileMask mask)
    {
        tiles[x][y] &= ~(1 << mask);
    }

    void clearMapBit(TileMask mask)
    {
        for (int i = 0; i < max_height; i++)
        {
            for (int j = 0; j < max_width; j++)
            {
                clearBit(i, j, mask);
            }
        }
    }

    uint16_t getTile(int x, int y)
    {
        return tiles[x][y];
    }

    void printMap()
    {
        for (int i = 0; i < tiles.size(); i++)
        {
            for (int j = 0; j < tiles[i].size(); j++)
            {
                cout << tiles[i][j] << " ";
            }
            cout << endl;
        }
    }

    vector<vector<TileStatus>> tileStatuses1; // New 2D array
    vector<vector<TileStatus>> tileStatuses2; // New 2D array

    int calcT1Point(const GameOptions &gameOptions)
    {
        int t1_point = 0;
        for (int i = 0; i < max_height; ++i)
        {
            for (int j = 0; j < max_width; ++j)
            {
                if (checkBitExist(i, j, TileMask::T1_CLOSE_TERRITORY) || checkBitExist(i, j, TileMask::T1_OPEN_TERRITORY))
                {
                    t1_point += gameOptions.territoryCoeff;
                    if (checkBitExist(i, j, TileMask::CASTLE))
                    {
                        t1_point += gameOptions.castleCoeff;
                    }
                }
                else if (checkBitExist(i, j, TileMask::T1_WALL))
                {
                    t1_point += gameOptions.wallCoeff;
                }
            }
        }
    }

    int calcT2Point(const GameOptions &gameOptions)
    {
        int t2_point = 0;
        for (int i = 0; i < max_height; ++i)
        {
            for (int j = 0; j < max_width; ++j)
            {
                if (checkBitExist(i, j, TileMask::T2_CLOSE_TERRITORY) || checkBitExist(i, j, TileMask::T2_OPEN_TERRITORY))
                {
                    t2_point += gameOptions.territoryCoeff;
                    if (checkBitExist(i, j, TileMask::CASTLE))
                        {
                            t2_point += gameOptions.castleCoeff;
                        }
                }
                else if (checkBitExist(i, j, TileMask::T2_WALL))
                {
                    t2_point += gameOptions.wallCoeff;
                }
            }
        }
    }

    TileStatus check_close_territory(int x, int y, bool is_t1)
    {
        auto &tileStatuses = is_t1 ? tileStatuses1 : tileStatuses2;
        const auto wallMask = is_t1 ? TileMask::T1_WALL : TileMask::T2_WALL;

        if (tileStatuses[x][y] != TileStatus::NOT_VISITED)
        {
            return tileStatuses[x][y];
        }

        if (x < 0 || x >= max_height || y < 0 || y >= max_width)
        {
            return tileStatuses[x][y] = NOT_TERRITORY;
        }

        // check 4 direction
        if (tiles[x - 1][y] != wallMask)
        {
            if (check_close_territory(x - 1, y, is_t1) == false)
                return tileStatuses[x][y] = NOT_TERRITORY;
        }
        if (tiles[x + 1][y] != wallMask)
        {
            if (check_close_territory(x + 1, y, is_t1) == false)
                return tileStatuses[x][y] = NOT_TERRITORY;
        }
        if (tiles[x][y - 1] != wallMask)
        {
            if (check_close_territory(x, y - 1, is_t1) == false)
                return tileStatuses[x][y] = NOT_TERRITORY;
        }
        if (tiles[x][y + 1] != wallMask)
        {
            if (check_close_territory(x, y + 1, is_t1) == false)
                return tileStatuses[x][y] = NOT_TERRITORY;
        }
        return tileStatuses[x][y] = IS_TERRITORY;
    }

    void update_close_and_open_territory()
    {
        MapState previousMap = *this;
        
        for (int i = 0; i < max_height; i++)
            for (int j = 0; j < max_width; j++)
            {
                if (tileStatuses1[i][j] == NOT_VISITED)
                {
                    tileStatuses1[i][j] = check_close_territory(i, j, true);
                }
                if (tileStatuses2[i][j] == NOT_VISITED)
                {
                    tileStatuses2[i][j] = check_close_territory(i, j, false);
                }
                if (tileStatuses1[i][j] == IS_TERRITORY)
                {
                    clearBit(i, j, TileMask::T1_OPEN_TERRITORY);
                    clearBit(i, j, TileMask::T2_OPEN_TERRITORY);
                    setBit(i, j, TileMask::T1_CLOSE_TERRITORY);
                }
                if (tileStatuses2[i][j] == IS_TERRITORY)
                {
                    clearBit(i, j, TileMask::T1_OPEN_TERRITORY);
                    clearBit(i, j, TileMask::T2_OPEN_TERRITORY);
                    setBit(i, j, TileMask::T2_CLOSE_TERRITORY);
                }
            }
            
        for (int i = 0; i < max_height; i++)
            for (int j = 0; j < max_width; j++)
            {
                if (previousMap.tileStatuses1[i][j] == IS_TERRITORY && tileStatuses1[i][j] == NOT_TERRITORY  && tileStatuses2[i][j] == NOT_TERRITORY)
                {
                    setBit(i, j, TileMask::T1_OPEN_TERRITORY);
                }
                else if (previousMap.tileStatuses2[i][j] == IS_TERRITORY && tileStatuses1[i][j] == NOT_TERRITORY  && tileStatuses2[i][j] == NOT_TERRITORY) 
                {
                    setBit(i, j, TileMask::T2_OPEN_TERRITORY);
                }
            }
    }

    void updateTerritory(vector<DestroyAction> destroyActions, vector<BuildAction> buildActions){
        clearMapBit(TileMask::T1_CLOSE_TERRITORY);
        clearMapBit(TileMask::T2_CLOSE_TERRITORY);

        // apply actions
        for (const DestroyAction& action : destroyActions)
        {
            if(action.isTeam1){
                clearBit(action.x, action.y, TileMask::T1_WALL);
            }
            else{
                clearBit(action.x, action.y, TileMask::T2_WALL);
            }
        }

        update_close_and_open_territory();
    }
};

typedef int CraftsmanID;

struct GameState
{
    MapState map;
    unordered_map<CraftsmanID, GameAction> lastTurnActions;
    unordered_map<CraftsmanID, Craftsman> craftsmen;

    // this function is immutable
    GameState applyActions(const unordered_map<CraftsmanID, GameAction>& actionByCraftsman) {
        GameState nextGameState = GameState();
        nextGameState.map = this->map;
        nextGameState.lastTurnActions = actionByCraftsman;
        nextGameState.craftsmen = this->craftsmen;
    }

    pair<int, int> craftsmanIDToArrayPos(CraftsmanID id) {
        return {craftsmen[id].x, craftsmen[id].y};
    }
};

struct GameOptions
{
    int mapWidth;
    int mapHeight;
    int maxTurns;

    int wallCoeff;
    int castleCoeff;
    int territoryCoeff;
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

struct GameAction
{
    CraftsmanID craftsmanId;
    ActionType actionType;
    SubActionType subActionType;
};

struct DestroyAction {
    bool isTeam1;
    int x;
    int y;
};

struct BuildAction {
    bool isTeam1;
    int x;
    int y;
};

struct Craftsman
{
    int id;
    int x;
    int y;
};

struct Game
{
    GameOptions gameOptions;
    vector<GameState> allTurns;

    vector<GameAction> actionBuffer;
    
    Game(GameOptions game_options, vector<vector<uint16_t>> map) {
        this->gameOptions = game_options;
        allTurns.push_back(GameState());
    }
};

// Game
// - initGame(gameOptions, map)
// - addAction(action): push action to a buffer
// - nextTurn(): apply all actions in buffer to current state, then push new state to allTurns

// GameState: represents a turn
// - applyActions(actions): return new GameState with actions applied

// MapState: represents a map

// - setTile(x, y, mask)
// - setBit(x, y, mask)
// - checkBitExist(x, y, mask)
// - clearBit(x, y, mask)
// - getTile(x, y)

// - buildWall(x, y, is_t1): set wall bit of tile (x, y) is_t1; open, close territory bit to 0
// - destroyWall(x, y, is_t1) set wall bit of tile (x, y) is_t1

// Với 1 turn mới

// clone trạng thái turn cũ
// xoá close territory của mọi ô của 2 bên
// phá tường
// xây tường
// update close territory của mọi ô bằng cách loang
// copy close territory của turn cũ sang open territory của turn mới nếu ô đó không phải là close territory

