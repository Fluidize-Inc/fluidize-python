import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from upath import UPath

from fluidize.core.modules.run.node.methods.base.execstrat import BaseExecutionStrategy
from fluidize.core.modules.run.node.node_runner import RunJob
from fluidize.core.modules.tracking.mlflow_tracker import MLFlowTracker
from fluidize.core.types import node
from fluidize.core.types.project import ProjectSummary
from fluidize.core.types.runs import RunFlowPayload, RunStatus, projectRunMetadata
from fluidize.core.utils.dataloader.data_loader import DataLoader
from fluidize.core.utils.dataloader.data_writer import DataWriter
from fluidize.core.utils.pathfinder.path_finder import PathFinder

logger = logging.getLogger(__name__)


class BaseProjectRunner(ABC):
    """
    Handles the execution of a project run, coordinating multiple node executions
    within a single run folder.
    """

    def __init__(self, project: ProjectSummary):
        """Initialize the project runner with a project"""
        self.project = project
        self.project_path = PathFinder.get_project_path(project)
        self.runs_path = PathFinder.get_runs_path(project)
        self.run_number = self._get_run_number(self.runs_path)
        self.run_path = PathFinder.get_run_path(self.project, self.run_number)
        self.strategy = self.get_default_execution_strategy()

        # Initialize MLFlow tracker
        try:
            self.mlflow_tracker: Optional[MLFlowTracker] = MLFlowTracker(project)
            self.mlflow_experiment_id: Optional[str] = None
            self.mlflow_run_id: Optional[str] = None
        except Exception as e:
            logger.warning(f"Failed to initialize MLFlow tracker: {e}")
            self.mlflow_tracker = None
            self.mlflow_experiment_id = None
            self.mlflow_run_id = None

    @abstractmethod
    def get_default_execution_strategy(self) -> type[BaseExecutionStrategy]:
        pass

    @abstractmethod
    def _get_run_number(self, runs_path: UPath) -> int:
        """
        Helper function to find the next available run number
        in the specified runs directory.
        """
        pass

    @abstractmethod
    def _copy_project_contents(self, source_path: UPath, destination_path: UPath) -> None:
        """
        Copy the contents of the project directory to the new run directory (excluding the 'run' directory).
        """
        pass

    def _get_run_id(self) -> str:
        """
        Generate a unique run ID based on the project ID and run number.
        """
        return f"{self.project.id}_run_{self.run_number}"

    def write_project_run_metadata(self, payload: RunFlowPayload) -> None:
        """
        Construct and save the project run metadata in the run directory.
        """
        self.metadata = projectRunMetadata(
            metadata_version="1.0",
            run_number=self.run_number,
            run_folder=self.run_path.name,
            name=payload.name or f"Run {self.run_number}",
            id=self._get_run_id(),
            date_created=datetime.now().isoformat(),
            date_modified=datetime.now().isoformat(),
            description=payload.description or "",
            tags=payload.tags or [],
            run_status=RunStatus.RUNNING,
            mlflow_run_id=self.mlflow_run_id,
            mlflow_experiment_id=self.mlflow_experiment_id,
        )

        # Instantiate the model and save it to the specified directory.
        self.metadata.save(directory=self.run_path)

    def prepare_run_environment(self, metadata: RunFlowPayload) -> int:
        """
        Create a new run folder for the project
        Returns the run number
        """
        # Create the new run directory
        DataWriter.create_directory(self.run_path)

        # Copy project contents to the new run directory
        self._copy_project_contents(self.project_path, self.run_path)

        # Start MLFlow tracking for this run
        if self.mlflow_tracker:
            try:
                # Setup experiment if not already done
                self.mlflow_experiment_id = self.mlflow_tracker.setup_experiment(self.project.id)

                # Start MLFlow run
                self.mlflow_run_id = self.mlflow_tracker.start_run(run_name=f"run_{self.run_number}")

                # Log run metadata
                self.mlflow_tracker.log_parameters({
                    "run_number": self.run_number,
                    "project_id": self.project.id,
                    "project_label": self.project.label,
                })

                self.mlflow_tracker.log_tag("run_name", metadata.name or f"Run {self.run_number}")
                if metadata.description:
                    self.mlflow_tracker.log_tag("description", metadata.description)
                if metadata.tags:
                    self.mlflow_tracker.log_tag("user_tags", ",".join(metadata.tags))

            except Exception:
                logger.exception("Failed to start MLFlow tracking")

        # Add Project metadata to the run directory (now includes MLFlow IDs)
        self.write_project_run_metadata(metadata)

        print(f"Created project run folder: {self.run_path}")
        return self.run_number

    def execute_node(self, node_id: str, prev_node_id: Optional[str] = None, **kwargs: Any) -> dict[str, Any]:  # noqa: C901
        """
        Execute a single node within the project run
        Returns the execution result
        """
        if self.run_number is None:
            msg = "Run environment not prepared. Call prepare_run_environment() first."
            raise ValueError(msg)

        print(f"Executing node {node_id} in run {self.run_number}")
        if self.strategy is None:
            self.strategy = self.get_default_execution_strategy()

        nodeProperties_simulation = node.nodeProperties_simulation.from_file(
            PathFinder.get_node_path(self.project, node_id, self.run_number)
        )
        prev_nodeProperties_simulation = (
            node.nodeProperties_simulation.from_file(
                PathFinder.get_node_path(self.project, prev_node_id, self.run_number)
            )
            if prev_node_id
            else None
        )

        # Start nested MLFlow run for this node
        node_mlflow_id = None
        if self.mlflow_tracker and self.mlflow_run_id:
            try:
                node_mlflow_id = self.mlflow_tracker.start_run(
                    run_name=f"node_{node_id}", parent_run_id=self.mlflow_run_id
                )

                # Log node information
                self.mlflow_tracker.log_parameters({
                    "node_id": node_id,
                    "node_type": nodeProperties_simulation.container_image,
                    "prev_node_id": prev_node_id or "none",
                })

                # Log parameters from parameters.json
                try:
                    parameters_path = PathFinder.get_node_parameters_path(self.project, node_id, self.run_number)
                    params_data = DataLoader.load_node_parameters(parameters_path)

                    # Log all parameters
                    for param in params_data.get("parameters", []):
                        param_key = f"{param['scope']}_{param['name']}"
                        self.mlflow_tracker.log_parameters({param_key: param["value"]})

                        # Log parameter metadata as tags
                        if param.get("description"):
                            self.mlflow_tracker.log_tag(f"param_{param['name']}_desc", param["description"])
                        if param.get("type"):
                            self.mlflow_tracker.log_tag(f"param_{param['name']}_type", param["type"])

                except Exception as e:
                    logger.warning(f"Failed to log node parameters: {e}")

            except Exception:
                logger.exception("Failed to start MLFlow tracking for node %s", node_id)

        job = RunJob(
            project=self.project,
            nodeProperties_simulation=nodeProperties_simulation,
            prev_nodeProperties_simulation=prev_nodeProperties_simulation,
            strategyClass=self.strategy,
            mlflow_tracker=self.mlflow_tracker if node_mlflow_id else None,
            run_id=self._get_run_id(),
            run_metadata=self.metadata,  # Pass entire metadata object
        )

        try:
            job.run()
            job_result = "success"

            # End the node MLFlow run
            if self.mlflow_tracker and node_mlflow_id:
                self.mlflow_tracker.end_run(status="FINISHED")

        except Exception:
            # End the node MLFlow run with failure status
            if self.mlflow_tracker and node_mlflow_id:
                self.mlflow_tracker.end_run(status="FAILED")
            raise

        # ISSUE #22:
        return {"node_id": node_id, "status": "success", "result": job_result}

    async def execute_flow(self, nodes_to_run: list[str], prev_nodes: list[str], **kwargs: Any) -> list[dict[str, Any]]:
        """
        Execute a flow of nodes in the correct order
        nodes_to_run: List of node IDs
        Returns execution results for all nodes
        """

        results = []
        try:
            for node_id, prev_node_id in zip(nodes_to_run, prev_nodes):
                result = await asyncio.to_thread(self.execute_node, node_id, prev_node_id=prev_node_id, **kwargs)
                results.append(result)

            # Update run status to SUCCESS
            self.metadata.edit(run_status=RunStatus.SUCCESS)

            # Log final metrics to MLFlow
            if self.mlflow_tracker and self.mlflow_run_id:
                try:
                    self.mlflow_tracker.log_metrics({
                        "total_nodes": len(nodes_to_run),
                        "successful_nodes": len(results),
                    })
                    self.mlflow_tracker.log_tag("final_status", "SUCCESS")
                    self.mlflow_tracker.end_run(status="FINISHED")
                except Exception:
                    logger.exception("Failed to finalize MLFlow tracking")

        except Exception as e:
            self.metadata.edit(run_status=RunStatus.FAILED)

            # Log failure to MLFlow
            if self.mlflow_tracker and self.mlflow_run_id:
                try:
                    self.mlflow_tracker.log_tag("final_status", "FAILED")
                    self.mlflow_tracker.log_tag("error_message", str(e))
                    self.mlflow_tracker.end_run(status="FAILED")
                except Exception:
                    logger.exception("Failed to log failure to MLFlow")
            raise

        return results
