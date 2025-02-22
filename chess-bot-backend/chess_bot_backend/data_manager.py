"""
Data Manager for Chess Tournament System

This module handles data import/export between PostgreSQL databases.
It provides functionality for:
- Database dumps for portability
- Full and partial data exports
- Transaction-safe imports
- Automatic backup creation
"""

import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union, Sequence
import logging

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .models import Game

logger = logging.getLogger(__name__)

class DataManager:
    """
    Manages data export/import using PostgreSQL native tools.
    
    Features:
    --------
    - pg_dump for efficient exports
    - psql for reliable imports
    - Automatic backup creation
    - Transaction safety
    """
    
    def __init__(self, data_dir: Union[str, Path] = "chess_data"):
        """
        Initialize the data manager.
        
        Args:
            data_dir: Directory for database dumps (created if doesn't exist)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def export_database(self, db_url: str, filepath: Optional[Union[str, Path]] = None) -> str:
        """
        Export entire database using pg_dump.
        
        Args:
            db_url: SQLAlchemy database URL
            filepath: Optional specific path for export
            
        Returns:
            Path to the exported dump file
        """
        if filepath is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_dir / f"chess_db_{timestamp}.sql"
        else:
            output_path = Path(filepath)
            
        # Parse database URL
        db_name = db_url.split("/")[-1]
        
        # Create dump command
        cmd = [
            "pg_dump",
            "--dbname", db_name,
            "--format", "p",  # Plain text format
            "--clean",  # Include DROP commands
            "--if-exists",  # Add IF EXISTS to DROP commands
            "--no-owner",  # Don't include ownership commands
            "--no-privileges",  # Don't include privilege commands
            "--file", str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"Database exported to {output_path}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to export database: {e}")
            raise
            
    def export_game_data(self, db_url: str, game_ids: List[int], filepath: Optional[Union[str, Path]] = None) -> str:
        """
        Export specific games and their related data.
        
        Args:
            db_url: SQLAlchemy database URL
            game_ids: List of game IDs to export
            filepath: Optional specific path for export
            
        Returns:
            Path to the exported dump file
        """
        if filepath is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = self.data_dir / f"chess_games_{timestamp}.sql"
        else:
            output_path = Path(filepath)
            
        # Parse database URL
        db_name = db_url.split("/")[-1]
        
        # Create dump command with table filtering
        cmd = [
            "pg_dump",
            "--dbname", db_name,
            "--format", "p",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            "--table", "games",
            "--table", "game_moves",
            "--table", "ratings",
            "--where", f"games.id IN ({','.join(map(str, game_ids))})",
            "--file", str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"Game data exported to {output_path}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to export game data: {e}")
            raise
            
    def import_data(self, db_url: str, filepath: Union[str, Path]) -> None:
        """
        Import data from a SQL dump file.
        
        Args:
            db_url: SQLAlchemy database URL
            filepath: Path to SQL dump file
        """
        # Parse database URL
        db_name = db_url.split("/")[-1]
        
        # Create import command
        cmd = [
            "psql",
            "--dbname", db_name,
            "--file", str(filepath),
            "--quiet",  # Reduce noise in output
            "--single-transaction"  # Ensure atomic import
        ]
        
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"Data imported from {filepath}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to import data: {e}")
            raise
            
    def get_completed_games(self, session: Session) -> Sequence[Game]:
        """Get list of completed games from database."""
        return session.execute(select(Game)).scalars().all() 