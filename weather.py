import customtkinter as ctk
import requests
import json
import csv
import os
import threading
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox, filedialog

# ==================== CONFIGURATION ====================
API_KEY = "Add your API here"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
HISTORY_FILE = "weather_history.json"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Colors
BG = "#F0F4F8"
WHITE = "#FFFFFF"
GRAY = "#E2E8F0"
DARK = "#1E293B"
LIGHT_DARK = "#475569"
BLUE = "#3B82F6"
GREEN = "#10B981"
RED = "#EF4444"

# ==================== DATA FUNCTIONS ====================

def fetch_weather(city):
    try:
        params = {"q": city, "appid": API_KEY, "units": "metric"}
        resp = requests.get(BASE_URL, params=params, timeout=10)
        
        if resp.status_code == 401:
            return {"error": "Invalid API Key"}
        if resp.status_code == 404:
            return {"error": f"City '{city}' not found"}
        if resp.status_code != 200:
            return {"error": f"API Error: {resp.status_code}"}
        
        data = resp.json()
        return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temp": round(data["main"]["temp"], 1),
            "feels": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "wind": round(data["wind"]["speed"] * 3.6, 1),
            "condition": data["weather"][0]["description"].title(),
            "pressure": data["main"]["pressure"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": str(e)}

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# ==================== MAIN APP ====================

class WeatherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Weather Dashboard")
        self.geometry("1100x750")
        self.minsize(1000, 650)
        self.configure(fg_color=BG)
        
        self.history = load_history()
        self.auto_refresh = False
        self.refresh_job = None
        self.countdown = 30
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, height=55, fg_color=BLUE, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Weather Dashboard", font=("Arial", 20, "bold"), 
                     text_color="white").pack(side="left", padx=25, pady=12)
        ctk.CTkLabel(header, text=f"{len(self.history)} records saved", 
                     font=("Arial", 11), text_color="#BFDBFE").pack(side="right", padx=25)
        
        # Tab View
        self.tabview = ctk.CTkTabview(self, fg_color=BG, 
                                      segmented_button_fg_color=WHITE,
                                      segmented_button_selected_color=BLUE,
                                      segmented_button_unselected_color=GRAY,
                                      text_color=DARK)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Tab 1: Current Weather
        self.current_tab = self.tabview.add("Current")
        self.setup_current_tab()
        
        # Tab 2: History
        self.history_tab = self.tabview.add("History")
        self.setup_history_tab()
        
        # Tab 3: Analysis
        self.analysis_tab = self.tabview.add("Analysis")
        self.setup_analysis_tab()
        
        # Tab 4: Multi City
        self.multi_tab = self.tabview.add("Multi City")
        self.setup_multi_tab()
    
    # ==================== CURRENT TAB ====================
    
    def setup_current_tab(self):
        tab = self.current_tab
        
        # Search bar
        search_frame = ctk.CTkFrame(tab, fg_color=WHITE, corner_radius=10)
        search_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(search_frame, text="City:", font=("Arial", 14)).pack(side="left", padx=(15, 5), pady=12)
        
        self.city_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter city name...", 
                                        font=("Arial", 13), height=38, border_width=0)
        self.city_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.city_entry.bind("<Return>", lambda e: self.get_weather())
        
        self.get_btn = ctk.CTkButton(search_frame, text="Get Weather", width=110, height=34,
                                      fg_color=BLUE, command=self.get_weather)
        self.get_btn.pack(side="right", padx=15, pady=6)
        
        # Auto refresh
        refresh_frame = ctk.CTkFrame(tab, fg_color="transparent")
        refresh_frame.pack(fill="x", padx=20, pady=5)
        
        self.auto_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(refresh_frame, text="Auto Refresh (30 sec)", variable=self.auto_var,
                      command=self.toggle_auto_refresh).pack(side="left")
        
        self.refresh_counter = ctk.CTkLabel(refresh_frame, text="", font=("Arial", 11), text_color=LIGHT_DARK)
        self.refresh_counter.pack(side="left", padx=15)
        
        # Weather display card
        weather_card = ctk.CTkFrame(tab, fg_color=WHITE, corner_radius=10)
        weather_card.pack(fill="x", padx=20, pady=10)
        
        self.city_title = ctk.CTkLabel(weather_card, text="—", font=("Arial", 26, "bold"), text_color=DARK)
        self.city_title.pack(pady=(18, 0))
        
        self.update_time = ctk.CTkLabel(weather_card, text="Search a city to begin", font=("Arial", 11), text_color=LIGHT_DARK)
        self.update_time.pack()
        
        self.temp_label = ctk.CTkLabel(weather_card, text="--°C", font=("Arial", 48, "bold"), text_color=BLUE)
        self.temp_label.pack(pady=5)
        
        self.condition_label = ctk.CTkLabel(weather_card, text="", font=("Arial", 13), text_color=LIGHT_DARK)
        self.condition_label.pack(pady=(0, 15))
        
        # Stats row (without icons)
        stats_frame = ctk.CTkFrame(tab, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=10)
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)
        
        self.humidity_label = ctk.CTkLabel(stats_frame, text="Humidity: --%", font=("Arial", 12), text_color=DARK)
        self.humidity_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.feels_label = ctk.CTkLabel(stats_frame, text="Feels Like: --°C", font=("Arial", 12), text_color=DARK)
        self.feels_label.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.wind_label = ctk.CTkLabel(stats_frame, text="Wind Speed: -- km/h", font=("Arial", 12), text_color=DARK)
        self.wind_label.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        self.pressure_label = ctk.CTkLabel(stats_frame, text="Pressure: -- hPa", font=("Arial", 12), text_color=DARK)
        self.pressure_label.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
    
    # ==================== HISTORY TAB ====================
    
    def setup_history_tab(self):
        tab = self.history_tab
        
        # Filter
        filter_frame = ctk.CTkFrame(tab, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(filter_frame, text="Filter by City:", font=("Arial", 12)).pack(side="left")
        self.filter_entry = ctk.CTkEntry(filter_frame, width=160, height=30, placeholder_text="City name")
        self.filter_entry.pack(side="left", padx=10)
        self.filter_entry.bind("<KeyRelease>", lambda e: self.refresh_history())
        
        ctk.CTkButton(filter_frame, text="Clear History", width=110, height=30, fg_color=RED,
                      command=self.clear_history).pack(side="right", padx=5)
        ctk.CTkButton(filter_frame, text="Export CSV", width=100, height=30, fg_color=GREEN,
                      command=self.export_history).pack(side="right")
        
        # Table header
        header_frame = ctk.CTkFrame(tab, fg_color=GRAY, corner_radius=6)
        header_frame.pack(fill="x", padx=20, pady=(0, 5))
        
        headers = [("City", 100), ("Temp", 60), ("Humidity", 70), ("Wind", 70), ("Condition", 120), ("Time", 140)]
        for text, width in headers:
            ctk.CTkLabel(header_frame, text=text, width=width, font=("Arial", 11, "bold"),
                         text_color=DARK).pack(side="left", padx=5, pady=6)
        
        # Scrollable list
        self.history_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.history_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.history_rows = []
        self.refresh_history()
    
    def refresh_history(self):
        for row in self.history_rows:
            row.destroy()
        self.history_rows.clear()
        
        filter_text = self.filter_entry.get().strip().lower()
        filtered = [h for h in reversed(self.history) if filter_text in h.get("city", "").lower()]
        
        for i, data in enumerate(filtered[:100]):
            bg = WHITE if i % 2 == 0 else GRAY
            row = ctk.CTkFrame(self.history_frame, fg_color=bg, corner_radius=4)
            row.pack(fill="x", pady=1)
            
            ctk.CTkLabel(row, text=f"{data['city']}, {data.get('country', '')}", width=100,
                         font=("Arial", 11), text_color=DARK).pack(side="left", padx=5, pady=6)
            ctk.CTkLabel(row, text=f"{data['temp']}°C", width=60,
                         font=("Arial", 11), text_color=DARK).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{data['humidity']}%", width=70,
                         font=("Arial", 11), text_color=DARK).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{data['wind']} km/h", width=70,
                         font=("Arial", 11), text_color=DARK).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=data['condition'][:15], width=120,
                         font=("Arial", 11), text_color=DARK).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=data['timestamp'][:16], width=140,
                         font=("Arial", 11), text_color=DARK).pack(side="left", padx=5)
            
            self.history_rows.append(row)
        
        if not filtered:
            label = ctk.CTkLabel(self.history_frame, text="No records found", font=("Arial", 13), text_color=LIGHT_DARK)
            label.pack(pady=30)
            self.history_rows.append(label)
    
    # ==================== ANALYSIS TAB ====================
    
    def setup_analysis_tab(self):
        tab = self.analysis_tab
        
        # Controls
        control_frame = ctk.CTkFrame(tab, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(control_frame, text="Metric:", font=("Arial", 12)).pack(side="left")
        self.metric_var = ctk.StringVar(value="Temperature")
        metric_menu = ctk.CTkOptionMenu(control_frame, values=["Temperature", "Humidity", "Wind Speed"],
                                         variable=self.metric_var, width=130)
        metric_menu.pack(side="left", padx=10)
        
        ctk.CTkLabel(control_frame, text="City:", font=("Arial", 12)).pack(side="left", padx=(20, 5))
        self.city_filter_var = ctk.StringVar(value="All")
        self.city_menu = ctk.CTkOptionMenu(control_frame, values=["All"], variable=self.city_filter_var, width=130)
        self.city_menu.pack(side="left")
        
        self.plot_btn = ctk.CTkButton(control_frame, text="Refresh Chart", width=110,
                                       command=self.plot_graph)
        self.plot_btn.pack(side="right")
        
        # Stats
        stats_frame = ctk.CTkFrame(tab, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 10))
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)
        
        self.avg_label = ctk.CTkLabel(stats_frame, text="Average: --", font=("Arial", 11), fg_color=WHITE, corner_radius=6)
        self.avg_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.min_label = ctk.CTkLabel(stats_frame, text="Minimum: --", font=("Arial", 11), fg_color=WHITE, corner_radius=6)
        self.min_label.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.max_label = ctk.CTkLabel(stats_frame, text="Maximum: --", font=("Arial", 11), fg_color=WHITE, corner_radius=6)
        self.max_label.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        self.count_label = ctk.CTkLabel(stats_frame, text="Records: --", font=("Arial", 11), fg_color=WHITE, corner_radius=6)
        self.count_label.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        
        # Graph frame
        self.graph_frame = ctk.CTkFrame(tab, fg_color=WHITE, corner_radius=10)
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.graph_canvas = None
        self.plot_graph()
    
    def plot_graph(self):
        if not self.history:
            self.show_empty_graph()
            return
        
        # Update city menu
        cities = sorted(set(h["city"] for h in self.history))
        self.city_menu.configure(values=["All"] + cities)
        
        metric_map = {"Temperature": "temp", "Humidity": "humidity", "Wind Speed": "wind"}
        unit_map = {"Temperature": "°C", "Humidity": "%", "Wind Speed": "km/h"}
        field = metric_map.get(self.metric_var.get(), "temp")
        unit = unit_map.get(self.metric_var.get(), "")
        
        city = self.city_filter_var.get()
        if city == "All":
            data = self.history
        else:
            data = [h for h in self.history if h["city"] == city]
        
        if not data:
            self.show_empty_graph()
            return
        
        # Update stats
        values = [h[field] for h in data]
        self.avg_label.configure(text=f"Average: {sum(values)/len(values):.1f}{unit}")
        self.min_label.configure(text=f"Minimum: {min(values):.1f}{unit}")
        self.max_label.configure(text=f"Maximum: {max(values):.1f}{unit}")
        self.count_label.configure(text=f"Records: {len(values)}")
        
        # Create graph
        fig, ax = plt.subplots(figsize=(7, 3.2), facecolor=WHITE)
        ax.set_facecolor(WHITE)
        
        times = [datetime.strptime(h["timestamp"], "%Y-%m-%d %H:%M:%S") for h in data]
        
        ax.plot(times, values, "o-", color=BLUE, linewidth=2, markersize=5)
        ax.fill_between(times, values, alpha=0.2, color=BLUE)
        ax.set_xlabel("Time", color=LIGHT_DARK)
        ax.set_ylabel(f"{self.metric_var.get()} ({unit})", color=LIGHT_DARK)
        ax.set_title(f"{self.metric_var.get()} Trend - {city}", color=DARK)
        ax.tick_params(colors=LIGHT_DARK)
        ax.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()
        
        self.graph_canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
    
    def show_empty_graph(self):
        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()
        label = ctk.CTkLabel(self.graph_frame, text="No data to display.\nFetch weather records first!",
                             font=("Arial", 13), text_color=LIGHT_DARK)
        label.pack(expand=True)
        self.graph_canvas = label
    
    # ==================== MULTI CITY TAB ====================
    
    def setup_multi_tab(self):
        tab = self.multi_tab
        
        ctk.CTkLabel(tab, text="Track Multiple Cities", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(tab, text="Enter up to 6 cities", font=("Arial", 11), text_color=LIGHT_DARK).pack()
        
        input_frame = ctk.CTkFrame(tab, fg_color=WHITE, corner_radius=10)
        input_frame.pack(fill="x", padx=30, pady=12)
        
        self.city_entries = []
        for i in range(6):
            row, col = divmod(i, 3)
            if col == 0:
                row_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
                row_frame.pack(fill="x", padx=15, pady=4)
            entry = ctk.CTkEntry(row_frame, placeholder_text=f"City {i+1}", width=170, height=32)
            entry.pack(side="left", padx=5, expand=True, fill="x")
            self.city_entries.append(entry)
        
        self.fetch_all_btn = ctk.CTkButton(input_frame, text="Fetch All Cities", height=36,
                                            fg_color=BLUE, command=self.fetch_all_cities)
        self.fetch_all_btn.pack(pady=12)
        
        self.multi_results = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.multi_results.pack(fill="both", expand=True, padx=20, pady=8)
    
    def fetch_all_cities(self):
        cities = [e.get().strip() for e in self.city_entries if e.get().strip()]
        if not cities:
            messagebox.showwarning("No Cities", "Enter at least one city")
            return
        
        for w in self.multi_results.winfo_children():
            w.destroy()
        
        self.fetch_all_btn.configure(state="disabled", text="Fetching...")
        
        def worker():
            results = []
            for city in cities:
                data = fetch_weather(city)
                if "error" not in data:
                    results.append((city, data))
                    self.history.insert(0, data)
            save_history(self.history)
            self.after(0, lambda: self.show_multi_results(results))
            self.after(0, self.refresh_history)
            self.after(0, self.plot_graph)
            self.after(0, lambda: self.fetch_all_btn.configure(state="normal", text="Fetch All Cities"))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def show_multi_results(self, results):
        for city, data in results:
            card = ctk.CTkFrame(self.multi_results, fg_color=WHITE, corner_radius=8)
            card.pack(fill="x", pady=4)
            
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 4))
            
            ctk.CTkLabel(top, text=f"{data['city']}, {data['country']}",
                         font=("Arial", 13, "bold")).pack(side="left")
            ctk.CTkLabel(top, text=f"{data['temp']}°C",
                         font=("Arial", 16, "bold")).pack(side="right")
            
            bottom = ctk.CTkFrame(card, fg_color="transparent")
            bottom.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkLabel(bottom, text=f"Humidity: {data['humidity']}%  |  Wind: {data['wind']} km/h  |  {data['condition']}",
                         font=("Arial", 10), text_color=LIGHT_DARK).pack()
    
    # ==================== CORE FUNCTIONS ====================
    
    def get_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Warning", "Please enter a city name")
            return
        
        self.get_btn.configure(state="disabled", text="Loading...")
        
        def worker():
            data = fetch_weather(city)
            self.after(0, lambda: self.display_weather(data))
            self.after(0, lambda: self.get_btn.configure(state="normal", text="Get Weather"))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def display_weather(self, data):
        if "error" in data:
            messagebox.showerror("Error", data["error"])
            return
        
        self.city_title.configure(text=f"{data['city']}, {data['country']}")
        self.update_time.configure(text=f"Last updated: {data['timestamp'][:16]}")
        self.temp_label.configure(text=f"{data['temp']}°C")
        self.condition_label.configure(text=data['condition'])
        
        self.humidity_label.configure(text=f"Humidity: {data['humidity']}%")
        self.feels_label.configure(text=f"Feels Like: {data['feels']}°C")
        self.wind_label.configure(text=f"Wind Speed: {data['wind']} km/h")
        self.pressure_label.configure(text=f"Pressure: {data['pressure']} hPa")
        
        self.history.insert(0, data)
        if len(self.history) > 100:
            self.history = self.history[:100]
        save_history(self.history)
        
        self.refresh_history()
        self.plot_graph()
        
        messagebox.showinfo("Success", f"Weather data for {data['city']} fetched!")
    
    def toggle_auto_refresh(self):
        self.auto_refresh = self.auto_var.get()
        if self.auto_refresh:
            self.countdown = 30
            self.auto_refresh_tick()
        else:
            if self.refresh_job:
                self.after_cancel(self.refresh_job)
                self.refresh_counter.configure(text="")
    
    def auto_refresh_tick(self):
        if not self.auto_refresh:
            return
        if self.countdown <= 0:
            self.get_weather()
            self.countdown = 30
        else:
            self.refresh_counter.configure(text=f"Refresh in {self.countdown}s")
            self.countdown -= 1
        self.refresh_job = self.after(1000, self.auto_refresh_tick)
    
    def clear_history(self):
        if messagebox.askyesno("Confirm", "Delete all weather history?"):
            self.history = []
            save_history(self.history)
            self.refresh_history()
            self.plot_graph()
            messagebox.showinfo("Success", "History cleared")
    
    def export_history(self):
        if not self.history:
            messagebox.showwarning("No Data", "No history to export")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.history[0].keys())
                writer.writeheader()
                writer.writerows(self.history)
            messagebox.showinfo("Exported", f"Saved to {path}")

# ==================== RUN ====================

if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
