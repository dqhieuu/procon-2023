#include <pybind11/pybind11.h>
#include "game_interfaces.h"

namespace py = pybind11;

PYBIND11_MODULE(game_interfaces_binding, m)
{

	m.def("add", &add, "A function that adds two numbers");
}