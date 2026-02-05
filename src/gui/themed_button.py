"""
Custom themed buttons with proper color support for Windows.
Uses tk.Button instead of ttk.Button to ensure colors display correctly.
"""

import tkinter as tk
from gui.theme import ReceiptsTheme


class ThemedButton(tk.Button):
    """A custom button that properly displays theme colors on Windows."""
    
    def __init__(self, parent, style='primary', **kwargs):
        """
        Create a themed button.
        
        Args:
            parent: Parent widget
            style: Button style - 'primary', 'secondary', 'tertiary', 'danger', 'success'
            **kwargs: Additional button arguments
        """
        # Get style configuration
        config = self._get_style_config(style)
        
        # Merge with provided kwargs
        config.update(kwargs)
        
        super().__init__(parent, **config)
        
        # Bind hover effects
        self._setup_hover_effects(style)
    
    def _get_style_config(self, style):
        """Get configuration for the specified style."""
        configs = {
            'primary': {
                'bg': '#3b82f6',
                'fg': '#ffffff',
                'activebackground': '#2563eb',
                'activeforeground': '#ffffff',
                'disabledforeground': '#94a3b8',
                'font': ('Segoe UI', 9),
                'relief': 'flat',
                'borderwidth': 0,
                'width': 14,
                'padx': 10,
                'pady': 4,
                'cursor': 'hand2'
            },
            'secondary': {
                'bg': '#334155',
                'fg': '#ffffff',
                'activebackground': '#475569',
                'activeforeground': '#ffffff',
                'disabledforeground': '#94a3b8',
                'font': ('Segoe UI', 9),
                'relief': 'flat',
                'borderwidth': 0,
                'width': 14,
                'padx': 10,
                'pady': 4,
                'cursor': 'hand2'
            },
            'tertiary': {
                'bg': '#1e293b',
                'fg': '#ffffff',
                'activebackground': '#334155',
                'activeforeground': '#ffffff',
                'disabledforeground': '#94a3b8',
                'font': ('Segoe UI', 9),
                'relief': 'flat',
                'borderwidth': 0,
                'width': 14,
                'padx': 10,
                'pady': 4,
                'cursor': 'hand2'
            },
            'danger': {
                'bg': '#dc2626',
                'fg': '#ffffff',
                'activebackground': '#b91c1c',
                'activeforeground': '#ffffff',
                'disabledforeground': '#94a3b8',
                'font': ('Segoe UI', 9),
                'relief': 'flat',
                'borderwidth': 0,
                'width': 14,
                'padx': 10,
                'pady': 4,
                'cursor': 'hand2'
            },
            'success': {
                'bg': '#16a34a',
                'fg': '#ffffff',
                'activebackground': '#15803d',
                'activeforeground': '#ffffff',
                'disabledforeground': '#94a3b8',
                'font': ('Segoe UI', 9),
                'relief': 'flat',
                'borderwidth': 0,
                'width': 14,
                'padx': 10,
                'pady': 4,
                'cursor': 'hand2'
            }
        }
        
        return configs.get(style.lower(), configs['primary'])
    
    def _setup_hover_effects(self, style):
        """Setup hover effects for the button."""
        # Store original colors
        self._original_bg = self['bg']
        self._original_fg = self['fg']
        
        # Define hover colors based on style
        hover_configs = {
            'primary': ('#2563eb', '#ffffff'),
            'secondary': ('#475569', '#ffffff'),
            'tertiary': ('#334155', '#ffffff'),
            'danger': ('#b91c1c', '#ffffff'),
            'success': ('#15803d', '#ffffff')
        }
        
        hover_bg, hover_fg = hover_configs.get(style.lower(), hover_configs['primary'])
        
        # Bind hover events
        self.bind('<Enter>', lambda e: self._on_enter(hover_bg, hover_fg))
        self.bind('<Leave>', lambda e: self._on_leave())
    
    def _on_enter(self, hover_bg, hover_fg):
        """Handle mouse enter event."""
        if self['state'] != 'disabled':
            self.config(bg=hover_bg, fg=hover_fg)
    
    def _on_leave(self):
        """Handle mouse leave event."""
        if self['state'] != 'disabled':
            self.config(bg=self._original_bg, fg=self._original_fg)
