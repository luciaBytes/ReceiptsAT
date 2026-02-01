"""
Enhanced progress tracking system for bulk operations.
Provides real-time progress indicators, time estimates, and detailed feedback.
"""

import time
import threading
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import tkinter as tk
from tkinter import ttk


class OperationStatus(Enum):
    """Status of an operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationResult:
    """Result of a single operation."""
    operation_id: str
    status: OperationStatus
    message: str
    data: Optional[Any] = None
    error: Optional[Exception] = None
    duration: Optional[float] = None


@dataclass
class ProgressUpdate:
    """Progress update information."""
    current: int
    total: int
    message: str
    percentage: float
    estimated_time_remaining: Optional[float] = None
    current_operation: Optional[str] = None
    operations_per_second: Optional[float] = None


class ProgressTracker:
    """
    Advanced progress tracking with time estimation and detailed feedback.
    """
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset all tracking data."""
        self.total_operations = 0
        self.completed_operations = 0
        self.failed_operations = 0
        self.start_time = None
        self.operation_times: List[float] = []
        self.current_operation = None
        self.results: List[OperationResult] = []
        self.is_cancelled = False
        
    def start(self, total_operations: int):
        """Start tracking progress for a batch of operations."""
        self.reset()
        self.total_operations = total_operations
        self.start_time = time.time()
        
    def update(self, operation_result: OperationResult) -> ProgressUpdate:
        """
        Update progress with completed operation result.
        
        Args:
            operation_result: Result of completed operation
            
        Returns:
            ProgressUpdate with current progress information
        """
        self.results.append(operation_result)
        
        if operation_result.status == OperationStatus.COMPLETED:
            self.completed_operations += 1
        elif operation_result.status == OperationStatus.FAILED:
            self.failed_operations += 1
            
        # Track operation timing if available
        if operation_result.duration:
            self.operation_times.append(operation_result.duration)
            
        return self._calculate_progress()
        
    def set_current_operation(self, operation_description: str):
        """Set the current operation being processed."""
        self.current_operation = operation_description
        
    def cancel(self):
        """Cancel the current operation batch."""
        self.is_cancelled = True
        
    def _calculate_progress(self) -> ProgressUpdate:
        """Calculate current progress and estimates."""
        processed_operations = self.completed_operations + self.failed_operations
        
        if self.total_operations == 0:
            percentage = 0
        else:
            percentage = (processed_operations / self.total_operations) * 100
            
        # Calculate time estimates
        estimated_time_remaining = None
        operations_per_second = None
        
        if processed_operations > 0 and self.start_time is not None:
            elapsed_time = time.time() - self.start_time
            # Prevent division by zero in fast operations or unit tests
            if elapsed_time > 0:
                operations_per_second = processed_operations / elapsed_time
                
                remaining_operations = self.total_operations - processed_operations
                if operations_per_second > 0:
                    estimated_time_remaining = remaining_operations / operations_per_second
                
        # Create status message
        message = f"Processando: {processed_operations}/{self.total_operations}"
        if self.failed_operations > 0:
            message += f" ({self.failed_operations} erros)"
            
        return ProgressUpdate(
            current=processed_operations,
            total=self.total_operations,
            message=message,
            percentage=percentage,
            estimated_time_remaining=estimated_time_remaining,
            current_operation=self.current_operation,
            operations_per_second=operations_per_second
        )
        
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the completed batch operation."""
        total_time = None
        if self.start_time is not None:
            total_time = time.time() - self.start_time
            
        return {
            'total_operations': self.total_operations,
            'completed_operations': self.completed_operations,
            'failed_operations': self.failed_operations,
            'success_rate': self.completed_operations / max(1, self.total_operations) * 100,
            'total_time': total_time,
            'average_time_per_operation': sum(self.operation_times) / max(1, len(self.operation_times)),
            'results': self.results
        }


class EnhancedProgressBar:
    """
    Enhanced progress bar widget with detailed information display.
    """
    
    def __init__(self, parent_frame: tk.Widget):
        self.parent_frame = parent_frame
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar()
        self.detail_var = tk.StringVar()
        self.time_var = tk.StringVar()
        
        self._setup_ui()
        self.is_visible = False
        
    def _setup_ui(self):
        """Set up the progress bar UI components."""
        # Main progress frame
        self.progress_frame = ttk.LabelFrame(self.parent_frame, text="Progresso da Operação", padding="10")
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            length=400,
            mode='determinate'
        )
        self.progress_bar.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Status labels
        self.status_label = ttk.Label(self.progress_frame, textvariable=self.status_var, font=('TkDefaultFont', 9, 'bold'))
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Time information
        self.time_label = ttk.Label(self.progress_frame, textvariable=self.time_var, font=('TkDefaultFont', 8))
        self.time_label.grid(row=1, column=2, sticky=tk.E)
        
        # Current operation detail
        self.detail_label = ttk.Label(self.progress_frame, textvariable=self.detail_var, font=('TkDefaultFont', 8))
        self.detail_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(2, 0))
        
        # Action buttons frame
        self.buttons_frame = ttk.Frame(self.progress_frame)
        self.buttons_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        
        # Pause/Resume button
        self.pause_button = ttk.Button(self.buttons_frame, text="Pausar", command=self._toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Cancel button  
        self.cancel_button = ttk.Button(self.buttons_frame, text="Cancelar", command=self._cancel_operation)
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Details button
        self.details_button = ttk.Button(self.buttons_frame, text="Ver Detalhes", command=self._show_details)
        self.details_button.pack(side=tk.LEFT)
        
        # Configure grid weights
        self.progress_frame.columnconfigure(0, weight=1)
        self.progress_frame.columnconfigure(1, weight=1)
        self.progress_frame.columnconfigure(2, weight=1)
        
        # Callback functions (to be set by parent)
        self.on_pause = None
        self.on_resume = None
        self.on_cancel = None
        self.on_show_details = None
        
        # State tracking
        self.is_paused = False
        
    def show(self):
        """Show the progress bar."""
        if not self.is_visible:
            self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
            self.is_visible = True
            
    def hide(self):
        """Hide the progress bar."""
        if self.is_visible:
            self.progress_frame.pack_forget()
            self.is_visible = False
            
    def update(self, progress_update: ProgressUpdate):
        """
        Update the progress bar with new progress information.
        
        Args:
            progress_update: Progress update information
        """
        # Update progress bar
        self.progress_var.set(progress_update.percentage)
        
        # Update status message
        self.status_var.set(progress_update.message)
        
        # Update current operation
        if progress_update.current_operation:
            self.detail_var.set(f"Atual: {progress_update.current_operation}")
        else:
            self.detail_var.set("")
            
        # Update time information
        time_info = ""
        if progress_update.operations_per_second:
            time_info += f"{progress_update.operations_per_second:.1f} ops/s"
            
        if progress_update.estimated_time_remaining:
            if time_info:
                time_info += " • "
            time_info += f"Restam: {self._format_time(progress_update.estimated_time_remaining)}"
            
        self.time_var.set(time_info)
        
        # Update UI
        self.progress_frame.update_idletasks()
        
    def set_callbacks(self, on_pause=None, on_resume=None, on_cancel=None, on_show_details=None):
        """Set callback functions for button actions."""
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_cancel = on_cancel
        self.on_show_details = on_show_details
        
    def _toggle_pause(self):
        """Handle pause/resume button click."""
        if self.is_paused:
            if self.on_resume:
                self.on_resume()
            self.pause_button.config(text="Pausar")
            self.is_paused = False
        else:
            if self.on_pause:
                self.on_pause()
            self.pause_button.config(text="Retomar")
            self.is_paused = True
            
    def _cancel_operation(self):
        """Handle cancel button click."""
        if self.on_cancel:
            self.on_cancel()
            
    def _show_details(self):
        """Handle details button click."""
        if self.on_show_details:
            self.on_show_details()
            
    def _format_time(self, seconds: float) -> str:
        """Format time duration for display."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
            
    def set_completion_state(self, success: bool, message: str):
        """Set the progress bar to completion state."""
        if success:
            self.progress_var.set(100)
            self.status_var.set(" " + message)
            self.detail_var.set("")
            self.time_var.set("")
        else:
            self.status_var.set(" " + message)
            
        # Hide pause button, show only details
        self.pause_button.pack_forget()
        self.cancel_button.pack_forget()


class OperationManager:
    """
    Manages bulk operations with progress tracking and UI feedback.
    """
    
    def __init__(self, progress_bar: EnhancedProgressBar):
        self.progress_bar = progress_bar
        self.tracker = ProgressTracker()
        self.is_paused = False
        self.is_cancelled = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        
        # Set up progress bar callbacks
        self.progress_bar.set_callbacks(
            on_pause=self.pause,
            on_resume=self.resume, 
            on_cancel=self.cancel,
            on_show_details=self.show_details
        )
        
    def execute_batch(self, operations: List[Callable], operation_descriptions: List[str] = None):
        """
        Execute a batch of operations with progress tracking.
        
        Args:
            operations: List of callable operations to execute
            operation_descriptions: Optional descriptions for each operation
        """
        if not operations:
            return
            
        # Initialize progress tracking
        self.tracker.start(len(operations))
        self.progress_bar.show()
        self.is_cancelled = False
        self.is_paused = False
        
        # Execute operations
        for i, operation in enumerate(operations):
            # Check for cancellation
            if self.is_cancelled:
                break
                
            # Check for pause
            self.pause_event.wait()
            
            # Update current operation
            description = operation_descriptions[i] if operation_descriptions and i < len(operation_descriptions) else f"Operação {i+1}"
            self.tracker.set_current_operation(description)
            
            # Execute operation
            start_time = time.time()
            try:
                result = operation()
                duration = time.time() - start_time
                
                operation_result = OperationResult(
                    operation_id=str(i),
                    status=OperationStatus.COMPLETED,
                    message=f"Operação {i+1} concluída",
                    data=result,
                    duration=duration
                )
                
            except Exception as e:
                duration = time.time() - start_time
                operation_result = OperationResult(
                    operation_id=str(i),
                    status=OperationStatus.FAILED,
                    message=f"Operação {i+1} falhou: {str(e)}",
                    error=e,
                    duration=duration
                )
                
            # Update progress
            progress_update = self.tracker.update(operation_result)
            self.progress_bar.update(progress_update)
            
        # Show completion state
        summary = self.tracker.get_summary()
        if self.is_cancelled:
            self.progress_bar.set_completion_state(False, "Operação cancelada")
        else:
            success_rate = summary['success_rate']
            if success_rate == 100:
                message = f"Concluído com sucesso! ({summary['completed_operations']} operações)"
            else:
                message = f"Concluído: {summary['completed_operations']} sucessos, {summary['failed_operations']} erros"
            self.progress_bar.set_completion_state(success_rate > 0, message)
            
    def pause(self):
        """Pause the current batch operation."""
        self.pause_event.clear()
        self.is_paused = True
        
    def resume(self):
        """Resume the paused batch operation."""
        self.pause_event.set()
        self.is_paused = False
        
    def cancel(self):
        """Cancel the current batch operation."""
        self.is_cancelled = True
        self.tracker.cancel()
        if self.is_paused:
            self.resume()  # Resume to allow cancellation to proceed
            
    def show_details(self):
        """Show detailed operation results."""
        summary = self.tracker.get_summary()
        
        # Create details window
        details_window = tk.Toplevel()
        details_window.title("Detalhes da Operação")
        details_window.geometry("600x400")
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(details_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add summary information
        details_text = f"""=== Resumo da Operação ===
Total de operações: {summary['total_operations']}
Operações concluídas: {summary['completed_operations']}
Operações falhadas: {summary['failed_operations']}
Taxa de sucesso: {summary['success_rate']:.1f}%
Tempo total: {summary['total_time']:.1f}s
Tempo médio por operação: {summary['average_time_per_operation']:.2f}s

=== Detalhes das Operações ===
"""
        
        for result in summary['results']:
            status_icon = "" if result.status == OperationStatus.COMPLETED else ""
            details_text += f"{status_icon} {result.operation_id}: {result.message}"
            if result.duration:
                details_text += f" ({result.duration:.2f}s)"
            details_text += "\n"
            
        text_widget.insert(tk.END, details_text)
        text_widget.config(state=tk.DISABLED)  # Make read-only
