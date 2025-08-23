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
        
        # Template descriptions for user guidance
        self.template_descriptions = {
            TemplateType.BASIC: {
                "title": "Modelo Básico",
                "description": "Template simples com campos essenciais para recibos de renda",
                "use_case": "Ideal para: Recibos simples de arrendamento residencial"
            },
            TemplateType.DETAILED: {
                "title": "Modelo Detalhado", 
                "description": "Template completo com campos adicionais e descrições",
                "use_case": "Ideal para: Gestão profissional com informações detalhadas"
            },
            TemplateType.PORTUGUESE: {
                "title": "Modelo Português",
                "description": "Template com nomes de campos em português e formato local",
                "use_case": "Ideal para: Utilizadores que preferem interface em português"
            },
            TemplateType.SAMPLE_DATA: {
                "title": "Dados de Exemplo",
                "description": "Template com dados de exemplo para aprendizagem",
                "use_case": "Ideal para: Primeiros utilizadores e testes"
            },
            TemplateType.INHERITANCE: {
                "title": "Herança",
                "description": "Template para propriedades com múltiplos proprietários",
                "use_case": "Ideal para: Propriedades herdadas ou em compropriedade"
            },
            TemplateType.MULTI_TENANT: {
                "title": "Múltiplos Inquilinos", 
                "description": "Template para propriedades com vários inquilinos",
                "use_case": "Ideal para: Quartos partilhados ou propriedades divididas"
            },
            TemplateType.BUSINESS: {
                "title": "Empresarial",
                "description": "Template para arrendamento comercial com IVA",
                "use_case": "Ideal para: Propriedades comerciais e empresariais"
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
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center the dialog
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and arrange dialog widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="🎯 Gerador de Templates CSV", 
            font=("Segoe UI", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")
        
        # Subtitle
        subtitle_label = ttk.Label(
            main_frame,
            text="Escolha um template para gerar um ficheiro CSV com a estrutura correta",
            font=("Segoe UI", 10)
        )
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky="w")
        
        # Template selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Tipos de Template", padding="15")
        selection_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 20))
        
        # Create scrollable frame for templates
        canvas = tk.Canvas(selection_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(selection_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        selection_frame.grid_rowconfigure(0, weight=1)
        selection_frame.grid_columnconfigure(0, weight=1)
        
        # Template selection variable
        self.selected_template = tk.StringVar()
        
        # Create template options
        row = 0
        for template_type in TemplateType:
            template_info = self.template_descriptions[template_type]
            
            # Template radio button frame
            template_frame = ttk.Frame(scrollable_frame, relief="solid", borderwidth=1, padding="10")
            template_frame.grid(row=row, column=0, sticky="ew", pady=5, padx=5)
            scrollable_frame.grid_columnconfigure(0, weight=1)
            
            # Radio button
            radio = ttk.Radiobutton(
                template_frame,
                text=template_info["title"],
                variable=self.selected_template,
                value=template_type.value,
                command=self._on_template_selected
            )
            radio.grid(row=0, column=0, sticky="w", pady=(0, 5))
            
            # Description
            desc_label = ttk.Label(
                template_frame,
                text=template_info["description"],
                font=("Segoe UI", 9),
                foreground="gray"
            )
            desc_label.grid(row=1, column=0, sticky="w", pady=(0, 3))
            
            # Use case
            usecase_label = ttk.Label(
                template_frame,
                text=template_info["use_case"],
                font=("Segoe UI", 8, "italic"),
                foreground="blue"
            )
            usecase_label.grid(row=2, column=0, sticky="w")
            
            row += 1
        
        # Set default selection
        self.selected_template.set(TemplateType.BASIC.value)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Opções", padding="15")
        options_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Template options
        self.include_samples = tk.BooleanVar(value=False)
        self.include_descriptions = tk.BooleanVar(value=True)
        self.use_portuguese = tk.BooleanVar(value=False)
        
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
        
        portuguese_cb = ttk.Checkbutton(
            options_frame,
            text="Usar nomes de campos em português",
            variable=self.use_portuguese
        )
        portuguese_cb.grid(row=2, column=0, sticky="w", pady=2)
        
        # Sample count frame
        count_frame = ttk.Frame(options_frame)
        count_frame.grid(row=3, column=0, sticky="w", pady=(10, 0))
        
        ttk.Label(count_frame, text="Número de exemplos:").grid(row=0, column=0, sticky="w")
        
        self.sample_count = tk.StringVar(value="3")
        count_spinbox = ttk.Spinbox(
            count_frame,
            from_=1,
            to=10,
            width=5,
            textvariable=self.sample_count
        )
        count_spinbox.grid(row=0, column=1, padx=(10, 0))
        
        # Preview frame
        self.preview_frame = ttk.LabelFrame(main_frame, text="Pré-visualização", padding="10")
        self.preview_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
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
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # Generate single template button
        generate_btn = ttk.Button(
            buttons_frame,
            text="📄 Gerar Template",
            command=self._generate_single_template,
            style="Accent.TButton"
        )
        generate_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Generate all templates button
        generate_all_btn = ttk.Button(
            buttons_frame,
            text="📁 Gerar Todos os Templates",
            command=self._generate_all_templates
        )
        generate_all_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Cancel button
        cancel_btn = ttk.Button(
            buttons_frame,
            text="Cancelar",
            command=self._cancel
        )
        cancel_btn.grid(row=0, column=2)
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Bind option changes to preview update
        self.include_samples.trace_add("write", self._on_option_changed)
        self.include_descriptions.trace_add("write", self._on_option_changed)
        self.use_portuguese.trace_add("write", self._on_option_changed)
        self.sample_count.trace_add("write", self._on_option_changed)
    
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
                    count = int(self.sample_count.get())
                    samples = self.generator._generate_sample_data(template_type, min(count, 3))  # Limit for preview
                    
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
            # Get file path from user
            template_type = TemplateType(self.selected_template.get())
            default_filename = f"{template_type.value}_template.csv"
            
            filepath = filedialog.asksaveasfilename(
                title="Guardar Template CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialname=default_filename,
                parent=self.window
            )
            
            if not filepath:
                return
            
            # Create configuration
            config = TemplateConfig(
                template_type=template_type,
                include_samples=self.include_samples.get(),
                include_descriptions=self.include_descriptions.get(),
                include_portuguese=self.use_portuguese.get(),
                sample_count=int(self.sample_count.get() or 3)
            )
            
            # Generate template
            success, message = self.generator.generate_template(template_type, filepath, config)
            
            if success:
                messagebox.showinfo(
                    "Sucesso",
                    f"Template gerado com sucesso!\n\nFicheiro: {os.path.basename(filepath)}\n\n{message}",
                    parent=self.window
                )
                self.result = filepath
                self.window.destroy()
            else:
                messagebox.showerror(
                    "Erro",
                    f"Falha ao gerar template:\n\n{message}",
                    parent=self.window
                )
        
        except Exception as e:
            logger.error(f"Error generating single template: {str(e)}")
            messagebox.showerror(
                "Erro",
                f"Erro inesperado:\n\n{str(e)}",
                parent=self.window
            )
    
    def _generate_all_templates(self):
        """Generate all available templates."""
        try:
            # Get directory from user
            directory = filedialog.askdirectory(
                title="Selecionar Pasta para Templates",
                parent=self.window
            )
            
            if not directory:
                return
            
            # Generate all templates
            success, message, results = self.generator.generate_multiple_templates(directory)
            
            # Also generate help file
            help_path = os.path.join(directory, "CSV_Template_Guide.md")
            help_success, help_message = self.generator.generate_help_file(help_path)
            
            # Show results
            if success and help_success:
                result_message = f"Todos os templates foram gerados com sucesso!\n\n"
                result_message += f"Pasta: {directory}\n\n"
                result_message += f"Templates gerados:\n"
                
                for filename, result in results.items():
                    status = "✅" if result else "❌"
                    result_message += f"  {status} {filename}\n"
                
                result_message += f"\n📖 Guia de utilização: CSV_Template_Guide.md"
                
                messagebox.showinfo(
                    "Sucesso",
                    result_message,
                    parent=self.window
                )
                
                self.result = directory
                self.window.destroy()
            else:
                error_message = f"Alguns templates falharam:\n\n{message}"
                if not help_success:
                    error_message += f"\nErro no guia: {help_message}"
                
                messagebox.showwarning(
                    "Aviso",
                    error_message,
                    parent=self.window
                )
        
        except Exception as e:
            logger.error(f"Error generating all templates: {str(e)}")
            messagebox.showerror(
                "Erro",
                f"Erro inesperado:\n\n{str(e)}",
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
