
class AppThemeSlice:
    def __init__(self):
        self.font_color = (0,0,0,0)
        self.font_bg_color = (0,0,0,0)
        self.graph_average_line_color = (0,0,0,0)
        self.graph_bottom_line_color = (0,0,0,0)
        self.graph_bg_color = (0,0,0,0)
        self.graph_line_color = (0,0,0,0)

class AppTheme:
    def __init__(self):
        self.color_transparent = (0, 0, 0, 0)
        

class DarkTheme(AppTheme):
    def __init__(self):
        super().__init__()
        self.color_green = (0, 255, 0, 255)
        self.color_blue = (0, 0, 128, 255)
        self.color_blue_half = (0, 0, 128, 100)
        self.color_pink = (248, 12, 255, 255)
        
        self.cpu_slice = AppThemeSlice()
        self.cpu_slice.font_color = self.color_green
        self.cpu_slice.font_bg_color = self.color_blue
        self.cpu_slice.graph_average_line_color = self.color_pink
        self.cpu_slice.graph_bottom_line_color = self.color_transparent
        self.cpu_slice.graph_bg_color = self.color_blue_half
        self.cpu_slice.graph_line_color = self.color_transparent
    
        self.dram_slice = AppThemeSlice()
        self.dram_slice.font_color = self.color_green
        self.dram_slice.font_bg_color = self.color_blue
        self.dram_slice.graph_average_line_color = self.color_transparent
        self.dram_slice.graph_bottom_line_color = self.color_transparent
        self.dram_slice.graph_bg_color = self.color_blue
        self.dram_slice.graph_line_color = self.color_green
        
        self.disk_slice = AppThemeSlice()
        self.disk_slice.font_color = self.color_green
        self.disk_slice.font_bg_color = self.color_blue
        self.disk_slice.graph_average_line_color = self.color_transparent
        self.disk_slice.graph_bottom_line_color = self.color_transparent 
        self.disk_slice.graph_bg_color = self.color_blue
        self.disk_slice.graph_line_color = self.color_green
        
        self.gpu_slice = AppThemeSlice()
        self.gpu_slice.font_color = self.color_green
        self.gpu_slice.font_bg_color = self.color_blue
        self.gpu_slice.graph_average_line_color = self.color_transparent
        self.gpu_slice.graph_bottom_line_color = self.color_transparent 
        self.gpu_slice.graph_bg_color = self.color_blue
        self.gpu_slice.graph_line_color = self.color_green
        
        self.vram_slice = AppThemeSlice()
        self.vram_slice.font_color = self.color_green
        self.vram_slice.font_bg_color = self.color_blue
        self.vram_slice.graph_average_line_color = self.color_transparent
        self.vram_slice.graph_bottom_line_color = self.color_transparent 
        self.vram_slice.graph_bg_color = self.color_blue
        self.vram_slice.graph_line_color = self.color_green
        
class LightTheme(DarkTheme):
    def __init__(self):
        super().__init__()
        pass
        
class Theme:
    def __init__(self):
        self.dark_theme = DarkTheme()
        self.light_theme = LightTheme()
    
    def is_dark_theme(self):
        return True
    
    def get_cpu_slice(self):
        # Some theme logic
        if self.is_dark_theme():
            return self.dark_theme.cpu_slice
        else:
            return self.light_theme.cpu_slice
            
    def get_dram_slice(self):
        # Some theme logic
        if self.is_dark_theme():
            return self.dark_theme.dram_slice
        else:
            return self.light_theme.dram_slice
            
    def get_disk_slice(self):
        # Some theme logic
        if self.is_dark_theme():
            return self.dark_theme.disk_slice
        else:
            return self.light_theme.disk_slice
    
    def get_gpu_slice(self):
        # Some theme logic
        if self.is_dark_theme():
            return self.dark_theme.gpu_slice
        else:
            return self.light_theme.gpu_slice
            
    def get_vram_slice(self):
        # Some theme logic
        if self.is_dark_theme():
            return self.dark_theme.vram_slice
        else:
            return self.light_theme.vram_slice
