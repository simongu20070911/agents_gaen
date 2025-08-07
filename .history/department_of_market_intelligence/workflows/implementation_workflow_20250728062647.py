# /department_of_market_intelligence/workflows/implementation_workflow.py
import json
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from ..agents.orchestrator import get_orchestrator_agent
from ..agents.coder import get_coder_agent
from ..agents.executor import get_experiment_executor_agent
from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, MetaValidatorCheckAgent, get_parallel_final_validation_agent
from .. import config
from ..tools.desktop_commander import desktop_commander_toolset # Need for file reading

class ImplementationWorkflowAgent(BaseAgent):
    """A custom agent to manage the entire implementation and execution phase."""

    def __init__(self, **kwargs):
        # Initialize parent first
        super().__init__(**kwargs)
        
        # Store agent references as private attributes after initialization
        self._orchestrator_planning_loop = None
        self._executor_loop = None
        self._results_extraction_loop = None
        self._coder_validation_loop_template = None

    def _create_validation_loop(self, agent_to_validate: BaseAgent, loop_name: str, max_loops: int = 5) -> SequentialAgent:
        """Helper factory to create a standard refinement/validation loop for an agent with final parallel validation."""
        # Main validation loop
        main_loop = LoopAgent(
            name=loop_name,
            max_iterations=max_loops,
            sub_agents=[
                SequentialAgent(
                    name=f"{agent_to_validate.name}_And_Validate_Seq",
                    sub_agents=[
                        agent_to_validate,
                        get_junior_validator_agent(),
                        get_senior_validator_agent(),
                        MetaValidatorCheckAgent(name=f"{agent_to_validate.name}_MetaCheck")
                    ]
                )
            ]
        )
        
        # Complete workflow with parallel final validation
        return SequentialAgent(
            name=f"{loop_name}_WithParallelValidation",
            sub_agents=[
                main_loop,
                get_parallel_final_validation_agent()
            ]
        )

    async def _execute_tasks_with_dag_parallelism(self, ctx: InvocationContext, tasks: list) -> AsyncGenerator[Event, None]:
        """Execute coding tasks in parallel following DAG dependency constraints."""
        completed_tasks = set()
        tasks_by_id = {task['task_id']: task for task in tasks}
        
        # Continue until all tasks are completed
        while len(completed_tasks) < len(tasks):
            # Find tasks ready to run (dependencies satisfied)
            ready_tasks = []
            for task in tasks:
                task_id = task['task_id']
                if task_id not in completed_tasks:
                    dependencies = set(task.get('dependencies', []))
                    if dependencies.issubset(completed_tasks):
                        ready_tasks.append(task)
            
            if not ready_tasks:
                # Circular dependency or error - break to avoid infinite loop
                remaining = [t['task_id'] for t in tasks if t['task_id'] not in completed_tasks]
                print(f"IMPLEMENTATION WORKFLOW: Warning - No ready tasks found. Remaining: {remaining}")
                break
            
            print(f"IMPLEMENTATION WORKFLOW: Executing {len(ready_tasks)} tasks in parallel: {[t['task_id'] for t in ready_tasks]}")
            
            if len(ready_tasks) == 1:
                # Single task - run directly without ParallelAgent overhead
                task = ready_tasks[0]
                print(f"  - Starting coding task: {task['task_id']}")
                async for event in self._execute_single_coding_task(ctx, task):
                    yield event
                completed_tasks.add(task['task_id'])
                print(f"  - Completed coding task: {task['task_id']}")
            else:
                # Multiple tasks - use ParallelAgent for true concurrency
                async for event in self._execute_parallel_coding_tasks(ctx, ready_tasks):
                    yield event
                for task in ready_tasks:
                    completed_tasks.add(task['task_id'])
                    print(f"  - Completed coding task: {task['task_id']}")

    async def _execute_single_coding_task(self, ctx: InvocationContext, task: dict) -> AsyncGenerator[Event, None]:
        """Execute a single coding task with validation."""
        # Set task-specific state
        original_subtask = ctx.session.state.get('coder_subtask')
        original_artifact = ctx.session.state.get('artifact_to_validate')
        original_version = ctx.session.state.get('validation_version')
        
        try:
            ctx.session.state['coder_subtask'] = task
            ctx.session.state['artifact_to_validate'] = f"coder_output_{task['task_id']}"
            ctx.session.state['validation_version'] = 0
            
            async for event in self._coder_validation_loop_template.run_async(ctx):
                yield event
        finally:
            # Restore original state
            if original_subtask is not None:
                ctx.session.state['coder_subtask'] = original_subtask
            if original_artifact is not None:
                ctx.session.state['artifact_to_validate'] = original_artifact
            if original_version is not None:
                ctx.session.state['validation_version'] = original_version

    async def _execute_parallel_coding_tasks(self, ctx: InvocationContext, tasks: list) -> AsyncGenerator[Event, None]:
        """Execute multiple coding tasks in parallel using ParallelAgent."""
        # Create task-specific coder agents for parallel execution
        parallel_coders = []
        
        for task in tasks:
            # Create a specialized coder agent for this specific task
            task_coder = self._create_task_specific_coder_agent(task)
            parallel_coders.append(task_coder)
        
        # Create and execute ParallelAgent
        parallel_execution = ParallelAgent(
            name=f"ParallelCoders_{len(tasks)}Tasks",
            sub_agents=parallel_coders
        )
        
        print(f"  - Starting {len(tasks)} parallel coding tasks: {[t['task_id'] for t in tasks]}")
        async for event in parallel_execution.run_async(ctx):
            yield event

    def _create_task_specific_coder_agent(self, task: dict) -> BaseAgent:
        """Create a task-specific coder agent that handles its own state management."""
        from ..agents.coder import get_coder_agent
        from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, MetaValidatorCheckAgent
        
        # Create a custom agent that manages task-specific state
        class TaskSpecificCoderAgent(BaseAgent):
            def __init__(self, task_data: dict):
                super().__init__(name=f"Coder_{task_data['task_id']}")
                # Store task data as private attribute to avoid Pydantic validation
                self._task_data = task_data
                self._validation_loop = None
            
            async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
                if self._validation_loop is None:
                    # Main coder validation loop
                    main_loop = LoopAgent(
                        name=f"CoderValidationLoop_{self._task_data['task_id']}",
                        max_iterations=config.MAX_CODE_REFINEMENT_LOOPS,
                        sub_agents=[
                            SequentialAgent(
                                name=f"Coder_{self._task_data['task_id']}_And_Validate_Seq",
                                sub_agents=[
                                    get_coder_agent(),
                                    get_junior_validator_agent(),
                                    get_senior_validator_agent(),
                                    MetaValidatorCheckAgent(name=f"Coder_{self._task_data['task_id']}_MetaCheck")
                                ]
                            )
                        ]
                    )
                    
                    # Complete workflow with parallel final validation
                    self._validation_loop = SequentialAgent(
                        name=f"CoderValidation_{self._task_data['task_id']}_WithParallelValidation",
                        sub_agents=[
                            main_loop,
                            get_parallel_final_validation_agent()
                        ]
                    )
                
                # Set task-specific state in a safe way
                original_subtask = ctx.session.state.get('coder_subtask')
                original_artifact = ctx.session.state.get('artifact_to_validate')
                original_version = ctx.session.state.get('validation_version')
                
                try:
                    # Set this task's context
                    ctx.session.state['coder_subtask'] = self._task_data
                    ctx.session.state['artifact_to_validate'] = f"coder_output_{self._task_data['task_id']}"
                    ctx.session.state['validation_version'] = 0
                    
                    # Execute the coding and validation loop
                    async for event in self._validation_loop.run_async(ctx):
                        yield event
                        
                finally:
                    # Restore original state to avoid interference
                    if original_subtask is not None:
                        ctx.session.state['coder_subtask'] = original_subtask
                    if original_artifact is not None:
                        ctx.session.state['artifact_to_validate'] = original_artifact
                    if original_version is not None:
                        ctx.session.state['validation_version'] = original_version
        
        return TaskSpecificCoderAgent(task)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Create agents lazily on first use
        if self._orchestrator_planning_loop is None:
            self._orchestrator_planning_loop = self._create_validation_loop(
                agent_to_validate=get_orchestrator_agent(),
                loop_name="OrchestratorPlanningLoop"
            )
            self._executor_loop = self._create_validation_loop(
                agent_to_validate=get_experiment_executor_agent(),
                loop_name="ExecutorValidationLoop"
            )
            self._results_extraction_loop = self._create_validation_loop(
                agent_to_validate=get_orchestrator_agent(),
                loop_name="ResultsExtractionLoop"
            )
            self._coder_validation_loop_template = self._create_validation_loop(
                agent_to_validate=get_coder_agent(),
                loop_name="CoderValidationLoop",
                max_loops=config.MAX_CODE_REFINEMENT_LOOPS
            )
        
        # 1. Orchestrator generates the implementation manifest
        print("IMPLEMENTATION WORKFLOW: Orchestrator is generating the implementation plan...")
        ctx.session.state['artifact_to_validate'] = ctx.session.state['plan_artifact_name']
        ctx.session.state['validation_version'] = 0
        async for event in self._orchestrator_planning_loop.run_async(ctx):
            yield event
        print("IMPLEMENTATION WORKFLOW: Implementation plan approved.")

        # 2. Read the manifest to set up parallel coding
        manifest_path = ctx.session.state['implementation_manifest_artifact']
        
        if config.DRY_RUN_MODE:
            # Mock manifest content for dry run - complex DAG for testing
            print(f"[DRY RUN] Would read manifest from {manifest_path}")
            # PROPERLY PARALLELIZED tasks demonstrating quantitative research workflow
            tasks = [
                # Parallel Data Fetching (no dependencies - all can run simultaneously)
                {"task_id": "market_data_fetch", "description": "Fetch OHLCV market data", "dependencies": [], "parallel_group": 1},
                {"task_id": "alt_data_fetch", "description": "Fetch alternative/sentiment data", "dependencies": [], "parallel_group": 1},
                {"task_id": "fundamental_data_fetch", "description": "Fetch fundamental/macro data", "dependencies": [], "parallel_group": 1},
                {"task_id": "reference_data_fetch", "description": "Fetch security reference data", "dependencies": [], "parallel_group": 1},
                
                # Parallel Data Validation & Cleaning (each depends only on its own fetch)
                {"task_id": "market_data_clean", "description": "Clean and validate market data", "dependencies": ["market_data_fetch"], "parallel_group": 2},
                {"task_id": "alt_data_clean", "description": "Clean and validate alt data", "dependencies": ["alt_data_fetch"], "parallel_group": 2},
                {"task_id": "fundamental_data_clean", "description": "Clean fundamental data", "dependencies": ["fundamental_data_fetch"], "parallel_group": 2},
                {"task_id": "reference_data_clean", "description": "Process reference data", "dependencies": ["reference_data_fetch"], "parallel_group": 2},
                
                # Parallel Feature Engineering (independent feature sets)
                {"task_id": "technical_features", "description": "Technical indicators (RSI, MACD, etc)", "dependencies": ["market_data_clean"], "parallel_group": 3},
                {"task_id": "microstructure_features", "description": "Market microstructure features", "dependencies": ["market_data_clean"], "parallel_group": 3},
                {"task_id": "sentiment_features", "description": "Sentiment and NLP features", "dependencies": ["alt_data_clean"], "parallel_group": 3},
                {"task_id": "fundamental_features", "description": "Fundamental ratios and factors", "dependencies": ["fundamental_data_clean"], "parallel_group": 3},
                {"task_id": "cross_sectional_features", "description": "Cross-sectional features", "dependencies": ["market_data_clean", "reference_data_clean"], "parallel_group": 3},
                
                # Feature Assembly - Convergence Point
                {"task_id": "feature_matrix_assembly", "description": "Assemble all features with alignment", 
                 "dependencies": ["technical_features", "microstructure_features", "sentiment_features", "fundamental_features", "cross_sectional_features"],
                 "stitching_point": {"merge_strategy": "datetime_align", "alignment_keys": ["timestamp", "symbol"]}},
                
                # Parallel Statistical Analysis (can run alongside feature assembly)
                {"task_id": "univariate_analysis", "description": "Univariate statistics", "dependencies": ["market_data_clean"], "parallel_group": 4},
                {"task_id": "correlation_analysis", "description": "Correlation matrices", "dependencies": ["market_data_clean"], "parallel_group": 4},
                {"task_id": "regime_analysis", "description": "Market regime detection", "dependencies": ["market_data_clean"], "parallel_group": 4},
                
                # Parallel Model Training (all use same feature matrix)
                {"task_id": "model_linear", "description": "Linear models (Ridge, Lasso)", "dependencies": ["feature_matrix_assembly"], "parallel_group": 5},
                {"task_id": "model_tree", "description": "Tree models (RF, XGBoost)", "dependencies": ["feature_matrix_assembly"], "parallel_group": 5},
                {"task_id": "model_neural", "description": "Neural networks", "dependencies": ["feature_matrix_assembly"], "parallel_group": 5},
                {"task_id": "model_ensemble", "description": "Ensemble methods", "dependencies": ["feature_matrix_assembly"], "parallel_group": 5},
                
                # Parallel Backtesting & Analysis (all models tested independently)
                {"task_id": "backtest_linear", "description": "Backtest linear models", "dependencies": ["model_linear"], "parallel_group": 6},
                {"task_id": "backtest_tree", "description": "Backtest tree models", "dependencies": ["model_tree"], "parallel_group": 6},
                {"task_id": "backtest_neural", "description": "Backtest neural models", "dependencies": ["model_neural"], "parallel_group": 6},
                {"task_id": "backtest_ensemble", "description": "Backtest ensemble", "dependencies": ["model_ensemble"], "parallel_group": 6},
                
                # Parallel Risk & Performance Analysis
                {"task_id": "performance_attribution", "description": "Performance attribution", "dependencies": ["backtest_linear", "backtest_tree", "backtest_neural", "backtest_ensemble"], "parallel_group": 7},
                {"task_id": "risk_metrics", "description": "Risk metrics calculation", "dependencies": ["backtest_linear", "backtest_tree", "backtest_neural", "backtest_ensemble"], "parallel_group": 7},
                {"task_id": "factor_analysis", "description": "Factor exposure analysis", "dependencies": ["backtest_linear", "backtest_tree", "backtest_neural", "backtest_ensemble"], "parallel_group": 7},
                
                # Visualization (can run in parallel with analysis)
                {"task_id": "performance_charts", "description": "Performance visualizations", "dependencies": ["backtest_linear", "backtest_tree", "backtest_neural", "backtest_ensemble"], "parallel_group": 8},
                {"task_id": "risk_charts", "description": "Risk visualizations", "dependencies": ["risk_metrics"], "parallel_group": 8},
                {"task_id": "feature_importance_viz", "description": "Feature importance plots", "dependencies": ["model_linear", "model_tree", "model_neural"], "parallel_group": 8},
                
                # Final Aggregation
                {"task_id": "results_aggregation", "description": "Aggregate all results and generate report", 
                 "dependencies": ["performance_attribution", "risk_metrics", "factor_analysis", "performance_charts", "risk_charts", "feature_importance_viz", 
                                 "univariate_analysis", "correlation_analysis", "regime_analysis"]}
            ]
        else:
            # Use the tool directly within the custom agent to read the file
            # This requires the tool to be available, but we don't add it to this agent's
            # `tools` list for the LLM. We call it programmatically.
            manifest_content_response = await desktop_commander_toolset.get_tools()[0].run_async(
                args={'path': manifest_path}, tool_context=None
            )
            tasks = json.loads(manifest_content_response['content'])
        
        # 3. Execute coding tasks in parallel with DAG dependency resolution
        print(f"IMPLEMENTATION WORKFLOW: Starting parallel coding phase for {len(tasks)} tasks...")
        async for event in self._execute_tasks_with_dag_parallelism(ctx, tasks):
            yield event
        print("IMPLEMENTATION WORKFLOW: All coding tasks complete.")

        # 4. Execute the experiments
        print("IMPLEMENTATION WORKFLOW: Executor is running the experiments...")
        ctx.session.state['artifact_to_validate'] = ctx.session.state['implementation_manifest_artifact']
        ctx.session.state['validation_version'] = 0
        async for event in self._executor_loop.run_async(ctx):
            yield event
        
        # Check if execution failed critically after validation
        if ctx.session.state.get('execution_status') == 'critical_error':
            print("IMPLEMENTATION WORKFLOW: Critical execution error confirmed by validators. Aborting for replanning.")
            return  # Exit early to trigger replanning at root level
        
        print("IMPLEMENTATION WORKFLOW: Experiment execution validated.")

        # 5. Orchestrator generates the results extraction script
        print("IMPLEMENTATION WORKFLOW: Orchestrator is planning results extraction...")
        ctx.session.state['current_task'] = 'generate_results_extraction_plan'
        ctx.session.state['artifact_to_validate'] = ctx.session.state['implementation_manifest_artifact']
        ctx.session.state['validation_version'] = 0
        async for event in self._results_extraction_loop.run_async(ctx):
            yield event
        print("IMPLEMENTATION WORKFLOW: Results extraction plan approved.")

        # 6. Execute the results extraction script
        print("IMPLEMENTATION WORKFLOW: Executing results extraction script...")
        extraction_script_path = ctx.session.state['results_extraction_script_artifact']
        # Use the executor agent one last time to run the final script
        ctx.session.state['execution_status'] = 'pending' # Reset status
        # We can reuse the executor agent directly here
        async for event in get_experiment_executor_agent().run_async(ctx):
             # This is a simplified call; the executor's prompt would need to handle this specific task
             yield event
        
        # The final results are now in an artifact, ready for the Chief Researcher
        # The root workflow will handle the final reporting step.