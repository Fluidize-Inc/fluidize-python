"""Unit tests for ExecutionLogger class."""

from unittest.mock import Mock, patch
from types import SimpleNamespace

import pytest

from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.logger.execution_logger import ExecutionLogger


class TestExecutionLogger:
    """Test suite for ExecutionLogger class."""

    @pytest.fixture
    def mock_project(self):
        """Create a mock ProjectSummary for testing."""
        return Mock(spec=ProjectSummary)

    @pytest.fixture
    def mock_run_metadata(self):
        """Create mock run metadata with run_number."""
        return SimpleNamespace(run_number=42)

    @pytest.fixture
    def invalid_run_metadata(self):
        """Create invalid run metadata without run_number."""
        return SimpleNamespace(other_field="value")

    def test_validate_run_metadata_valid(self, mock_run_metadata):
        """Test _validate_run_metadata with valid metadata."""
        result = ExecutionLogger._validate_run_metadata(mock_run_metadata)
        assert result is True

    def test_validate_run_metadata_none(self):
        """Test _validate_run_metadata with None."""
        result = ExecutionLogger._validate_run_metadata(None)
        assert result is False

    def test_validate_run_metadata_missing_run_number(self, invalid_run_metadata):
        """Test _validate_run_metadata with missing run_number."""
        result = ExecutionLogger._validate_run_metadata(invalid_run_metadata)
        assert result is False

    def test_validate_run_metadata_none_run_number(self):
        """Test _validate_run_metadata with None run_number."""
        metadata = SimpleNamespace(run_number=None)
        result = ExecutionLogger._validate_run_metadata(metadata)
        assert result is False

    @patch("fluidize.core.utils.logger.execution_logger.DataWriter")
    @patch("fluidize.core.utils.logger.execution_logger.PathFinder")
    def test_save_execution_logs_success(self, mock_pathfinder, mock_datawriter, mock_project, mock_run_metadata):
        """Test successful execution log saving."""
        # Setup mocks
        mock_logs_path = Mock()
        mock_pathfinder.get_logs_path.return_value = mock_logs_path
        mock_logs_path.__truediv__ = Mock(return_value="mock_nodes_dir")
        mock_datawriter.create_directory.return_value = True

        mock_stdout_path = "mock_stdout_path"
        mock_stderr_path = "mock_stderr_path"
        mock_pathfinder.get_log_path.side_effect = [mock_stdout_path, mock_stderr_path]
        mock_datawriter.write_text.return_value = True

        # Test execution
        result = ExecutionLogger.save_execution_logs(
            mock_project, mock_run_metadata, "test_node", "stdout content", "stderr content"
        )

        # Assertions
        assert result is True
        mock_pathfinder.get_logs_path.assert_called_once_with(mock_project, 42)
        mock_datawriter.create_directory.assert_called_once()
        assert mock_pathfinder.get_log_path.call_count == 2
        assert mock_datawriter.write_text.call_count == 2

    def test_save_execution_logs_invalid_metadata(self, mock_project):
        """Test save_execution_logs with invalid metadata."""
        result = ExecutionLogger.save_execution_logs(
            mock_project, None, "test_node", "stdout content", "stderr content"
        )
        assert result is False

    @patch("fluidize.core.utils.logger.execution_logger.DataWriter")
    @patch("fluidize.core.utils.logger.execution_logger.PathFinder")
    def test_save_execution_logs_exception(self, mock_pathfinder, mock_datawriter, mock_project, mock_run_metadata):
        """Test save_execution_logs handling exceptions."""
        # Setup mocks to raise exception
        mock_pathfinder.get_logs_path.side_effect = Exception("Test exception")

        # Test execution
        result = ExecutionLogger.save_execution_logs(
            mock_project, mock_run_metadata, "test_node", "stdout content", "stderr content"
        )

        # Assertions
        assert result is False

    @patch("fluidize.core.utils.logger.execution_logger.DataWriter")
    @patch("fluidize.core.utils.logger.execution_logger.PathFinder")
    def test_save_stdout_success(self, mock_pathfinder, mock_datawriter, mock_project, mock_run_metadata):
        """Test successful stdout log saving."""
        # Setup mocks
        mock_stdout_path = "mock_stdout_path"
        mock_pathfinder.get_log_path.return_value = mock_stdout_path
        mock_datawriter.write_text.return_value = True

        # Test execution
        result = ExecutionLogger.save_stdout(mock_project, mock_run_metadata, "test_node", "stdout content")

        # Assertions
        assert result is True
        mock_pathfinder.get_log_path.assert_called_once_with(mock_project, 42, "test_node", "stdout")
        mock_datawriter.write_text.assert_called_once_with(mock_stdout_path, "stdout content")

    def test_save_stdout_no_content(self, mock_project, mock_run_metadata):
        """Test save_stdout with empty content."""
        result = ExecutionLogger.save_stdout(mock_project, mock_run_metadata, "test_node", "")
        assert result is False

    def test_save_stdout_invalid_metadata(self, mock_project):
        """Test save_stdout with invalid metadata."""
        result = ExecutionLogger.save_stdout(mock_project, None, "test_node", "stdout content")
        assert result is False

    @patch("fluidize.core.utils.logger.execution_logger.DataWriter")
    @patch("fluidize.core.utils.logger.execution_logger.PathFinder")
    def test_save_stderr_success(self, mock_pathfinder, mock_datawriter, mock_project, mock_run_metadata):
        """Test successful stderr log saving."""
        # Setup mocks
        mock_stderr_path = "mock_stderr_path"
        mock_pathfinder.get_log_path.return_value = mock_stderr_path
        mock_datawriter.write_text.return_value = True

        # Test execution
        result = ExecutionLogger.save_stderr(mock_project, mock_run_metadata, "test_node", "stderr content")

        # Assertions
        assert result is True
        mock_pathfinder.get_log_path.assert_called_once_with(mock_project, 42, "test_node", "stderr")
        mock_datawriter.write_text.assert_called_once_with(mock_stderr_path, "stderr content")

    def test_save_stderr_no_content(self, mock_project, mock_run_metadata):
        """Test save_stderr with empty content."""
        result = ExecutionLogger.save_stderr(mock_project, mock_run_metadata, "test_node", "")
        assert result is False

    def test_save_stderr_invalid_metadata(self, mock_project):
        """Test save_stderr with invalid metadata."""
        result = ExecutionLogger.save_stderr(mock_project, None, "test_node", "stderr content")
        assert result is False

    @patch("fluidize.core.utils.logger.execution_logger.DataWriter")
    @patch("fluidize.core.utils.logger.execution_logger.PathFinder")
    def test_save_stderr_exception(self, mock_pathfinder, mock_datawriter, mock_project, mock_run_metadata):
        """Test save_stderr handling exceptions."""
        # Setup mocks to raise exception
        mock_pathfinder.get_log_path.side_effect = Exception("Test exception")

        # Test execution
        result = ExecutionLogger.save_stderr(mock_project, mock_run_metadata, "test_node", "stderr content")

        # Assertions
        assert result is False

    @patch("fluidize.core.utils.logger.execution_logger.DataWriter")
    @patch("fluidize.core.utils.logger.execution_logger.PathFinder")
    def test_save_execution_logs_partial_success(self, mock_pathfinder, mock_datawriter, mock_project, mock_run_metadata):
        """Test save_execution_logs with partial success (only stderr has content)."""
        # Setup mocks
        mock_logs_path = Mock()
        mock_pathfinder.get_logs_path.return_value = mock_logs_path
        mock_logs_path.__truediv__ = Mock(return_value="mock_nodes_dir")
        mock_datawriter.create_directory.return_value = True

        mock_stderr_path = "mock_stderr_path"
        mock_pathfinder.get_log_path.return_value = mock_stderr_path
        mock_datawriter.write_text.return_value = True

        # Test execution with empty stdout
        result = ExecutionLogger.save_execution_logs(
            mock_project, mock_run_metadata, "test_node", "", "stderr content"
        )

        # Assertions - should return True since stderr was saved
        assert result is True
        mock_pathfinder.get_logs_path.assert_called_once_with(mock_project, 42)
        mock_datawriter.create_directory.assert_called_once()
