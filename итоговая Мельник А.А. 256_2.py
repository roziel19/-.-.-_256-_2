from flask import Flask, request, jsonify

app = Flask(__name__)

class UAVView:
    def display_status(self, model):
        return {
            "altitude": model.altitude,
            "speed": model.speed,
            "position": model.position,
            "battery_level": model.battery_level,
            "direction": model.current_direction
        }

    def alert(self, message):
        return {"тревога": message}

class UAVDataModel:
    def __init__(self):
        self.altitude = 0
        self.position = (0, 0)
        self.speed = 0
        self.current_direction = 0
        self.battery_level = 100

    def update_direction(self, new_direction):
        self.current_direction = new_direction

    def update_altitude(self, new_altitude):
        self.altitude = new_altitude

    def update_position(self, new_position):
        self.position = new_position

    def update_speed(self, new_speed):
        self.speed = new_speed

    def update_battery_level(self, consumption):
        self.battery_level -= consumption



    def estimate_remaining_flight_time(self):
        if self.speed > 0:
            return self.battery_level / (self.speed * 0.1)  # Примерный расчет времени
        return float('inf')






# Модуль обработки препятствий
class ObstacleHandler:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def process_obstacle_data(self, data):
        if data['дистанция'] < 10:
            self.view.alert(f"Препятствие обнаружено на {data['дистанция']} МЕТРОВ!")
            self.adjust_course()
        elif data['дистанция'] < 5:
            self.view.alert("Слишком близко к препятствию, остановка!")
            self.model.update_speed(0)

    def adjust_course(self):
        new_direction = (self.model.current_direction + 45) % 360
        self.model.update_direction(new_direction)
        new_position = (self.model.position[0] + 10, self.model.position[1] + 10)
        self.view.display_status(self.model)
        self.model.update_position(new_position)


# Модуль мониторинга батареи
class BatteryMonitor:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def check_battery(self):
        if self.model.battery_level < 20:
            self.view.alert("Низкий заряд батареи! Возвращаемся на базу.")
            self.return_to_base()

    def return_to_base(self):
        self.model.update_position((0, 0))
        self.model.update_altitude(0)
        self.model.update_speed(0)
        self.view.alert("Дрон вернулся на базу")
        self.view.display_status(self.model)


# Контроллер дрона
class UAVController:
    def __init__(self, model, view, obstacle_handler, battery_monitor):
        self.model = model
        self.view = view
        self.obstacle_handler = obstacle_handler
        self.battery_monitor = battery_monitor

    def change_position(self, new_position):
        self.model.update_position(new_position)
        return self.view.display_status(self.model)

    def change_altitude(self, new_altitude):
        self.model.update_altitude(new_altitude)
        return self.view.display_status(self.model)

    def change_speed(self, new_speed):
        self.model.update_speed(new_speed)
        return self.view.display_status(self.model)

    def process_sensor_data(self, sensor_data):
        self.obstacle_handler.process_obstacle_data(sensor_data)
        self.battery_monitor.check_battery()


# API для управления дроном
uav_model = UAVDataModel()
uav_view = UAVView()
obstacle_handler = ObstacleHandler(uav_model, uav_view)
battery_monitor = BatteryMonitor(uav_model, uav_view)
uav_controller = UAVController(uav_model, uav_view, obstacle_handler, battery_monitor)

@app.route('/')
def index():
    return app.send_static_file('index.html')  # Убедитесь, что index.html лежит в папке static

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(uav_view.display_status(uav_model))

@app.route('/position', methods=['POST'])
def update_position():
    data = request.get_json()
    new_position = data.get('position', (0, 0))
    return jsonify(uav_controller.change_position(new_position))

@app.route('/altitude', methods=['POST'])
def update_altitude():
    data = request.get_json()
    new_altitude = data.get('altitude', 0)
    return jsonify(uav_controller.change_altitude(new_altitude))

@app.route('/battery', methods=['GET'])
def check_battery():
    return jsonify(battery_monitor.check_battery())

@app.route('/speed', methods=['POST'])
def update_speed():
    data = request.get_json()
    new_speed = data.get('speed', 0)
    return jsonify(uav_controller.change_speed(new_speed))



if __name__ == '__main__':
    app.run(debug=True)
