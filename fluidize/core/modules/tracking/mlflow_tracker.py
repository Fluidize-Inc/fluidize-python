import logging
from typing import Any, Optional

import mlflow
from mlflow.tracking import MlflowClient

from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.pathfinder.path_finder import PathFinder

logger = logging.getLogger(__name__)


class MLFlowTracker:
    """
    MLFlow tracking integration for Fluidize experiments.
    Handles both local and cloud storage based on project location.
    """

    def __init__(self, project: ProjectSummary):
        """
        Initialize MLFlow tracker for a project.

        Args:
            project: Project summary object
        """
        self.project = project

        # Get tracking URI from PathFinder - it handles user context automatically
        self.tracking_uri = PathFinder.get_mlflow_tracking_uri()
        mlflow.set_tracking_uri(self.tracking_uri)

        self.client = MlflowClient()
        self.current_run_id: Optional[str] = None
        self.run_stack: list[str] = []  # Stack to track nested runs

        logger.info(f"MLFlow tracker initialized with URI: {self.tracking_uri}")

    def setup_experiment(self, project_id: str) -> str:
        """
        Create or get MLFlow experiment for a project.

        Args:
            project_id: The project ID to use as experiment name

        Returns:
            Experiment ID
        """
        experiment_name = f"project_{project_id}"

        try:
            experiment = self.client.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = self.client.create_experiment(
                    experiment_name, tags={"project_id": project_id, "project_label": self.project.label}
                )
            else:
                experiment_id = experiment.experiment_id
        except Exception:
            logger.exception("Error setting up experiment")
            # Create experiment without tags if there's an error
            experiment_id = mlflow.create_experiment(experiment_name)

        mlflow.set_experiment(experiment_name)
        return experiment_id

    def start_run(self, run_name: str, parent_run_id: Optional[str] = None) -> str:
        """
        Start a new MLFlow run.

        Args:
            run_name: Name for the run
            parent_run_id: Optional parent run ID for nested runs

        Returns:
            Run ID
        """
        try:
            # Push current run to stack if starting a nested run
            if parent_run_id and self.current_run_id:
                self.run_stack.append(self.current_run_id)

            if parent_run_id:
                # Create nested run
                run = mlflow.start_run(run_name=run_name, nested=True, parent_run_id=parent_run_id)
            else:
                # Create new top-level run
                run = mlflow.start_run(run_name=run_name)

            self.current_run_id = run.info.run_id
            logger.info(f"Started MLFlow run: {run_name} (ID: {self.current_run_id})")

        except Exception:
            logger.exception("Error starting MLFlow run")
            raise

        return self.current_run_id or ""

    def log_parameters(self, params: dict[str, Any]) -> None:
        """
        Log parameters to the current MLFlow run.

        Args:
            params: Dictionary of parameter names and values
        """
        if not self.current_run_id:
            logger.warning("No active MLFlow run to log parameters to")
            return

        try:
            for key, value in params.items():
                # MLFlow requires string values for parameters
                mlflow.log_param(key, str(value))
            logger.info(f"Logged {len(params)} parameters to MLFlow")
        except Exception:
            logger.exception("Error logging parameters")

    def log_metrics(self, metrics: dict[str, float]) -> None:
        """
        Log metrics to the current MLFlow run.

        Args:
            metrics: Dictionary of metric names and values
        """
        if not self.current_run_id:
            logger.warning("No active MLFlow run to log metrics to")
            return

        try:
            for key, value in metrics.items():
                mlflow.log_metric(key, value)
            logger.info(f"Logged {len(metrics)} metrics to MLFlow")
        except Exception:
            logger.exception("Error logging metrics")

    def log_tag(self, key: str, value: str) -> None:
        """
        Log a tag to the current MLFlow run.

        Args:
            key: Tag key
            value: Tag value
        """
        if not self.current_run_id:
            logger.warning("No active MLFlow run to log tags to")
            return

        try:
            mlflow.set_tag(key, value)
        except Exception:
            logger.exception("Error logging tag %s", key)

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None) -> None:
        """
        Log an artifact file to the current MLFlow run.

        Args:
            local_path: Path to the local file
            artifact_path: Optional path within the artifact store
        """
        if not self.current_run_id:
            logger.warning("No active MLFlow run to log artifacts to")
            return

        try:
            mlflow.log_artifact(local_path, artifact_path)
            logger.info(f"Logged artifact: {local_path}")
        except Exception:
            logger.exception("Error logging artifact")

    def end_run(self, status: Optional[str] = None) -> None:
        """
        End the current MLFlow run and restore parent run context if nested.

        Args:
            status: Optional status (FINISHED, FAILED, KILLED)
        """
        try:
            ended_run_id = self.current_run_id

            if status:
                mlflow.end_run(status=status)
            else:
                mlflow.end_run()

            logger.info(f"Ended MLFlow run: {ended_run_id}")

            # Restore parent run context if we have nested runs
            if self.run_stack:
                self.current_run_id = self.run_stack.pop()
                logger.info(f"Restored parent MLFlow run: {self.current_run_id}")
            else:
                self.current_run_id = None

        except Exception:
            logger.exception("Error ending MLFlow run")

    def get_run(self, run_id: str) -> Optional[mlflow.entities.Run]:
        """
        Get a specific MLFlow run.

        Args:
            run_id: The run ID to retrieve

        Returns:
            MLFlow Run object or None
        """
        try:
            return self.client.get_run(run_id)
        except Exception:
            logger.exception("Error getting run %s", run_id)
            return None

    def search_runs(self, experiment_id: str, filter_string: str = "") -> list:
        """
        Search for runs in an experiment.

        Args:
            experiment_id: The experiment ID to search
            filter_string: Optional filter string (e.g., "params.rho > 1.0")

        Returns:
            List of runs
        """
        try:
            return self.client.search_runs(
                experiment_ids=[experiment_id], filter_string=filter_string, order_by=["start_time DESC"]
            )
        except Exception:
            logger.exception("Error searching runs")
            return []
