from renderer.mandelbrot import MandelbrotRenderer

job = {
    "width": 3,
    "height": 3,
    "real_min": -1,
    "real_max": 1,
    "imag_min": -1,
    "imag_max": 1,
    "max_iterations": 100,
}
renderer = MandelbrotRenderer(job)

assert renderer.caculcate_iterations(1 + 1j) == 2

assert renderer.caculcate_iterations(0) is None

assert renderer.caculcate_iterations(-1) is None

assert renderer.caculcate_iterations(1) == 3

print("All 4 tests passed!")
