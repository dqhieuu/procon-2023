#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "game_interfaces.h"

namespace py = pybind11;
using namespace pybind11::literals;

PYBIND11_MODULE(game_interfaces_binding, m)
{
	py::enum_<ActionType>(m, "ActionType")
		.value("MOVE", ActionType::MOVE)
		.value("BUILD", ActionType::BUILD)
		.value("DESTROY", ActionType::DESTROY)
		.value("STAY", ActionType::STAY);

	py::enum_<SubActionType>(m, "SubActionType")
		.value("MOVE_UP", SubActionType::MOVE_UP)
		.value("MOVE_DOWN", SubActionType::MOVE_DOWN)
		.value("MOVE_LEFT", SubActionType::MOVE_LEFT)
		.value("MOVE_RIGHT", SubActionType::MOVE_RIGHT)
		.value("MOVE_UP_LEFT", SubActionType::MOVE_UP_LEFT)
		.value("MOVE_UP_RIGHT", SubActionType::MOVE_UP_RIGHT)
		.value("MOVE_DOWN_LEFT", SubActionType::MOVE_DOWN_LEFT)
		.value("MOVE_DOWN_RIGHT", SubActionType::MOVE_DOWN_RIGHT)
		.value("BUILD_UP", SubActionType::BUILD_UP)
		.value("BUILD_DOWN", SubActionType::BUILD_DOWN)
		.value("BUILD_LEFT", SubActionType::BUILD_LEFT)
		.value("BUILD_RIGHT", SubActionType::BUILD_RIGHT)
		.value("DESTROY_UP", SubActionType::DESTROY_UP)
		.value("DESTROY_DOWN", SubActionType::DESTROY_DOWN)
		.value("DESTROY_LEFT", SubActionType::DESTROY_LEFT)
		.value("DESTROY_RIGHT", SubActionType::DESTROY_RIGHT)
		.value("STAY", SubActionType::STAY_STAY);

	py::enum_<TileMask>(m, "TileMask")
		.value("CASTLE", TileMask::CASTLE)
		.value("POND", TileMask::POND)
		.value("T1_WALL", TileMask::T1_WALL)
		.value("T2_WALL", TileMask::T2_WALL)
		.value("T1_CRAFTSMAN", TileMask::T1_CRAFTSMAN)
		.value("T2_CRAFTSMAN", TileMask::T2_CRAFTSMAN)
		.value("T1_CLOSE_TERRITORY", TileMask::T1_CLOSE_TERRITORY)
		.value("T2_CLOSE_TERRITORY", TileMask::T2_CLOSE_TERRITORY)
		.value("T1_OPEN_TERRITORY", TileMask::T1_OPEN_TERRITORY)
		.value("T2_OPEN_TERRITORY", TileMask::T2_OPEN_TERRITORY);

	py::enum_<TileStatus>(m, "TileStatus")
		.value("NOT_VISITED", TileStatus::NOT_VISITED)
		.value("IS_TERRITORY", TileStatus::IS_TERRITORY)
		.value("NOT_TERRITORY", TileStatus::NOT_TERRITORY);

	py::class_<GameOptions>(m, "GameOptions")
		.def(py::init<>())
		.def_readwrite("mapWidth", &GameOptions::mapWidth)
		.def_readwrite("mapHeight", &GameOptions::mapHeight)
		.def_readwrite("maxTurns", &GameOptions::maxTurns)
		.def_readwrite("wallCoeff", &GameOptions::wallCoeff)
		.def_readwrite("castleCoeff", &GameOptions::castleCoeff)
		.def_readwrite("territoryCoeff", &GameOptions::territoryCoeff);

	py::class_<GameAction>(m, "GameAction")
		.def(py::init<CraftsmanID, ActionType, SubActionType>(), "craftsmanId"_a, "actionType"_a, "subActionType"_a)
		.def_readwrite("craftsmanId", &GameAction::craftsmanId)
		.def_readwrite("actionType", &GameAction::actionType)
		.def_readwrite("subActionType", &GameAction::subActionType);

	py::class_<Craftsman>(m, "Craftsman")
		.def(py::init<int32_t, int32_t, int32_t, bool>(), "id"_a, "x"_a, "y"_a, "isT1"_a)
		.def_readwrite("id", &Craftsman::id)
		.def_readwrite("x", &Craftsman::x)
		.def_readwrite("y", &Craftsman::y)
		.def_readwrite("isT1", &Craftsman::isT1);

	py::class_<MapState>(m, "MapState")
		.def(py::init<int32_t, int32_t>(), "width"_a, "height"_a)
		.def("printMap", &MapState::printMap)
		.def("calcPoints", &MapState::calcPoints)
		.def_readwrite("tiles", &MapState::tiles);

	py::class_<GameState>(m, "GameState")
		.def(py::init<MapState, std::unordered_map<CraftsmanID, Craftsman>>(), "mapState"_a, "craftsmen"_a)
		.def(py::init<MapState, std::unordered_map<CraftsmanID, Craftsman>, int, bool>(), "mapState"_a, "craftsmen"_a, "turn"_a, "isT1Turn"_a)
		.def("applyActions", &GameState::applyActions, "actions"_a)
		.def("findCraftsmanIdByPos", &GameState::findCraftsmanIdByPos, "x"_a, "y"_a)
		.def_readonly("lastTurnActions", &GameState::lastTurnActions)
		.def_readwrite("craftsmen", &GameState::craftsmen)
		.def_readwrite("map", &GameState::map)
		.def_readwrite("turn", &GameState::turn)
		.def_readwrite("isT1Turn", &GameState::isT1Turn);

	py::class_<Game>(m, "Game")
		.def(py::init<GameOptions, std::vector<std::vector<uint32_t>>, std::vector<Craftsman>>(), "gameOptions"_a, "map"_a, "craftsmen"_a)
		.def("addAction", &Game::addAction, "action"_a)
		.def("nextTurn", &Game::nextTurn, py::call_guard<py::gil_scoped_release>()) // multithreaded heavy function
		.def("getCurrentState", &Game::getCurrentState)
		.def_readwrite("gameOptions", &Game::gameOptions)
		.def("__copy__", [](const Game &self)
			 {
				auto copy = self;
				return copy; })
		.def(
			"__deepcopy__", [](const Game &self, py::dict)
			{
				auto copy = self;
				return copy; },
			"memo"_a);
}