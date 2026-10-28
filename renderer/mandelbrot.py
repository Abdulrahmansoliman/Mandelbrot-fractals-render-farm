def caculcate_iterations(c, iterations):
    z = 0
    for i in range(iterations):
        z = z * z + c
        if abs(z) > 2:
            return i
    return None
