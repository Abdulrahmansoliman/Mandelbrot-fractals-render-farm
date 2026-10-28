class MandelbrotRenderer:
    def __init__(self, job):
        self.width = job["width"]
        self.height = job["height"]

        self.real_min = job["real_min"]
        self.real_max = job["real_max"]

        self.imag_min = job["imag_min"]
        self.imag_max = job["imag_max"]

        self.max_iterations = job["max_iterations"]


    def caculcate_iterations(self, c):
        """
        I am implementign the equation of f(z) = z^2 + c
        while abs(z) > 2
        """
        z = 0
        for i in range(self.max_iterations):
            z = z * z + c
            if abs(z) > 2:
                return i
        return None 


    def pixel_to_complex(self, row, col):
        """
        I suppose the input will be like the following
        width = 3
        height = 3

        real_min = -1
        real_max = 1

        imag_min = -1
        imag_max = 1
        """
        horizontal_fraction = col / (self.width - 1)
        vertical_fraction = row / (self.height - 1)

        real = self.real_min + horizontal_fraction * (self.real_max - self.real_min)
        imag = self.imag_max - vertical_fraction * (self.imag_max - self.imag_min)

        return complex(real, imag)
    


    
    def render_tile(self, task):
        """
        I will convert each pixel into one complex number
        """
        results = []
        for row in range(task["row_start"], task["row_end"]):
            current_row = []
            
            for col in range(task["col_start"], task["col_end"]):

                # Convert the pixel position into a complex number.
                c = self.pixel_to_complex(row, col)
                iterations = self.escape_iterations(c)
                current_row.append(iterations)

            results.append(current_row)

        return results
    