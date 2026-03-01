import numpy as np

class VirtualCursorPath:
    def __init__(self):
        pass

    def get_virtual_cursor_path(self,current_position,desired_position,viewport_width,viewport_height):
        path = self._calculate_path(current_position[0],current_position[1],desired_position[0],desired_position[1],viewport_width,viewport_height)
        path[0]=self._avoid_bounds(path[0], 0,viewport_width)
        path[1]=self._avoid_bounds(path[1], 0,viewport_height)
        return path


    @staticmethod
    def _avoid_bounds(array_of_cursor_coordinates,minima_coordinate,maxima_coordinate):
        array_avoiding_minima = [1 if cursor_coordinate == minima_coordinate else cursor_coordinate for cursor_coordinate in array_of_cursor_coordinates]
        array_avoiding_maxima = [maxima_coordinate-1 if cursor_coordinate == maxima_coordinate else cursor_coordinate for cursor_coordinate in array_avoiding_minima]
        return array_avoiding_maxima

    @staticmethod
    def _calculate_path(start_x, start_y,dest_x, dest_y, x_max, y_max, G_0=5, W_0=10, M_0=15, D_0=30):
        sqrt3 = np.sqrt(3)
        sqrt5 = np.sqrt(5)
        x_array = []
        y_array = []
        current_x,current_y = start_x,start_y
        v_x = v_y = W_x = W_y = 0
        while True:
            dist = np.hypot(dest_x - start_x, dest_y - start_y)
            if dist < 1:
                break

            # Force calculation
            W_mag = min(W_0, dist)
            if dist >= D_0:
                W_x = W_x / sqrt3 + (2 * np.random.random() - 1) * W_mag / sqrt5
                W_y = W_y / sqrt3 + (2 * np.random.random() - 1) * W_mag / sqrt5
            else:
                W_x /= sqrt3
                W_y /= sqrt3
                if M_0 < 3:
                    M_0 = np.random.random() * 3 + 3
                else:
                    M_0 /= sqrt5

            # Speed calculation
            v_x += (W_x + G_0 * (dest_x - start_x) / dist)
            v_y += (W_y + G_0 * (dest_y - start_y) / dist)

            # Limit the maximum speed
            v_mag = np.hypot(v_x, v_y)
            if v_mag > M_0:
                v_x = (v_x / v_mag) * M_0
                v_y = (v_y / v_mag) * M_0

            # Update positions
            start_x += v_x
            start_y += v_y
            
            # Limit positions to [0, x_max] and [0, y_max]
            start_x = max(0, min(start_x, x_max))
            start_y = max(0, min(start_y, y_max))
            
            move_x = int(np.round(start_x))
            move_y = int(np.round(start_y))

            if current_x != move_x or current_y != move_y:
                current_x = move_x
                current_y = move_y
                x_array.append(current_x)
                y_array.append(current_y)
        return [x_array,y_array]
    

if __name__ == "__main__":
    path = VirtualCursorPath().get_virtual_cursor_path([0,0],[100,200],1000,1000)