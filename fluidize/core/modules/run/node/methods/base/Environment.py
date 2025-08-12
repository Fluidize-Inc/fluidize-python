from abc import ABC, abstractmethod

from jinja2 import Environment, FileSystemLoader
from upath import UPath

from fluidize.core.types.node import nodeProperties_simulation
from fluidize.core.types.project import ProjectSummary
from fluidize.core.utils.dataloader.data_loader import DataLoader
from fluidize.core.utils.pathfinder.path_finder import PathFinder


class BaseEnvironmentManager(ABC):
    def __init__(
        self, node: nodeProperties_simulation, prev_node: nodeProperties_simulation, project: ProjectSummary
    ) -> None:
        self.node = node
        self.prev_node = prev_node
        self.project = project
        self.node_folder = PathFinder.get_node_path(project, node.node_id)
        self.node_run_folder = node.directory
        # Maybe some stronger checking on the node run folder?

    def load_node_parameters(self):
        # Load parameters via JSONDataLoader helper rather than local file access here
        try:
            # JSONDataLoader will handle the appropriate storage based on project location
            param_data = DataLoader.load_node_parameters(self.node_run_folder)
            all_params = param_data.get("parameters", [])
            # separate them by scope
            simulation_params = [p for p in all_params if p.get("scope") == "simulation"]
            properties_params = [p for p in all_params if p.get("scope") == "properties"]
        except Exception as e:
            print(f"ERROR: Failed to load parameters: {e}")
            return None, None
        return simulation_params, properties_params

    def process_parameters(self, simulation_params, properties_params) -> None:  # noqa: C901
        # Consolidate all parameters into a single context dictionary
        context = {param["name"]: param["value"] for param in simulation_params}
        context.update({param["name"]: param["value"] for param in properties_params})

        # Create a map of parameter names to their locations for targeted processing
        param_locations: dict[str, list[str]] = {}

        # Process simulation parameters with location tags
        for param in simulation_params:
            if param.get("location"):
                param_name = param["name"]
                if param_name not in param_locations:
                    param_locations[param_name] = []
                param_locations[param_name].extend(param["location"])

        # Process properties parameters with location tags
        for param in properties_params:
            if param.get("location"):
                param_name = param["name"]
                if param_name not in param_locations:
                    param_locations[param_name] = []
                param_locations[param_name].extend(param["location"])

        # Get unique file paths that need processing based on parameter locations
        files_to_process = set()
        for _param_name, locations in param_locations.items():
            for location in locations:
                location_path = self.node_run_folder / location
                if location_path.exists():
                    if location_path.is_file():
                        files_to_process.add(location_path)
                    elif location_path.is_dir():
                        # Add all files in the directory
                        for file_path in location_path.rglob("*"):
                            if file_path.is_file():
                                files_to_process.add(file_path)

        print(f"🔧 [Environment] Processing {len(files_to_process)} targeted files (vs exhaustive search)")

        # Process only the targeted files
        for file_path in files_to_process:
            try:
                content = self._get_file_content(file_path)

                if content and "{{" in content:
                    # Replace the parameter in the file content
                    updated_content = self.render_template(content, context)

                    # Only write back if content actually changed
                    if updated_content != content:
                        self._write_file_content(file_path, updated_content)
                        print(f"📝 [Environment] Updated parameters in: {file_path.relative_to(self.node_run_folder)}")

            except UnicodeDecodeError:
                # Skip binary files that can't be decoded
                continue
            except Exception as e:
                print(f"Warning: Could not process file {file_path}: {e}")
                continue

        # Skip parameters without location tags to avoid exhaustive search
        params_without_location = [p for p in simulation_params + properties_params if not p.get("location")]
        if params_without_location:
            param_names = [p["name"] for p in params_without_location]
            print(
                f"⚠️ [Environment] Skipping {len(params_without_location)} parameters without location tags: {param_names}"
            )

    @abstractmethod
    def _get_file_content(self, loc: UPath) -> str:
        """Abstract method to get file content based on the location. Should be implemented in subclasses."""
        pass

    @abstractmethod
    def _write_file_content(self, loc: UPath, content: str) -> None:
        """Abstract method to write content back to the file based on the location. Should be implemented in subclasses."""
        pass

    def render_template(self, content: str, context: dict) -> str:
        """Renders a template with the given context."""
        env = Environment(loader=FileSystemLoader("."), autoescape=True)
        template = env.from_string(content)
        return template.render(context)
