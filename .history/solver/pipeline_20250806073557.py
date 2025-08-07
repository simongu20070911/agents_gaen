# solver/pipeline.py

import time
import os
import threading
from typing import Dict, Any, Optional
import requests
import json
import pickle

# Import our custom prompts
from . import prompts

# --- Global Configuration ---
# These should be set as environment variables for security,
# but we can hard-code for this specific project as per the manual.
PROXY_BASE_URL = os.environ.get("PROXY_BASE_URL", "http://127.0.0.1:11434")
PROXY_AUTH_TOKEN = os.environ.get("PROXY_AUTH_TOKEN", "sk-7m-daily-token-1")

print("Configured to use Gemini Balance proxy via requests.")

# --- Global Parallel Timing Tracking ---
_parallel_timing_lock = threading.Lock()
_parallel_start_times = {}
_parallel_first_response_times = {}

# --- End of Output Marker ---
END_OF_OUTPUT_PROMPT = """

### IMPORTANT: Output Completion Marker ###
You MUST end your complete response with the exact text "<end of output>" on a new line.
This marker indicates that your response is complete and not truncated.
Do not include any text after this marker.

Example of a valid ending:
```
...and therefore the answer is 42.

<end of output>
```
"""

END_OF_OUTPUT_MARKER = "<end of output>"


def call_llm(prompt: str, config: Dict[str, Any], call_id: str = None, retry_count: int = 0) -> str:
    """
    A wrapper function to call the specified LLM via the gemini-balance proxy.
    It centralizes model configuration, API calls, and basic error handling.
    Supports both Gemini native and OpenAI-compatible endpoints.

    Args:
        prompt: The fully formatted prompt to send to the LLM.
        config: The global configuration dictionary.
        call_id: Optional identifier for parallel timing analysis.

    Returns:
        The text response from the LLM.
    """
    # --- Load all configurations ---
    model_name = config['model_name']
    temperature = float(config['temperature'])
    max_retries = config['max_retries']
    thinking_budget = config.get('thinking_budget', 0)
    endpoint_type = config.get('endpoint_type', 'gemini')  # Default to gemini
    oai_streaming = config.get('oai_streaming', True)  # Default to streaming for OAI
    
    # Track parallel timing if call_id provided
    if call_id:
        with _parallel_timing_lock:
            _parallel_start_times[call_id] = time.time()
            print(f"[{time.time():.3f}] {call_id}: CALL STARTED")
    
    # Append end of output prompt to ensure complete responses
    full_prompt = prompt + END_OF_OUTPUT_PROMPT
    
    print(f"--- Calling LIVE LLM ({model_name}) via {endpoint_type} endpoint ---")
    print(f"Prompt length: {len(full_prompt)} chars")
    if retry_count > 0:
        print(f"Retry attempt {retry_count} due to missing end marker")
    if thinking_budget > 0:
        print(f"Requesting thinking_budget: {thinking_budget}")
    if endpoint_type == 'openai' and oai_streaming:
        print("Using streaming mode")
    
    # Set timeout based on thinking budget
    timeout = 300 if thinking_budget > 0 else 60
    
    # --- REAL API CALL LOOP ---
    streaming_failures = 0
    STREAMING_RETRY_THRESHOLD = 5  # After this many streaming failures, try non-streaming
    
    for attempt in range(max_retries):
        try:
            if endpoint_type == 'openai':
                # Use OpenAI-compatible endpoint
                # Decide whether to use streaming based on failure count
                use_streaming = oai_streaming and (streaming_failures < STREAMING_RETRY_THRESHOLD)
                
                if not use_streaming and oai_streaming:
                    print(f"Falling back to non-streaming mode after {streaming_failures} streaming failures")
                
                show_window = config.get('show_streaming_window', True) if use_streaming else False
                window_size = config.get('streaming_window_size', 250)
                response_text = _call_openai_endpoint(full_prompt, model_name, temperature, thinking_budget, 
                                                    use_streaming, show_window, window_size, call_id)
            else:
                # Use Gemini native endpoint
                response_text = _call_gemini_endpoint(full_prompt, model_name, temperature, thinking_budget, timeout)
            
            if response_text:
                # Debug: Check if response is just echoing the prompt
                if response_text.strip().startswith("### Core Instructions ###"):
                    print(f"ERROR: LLM response appears to be echoing the prompt!")
                    print(f"Response length: {len(response_text)} chars")
                    print(f"First 200 chars: {response_text[:200]}...")
                    raise ValueError("LLM is echoing the prompt instead of generating a response")
                
                # Check if response contains end of output marker
                if END_OF_OUTPUT_MARKER in response_text:
                    # Remove the marker and any trailing whitespace
                    response_text = response_text.split(END_OF_OUTPUT_MARKER)[0].rstrip()
                    return response_text
                else:
                    print(f"Warning: Response missing '{END_OF_OUTPUT_MARKER}' marker. Response may be incomplete.")
                    
                    # Check if we should retry
                    max_marker_retries = config.get('max_marker_retries', 2)
                    if retry_count < max_marker_retries:
                        print(f"Retrying to get complete response...")
                        return call_llm(prompt, config, call_id, retry_count + 1)
                    else:
                        print(f"Max retries ({max_marker_retries}) reached for end marker. Proceeding with potentially incomplete response.")
                        return response_text
            else:
                print(f"Warning: LLM returned an empty response on attempt {attempt + 1}.")
                raise ValueError("LLM returned empty response.")
                
        except Exception as e:
            error_str = str(e)
            
            # Check if this is a streaming-specific failure
            if "No content collected from streaming response" in error_str:
                streaming_failures += 1
                print(f"Streaming failure #{streaming_failures}: {e}")
            else:
                print(f"LLM API call failed on attempt {attempt + 1}/{max_retries}: {e}")
            
            if attempt + 1 == max_retries:
                raise
            time.sleep(5)
    
    raise Exception("LLM call failed after all retries.")


def _call_gemini_endpoint(prompt: str, model_name: str, temperature: float, thinking_budget: int, timeout: int) -> str:
    """Call the Gemini native endpoint (/v1beta)"""
    url = f"{PROXY_BASE_URL}/v1beta/models/{model_name}:generateContent"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": temperature
        }
    }
    
    # Add thinking_config at top level if specified
    if thinking_budget > 0:
        payload["thinking_config"] = {
            "thinking_budget": thinking_budget
        }
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": PROXY_AUTH_TOKEN
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()
    
    # Parse the response - extract all non-thinking text parts
    result = response.json()
    if 'candidates' in result and len(result['candidates']) > 0:
        candidate = result['candidates'][0]
        if 'content' in candidate and 'parts' in candidate['content']:
            # Concatenate all non-thinking text parts
            response_text = ""
            for part in candidate['content']['parts']:
                if 'text' in part and not part.get('thought', False):
                    response_text += part['text']
            return response_text
    
    raise ValueError("No valid response in Gemini endpoint result")


def _call_openai_endpoint(prompt: str, model_name: str, temperature: float, thinking_budget: int, 
                         streaming: bool = True, show_window: bool = True, window_size: int = 250, call_id: str = None) -> str:
    """Call the OpenAI-compatible endpoint (/v1/chat/completions) with optional streaming"""
    url = f"{PROXY_BASE_URL}/v1/chat/completions"
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "stream": streaming
    }
    
    # Add thinking configuration
    if thinking_budget > 0:
        # Use extra_body method for explicit budget control
        payload["extra_body"] = {
            "google": {
                "thinking_config": {
                    "thinking_budget": thinking_budget
                }
            }
        }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PROXY_AUTH_TOKEN}"
    }
    
    # Longer timeout for thinking (streaming helps prevent timeouts)
    timeout = 600 if thinking_budget > 0 else 120
    
    if streaming:
        # Handle streaming response
        return _handle_streaming_response(url, payload, headers, timeout, show_window, window_size, call_id)
    else:
        # Handle non-streaming response
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse the response - extract just the content (not reasoning_content)
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            message = result['choices'][0]['message']
            if 'content' in message:
                return message['content']
        
        raise ValueError("No valid response in OpenAI endpoint result")


def _handle_streaming_response(url: str, payload: dict, headers: dict, timeout: int, 
                             show_window: bool = True, window_size: int = 250, call_id: str = None) -> str:
    """Handle SSE streaming response from OpenAI endpoint with optional live display"""
    import json
    import sys
    
    # Make the request with streaming
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Streaming request failed: {e}")
        raise
    
    collected_content = []
    collected_reasoning = []
    chunks_received = 0
    first_chunk_received = False
    
    # For live window display
    window_buffer = ""  # Rolling buffer for display only
    
    def display_window(new_text: str, window_size: int):
        """Display a rolling window of the streaming text"""
        nonlocal window_buffer
        
        # Add new text to buffer
        window_buffer += new_text
        
        # Keep only the last window_size characters
        if len(window_buffer) > window_size:
            window_buffer = window_buffer[-window_size:]
        
        # Clean for display - remove newlines
        display_text = window_buffer.replace('\n', ' ').replace('\r', ' ')
        
        # Pad to consistent width
        display_text = display_text.ljust(window_size)
        
        # Move cursor to beginning of line and print
        sys.stdout.write('\r[Streaming] ' + display_text)
        sys.stdout.flush()
    
    try:
        # Process the SSE stream
        line_count = 0
        last_chunk_time = time.time()
        stream_timeout = 30  # 30 seconds timeout between chunks
        
        for line in response.iter_lines(decode_unicode=True, chunk_size=1024):
            line_count += 1
            current_time = time.time()
            
            # Check for timeout between chunks
            if current_time - last_chunk_time > stream_timeout:
                print(f"\nWarning: Stream timeout - no data for {stream_timeout} seconds")
                break
                
            if not line:
                continue
                
            last_chunk_time = current_time
            
            # SSE format: "data: {...}"
            if line.startswith('data: '):
                data_str = line[6:]  # Remove "data: " prefix
                
                # Handle the [DONE] marker
                if data_str == '[DONE]':
                    break
                    
                try:
                    chunk = json.loads(data_str)
                    chunks_received += 1
                    
                    # Extract content from the chunk
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        
                        # Debug: Print first few chunks to understand structure
                        if chunks_received <= 5:
                            print(f"DEBUG Chunk {chunks_received}: {chunk}")
                            
                        # Check for early termination
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            finish_reason = chunk['choices'][0].get('finish_reason')
                            if finish_reason:
                                print(f"Stream finished with reason: {finish_reason}")
                                break
                        
                        # Track first chunk for parallel timing (content OR reasoning)
                        if not first_chunk_received and call_id:
                            if ('content' in delta and delta['content']) or ('reasoning_content' in delta and delta['reasoning_content']):
                                with _parallel_timing_lock:
                                    _parallel_first_response_times[call_id] = time.time()
                                    print(f"[{time.time():.3f}] {call_id}: FIRST CHUNK RECEIVED")
                                first_chunk_received = True
                        
                        # Collect content (not reasoning_content)
                        if 'content' in delta:
                            content_chunk = delta['content']
                            if content_chunk:  # Only append non-empty chunks
                                collected_content.append(content_chunk)
                                if show_window:
                                    # Pass only the new chunk to display_window
                                    display_window(content_chunk, window_size)
                        
                        # Note: reasoning_content might come in delta too
                        if 'reasoning_content' in delta:
                            reasoning_chunk = delta['reasoning_content']
                            if reasoning_chunk:  # Only append non-empty chunks
                                collected_reasoning.append(reasoning_chunk)
                                if show_window:
                                    # Pass only the new chunk to display_window
                                    display_window(reasoning_chunk, window_size)
                        
                        # Print progress every 100 chunks (only if not showing window)
                        if not show_window and chunks_received % 100 == 0:
                            # Extract sample number from call_id if available
                            if call_id and 'sample_' in call_id:
                                sample_num = call_id.split('_')[1]
                                print(f"   -> Receiving answer tokens of sample {sample_num} ({chunks_received} chunks received)")
                            else:
                                print(f"   -> Streaming... ({chunks_received} chunks received)")
                            
                except json.JSONDecodeError:
                    # Skip malformed chunks
                    continue
                    
    except requests.exceptions.ChunkedEncodingError as e:
        # Common issue with streaming - connection dropped
        print(f"Warning: Stream interrupted after {chunks_received} chunks, {line_count} lines: {e}")
        # Try to return what we have so far
        
    except Exception as e:
        print(f"Error during streaming after {chunks_received} chunks, {line_count} lines: {e}")
        # Try to return partial content if available
    
    # Clear the streaming window if it was shown
    if show_window and window_buffer:
        # Clear the line completely
        sys.stdout.write('\r' + ' ' * (window_size + 20) + '\r')
        sys.stdout.flush()
        # Print a newline to move to the next line for subsequent output
        print()
    
    # Join all collected content
    final_content = ''.join(collected_content)
    
    if final_content:
        # Print stats (ensuring we're on a new line)
        if collected_reasoning:
            reasoning_text = ''.join(collected_reasoning)
            print(f"   -> Streamed response complete: {len(final_content)} chars (+ {len(reasoning_text)} reasoning chars)")
        else:
            print(f"   -> Streamed response complete: {len(final_content)} chars")
        return final_content
    else:
        # If streaming failed, provide more detailed error info
        error_msg = f"No content collected from streaming response (received {chunks_received} chunks)"
        if chunks_received > 0:
            error_msg += f"\nFirst chunk received: {first_chunk_received}"
            error_msg += f"\nCollected content pieces: {len(collected_content)}"
            error_msg += f"\nCollected reasoning pieces: {len(collected_reasoning)}"
            error_msg += f"\nTotal lines processed: {line_count}"
            
            # Special case: if we got exactly 1 chunk, it might be a complete response
            if chunks_received == 1 and line_count > 0:
                error_msg += "\nNote: Received only 1 chunk - possible complete response in single chunk or connection issue"
        raise ValueError(error_msg)


def save_checkpoint(checkpoint_data: Dict[str, Any], problem_id: str, output_dir: str):
    """Save checkpoint data to allow resuming from interrupted state."""
    checkpoint_path = os.path.join(output_dir, f"{problem_id}_checkpoint.pkl")
    with open(checkpoint_path, 'wb') as f:
        pickle.dump(checkpoint_data, f)
    print(f"Checkpoint saved to: {checkpoint_path}")


def load_checkpoint(problem_id: str, output_dir: str) -> Optional[Dict[str, Any]]:
    """Load checkpoint data if it exists."""
    checkpoint_path = os.path.join(output_dir, f"{problem_id}_checkpoint.pkl")
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'rb') as f:
            checkpoint_data = pickle.load(f)
        print(f"Checkpoint loaded from: {checkpoint_path}")
        return checkpoint_data
    return None


def recreate_checkpoint_from_outputs(problem_id: str, output_dir: str) -> Optional[Dict[str, Any]]:
    """Recreate a checkpoint from existing output files for continuation."""
    # Check if we have a final accepted solution
    final_solution_path = os.path.join(output_dir, "07_FINAL_ACCEPTED_SOLUTION.md")
    if not os.path.exists(final_solution_path):
        return None
    
    print(f"Found completed solution for {problem_id}. Creating checkpoint for continuation...")
    
    # Read the final solution
    with open(final_solution_path, 'r', encoding='utf-8') as f:
        final_solution = f.read()
    
    # Count initial solutions
    initial_solutions = []
    for i in range(1, 10000):  # Check up to 10000 samples to handle large runs
        sample_path = os.path.join(output_dir, f"01_initial_solution_sample_{i}.md")
        if os.path.exists(sample_path):
            with open(sample_path, 'r', encoding='utf-8') as f:
                initial_solutions.append((i-1, f.read()))
        else:
            break
    
    # Count correction iterations
    global_iteration_count = 0
    for i in range(1, 1000):  # Check up to 1000 iterations
        iter_path = os.path.join(output_dir, f"05_corrected_solution_iter_{i}.md")
        if os.path.exists(iter_path):
            global_iteration_count = i
        else:
            break
    
    # Create checkpoint for continuation
    checkpoint = {
        'stage': 'completed_continuation',
        'initial_solutions': initial_solutions,
        'current_solution': final_solution,
        'problem_id': problem_id,
        'global_iteration_count': global_iteration_count,
        'final_check_retry_count': 0,
        'loop_iteration': 0,
        'was_previously_accepted': True
    }
    
    # Save the recreated checkpoint
    save_checkpoint(checkpoint, problem_id, output_dir)
    
    return checkpoint


def delete_checkpoint(problem_id: str, output_dir: str):
    """Delete checkpoint file after successful completion."""
    checkpoint_path = os.path.join(output_dir, f"{problem_id}_checkpoint.pkl")
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        print(f"Checkpoint deleted: {checkpoint_path}")


def analyze_parallel_timing():
    """Analyze timing results to determine if calls were truly parallel"""
    with _parallel_timing_lock:
        if len(_parallel_start_times) < 2:
            return
            
        print("\n=== PARALLEL TIMING ANALYSIS ===")
        
        # Sort by call_id for consistent output
        sorted_calls = sorted(_parallel_start_times.keys())
        
        print("Start times:")
        for call_id in sorted_calls:
            print(f"  {call_id}: {_parallel_start_times[call_id]:.3f}s")
        
        print("\nFirst response times:")
        for call_id in sorted_calls:
            if call_id in _parallel_first_response_times:
                print(f"  {call_id}: {_parallel_first_response_times[call_id]:.3f}s")
        
        # Calculate time differences
        start_diff = max(_parallel_start_times.values()) - min(_parallel_start_times.values())
        print(f"\nStart time spread: {start_diff:.3f}s")
        
        if _parallel_first_response_times:
            response_diff = max(_parallel_first_response_times.values()) - min(_parallel_first_response_times.values())
            print(f"First response spread: {response_diff:.3f}s")
            
            # Determine if truly parallel
            if start_diff < 0.1:  # Started within 100ms
                if response_diff < 2.0:  # First responses within 2s
                    print("\n✅ PARALLEL EXECUTION DETECTED")
                    print("Calls started nearly simultaneously and received responses in overlapping timeframes")
                else:
                    print("\n⚠️  SEQUENTIAL PROCESSING SUSPECTED")
                    print("Calls started together but responses were staggered significantly")
            else:
                print("\n❌ SEQUENTIAL EXECUTION")
                print("Calls were not started simultaneously")
        
        # Clear timing data for next analysis
        _parallel_start_times.clear()
        _parallel_first_response_times.clear()


def step1_generate_initial(problem_statement: str, config: Dict[str, Any], call_id: str = None) -> str:
    """
    Performs Step 1 of the pipeline: Initial solution generation.

    Args:
        problem_statement: The string of the problem.
        config: The global configuration dictionary.
        call_id: Optional identifier for parallel timing analysis.

    Returns:
        A single solution attempt as a string.
    """
    print("\n--- STEP 1: GENERATING INITIAL SOLUTION ---")
    prompt = prompts.GENERATOR_PROMPT_TEMPLATE.format(
        problem_statement=problem_statement
    )
    solution = call_llm(prompt, config, call_id)
    return solution


def step2_self_improve(problem_statement: str, incomplete_solution: str, config: Dict[str, Any]) -> str:
    """
    Performs Step 2 of the pipeline: Self-improvement on an incomplete solution.

    Args:
        problem_statement: The string of the problem.
        incomplete_solution: The text of the incomplete solution from Step 1.
        config: The global configuration dictionary.

    Returns:
        A refined and completed solution string.
    """
    print("\n--- STEP 2: PERFORMING SELF-IMPROVEMENT ---")
    prompt = prompts.SELF_IMPROVEMENT_PROMPT_TEMPLATE.format(
        problem_statement=problem_statement,
        incomplete_solution=incomplete_solution
    )
    refined_solution = call_llm(prompt, config)
    return refined_solution


def step3_verify_solution(problem_statement: str, solution_to_verify: str, config: Dict[str, Any], call_id: str = None) -> str:
    """
    Performs Step 3 of the pipeline: Verification of a solution.

    Args:
        problem_statement: The string of the problem.
        solution_to_verify: The solution text to be checked.
        config: The global configuration dictionary.
        call_id: Optional identifier for parallel timing analysis.

    Returns:
        A bug report string.
    """
    print("\n--- STEP 3: VERIFYING SOLUTION (JUNIOR GRADER) ---")
    prompt = prompts.VERIFIER_PROMPT_TEMPLATE.format(
        problem_statement=problem_statement,
        solution_to_verify=solution_to_verify
    )
    bug_report = call_llm(prompt, config, call_id)
    return bug_report


def step4_meta_verify(problem_statement: str, solution_to_verify: str, bug_report: str, config: Dict[str, Any]) -> str:
    """
    Performs Step 4 of the pipeline: Meta-verification of a bug report.

    Args:
        problem_statement: The string of the problem.
        solution_to_verify: The solution text that was checked.
        bug_report: The raw bug report from the verifier (Step 3).
        config: The global configuration dictionary.

    Returns:
        A curated bug report string, with trivial findings removed.
    """
    print("\n--- STEP 4: META-VERIFYING BUG REPORT (CHIEF GRADER) ---")
    prompt = prompts.META_VERIFIER_PROMPT_TEMPLATE.format(
        problem_statement=problem_statement,
        solution_to_verify=solution_to_verify,
        bug_report=bug_report
    )
    curated_bug_report = call_llm(prompt, config)
    return curated_bug_report


def step5_correct_solution(problem_statement: str, flawed_solution: str, curated_bug_report: str, config: Dict[str, Any]) -> str:
    """
    Performs Step 5 of the pipeline: Correction of a solution based on feedback.

    Args:
        problem_statement: The string of the problem.
        flawed_solution: The solution text that contains errors.
        curated_bug_report: The curated bug report from the meta-verifier (Step 4).
        config: The global configuration dictionary.

    Returns:
        A new, corrected solution string.
    """
    print("\n--- STEP 5: CORRECTING SOLUTION (REVISING AUTHOR) ---")
    prompt = prompts.CORRECTION_PROMPT_TEMPLATE.format(
        problem_statement=problem_statement,
        flawed_solution=flawed_solution,
        bug_report=curated_bug_report
    )
    corrected_solution = call_llm(prompt, config)
    return corrected_solution