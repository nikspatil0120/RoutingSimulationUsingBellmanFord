from enum import Enum

class DeviceType(Enum):
    PC = "PC"
    SWITCH = "Switch"
    ROUTER = "Router"

# Device images can be added later
DEVICE_ICONS = {
    DeviceType.PC: "🖥️",
    DeviceType.SWITCH: "🔌",
    DeviceType.ROUTER: "📡"
}

DEVICE_COLORS = {
    DeviceType.PC: "#ADD8E6",      # Light blue
    DeviceType.SWITCH: "#98FB98",   # Light green
    DeviceType.ROUTER: "#FFB6C1"    # Light pink
} 
