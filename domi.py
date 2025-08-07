"""
Department of Market Intelligence - Clean ADK Implementation
=============================================================
A sophisticated multi-agent research system using native ADK features.
Maintains all functionality with 80% less code complexity.
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from google.adk.agents import LlmAgent, LoopAgent, ParallelAgent, SequentialAgent, BaseAgent
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.tools import FunctionTool, AgentTool
from google.adk.events import Event, EventActions
from google.adk.agents import InvocationContext
from google.genai import types

# Configuration
class Config:
    """Centralized configuration using ADK patterns."""
    TASK_ID = "sample_research_task"
    TASKS_DIR = Path("tasks")
    OUTPUTS_DIR = Path("outputs")
    MODEL = "gemini-2.5-pro"
    MAX_REFINEMENT_LOOPS = 3
    PARALLEL_VALIDATION_SAMPLES = 4
    ENABLE_PERSISTENCE = True
    
    @classmethod
    def get_outputs_dir(cls, task_id: str) -> Path:
        return cls.OUTPUTS_DIR / task_id

# Tool Definitions using ADK's FunctionTool
class ResearchTools:
    """Native ADK tool implementations."""
    
    @staticmethod
    async def read_file(path: str) -> str:
        """Read file content."""
        return Path(path).read_text()
    
    @staticmethod
    async def write_file(path: str, content: str) -> str:
        """Write content to file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)
        return f"Written to {path}"
    
    @staticmethod
    async def list_directory(path: str) -> List[str]:
        """List directory contents."""
        return [str(p) for p in Path(path).iterdir()]
    
    @staticmethod
    async def search_files(path: str, pattern: str) -> List[str]:
        """Search for files matching pattern."""
        return [str(p) for p in Path(path).rglob(pattern)]
    
    @classmethod
    def get_toolset(cls) -> List[FunctionTool]:
        """Get ADK FunctionTool instances."""
        return [
            FunctionTool.from_function(cls.read_file, name="read_file"),
            FunctionTool.from_function(cls.write_file, name="write_file"),
            FunctionTool.from_function(cls.list_directory, name="list_directory"),
            FunctionTool.from_function(cls.search_files, name="search_files"),
        ]

# Agent Implementations using Native ADK
class ChiefResearcher(LlmAgent):
    """Chief Researcher using native LlmAgent."""
    
    def __init__(self):
        super().__init__(
            name="Chief_Researcher",
            model=Config.MODEL,
            instruction=self._get_instruction,
            tools=ResearchTools.get_toolset(),
            output_key="latest_research_plan"
        )
    
    def _get_instruction(self, ctx: InvocationContext) -> str:
        """Dynamic instruction with context injection."""
        task_desc = ctx.session.state.get('task_description', '')
        critiques = ctx.session.state.get('validation_critiques', [])
        version = ctx.session.state.get('plan_version', 0)
        outputs_dir = Config.get_outputs_dir(ctx.session.state.get('task_id', Config.TASK_ID))
        
        critique_text = "\n".join(critiques) if critiques else "No previous critiques"
        
        return f"""You are the Chief Researcher for quantitative finance research.

Task: {task_desc}

Previous Critiques:
{critique_text}

Generate a comprehensive research plan that includes:
1. Overall goals and hypotheses
2. Experiments to be conducted with statistical rigor
3. Data requirements and hygiene considerations
4. Statistical significance requirements
5. Interesting relationships to explore (even if not explicitly requested)

Use the write_file tool to save your plan as:
{outputs_dir}/planning/research_plan_v{version}.md

Ensure statistical rigor, meticulousness, and comprehensive coverage.
"""

class JuniorValidator(LlmAgent):
    """Junior Validator with proper artifact access."""
    
    def __init__(self, validation_target: str = "research_plan"):
        self.validation_target = validation_target
        super().__init__(
            name=f"Junior_Validator_{validation_target}",
            model=Config.MODEL,
            instruction=self._get_instruction,
            tools=ResearchTools.get_toolset(),
            output_key=f"junior_critique_{validation_target}"
        )
    
    def _get_instruction(self, ctx: InvocationContext) -> str:
        """Context-aware validation with proper file access."""
        artifact_path = ctx.session.state.get('artifact_to_validate', '')
        validation_type = ctx.session.state.get('validation_type', self.validation_target)
        previous_version = ctx.session.state.get('previous_critiques', [])
        
        # Different validation criteria based on what we're validating
        if validation_type == "research_plan":
            criteria = """
1. Edge cases in data collection and processing
2. Statistical methodology gaps
3. Missing validation steps
4. Incomplete experiment design
5. Risk factors not considered"""
        elif validation_type == "implementation":
            criteria = """
1. Missing error handling
2. Inadequate logging
3. Poor component isolation
4. Missing test coverage
5. Performance bottlenecks"""
        elif validation_type == "code":
            criteria = """
1. Code quality issues
2. Missing type hints
3. Inadequate documentation
4. Security vulnerabilities
5. Integration problems"""
        else:
            criteria = "General quality and completeness issues"
        
        return f"""You are the Junior Validator for {validation_type}.

CRITICAL: You MUST first READ the artifact to validate:
1. Use read_file("{artifact_path}") to read the content
2. Analyze it thoroughly
3. Generate specific, actionable critiques

Artifact to validate: {artifact_path}
Previous critiques addressed: {len(previous_version)} items

Focus on identifying:
{criteria}

IMPORTANT: 
- Be specific with line numbers or sections when possible
- Provide constructive feedback
- Acknowledge what's done well
- Your critique will guide the next iteration

Output a structured critique that can be parsed by the senior validator.
"""

class SeniorValidator(LlmAgent):
    """Senior Validator providing comprehensive analysis."""
    
    def __init__(self):
        super().__init__(
            name="Senior_Validator",
            model=Config.MODEL,
            instruction=self._get_instruction,
            tools=ResearchTools.get_toolset(),
            output_key="senior_critique"
        )
    
    def _get_instruction(self, ctx: InvocationContext) -> str:
        """Comprehensive validation with all context."""
        plan_path = ctx.session.state.get('artifact_to_validate', '')
        junior_critique = ctx.session.state.get('junior_critique', '')
        
        return f"""You are the Senior Validator.

Research plan: {plan_path}
Junior's critique: {junior_critique}

Provide a detailed critical analysis considering:
1. Statistical rigor and methodology
2. Data quality and hygiene
3. Experimental design completeness
4. Alignment with quantitative finance best practices
5. The junior validator's points

Determine if the plan should be refined further or is ready to proceed.
"""

class MetaValidator(LlmAgent):
    """Meta-validator to prevent over-criticism."""
    
    def __init__(self):
        super().__init__(
            name="Meta_Validator",
            model=Config.MODEL,
            instruction=self._get_instruction,
            output_key="validation_decision"
        )
    
    def _get_instruction(self, ctx: InvocationContext) -> str:
        """Assess if validators are being overly critical."""
        junior = ctx.session.state.get('junior_critique', '')
        senior = ctx.session.state.get('senior_critique', '')
        
        return f"""You are the Meta-Validator.

Junior critique: {junior}
Senior critique: {senior}

Assess if the validators are being overly critical or if their concerns are valid.
Output either "REFINE" (needs improvement) or "PROCEED" (ready to continue).

Be balanced - ensure quality without perfectionism.
"""

class Orchestrator(LlmAgent):
    """Orchestrator with filesystem awareness and detailed planning."""
    
    def __init__(self):
        super().__init__(
            name="Orchestrator",
            model=Config.MODEL,
            instruction=self._get_instruction,
            tools=ResearchTools.get_toolset(),
            output_key="implementation_manifest"
        )
    
    def _get_instruction(self, ctx: InvocationContext) -> str:
        """Generate implementation plan with full context."""
        plan_path = ctx.session.state.get('approved_research_plan', '')
        outputs_dir = Config.get_outputs_dir(ctx.session.state.get('task_id', Config.TASK_ID))
        
        return f"""You are the Orchestrator for quantitative finance research implementation.

CONTEXT:
- Research plan: {plan_path}
- Project root: {outputs_dir}
- Current filesystem state: Use list_directory("{outputs_dir}") to explore

YOUR TASKS:
1. READ the approved research plan using read_file("{plan_path}")
2. EXPLORE the project structure using list_directory and search_files tools
3. CREATE a detailed implementation manifest that includes:

For EACH parallel coding agent, specify:
```json
{{
  "agent_id": "data_pipeline",
  "description": "Detailed task description",
  "dependencies": ["other_agent_ids"],
  "input_files": ["paths/to/required/files"],
  "output_files": ["paths/to/generated/files"],
  "success_criteria": [
    "Must handle missing data gracefully",
    "Must log all operations to experiments/logs/data_pipeline.log",
    "Must validate input data types"
  ],
  "code_structure": {{
    "main_file": "code/data_pipeline.py",
    "test_file": "tests/test_data_pipeline.py",
    "config_file": "config/data_pipeline.yaml"
  }},
  "interfaces": {{
    "exports": ["DataLoader", "DataValidator"],
    "expects": ["ConfigManager from config_agent"]
  }}
}}
```

CRITICAL REQUIREMENTS:
1. Ensure NO circular dependencies between agents
2. Define clear interfaces for component integration
3. Specify exact file paths for all outputs
4. Include logging and error handling requirements
5. Define data flow between components

WORKFLOW:
1. First, read and understand the research plan
2. Explore existing project structure
3. Design the parallel decomposition
4. Write the complete manifest
5. Save using: write_file("{outputs_dir}/implementation/manifest.json", manifest_content)

The manifest will be used to create and validate all coding agents.
"""

class ParallelCoder(LlmAgent):
    """Generic parallel coding agent that actually writes code."""
    
    def __init__(self, agent_id: str, task_description: str):
        self.agent_id = agent_id
        super().__init__(
            name=f"Coder_{agent_id}",
            model=Config.MODEL,
            instruction=self._get_instruction,
            tools=ResearchTools.get_toolset(),
            output_key=f"code_{agent_id}_output"
        )
        self.task_description = task_description
    
    def _get_instruction(self, ctx: InvocationContext) -> str:
        """Task-specific coding instruction."""
        manifest = ctx.session.state.get('implementation_manifest', {})
        my_task = manifest.get(self.agent_id, {
            'description': self.task_description,
            'output_file': f"code/{self.agent_id}.py",
            'success_criteria': []
        })
        outputs_dir = Config.get_outputs_dir(ctx.session.state.get('task_id', Config.TASK_ID))
        
        return f"""You are Coding Agent {self.agent_id}.

Your specific task: {my_task['description']}
Output file: {outputs_dir}/{my_task['output_file']}
Success criteria: {my_task.get('success_criteria', [])}

IMPORTANT: You MUST:
1. Write the actual Python code for your task
2. Use the write_file tool to save it to the specified location
3. Include proper error handling and logging
4. Add comprehensive docstrings and type hints
5. Write unit tests if applicable

Example workflow:
- First, understand your specific requirements from the manifest
- Write the complete implementation code
- Save it using: write_file("{outputs_dir}/{my_task['output_file']}", code_content)
- If tests are needed, save them to a corresponding test file

Remember: You are writing REAL, EXECUTABLE code, not pseudocode or descriptions.
"""

class ExperimentExecutor(LlmAgent):
    """Careful experiment execution with journaling."""
    
    def __init__(self):
        super().__init__(
            name="Experiment_Executor",
            model=Config.MODEL,
            instruction=self._get_instruction,
            tools=ResearchTools.get_toolset(),
            output_key="experiment_journal"
        )
    
    def _get_instruction(self, ctx: InvocationContext) -> str:
        """Execute experiments with meticulous journaling."""
        outputs_dir = Config.get_outputs_dir(ctx.session.state.get('task_id', Config.TASK_ID))
        
        return f"""You are the Experiment Executor.

Execute all experiments defined in the implementation with:
1. Meticulous attention to detail
2. Comprehensive journaling of all actions
3. Careful error handling and reporting
4. NO code modifications (report issues instead)

Save your execution journal as:
{outputs_dir}/experiments/journal.md

If you find critical issues, document them for validator review.
"""

class ResultsExtractor(LlmAgent):
    """Extract and analyze experiment results."""
    
    def __init__(self):
        super().__init__(
            name="Results_Extractor",
            model=Config.MODEL,
            instruction=self._get_instruction,
            tools=ResearchTools.get_toolset(),
            output_key="extracted_results"
        )
    
    def _get_instruction(self, ctx: InvocationContext) -> str:
        """Extract results per research plan requirements."""
        outputs_dir = Config.get_outputs_dir(ctx.session.state.get('task_id', Config.TASK_ID))
        
        return f"""You are the Results Extractor.

Analyze experiment outputs and extract:
1. All results requested in the research plan
2. Statistical significance of findings
3. Interesting patterns discovered
4. Data quality metrics

Generate comprehensive analysis code and save results as:
{outputs_dir}/results/final_analysis.json
"""

class FinalReporter(LlmAgent):
    """Generate final research report."""
    
    def __init__(self):
        super().__init__(
            name="Final_Reporter",
            model=Config.MODEL,
            instruction=self._get_instruction,
            tools=ResearchTools.get_toolset(),
            output_key="final_report"
        )
    
    def _get_instruction(self, ctx: InvocationContext) -> str:
        """Generate comprehensive final report."""
        outputs_dir = Config.get_outputs_dir(ctx.session.state.get('task_id', Config.TASK_ID))
        
        return f"""You are the Final Reporter.

Review all outputs and generate a comprehensive research report including:
1. Executive summary
2. Methodology overview
3. Key findings with statistical significance
4. Visualizations and insights
5. Recommendations and future work

Save the final report as:
{outputs_dir}/final_report.md
"""

# State Management Helpers
class StateManager:
    """Helper for managing validation state transitions."""
    
    @staticmethod
    def update_validation_state(ctx: InvocationContext, phase: str, status: str):
        """Update validation state for tracking."""
        validation_history = ctx.session.state.get('validation_history', [])
        validation_history.append({
            'phase': phase,
            'status': status,
            'timestamp': str(Path.ctime(Path.cwd())),
            'iteration': ctx.session.state.get('current_iteration', 0)
        })
        ctx.session.state['validation_history'] = validation_history
    
    @staticmethod
    def get_latest_artifact(ctx: InvocationContext, artifact_type: str) -> str:
        """Get the latest artifact path of a given type."""
        task_id = ctx.session.state.get('task_id', Config.TASK_ID)
        outputs_dir = Config.get_outputs_dir(task_id)
        
        # Map artifact types to paths
        artifact_patterns = {
            'research_plan': f"{outputs_dir}/planning/research_plan_v*.md",
            'implementation_manifest': f"{outputs_dir}/implementation/manifest.json",
            'code': f"{outputs_dir}/code/*.py",
            'experiment_journal': f"{outputs_dir}/experiments/journal.md",
            'results': f"{outputs_dir}/results/final_analysis.json"
        }
        
        pattern = artifact_patterns.get(artifact_type, "")
        if pattern:
            files = list(Path(outputs_dir).glob(pattern.split('/')[-1]))
            if files:
                return str(max(files, key=lambda f: f.stat().st_mtime))
        return ""

# Enhanced Validation Loop Builder
def create_validation_loop(agent_to_validate: BaseAgent, loop_name: str, validation_type: str = "research_plan") -> SequentialAgent:
    """Create a validation loop with proper state management."""
    
    class ValidationStateUpdater(BaseAgent):
        """Helper agent to update validation state between iterations."""
        
        def __init__(self, phase_name: str):
            super().__init__(name=f"StateUpdater_{phase_name}")
            self.phase_name = phase_name
        
        async def _run_async_impl(self, ctx: InvocationContext):
            """Update state for next validation iteration."""
            # Increment iteration counter
            current_iter = ctx.session.state.get(f'{self.phase_name}_iteration', 0)
            ctx.session.state[f'{self.phase_name}_iteration'] = current_iter + 1
            
            # Set artifact to validate
            artifact = StateManager.get_latest_artifact(ctx, validation_type)
            ctx.session.state['artifact_to_validate'] = artifact
            ctx.session.state['validation_type'] = validation_type
            
            # Collect previous critiques
            critiques = []
            if ctx.session.state.get(f'junior_critique_{validation_type}'):
                critiques.append(ctx.session.state[f'junior_critique_{validation_type}'])
            if ctx.session.state.get(f'senior_critique_{validation_type}'):
                critiques.append(ctx.session.state[f'senior_critique_{validation_type}'])
            ctx.session.state['previous_critiques'] = critiques
            
            # Update validation history
            StateManager.update_validation_state(ctx, self.phase_name, 'in_progress')
            
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"Updated state for {self.phase_name} iteration {current_iter + 1}")])
            )
    
    # Create the validation sequence with state management
    validation_sequence = SequentialAgent(
        name=f"{loop_name}_ValidationSequence",
        sub_agents=[
            ValidationStateUpdater(loop_name),
            agent_to_validate,
            JuniorValidator(validation_type),
            SeniorValidator(validation_type),
            MetaValidator()
        ]
    )
    
    # Create loop with exit condition
    return LoopAgent(
        name=f"{loop_name}_Loop",
        sub_agents=[validation_sequence],
        max_iterations=Config.MAX_REFINEMENT_LOOPS,
        exit_condition=lambda ctx: ctx.session.state.get('validation_decision') == 'PROCEED'
    )

# Parallel Validation
def create_parallel_validation(agent: BaseAgent) -> ParallelAgent:
    """Create parallel validation with multiple samples."""
    validators = [
        SequentialAgent(
            name=f"ParallelValidator_{i}",
            sub_agents=[JuniorValidator(), SeniorValidator()]
        )
        for i in range(Config.PARALLEL_VALIDATION_SAMPLES)
    ]
    
    return ParallelAgent(
        name="ParallelValidation",
        sub_agents=[agent] + validators
    )

# Main Workflow using Native ADK
class ResearchWorkflow:
    """Complete research workflow using ADK's native orchestration."""
    
    @staticmethod
    def create_workflow() -> BaseAgent:
        """Build the complete multi-agent workflow."""
        
        # Phase 1: Research Planning with validation loop
        planning_phase = SequentialAgent(
            name="PlanningPhase",
            sub_agents=[
                create_validation_loop(ChiefResearcher(), "Planning"),
                create_parallel_validation(ChiefResearcher())
            ]
        )
        
        # Phase 2: Implementation Planning with validation
        implementation_phase = create_validation_loop(Orchestrator(), "Implementation")
        
        # Phase 3: Parallel Coding (dynamically created based on orchestrator output)
        # Note: In real implementation, this would read the manifest and create agents
        coding_phase = ParallelAgent(
            name="CodingPhase",
            sub_agents=[
                create_validation_loop(
                    ParallelCoder("data_pipeline", "Build data ingestion pipeline"),
                    "DataPipeline"
                ),
                create_validation_loop(
                    ParallelCoder("analysis_engine", "Build statistical analysis engine"),
                    "AnalysisEngine"
                ),
                create_validation_loop(
                    ParallelCoder("visualization", "Build visualization components"),
                    "Visualization"
                )
            ]
        )
        
        # Phase 4: Experiment Execution with validation
        execution_phase = create_validation_loop(ExperimentExecutor(), "Execution")
        
        # Phase 5: Results Extraction with validation
        extraction_phase = create_validation_loop(ResultsExtractor(), "Extraction")
        
        # Phase 6: Final Reporting
        reporting_phase = FinalReporter()
        
        # Complete workflow
        return SequentialAgent(
            name="CompleteResearchWorkflow",
            sub_agents=[
                planning_phase,
                implementation_phase,
                coding_phase,
                execution_phase,
                extraction_phase,
                reporting_phase
            ]
        )
    
    @staticmethod
    async def run(task_id: str, task_description: str):
        """Run the complete research workflow."""
        
        # Initialize session service (persistent or in-memory)
        if Config.ENABLE_PERSISTENCE:
            session_service = DatabaseSessionService(
                connection_string="sqlite:///domi_sessions.db"
            )
        else:
            session_service = InMemorySessionService()
        
        # Create workflow
        workflow = ResearchWorkflow.create_workflow()
        
        # Initialize runner with native ADK features
        runner = Runner(
            agent=workflow,
            session_service=session_service,
            artifact_service=None,  # Could add GCS artifact service
            memory_service=None,    # Could add memory service
        )
        
        # Initialize session state
        initial_state = {
            'task_id': task_id,
            'task_description': task_description,
            'plan_version': 0,
            'validation_critiques': []
        }
        
        # Run the workflow
        user_message = types.Content(parts=[types.Part(text=task_description)])
        
        async for event in runner.run_async(
            user_id="researcher",
            session_id=f"research_{task_id}",
            new_message=user_message,
            initial_state=initial_state
        ):
            # Stream events (could be sent to UI)
            if event.content:
                print(f"[{event.author}]: {event.content.parts[0].text[:100]}...")
            
            # The runner handles all state persistence automatically
        
        print(f"Research workflow completed for task: {task_id}")

# Simplified API
async def conduct_research(task_id: str):
    """Simple API to run complete research pipeline."""
    # Load task description
    task_path = Config.TASKS_DIR / f"{task_id}.md"
    task_description = task_path.read_text()
    
    # Run workflow
    await ResearchWorkflow.run(task_id, task_description)

# Example usage
if __name__ == "__main__":
    # Run research with one line
    asyncio.run(conduct_research("sample_research_task"))