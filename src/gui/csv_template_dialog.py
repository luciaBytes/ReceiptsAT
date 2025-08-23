#!/usr/bin/env python3
"""
GUI Integration for CSV Template Generator

This module provides a user-friendly interface for generating CSV templates
within the main application window.

Author: Assistant
Date: August 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from typing import Optional, Dict, Any
import logging

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.csv_template_generator import CSVTemplateGenerator, TemplateType, TemplateConfig

logger = logging.getLogger(__name__)

class CSVTemplateDialog:
    """Dialog for CSV template generation with user-friendly interface."""
    
    def __init__(self, parent: tk.Tk):
        """
        Initialize the CSV template dialog.
        
        Args:
            parent: Parent window
        """
        self.parent = parent
        self.generator = CSVTemplateGenerator()
        self.window = None
        self.result = None
        
        # Initialize GUI variables
        self.selected_template = None
        self.include_samples = None
        self.include_descriptions = None
        self.use_portuguese = None
        self.sample_count = None
        
        # Template descriptions for user guidance
        self.template_descriptions = {
            TemplateType.BASIC: {
                "title": "Modelo Básico",
                "description": "Template simples com campos essenciais para recibos de renda",
                "use_case": "Ideal para: Recibos simples de arrendamento residencial"
            },
            TemplateType.DETAILED: {
                "title": "Modelo Detalhado", 
                "description": "Template completo com campos adicionais para gestão profissional",
                "use_case": "Ideal para: Gestão profissional com informações detalhadas"
            }
        }
    
    def show_dialog(self) -> Optional[str]:
        """
        Show the CSV template generation dialog.
        
        Returns:
            Path to generated template or None if cancelled
        """
        self._create_dialog()
        self.window.wait_window()
        return self.result
    
    def _create_dialog(self):
        """Create and configure the dialog window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Gerador de Templates CSV")
        self.window.geometry("700x480")
        self.window.resizable(True, True)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center the dialog
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.window.winfo_screenheight() // 2) - (480 // 2)
        self.window.geometry(f"700x480+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and arrange dialog widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)  # Preview frame gets the weight, not template frame
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Template selection frame - more compact
        selection_frame = ttk.LabelFrame(main_frame, text="Tipos de Template", padding="10")
        selection_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Template selection variable
        self.selected_template = tk.StringVar()
        
        # Create side-by-side layout for template options
        templates_container = ttk.Frame(selection_frame)
        templates_container.grid(row=0, column=0, sticky="ew")
        selection_frame.grid_columnconfigure(0, weight=1)
        templates_container.grid_columnconfigure(0, weight=1)
        templates_container.grid_columnconfigure(1, weight=1)
        
        # Create template options side by side
        col = 0
        for template_type in TemplateType:
            template_info = self.template_descriptions[template_type]
            
            # Template radio button frame - reduced padding
            template_frame = ttk.Frame(templates_container, relief="solid", borderwidth=1, padding="8")
            template_frame.grid(row=0, column=col, sticky="ew", pady=3, padx=3)
            
            # Radio button
            radio = ttk.Radiobutton(
                template_frame,
                text=template_info["title"],
                variable=self.selected_template,
                value=template_type.value,
                command=self._on_template_selected
            )
            radio.grid(row=0, column=0, sticky="w", pady=(0, 3))
            
            # Description
            desc_label = ttk.Label(
                template_frame,
                text=template_info["description"],
                font=("Segoe UI", 9),
                foreground="gray",
                wraplength=250  # Wrap text for side-by-side layout
            )
            desc_label.grid(row=1, column=0, sticky="w", pady=(0, 2))
            
            # Use case
            usecase_label = ttk.Label(
                template_frame,
                text=template_info["use_case"],
                font=("Segoe UI", 8, "italic"),
                foreground="blue",
                wraplength=250  # Wrap text for side-by-side layout
            )
            usecase_label.grid(row=2, column=0, sticky="w")
            
            col += 1
        
        # Set default selection
        self.selected_template.set(TemplateType.BASIC.value)
        
        # Options frame - moved from row=3 to row=1
        options_frame = ttk.LabelFrame(main_frame, text="Opções", padding="15")
        options_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Template options
        self.include_samples = tk.BooleanVar(value=False)
        self.include_descriptions = tk.BooleanVar(value=True)
        self.use_portuguese = tk.BooleanVar(value=False)  # Keep for internal use but don't show UI
        
        samples_cb = ttk.Checkbutton(
            options_frame,
            text="Incluir dados de exemplo",
            variable=self.include_samples
        )
        samples_cb.grid(row=0, column=0, sticky="w", pady=2)
        
        descriptions_cb = ttk.Checkbutton(
            options_frame,
            text="Incluir descrições dos campos",
            variable=self.include_descriptions
        )
        descriptions_cb.grid(row=1, column=0, sticky="w", pady=2)
        
        # Set fixed sample count to 1 (no user control)
        self.sample_count = tk.StringVar(value="1")
        
        # Preview frame - moved from row=4 to row=2
        self.preview_frame = ttk.LabelFrame(main_frame, text="Pré-visualização", padding="10")
        self.preview_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        self.preview_text = tk.Text(
            self.preview_frame,
            height=6,
            width=60,
            font=("Consolas", 9),
            wrap=tk.NONE
        )
        
        preview_scroll = ttk.Scrollbar(self.preview_frame, orient="horizontal", command=self.preview_text.xview)
        self.preview_text.configure(xscrollcommand=preview_scroll.set)
        
        self.preview_text.grid(row=0, column=0, sticky="ew")
        preview_scroll.grid(row=1, column=0, sticky="ew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        # Update preview
        self._update_preview()
        
        # Buttons frame - moved from row=5 to row=3
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        # Generate single template button
        generate_btn = ttk.Button(
            buttons_frame,
            text="Gerar Template",
            command=self._generate_single_template,
            style="Accent.TButton"
        )
        generate_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Cancel button
        cancel_btn = ttk.Button(
            buttons_frame,
            text="Cancelar",
            command=self._cancel
        )
        cancel_btn.grid(row=0, column=1)
        
        # Bind option changes to preview update
        self.include_samples.trace_add("write", self._on_option_changed)
        self.include_descriptions.trace_add("write", self._on_option_changed)
    
    def _on_template_selected(self):
        """Handle template selection change."""
        self._update_preview()
    
    def _on_option_changed(self, *args):
        """Handle option change."""
        self._update_preview()
    
    def _update_preview(self):
        """Update the template preview."""
        try:
            template_type = TemplateType(self.selected_template.get())
            template_info = self.generator.get_template_info(template_type)
            
            if "error" in template_info:
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, "Erro: Template não encontrado")
                return
            
            # Build preview
            preview_lines = []
            
            # Add descriptions if enabled
            if self.include_descriptions.get():
                desc_line = "# " + " | ".join([f["description"] for f in template_info["fields"]])
                preview_lines.append(desc_line)
            
            # Add headers
            if self.use_portuguese.get():
                headers = [f["portuguese_name"] for f in template_info["fields"]]
            else:
                headers = [f["name"] for f in template_info["fields"]]
            
            preview_lines.append(",".join(headers))
            
            # Add sample data if enabled
            if self.include_samples.get():
                try:
                    count = 1  # Fixed to 1 sample only
                    samples = self.generator._generate_sample_data(template_type, count)
                    
                    for sample in samples:
                        row = []
                        for field in template_info["fields"]:
                            field_key = field["portuguese_name"] if self.use_portuguese.get() else field["name"]
                            value = sample.get(field_key, sample.get(field["name"], field["example"]))
                            row.append(str(value))
                        preview_lines.append(",".join(row))
                except ValueError:
                    pass  # Invalid sample count, skip samples
            
            # Update preview text
            preview_text = "\n".join(preview_lines)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, preview_text)
            
        except Exception as e:
            logger.error(f"Error updating preview: {str(e)}")
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"Erro na pré-visualização: {str(e)}")
    
    def _generate_single_template(self):
        """Generate a single CSV template."""
        try:
            # Safety check for variable initialization
            if not self.selected_template or not hasattr(self.selected_template, 'get'):
                messagebox.showerror(
                    "Erro de Inicialização",
                    "Dialog não foi inicializado corretamente. Feche e reabra a janela.",
                    parent=self.window
                )
                return
                
            # Get the selected template type
            template_value = self.selected_template.get()
            if not template_value:
                messagebox.showerror(
                    "Erro de Seleção",
                    "Por favor, selecione um tipo de template.",
                    parent=self.window
                )
                return
                
            # Get file path from user
            try:
                template_type = TemplateType(template_value)
            except ValueError:
                messagebox.showerror(
                    "Erro de Template",
                    f"Tipo de template inválido: {template_value}",
                    parent=self.window
                )
                return
                
            default_filename = f"{template_type.value}_template.csv"
            
            filepath = filedialog.asksaveasfilename(
                title="Guardar Template CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=default_filename,  # Fixed: was 'initialname', should be 'initialfile'
                parent=self.window
            )
            
            if not filepath:
                return
            
            # Safety checks for option variables
            try:
                include_samples = self.include_samples.get() if self.include_samples else False
                include_descriptions = self.include_descriptions.get() if self.include_descriptions else True
                use_portuguese = self.use_portuguese.get() if self.use_portuguese else False
            except Exception as e:
                messagebox.showerror(
                    "Erro de Opções",
                    f"Erro ao ler opções do template: {str(e)}",
                    parent=self.window
                )
                return
            
            # Create configuration
            config = TemplateConfig(
                template_type=template_type,
                include_samples=include_samples,
                include_descriptions=include_descriptions,
                include_portuguese=use_portuguese,
                sample_count=1  # Fixed to 1 sample only
            )
            
            # Generate template
            success, message = self.generator.generate_template(template_type, filepath, config)
            
            if success:
                # Just set the result and close dialog - main window will show success message
                self.result = filepath
                self.window.destroy()
            else:
                messagebox.showerror(
                    "Erro",
                    f"Falha ao gerar template:\n\n{message}",
                    parent=self.window
                )
        
        except ValueError as ve:
            logger.error(f"Invalid template type: {str(ve)}")
            messagebox.showerror(
                "Erro de Configuração",
                f"Tipo de template inválido:\n\n{str(ve)}",
                parent=self.window
            )
        except FileNotFoundError as fe:
            logger.error(f"File path error: {str(fe)}")
            messagebox.showerror(
                "Erro de Ficheiro",
                f"Erro ao aceder ao ficheiro:\n\n{str(fe)}",
                parent=self.window
            )
        except PermissionError as pe:
            logger.error(f"Permission error: {str(pe)}")
            messagebox.showerror(
                "Erro de Permissão",
                f"Sem permissão para escrever no ficheiro:\n\n{str(pe)}",
                parent=self.window
            )
        except Exception as e:
            logger.error(f"Error generating single template: {str(e)}")
            import traceback
            traceback.print_exc()  # This will help debug the issue
            messagebox.showerror(
                "Erro Inesperado",
                f"Erro inesperado ao gerar template:\n\n{str(e)}\n\nVerifique os logs para mais detalhes.",
                parent=self.window
            )
    
    def _cancel(self):
        """Cancel the dialog."""
        self.result = None
        self.window.destroy()

def show_csv_template_dialog(parent: tk.Tk) -> Optional[str]:
    """
    Show the CSV template generation dialog.
    
    Args:
        parent: Parent window
        
    Returns:
        Path to generated template(s) or None if cancelled
    """
    dialog = CSVTemplateDialog(parent)
    return dialog.show_dialog()

def main():
    """Test the CSV template dialog."""
    # Create test window
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    # Show dialog
    result = show_csv_template_dialog(root)
    
    if result:
        print(f"Template generated: {result}")
    else:
        print("Dialog cancelled")
    
    root.destroy()

if __name__ == "__main__":
    main()
