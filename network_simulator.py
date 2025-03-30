import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from bellman_ford import bellman_ford, get_shortest_path
from network_devices import DeviceType, DEVICE_ICONS, DEVICE_COLORS
from PIL import Image, ImageTk
import os
import json
import tkinter.font as tkFont
from ttkthemes import ThemedTk
import math

class NetworkSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Routing Simulator")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        self.device_images = self.load_device_icons()
        self.device_counters = {
            DeviceType.PC: 0,
            DeviceType.SWITCH: 0,
            DeviceType.ROUTER: 0
        }
        self.source_var = tk.StringVar()
        self.target_var = tk.StringVar()
        self.devices = []
        self.connections = []
        self.selected_device = None
        self.connecting_device = None
        self.dragging_device = None
        self.drag_start_x = None
        self.drag_start_y = None
        self.setup_gui()

    def configure_styles(self):
        self.colors = {
            'primary': '#2196F3',
            'primary_hover': '#1976D2',
            'secondary': '#FF4081',
            'secondary_hover': '#F50057',
            'success': '#4CAF50',
            'success_hover': '#388E3C',
            'warning': '#FFC107',
            'error': '#F44336',
            'error_hover': '#D32F2F',
            'background': '#F5F5F5',
            'toolbar': '#FFFFFF',
        }

        self.style.configure(
            'Action.TButton',
            padding=(15, 10),
            background=self.colors['primary'],
            foreground='white',
            font=('Helvetica', 10, 'bold'),
            borderwidth=0,
            relief='flat'
        )
        
        self.style.map(
            'Action.TButton',
            background=[('active', self.colors['primary_hover'])],
            relief=[('pressed', 'sunken')]
        )

        self.style.configure(
            'Device.TButton',
            padding=(12, 8),
            background=self.colors['secondary'],
            foreground='white',
            font=('Helvetica', 10),
            borderwidth=0,
            relief='flat'
        )
        
        self.style.map(
            'Device.TButton',
            background=[('active', self.colors['secondary_hover'])],
            relief=[('pressed', 'sunken')]
        )

        self.style.configure(
            'Remove.TButton',
            padding=(12, 8),
            background=self.colors['error'],
            foreground='white',
            font=('Helvetica', 10),
            borderwidth=0,
            relief='flat'
        )
        
        self.style.map(
            'Remove.TButton',
            background=[('active', self.colors['error_hover'])],
            relief=[('pressed', 'sunken')]
        )

        self.style.configure(
            'Toolbar.TFrame',
            background=self.colors['toolbar']
        )

    def setup_gui(self):
        self.root.configure(bg=self.colors['background'])
        self.toolbar = ttk.Frame(self.root, style='Toolbar.TFrame')
        self.toolbar.pack(fill="x", padx=10, pady=5)
        self.canvas_frame = ttk.LabelFrame(self.root, text="Network Design")
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.create_toolbar()
        self.create_canvas()

    def create_toolbar(self):
        self.file_menu = tk.Menu(
            self.toolbar,
            tearoff=0,
            bg=self.colors['primary'],
            fg='white',
            activebackground=self.colors['primary_hover'],
            activeforeground='white',
            font=('Helvetica', 10),
            relief='flat',
            bd=0
        )
        
        self.file_menu.add_command(label="Save Network 💾", command=self.save_network, font=('Helvetica', 10))
        self.file_menu.add_command(label="Open Network 📂", command=self.load_network, font=('Helvetica', 10))
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Close Network ❌", command=self.close_network, font=('Helvetica', 10))

        file_button = ttk.Button(
            self.toolbar,
            text="File 📁",
            style='Action.TButton',
            command=lambda e=None: self.file_menu.post(
                file_button.winfo_rootx(),
                file_button.winfo_rooty() + file_button.winfo_height()
            )
        )
        file_button.pack(side="left", padx=5)

        for device_type in DeviceType:
            btn = ttk.Button(
                self.toolbar,
                text=f"Add {device_type.value} {DEVICE_ICONS[device_type]}",
                style='Device.TButton',
                command=lambda d=device_type: self.set_selected_device(d)
            )
            btn.pack(side="left", padx=5)

        ttk.Button(
            self.toolbar,
            text="Move Device 🔄",
            style='Action.TButton',
            command=self.start_move_mode
        ).pack(side="left", padx=5)

        ttk.Button(
            self.toolbar,
            text="Connect Devices 🔗",
            style='Action.TButton',
            command=self.start_connection_mode
        ).pack(side="left", padx=5)

        ttk.Button(
            self.toolbar,
            text="Remove 🗑️",
            style='Remove.TButton',
            command=self.start_remove_mode
        ).pack(side="left", padx=5)

        path_frame = ttk.Frame(self.toolbar, style='Toolbar.TFrame')
        path_frame.pack(side="left", padx=10)

        ttk.Label(
            path_frame,
            text="From:",
            font=('Helvetica', 10, 'bold'),
            background=self.colors['toolbar']
        ).pack(side="left", padx=2)

        self.source_combo = ttk.Combobox(
            path_frame,
            textvariable=self.source_var,
            width=8,
            font=('Helvetica', 10),
            state='readonly'
        )
        self.source_combo.pack(side="left", padx=2)

        ttk.Label(
            path_frame,
            text="To:",
            font=('Helvetica', 10, 'bold'),
            background=self.colors['toolbar']
        ).pack(side="left", padx=2)

        self.target_combo = ttk.Combobox(
            path_frame,
            textvariable=self.target_var,
            width=8,
            font=('Helvetica', 10),
            state='readonly'
        )
        self.target_combo.pack(side="left", padx=2)

        ttk.Button(
            path_frame,
            text="Find Path 🔍",
            style='Action.TButton',
            command=self.find_shortest_path
        ).pack(side="left", padx=5)

    def create_canvas(self):
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=800,
            height=600,
            bg='white',
            relief='ridge',
            bd=2
        )
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.canvas.bind("<Button-1>", self.canvas_clicked)
        self.canvas.bind("<B1-Motion>", self.canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
        self.canvas.bind("<Motion>", self.canvas_motion)

    def set_selected_device(self, device_type):
        self.selected_device = device_type
        self.connecting_device = None
        self.canvas.config(cursor="cross")

    def start_move_mode(self):
        self.selected_device = None
        self.connecting_device = None
        self.canvas.config(cursor="fleur")

    def start_connection_mode(self):
        self.selected_device = None
        self.connecting_device = None
        self.canvas.config(cursor="hand2")

    def start_remove_mode(self):
        self.selected_device = None
        self.connecting_device = None
        self.canvas.config(cursor="X_cursor")

    def canvas_clicked(self, event):
        x, y = event.x, event.y
        
        if self.selected_device:
            type_specific_id = self.get_next_device_id(self.selected_device)
            device_id = len(self.devices)
            self.devices.append((self.selected_device, type_specific_id, x, y))
            self.draw_device(device_id, self.selected_device, type_specific_id, x, y)
            self.update_device_combos()
        
        elif self.canvas.cget('cursor') == 'X_cursor':
            device_id = self.find_device_at_position(x, y)
            if device_id is not None:
                self.remove_device(device_id)
            else:
                self.remove_connection_at_position(x, y)
                
        elif self.canvas.cget('cursor') == 'hand2':
            device_id = self.find_device_at_position(x, y)
            if device_id is not None:
                if self.connecting_device is None:
                    self.connecting_device = device_id
                else:
                    if device_id != self.connecting_device:
                        self.add_connection(self.connecting_device, device_id)
                    self.connecting_device = None
                    self.canvas.delete("temp_line")
        
        elif self.canvas.cget('cursor') == 'fleur':
            device_id = self.find_device_at_position(x, y)
            if device_id is not None:
                self.dragging_device = device_id
                self.drag_start_x = x
                self.drag_start_y = y

    def canvas_drag(self, event):
        if self.dragging_device is not None:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            device = list(self.devices[self.dragging_device])
            new_x = device[2] + dx
            new_y = device[3] + dy
            
            device[2] = new_x
            device[3] = new_y
            self.devices[self.dragging_device] = tuple(device)
            
            self.canvas.delete(f"device_{self.dragging_device}")
            self.draw_device(self.dragging_device, device[0], device[1], new_x, new_y)
            
            self.update_connections_for_device(self.dragging_device)
            
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def canvas_release(self, event):
        if self.dragging_device is not None:
            self.canvas.delete("highlight")
            self.dragging_device = None
            self.drag_start_x = None
            self.drag_start_y = None

    def canvas_motion(self, event):
        if self.connecting_device is not None:
            self.canvas.delete("temp_line")
            start_device = self.devices[self.connecting_device]
            
            target_device = self.find_device_at_position(event.x, event.y)
            if target_device is not None and target_device != self.connecting_device:
                self.canvas.create_line(
                    start_device[2], start_device[3],
                    event.x, event.y,
                    tags="temp_line",
                    dash=(4, 2)
                )

    def draw_device(self, device_id, device_type, type_specific_id, x, y):
        if self.device_images:
            image = self.device_images[device_type]
            self.canvas.create_image(
                x, y,
                image=image,
                tags=f"device_{device_id}"
            )
            
            self.canvas.create_text(
                x, y + 20,
                text=f"{device_type.value}\n{type_specific_id}",
                tags=f"device_{device_id}",
                fill="black",
                font=("Arial", 8),
                justify="center"
            )
        else:
            size = 30
            color = DEVICE_COLORS[device_type]
            
            self.canvas.create_oval(
                x-size/2, y-size/2,
                x+size/2, y+size/2,
                fill=color,
                tags=f"device_{device_id}"
            )
            
            self.canvas.create_text(
                x, y,
                text=f"{device_type.value}\n{type_specific_id}",
                tags=f"device_{device_id}"
            )

    def draw_connection(self, device1_id, device2_id):
        d1 = self.devices[device1_id]
        d2 = self.devices[device2_id]
        
        conn_id = f"connection_{min(device1_id, device2_id)}_{max(device1_id, device2_id)}"
        
        if self.dragging_device is not None:
            self.canvas.create_line(
                d1[2], d1[3], d2[2], d2[3],
                tags=(conn_id, "connection"),
                width=2
            )
            return
        
        steps = 20
        dx = (d2[2] - d1[2]) / steps
        dy = (d2[3] - d1[3]) / steps
        
        def animate_connection(step):
            if step <= steps:
                progress = step/steps
                end_x = d1[2] + dx * step
                end_y = d1[3] + dy * step
                
                self.canvas.delete(conn_id)
                
                dash_length = 10
                dash_pattern = (dash_length, dash_length)
                dash_offset = -int(progress * dash_length * 2)
                
                self.canvas.create_line(
                    d1[2], d1[3], end_x, end_y,
                    tags=(conn_id, "connection"),
                    width=2,
                    dash=dash_pattern,
                    dashoffset=dash_offset
                )
                
                if step < steps:
                    self.root.after(20, lambda: animate_connection(step + 1))
                else:
                    self.canvas.create_line(
                        d1[2], d1[3], d2[2], d2[3],
                        tags=(conn_id, "connection"),
                        width=2
                    )
        
        animate_connection(1)

    def update_connections_for_device(self, device_id):
        for d1, d2 in self.connections:
            if d1 == device_id or d2 == device_id:
                conn_id = f"connection_{min(d1, d2)}_{max(d1, d2)}"
                self.canvas.delete(conn_id)
                self.draw_connection(d1, d2)

    def find_device_at_position(self, x, y):
        for i, (_, _, dev_x, dev_y) in enumerate(self.devices):
            if abs(x - dev_x) < 20 and abs(y - dev_y) < 20:
                return i
        return None

    def get_next_device_id(self, device_type):
        next_id = self.device_counters[device_type]
        self.device_counters[device_type] += 1
        return next_id

    def update_device_combos(self):
        device_list = [f"{d[0].value} {d[1]}" for d in self.devices]
        self.source_combo['values'] = device_list
        self.target_combo['values'] = device_list

    def calculate_edge_cost(self, device1_id, device2_id):
        d1_type = self.devices[device1_id][0]
        d2_type = self.devices[device2_id][0]
        
        if (d1_type == DeviceType.PC and d2_type == DeviceType.SWITCH) or \
           (d2_type == DeviceType.PC and d1_type == DeviceType.SWITCH):
            return 1
        elif (d1_type == DeviceType.PC and d2_type == DeviceType.ROUTER) or \
             (d2_type == DeviceType.PC and d1_type == DeviceType.ROUTER):
            return 2
        elif (d1_type == DeviceType.SWITCH and d2_type == DeviceType.ROUTER) or \
             (d2_type == DeviceType.SWITCH and d1_type == DeviceType.ROUTER):
            return 2
        elif d1_type == DeviceType.ROUTER and d2_type == DeviceType.ROUTER:
            return 3
        elif d1_type == DeviceType.SWITCH and d2_type == DeviceType.SWITCH:
            return 2
        return 1

    def find_shortest_path(self):
        self.canvas.delete("highlight")
        
        if not self.source_var.get() or not self.target_var.get():
            messagebox.showwarning("Error", "Please select source and target devices")
            return
        
        try:    
            source_parts = self.source_var.get().split()
            target_parts = self.target_var.get().split()
            
            source_type = ' '.join(source_parts[:-1])
            target_type = ' '.join(target_parts[:-1])
            source_type_id = int(source_parts[-1])
            target_type_id = int(target_parts[-1])
            
            source_id = None
            target_id = None
            for i, (dev_type, type_id, _, _) in enumerate(self.devices):
                if dev_type.value == source_type and type_id == source_type_id:
                    source_id = i
                if dev_type.value == target_type and type_id == target_type_id:
                    target_id = i
                    
            if source_id is None or target_id is None:
                messagebox.showerror("Error", "Could not find selected devices")
                return
                
            G = nx.Graph()
            
            for i in range(len(self.devices)):
                G.add_node(i)
            
            for d1, d2 in self.connections:
                weight = self.calculate_edge_cost(d1, d2)
                G.add_edge(d1, d2, weight=weight)
                G.add_edge(d2, d1, weight=weight)
            
            if not nx.has_path(G, source_id, target_id):
                messagebox.showwarning("No Path", "No path exists between selected devices!")
                return
            
            try:
                path = nx.shortest_path(G, source_id, target_id, weight='weight')
                total_cost = nx.shortest_path_length(G, source_id, target_id, weight='weight')
                self.highlight_path(path, total_cost)
            except nx.NetworkXNoPath:
                messagebox.showwarning("No Path", "No path exists between selected devices!")
                
        except ValueError as e:
            messagebox.showerror("Error", "Invalid source or target selection")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def highlight_path(self, path, total_cost):
        self.canvas.delete("highlight")
        
        def animate_path(index):
            if index < len(path) - 1:
                d1 = self.devices[path[index]]
                d2 = self.devices[path[index + 1]]
                
                self.animate_gradient_line(d1[2], d1[3], d2[2], d2[3], self.colors['success'])
                
                self.ripple_highlight(d1[2], d1[3])
                if index == len(path) - 2:
                    self.ripple_highlight(d2[2], d2[3])
                    
                self.root.after(500, lambda: animate_path(index + 1))
                
            if index == len(path) - 1:
                self.animate_cost_display(total_cost)
        
        animate_path(0)

    def animate_gradient_line(self, x1, y1, x2, y2, color):
        steps = 30
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        
        def draw_segment(step, prev_line=None):
            if step <= steps:
                if prev_line:
                    self.canvas.delete(prev_line)
                
                end_x = x1 + dx * step
                end_y = y1 + dy * step
                
                width = 3 + math.sin(step/steps * math.pi) * 2
                
                line = self.canvas.create_line(
                    x1, y1, end_x, end_y,
                    fill=color,
                    width=width,
                    tags="highlight",
                    smooth=True,
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND
                )
                
                self.root.after(20, lambda: draw_segment(step + 1, line))
        
        draw_segment(1)

    def ripple_highlight(self, x, y):
        num_rings = 3
        max_radius = 25
        duration = 1000
        steps = 20
        
        def animate_ripples(step):
            if step < steps:
                self.canvas.delete("ripple")
                
                for ring in range(num_rings):
                    progress = (step + ring * (steps/num_rings)) % steps
                    radius = (progress/steps) * max_radius
                    opacity = int(255 * (1 - progress/steps))
                    
                    if opacity > 0:
                        color = self.colors['success']
                        self.canvas.create_oval(
                            x - radius, y - radius,
                            x + radius, y + radius,
                            outline=color,
                            width=2,
                            tags=("highlight", "ripple")
                        )
                
                self.root.after(duration//steps, lambda: animate_ripples(step + 1))
        
        animate_ripples(0)

    def animate_cost_display(self, total_cost):
        panel_width = 150
        panel_height = 40
        
        def animate_panel(step, max_steps=10):
            if step <= max_steps:
                progress = step/max_steps
                current_width = panel_width * progress
                
                self.canvas.delete("cost_panel")
                
                self.canvas.create_rectangle(
                    10, 10,
                    10 + current_width, 10 + panel_height,
                    fill='white',
                    outline=self.colors['success'],
                    width=2,
                    tags=("highlight", "cost_panel")
                )
                
                if step == max_steps:
                    self.animate_cost_text(total_cost)
                else:
                    self.root.after(30, lambda: animate_panel(step + 1))
        
        animate_panel(1)

    def animate_cost_text(self, total_cost):
        text = f"Path Cost: {total_cost}"
        chars = list(text)
        
        def animate_text(index):
            if index <= len(chars):
                self.canvas.delete("cost_text")
                
                self.canvas.create_text(
                    15, 25,
                    text=''.join(chars[:index]),
                    fill=self.colors['success'],
                    font=('Helvetica', 12, 'bold'),
                    anchor="w",
                    tags=("highlight", "cost_text")
                )
                
                if index < len(chars):
                    self.root.after(50, lambda: animate_text(index + 1))
        
        animate_text(1)

    def save_network(self):
        network_config = {
            'device_counters': {str(k.value): v for k, v in self.device_counters.items()},
            'devices': [
                {
                    'type': str(device[0].value),
                    'id': device[1],
                    'x': device[2],
                    'y': device[3]
                } 
                for device in self.devices
            ],
            'connections': self.connections
        }
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Network Configuration"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(network_config, f, indent=4)
                messagebox.showinfo("Success", "Network configuration saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save network: {str(e)}")

    def load_network(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Open Network Configuration"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    network_config = json.load(f)
                
                self.clear_network()
                
                if 'device_counters' in network_config:
                    self.device_counters = {
                        DeviceType(k): v 
                        for k, v in network_config['device_counters'].items()
                    }
                
                for device in network_config['devices']:
                    self.devices.append((
                        DeviceType(device['type']),
                        int(device['id']),
                        float(device['x']),
                        float(device['y'])
                    ))
                
                self.connections = [
                    (int(d1), int(d2)) 
                    for d1, d2 in network_config['connections']
                ]
                
                self.redraw_network()
                self.update_device_combos()
                
                messagebox.showinfo("Success", "Network configuration loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load network: {str(e)}")

    def clear_network(self):
        self.canvas.delete("all")
        self.devices.clear()
        self.connections.clear()
        self.selected_device = None
        self.connecting_device = None
        self.source_var.set('')
        self.target_var.set('')
        for device_type in DeviceType:
            self.device_counters[device_type] = 0

    def close_network(self):
        if self.devices or self.connections:
            if messagebox.askyesno("Close Network", "Are you sure you want to close the current network? All unsaved changes will be lost."):
                self.clear_network()
                messagebox.showinfo("Success", "Network closed successfully!")

    def redraw_network(self):
        self.canvas.delete("all")
        for i, (device_type, type_id, x, y) in enumerate(self.devices):
            self.draw_device(i, device_type, type_id, x, y)
        for d1, d2 in self.connections:
            self.draw_connection(d1, d2)

    def load_device_icons(self):
        icon_size = (32, 32)
        icons = {}
        
        try:
            for device_type in DeviceType:
                image_path = os.path.join('images', f'{device_type.value.lower()}.png')
                if os.path.exists(image_path):
                    image = Image.open(image_path)
                    image = image.resize(icon_size, Image.Resampling.LANCZOS)
                    icons[device_type] = ImageTk.PhotoImage(image)
                else:
                    icons[device_type] = None
            return icons
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to load device icons: {str(e)}\nUsing default shapes.")
            return None

    def remove_device(self, device_id):
        self.canvas.delete(f"device_{device_id}")
        
        connections_to_remove = []
        for d1, d2 in self.connections:
            if d1 == device_id or d2 == device_id:
                conn_id = f"connection_{min(d1, d2)}_{max(d1, d2)}"
                self.canvas.delete(conn_id)
                connections_to_remove.append((d1, d2))
        
        for conn in connections_to_remove:
            self.connections.remove(conn)
        
        self.devices.pop(device_id)
        
        self.canvas.delete("highlight")
        self.update_device_combos()
        self.redraw_network()

    def remove_connection_at_position(self, x, y):
        for d1, d2 in self.connections[:]:
            dev1 = self.devices[d1]
            dev2 = self.devices[d2]
            
            if self.is_point_near_line(x, y, dev1[2], dev1[3], dev2[2], dev2[3]):
                conn_id = f"connection_{min(d1, d2)}_{max(d1, d2)}"
                self.canvas.delete(conn_id)
                self.connections.remove((d1, d2))
                self.canvas.delete("highlight")
                return True
        return False

    def is_point_near_line(self, px, py, x1, y1, x2, y2):
        numerator = abs((y2-y1)*px - (x2-x1)*py + x2*y1 - y2*x1)
        denominator = ((y2-y1)**2 + (x2-x1)**2)**0.5
        
        if denominator == 0:
            return False
        
        distance = numerator/denominator
        
        if min(x1, x2) <= px <= max(x1, x2) and min(y1, y2) <= py <= max(y1, y2):
            return distance < 10
        return False

    def add_connection(self, device1_id, device2_id):
        if device1_id == device2_id:
            return False
        
        if (device1_id, device2_id) in self.connections or (device2_id, device1_id) in self.connections:
            return False

        device1_type = self.devices[device1_id][0]
        device2_type = self.devices[device2_id][0]
        
        connection = (min(device1_id, device2_id), max(device1_id, device2_id))
        self.connections.append(connection)

        self.draw_connection(device1_id, device2_id)
        self.canvas.delete("temp_line")
        return True

if __name__ == "__main__":
    root = ThemedTk(theme="clam")
    app = NetworkSimulator(root)
    root.mainloop()
