from renderer.mandelbrot import escape_iterations
assert escape_iterations(1 + 1j, 100) == 2

assert escape_iterations(0, 100) is None

assert escape_iterations(-1, 100) is None

assert escape_iterations(1, 100) == 3

print("All 4 tests passed!")