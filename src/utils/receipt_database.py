"""
Receipt Database Manager - handles storage and retrieval of receipt history.
"""

import sqlite3
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager

try:
    from .logger import get_logger
except ImportError:
    from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ReceiptRecord:
    """Data class for stored receipt information."""
    id: Optional[int] = None
    contract_id: str = ""
    tenant_name: str = ""
    from_date: str = ""
    to_date: str = ""
    payment_date: str = ""
    value: float = 0.0
    receipt_type: str = ""
    receipt_number: str = ""
    status: str = ""
    error_message: str = ""
    timestamp: str = ""
    processing_mode: str = ""
    dry_run: bool = False
    tenant_count: int = 1
    landlord_count: int = 1
    is_inheritance: bool = False
    
    def __post_init__(self):
        """Ensure timestamp is set if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ReceiptDatabase:
    """Manages the SQLite database for receipt history."""
    
    def __init__(self, db_path: str = None):
        """Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Create database in logs directory for consistency
            os.makedirs("logs", exist_ok=True)
            db_path = "logs/receipts_history.db"
        
        self.db_path = db_path
        self._init_database()
        logger.info(f"Receipt database initialized at: {self.db_path}")
    
    def _init_database(self):
        """Initialize the database schema."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create receipts table with comprehensive fields
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS receipts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_id TEXT NOT NULL,
                        tenant_name TEXT,
                        from_date TEXT NOT NULL,
                        to_date TEXT NOT NULL,
                        payment_date TEXT,
                        value REAL NOT NULL,
                        receipt_type TEXT,
                        receipt_number TEXT,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        timestamp TEXT NOT NULL,
                        processing_mode TEXT,
                        dry_run BOOLEAN DEFAULT FALSE,
                        tenant_count INTEGER DEFAULT 1,
                        landlord_count INTEGER DEFAULT 1,
                        is_inheritance BOOLEAN DEFAULT FALSE,
                        
                        -- Create indexes for common queries
                        UNIQUE(contract_id, from_date, to_date, timestamp)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_contract_id ON receipts(contract_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON receipts(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON receipts(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_dates ON receipts(from_date, to_date)')
                
                # Create statistics view for quick analytics
                cursor.execute('''
                    CREATE VIEW IF NOT EXISTS receipt_stats AS
                    SELECT 
                        COUNT(*) as total_receipts,
                        COUNT(CASE WHEN status = 'Success' THEN 1 END) as successful_receipts,
                        COUNT(CASE WHEN status = 'Failed' THEN 1 END) as failed_receipts,
                        COUNT(CASE WHEN dry_run = 1 THEN 1 END) as dry_run_receipts,
                        SUM(value) as total_value,
                        AVG(value) as average_value,
                        MIN(timestamp) as earliest_receipt,
                        MAX(timestamp) as latest_receipt,
                        COUNT(DISTINCT contract_id) as unique_contracts
                    FROM receipts
                ''')
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def add_receipt(self, receipt: ReceiptRecord) -> int:
        """Add a receipt record to the database.
        
        Args:
            receipt: ReceiptRecord to store
            
        Returns:
            The ID of the inserted receipt
            
        Raises:
            sqlite3.IntegrityError: If receipt already exists (duplicate)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert receipt to dict and remove id for insertion
                data = asdict(receipt)
                data.pop('id')
                
                # Prepare SQL
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                sql = f'INSERT INTO receipts ({columns}) VALUES ({placeholders})'
                
                cursor.execute(sql, list(data.values()))
                receipt_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added receipt record with ID {receipt_id} for contract {receipt.contract_id}")
                return receipt_id
                
        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate receipt detected for contract {receipt.contract_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to add receipt: {e}")
            raise
    
    def add_receipts_batch(self, receipts: List[ReceiptRecord]) -> List[int]:
        """Add multiple receipts in a single transaction.
        
        Args:
            receipts: List of ReceiptRecord objects to store
            
        Returns:
            List of inserted receipt IDs
        """
        receipt_ids = []
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for receipt in receipts:
                    try:
                        data = asdict(receipt)
                        data.pop('id')
                        
                        columns = ', '.join(data.keys())
                        placeholders = ', '.join(['?' for _ in data])
                        sql = f'INSERT INTO receipts ({columns}) VALUES ({placeholders})'
                        
                        cursor.execute(sql, list(data.values()))
                        receipt_ids.append(cursor.lastrowid)
                        
                    except sqlite3.IntegrityError:
                        # Skip duplicates but continue with others
                        logger.warning(f"Skipping duplicate receipt for contract {receipt.contract_id}")
                        continue
                
                conn.commit()
                logger.info(f"Added {len(receipt_ids)} receipt records in batch")
                return receipt_ids
                
        except Exception as e:
            logger.error(f"Failed to add receipts batch: {e}")
            raise
    
    def get_receipt_by_id(self, receipt_id: int) -> Optional[ReceiptRecord]:
        """Get a receipt by its ID.
        
        Args:
            receipt_id: The receipt ID to retrieve
            
        Returns:
            ReceiptRecord if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM receipts WHERE id = ?', (receipt_id,))
                row = cursor.fetchone()
                
                if row:
                    return ReceiptRecord(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Failed to get receipt by ID {receipt_id}: {e}")
            return None
    
    def get_receipts_by_contract(self, contract_id: str) -> List[ReceiptRecord]:
        """Get all receipts for a specific contract.
        
        Args:
            contract_id: The contract ID to search for
            
        Returns:
            List of ReceiptRecord objects for the contract
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM receipts 
                    WHERE contract_id = ? 
                    ORDER BY timestamp DESC
                ''', (contract_id,))
                
                rows = cursor.fetchall()
                return [ReceiptRecord(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get receipts for contract {contract_id}: {e}")
            return []
    
    def get_recent_receipts(self, limit: int = 100) -> List[ReceiptRecord]:
        """Get the most recent receipts.
        
        Args:
            limit: Maximum number of receipts to return
            
        Returns:
            List of recent ReceiptRecord objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM receipts 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [ReceiptRecord(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get recent receipts: {e}")
            return []
    
    def search_receipts(self, 
                       contract_id: str = None,
                       tenant_name: str = None,
                       status: str = None,
                       from_date: str = None,
                       to_date: str = None,
                       dry_run: bool = None) -> List[ReceiptRecord]:
        """Search receipts with various filters.
        
        Args:
            contract_id: Filter by contract ID (partial match)
            tenant_name: Filter by tenant name (partial match)
            status: Filter by status (exact match)
            from_date: Filter by receipts from this date onwards
            to_date: Filter by receipts up to this date
            dry_run: Filter by dry run status
            
        Returns:
            List of matching ReceiptRecord objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                where_clauses = []
                params = []
                
                if contract_id:
                    where_clauses.append('contract_id LIKE ?')
                    params.append(f'%{contract_id}%')
                
                if tenant_name:
                    where_clauses.append('tenant_name LIKE ?')
                    params.append(f'%{tenant_name}%')
                
                if status:
                    where_clauses.append('status = ?')
                    params.append(status)
                
                if from_date:
                    where_clauses.append('timestamp >= ?')
                    params.append(from_date)
                
                if to_date:
                    where_clauses.append('timestamp <= ?')
                    params.append(to_date)
                
                if dry_run is not None:
                    where_clauses.append('dry_run = ?')
                    params.append(dry_run)
                
                where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
                sql = f'''
                    SELECT * FROM receipts 
                    WHERE {where_sql}
                    ORDER BY timestamp DESC
                '''
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                logger.info(f"Found {len(rows)} receipts matching search criteria")
                return [ReceiptRecord(**dict(row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to search receipts: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about stored receipts.
        
        Returns:
            Dictionary containing various statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get basic stats from view
                cursor.execute('SELECT * FROM receipt_stats')
                stats_row = cursor.fetchone()
                stats = dict(stats_row) if stats_row else {}
                
                # Get additional statistics
                cursor.execute('''
                    SELECT 
                        COUNT(DISTINCT DATE(timestamp)) as active_days,
                        COUNT(CASE WHEN status = 'Success' AND dry_run = 0 THEN 1 END) as real_successful_receipts,
                        SUM(CASE WHEN status = 'Success' AND dry_run = 0 THEN value ELSE 0 END) as real_total_value
                    FROM receipts
                ''')
                additional_row = cursor.fetchone()
                if additional_row:
                    stats.update(dict(additional_row))
                
                # Get status breakdown
                cursor.execute('''
                    SELECT status, COUNT(*) as count
                    FROM receipts
                    GROUP BY status
                    ORDER BY count DESC
                ''')
                status_breakdown = {row['status']: row['count'] for row in cursor.fetchall()}
                stats['status_breakdown'] = status_breakdown
                
                # Get monthly breakdown (last 12 months)
                cursor.execute('''
                    SELECT 
                        strftime('%Y-%m', timestamp) as month,
                        COUNT(*) as count,
                        SUM(value) as total_value
                    FROM receipts
                    WHERE timestamp >= date('now', '-12 months')
                    GROUP BY strftime('%Y-%m', timestamp)
                    ORDER BY month DESC
                ''')
                monthly_data = [dict(row) for row in cursor.fetchall()]
                stats['monthly_breakdown'] = monthly_data
                
                logger.info("Retrieved receipt statistics successfully")
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def delete_receipt(self, receipt_id: int) -> bool:
        """Delete a receipt by ID.
        
        Args:
            receipt_id: ID of the receipt to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM receipts WHERE id = ?', (receipt_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
                
                if deleted:
                    logger.info(f"Deleted receipt with ID {receipt_id}")
                else:
                    logger.warning(f"Receipt with ID {receipt_id} not found for deletion")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete receipt {receipt_id}: {e}")
            return False
    
    def clear_all_receipts(self) -> int:
        """Clear all receipt records from the database.
        
        Returns:
            Number of receipts deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM receipts')
                count = cursor.fetchone()[0]
                
                cursor.execute('DELETE FROM receipts')
                conn.commit()
                
                logger.info(f"Cleared {count} receipt records from database")
                return count
                
        except Exception as e:
            logger.error(f"Failed to clear receipts: {e}")
            return 0
    
    def export_to_csv(self, file_path: str) -> bool:
        """Export all receipts to a CSV file.
        
        Args:
            file_path: Path where to save the CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import csv
            
            receipts = self.get_recent_receipts(limit=10000)  # Export all recent
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                if not receipts:
                    logger.warning("No receipts to export")
                    return False
                
                # Use all fields from the first receipt as headers
                fieldnames = list(asdict(receipts[0]).keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for receipt in receipts:
                    writer.writerow(asdict(receipt))
            
            logger.info(f"Exported {len(receipts)} receipts to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export receipts to CSV: {e}")
            return False
