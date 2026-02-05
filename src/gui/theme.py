"""
Professional UX Design Theme
Based on the UX Design Specification for Recibos Application
"""

from tkinter import ttk

class ReceiptsTheme:
    """
    Professional blue and neutral color scheme for the receipts application.
    Implements the design system from the UX specification.
    """
    
    # Dark Mode Color Scheme
    BG_DARKEST = '#0f172a'     # Main background
    BG_DARK = '#1e293b'        # Card backgrounds
    BG_MEDIUM = '#334155'      # Elevated surfaces
    BLUE_PRIMARY = '#3b82f6'   # Primary action color
    BLUE_HOVER = '#2563eb'     # Hover states
    BORDER_DARK = '#475569'    # Borders, dividers
    
    # Compatibility aliases
    BLUE_DARKEST = BG_DARKEST
    BLUE_DARK = BG_DARK
    BLUE_MEDIUM = BG_MEDIUM
    BLUE_LIGHT = TEXT_GRAY = '#94a3b8'
    BLUE_PALE = '#334155'
    WHITE = TEXT_WHITE = '#ffffff'
    LIGHT_GRAY = BG_DARK
    BORDER_GRAY = BORDER_DARK
    TEXT_BLACK = '#ffffff'  # In dark mode, "black" text is white
    
    # Text Colors
    TEXT_MUTED = '#64748b'     # Muted text
    
    # Status Colors (Minimal Use)
    SUCCESS_BG = '#dcfce7'     # Light green background
    SUCCESS_TEXT = '#166534'   # Dark green text
    ERROR_BG = '#fee2e2'       # Light red background
    ERROR_TEXT = '#991b1b'     # Dark red text
    WARNING_BG = '#fef3c7'     # Light amber background
    WARNING_TEXT = '#92400e'   # Dark amber text
    
    @classmethod
    def apply(cls, root):
        """Apply the professional theme to the application."""
        style = ttk.Style()
        
        # Use a theme that supports better styling on Windows
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        # Configure root window background
        root.configure(bg=cls.BG_DARKEST)
        
        # ===== Frame Styles =====
        style.configure('TFrame', background=cls.WHITE)
        style.configure('Card.TFrame', 
                       background=cls.WHITE,
                       relief='flat',
                       borderwidth=0)
        style.configure('Header.TFrame',
                       background=cls.BLUE_DARKEST)
        style.configure('StatusBar.TFrame',
                       background=cls.BLUE_PALE)
        
        # ===== Label Styles =====
        style.configure('TLabel',
                       background=cls.WHITE,
                       foreground=cls.TEXT_BLACK,
                       font=('Segoe UI', 10))
        
        style.configure('Header.TLabel',
                       background=cls.BLUE_DARKEST,
                       foreground=cls.TEXT_WHITE,
                       font=('Segoe UI', 12, 'bold'),
                       padding=(10, 8))
        
        style.configure('SectionTitle.TLabel',
                       background=cls.WHITE,
                       foreground=cls.BLUE_DARK,
                       font=('Segoe UI', 11, 'bold'),
                       padding=(0, 5))
        
        style.configure('Secondary.TLabel',
                       background=cls.WHITE,
                       foreground=cls.BLUE_LIGHT,
                       font=('Segoe UI', 9))
        
        style.configure('Status.TLabel',
                       background=cls.BLUE_PALE,
                       foreground=cls.TEXT_BLACK,
                       font=('Segoe UI', 9),
                       padding=(8, 5))
        
        # ===== Button Styles =====
        # Primary Action Button (Dark blue solid)
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(24, 12),
                       relief='flat',
                       borderwidth=1,
                       background=cls.BLUE_DARKEST,
                       foreground=cls.TEXT_WHITE,
                       focuscolor=cls.BLUE_MEDIUM)
        style.map('Primary.TButton',
                 background=[('active', cls.BLUE_MEDIUM),
                           ('pressed', cls.BLUE_DARK),
                           ('disabled', cls.BORDER_GRAY)],
                 foreground=[('disabled', cls.BLUE_LIGHT)],
                 relief=[('pressed', 'sunken')])
        
        # Secondary Action Button (Medium blue outline)
        style.configure('Secondary.TButton',
                       font=('Segoe UI', 10),
                       padding=(24, 12),
                       relief='solid',
                       borderwidth=2,
                       background=cls.WHITE,
                       foreground=cls.BLUE_DARK,
                       bordercolor=cls.BLUE_DARK,
                       focuscolor=cls.BLUE_PALE)
        style.map('Secondary.TButton',
                 background=[('active', cls.BLUE_PALE),
                           ('pressed', cls.BLUE_PALE),
                           ('disabled', cls.LIGHT_GRAY)],
                 foreground=[('disabled', cls.BLUE_LIGHT)],
                 relief=[('pressed', 'sunken')])
        
        # Tertiary Action Button (Gray outline)
        style.configure('Tertiary.TButton',
                       font=('Segoe UI', 10),
                       padding=(20, 10),
                       relief='solid',
                       borderwidth=1,
                       background=cls.WHITE,
                       foreground=cls.TEXT_BLACK,
                       bordercolor=cls.BORDER_GRAY,
                       focuscolor=cls.LIGHT_GRAY)
        style.map('Tertiary.TButton',
                 background=[('active', cls.LIGHT_GRAY),
                           ('pressed', cls.LIGHT_GRAY),
                           ('disabled', cls.LIGHT_GRAY)],
                 foreground=[('disabled', cls.BLUE_LIGHT)],
                 relief=[('pressed', 'sunken')])
        
        # Success Button
        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(24, 12),
                       relief='flat',
                       borderwidth=1,
                       background=cls.SUCCESS_BG,
                       foreground=cls.SUCCESS_TEXT)
        style.map('Success.TButton',
                 relief=[('pressed', 'sunken')])
        
        # Danger/Cancel Button
        style.configure('Danger.TButton',
                       font=('Segoe UI', 10),
                       padding=(20, 10),
                       relief='solid',
                       borderwidth=2,
                       background=cls.WHITE,
                       foreground=cls.ERROR_TEXT,
                       bordercolor=cls.ERROR_TEXT,
                       focuscolor=cls.ERROR_BG)
        style.map('Danger.TButton',
                 background=[('active', cls.ERROR_BG),
                           ('pressed', cls.ERROR_BG)],
                 relief=[('pressed', 'sunken')])
        
        # ===== LabelFrame Styles (Cards) =====
        style.configure('Card.TLabelframe',
                       background=cls.WHITE,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=cls.BORDER_GRAY)
        style.configure('Card.TLabelframe.Label',
                       foreground=cls.BLUE_DARK,
                       background=cls.WHITE,
                       font=('Segoe UI', 11, 'bold'),
                       padding=(0, 8, 0, 4))
        
        # ===== Entry and Combobox Styles =====
        style.configure('TEntry',
                       fieldbackground=cls.WHITE,
                       foreground=cls.TEXT_BLACK,
                       bordercolor=cls.BORDER_GRAY,
                       lightcolor=cls.BLUE_PALE,
                       darkcolor=cls.BLUE_PALE,
                       relief='solid',
                       borderwidth=1,
                       padding=10,
                       font=('Segoe UI', 10))
        
        style.configure('TCombobox',
                       fieldbackground=cls.WHITE,
                       foreground=cls.TEXT_BLACK,
                       bordercolor=cls.BORDER_GRAY,
                       relief='solid',
                       borderwidth=1,
                       padding=10,
                       arrowsize=16,
                       font=('Segoe UI', 10))
        style.map('TCombobox',
                 fieldbackground=[('readonly', cls.WHITE)],
                 foreground=[('readonly', cls.TEXT_BLACK)],
                 selectbackground=[('readonly', cls.BLUE_PALE)],
                 selectforeground=[('readonly', cls.TEXT_BLACK)])
        
        # ===== Checkbutton and Radiobutton Styles =====
        style.configure('TCheckbutton',
                       background=cls.WHITE,
                       foreground=cls.TEXT_BLACK,
                       font=('Segoe UI', 10))
        
        style.configure('TRadiobutton',
                       background=cls.WHITE,
                       foreground=cls.TEXT_BLACK,
                       font=('Segoe UI', 10))
        
        # ===== Progress Bar Style =====
        style.configure('TProgressbar',
                       background=cls.BLUE_DARKEST,
                       troughcolor=cls.BLUE_PALE,
                       borderwidth=0,
                       thickness=20)
        
        # ===== Treeview (Table) Style =====
        style.configure('Treeview',
                       background=cls.WHITE,
                       fieldbackground=cls.WHITE,
                       foreground=cls.TEXT_BLACK,
                       borderwidth=1,
                       relief='solid',
                       font=('Segoe UI', 9))
        style.configure('Treeview.Heading',
                       background=cls.BLUE_DARK,
                       foreground=cls.TEXT_WHITE,
                       borderwidth=0,
                       relief='flat',
                       font=('Segoe UI', 10, 'bold'))
        style.map('Treeview',
                 background=[('selected', cls.BLUE_MEDIUM)],
                 foreground=[('selected', cls.TEXT_WHITE)])
        style.map('Treeview.Heading',
                 background=[('active', cls.BLUE_MEDIUM)])
        
        # ===== Notebook (Tabs) Style =====
        style.configure('TNotebook',
                       background=cls.LIGHT_GRAY,
                       borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=cls.LIGHT_GRAY,
                       foreground=cls.BLUE_LIGHT,
                       padding=(20, 10),
                       font=('Segoe UI', 10))
        style.map('TNotebook.Tab',
                 background=[('selected', cls.WHITE)],
                 foreground=[('selected', cls.BLUE_DARK)],
                 expand=[('selected', [1, 1, 1, 0])])
        
        # ===== Scrollbar Style =====
        style.configure('TScrollbar',
                       background=cls.BORDER_GRAY,
                       troughcolor=cls.LIGHT_GRAY,
                       borderwidth=0,
                       arrowsize=14)
        style.map('TScrollbar',
                 background=[('active', cls.BLUE_LIGHT)])
        
        # ===== Separator Style =====
        style.configure('TSeparator',
                       background=cls.BORDER_GRAY)
        
        return style
    
    @classmethod
    def get_card_shadow_config(cls):
        """
        Returns configuration for card shadow effect.
        Note: Tkinter doesn't support box-shadow natively, 
        but we can simulate with a subtle border.
        """
        return {
            'highlightbackground': cls.BORDER_GRAY,
            'highlightthickness': 1,
            'borderwidth': 0
        }
    
    @classmethod
    def get_drop_zone_config(cls):
        """Returns configuration for file drop zone."""
        return {
            'bg': cls.WHITE,
            'fg': cls.BLUE_LIGHT,
            'font': ('Segoe UI', 10),
            'borderwidth': 2,
            'relief': 'solid',
            'highlightbackground': cls.BLUE_MEDIUM,
            'highlightthickness': 2
        }
