class TileGenerator:
    def __init__(self, job):
        self.width = job["width"]
        self.height = job["height"]
        self.tile_size = job["tile_size"]
    
    def generate_tiles(self):
        """
        I will iterate over the height and widht and take my step size 
        as the tile size, and add each tile in the tasks with its task id
        """
        tasks = []
        task_id = 0
        
        for row in range(0, self.height, self.tile_size):
            for col in range(0, self.width, self.tile_size):
                # I am doing this as i don't want at the last tile to excceed the boundary
                row_end = min(row + self.tile_size, self.height)
                col_end = min(col + self.tile_size, self.width)
                
                task = {
                    "task_id": task_id,
                    "row_start": row,
                    "row_end": row_end,
                    "col_start": col,
                    "col_end": col_end
                }

                tasks.append(task)
                task_id += 1
        
        return tasks