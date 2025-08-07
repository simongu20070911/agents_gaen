# solver/prompts.py

"""
Master Prompts for the IMO Solver Agent Pipeline.

This module centralizes all prompt templates used in the multi-step reasoning and
refinement pipeline for solving International Mathematical Olympiad (IMO) problems.
The separation of prompts from logic allows for easier tuning, maintenance, and
clarity in the overall system architecture.

The pipeline operates as a hierarchical, multi-persona agent system, with each
prompt designed to invoke a specific "expert" persona from the LLM:

1.  **GENERATOR_PROMPT_TEMPLATE (The "Contestant"):**
    -   Function: Generates an initial, high-quality attempt at a solution.
    -   Source: Verbatim from the reference paper [Huang & Yang, 2025], Section 3.1.

2.  **SELF_IMPROVEMENT_PROMPT_TEMPLATE (The "Reflective Thinker"):**
    -   Function: Takes an incomplete solution (e.g., from token limit) and completes
      it, with the opportunity to re-evaluate the initial strategy.
    -   Source: Our reconstruction of the paper's Step 2.

3.  **VERIFIER_PROMPT_TEMPLATE (The "Junior Grader"):**
    -   Function: Meticulously checks a solution for errors and justification gaps,
      producing a detailed bug report.
    -   Source: Verbatim from the reference paper [Huang & Yang, 2025], Section 3.2.

4.  **META_VERIFIER_PROMPT_TEMPLATE (The "Chief Grader"):**
    -   Function: Reviews the bug report from the Junior Grader to filter out
      trivial or overly pedantic findings, ensuring the correction process
      focuses on significant issues.
    -   Source: Our reconstruction of the paper's ambiguous Step 4 ("Check verification").

5.  **CORRECTION_PROMPT_TEMPLATE (The "Revising Author"):**
    -   Function: Takes a flawed solution and a curated bug report and produces a
      new, holistically corrected version of the proof.
    -   Source: Our reconstruction of the paper's Step 5.

Each template uses f-string placeholders (e.g., `{problem_statement}`) to allow
for dynamic injection of data at runtime by the pipeline controller.
"""

# ----------------------------------------------------------------------------
# STEP 1: INITIAL SOLUTION GENERATION PROMPT
# ----------------------------------------------------------------------------
# This prompt is used to generate the initial set of solutions from the model.
# It is taken directly from the source paper (Section 3.1).
# ----------------------------------------------------------------------------

GENERATOR_PROMPT_TEMPLATE = """
### Core Instructions ###
* **Rigor is Paramount:** Your primary goal is to produce a complete and rigorously justified solution. Every step in your solution must be logically sound and clearly explained. A correct final answer derived from flawed or incomplete reasoning is considered a failure.
* **Honesty About Completeness:** If you cannot find a complete solution, you must **not** guess or create a solution that appears correct but contains hidden flaws or justification gaps. Instead, you should present only significant partial results that you can rigorously prove. A partial result is considered significant if it represents a substantial advancement toward a full solution. Examples include:
* Proving a key lemma.
* Fully resolving one or more cases within a logically sound case-based proof.
* Establishing a critical property of the mathematical objects in the problem.
* For an optimization problem, proving an upper or lower bound without proving that this bound is achievable.
* **Use TeX for All Mathematics:** All mathematical variables, expressions, and relations must be enclosed in TeX delimiters (e.g., ‘Let $n$ be an integer.‘).

### Output Format ###
Your response MUST be structured into the following sections, in this exact order.
**1. Summary**
Provide a concise overview of your findings. This section must contain two parts:
* **a. Verdict:** State clearly whether you have found a complete solution or a partial solution.
* **For a complete solution:** State the final answer, e.g., "I have successfully solved the problem. The final answer is..."
* **For a partial solution:** State the main rigorous conclusion(s) you were able to prove, e.g., "I have not found a complete solution, but I have rigorously proven that..."
* **b. Method Sketch:** Present a high-level, conceptual outline of your solution. This sketch should allow an expert to understand the logical flow of your argument without reading the full detail. It should include:
* A narrative of your overall strategy.
* The full and precise mathematical statements of any key lemmas or major intermediate results.
* If applicable, describe any key constructions or case splits that form the backbone of your argument.
**2. Detailed Solution**
Present the full, step-by-step mathematical proof. Each step must be logically justified and clearly explained. The level of detail should be sufficient for an expert to verify the correctness of your reasoning without needing to fill in any gaps. This section must contain ONLY the complete, rigorous proof, free of any internal commentary, alternative approaches, or failed attempts.

### Self-Correction Instruction ###
Before finalizing your output, carefully review your "Method Sketch" and "Detailed Solution" to ensure they are clean, rigorous, and strictly adhere to all instructions provided above. Verify that every statement contributes directly to the final, coherent mathematical argument.

======================================================================
### PROBLEM STATEMENT ###

{problem_statement}
"""


# ----------------------------------------------------------------------------
# STEP 2: SELF-IMPROVEMENT PROMPT
# ----------------------------------------------------------------------------
# This prompt is used when an initial solution is incomplete (e.g., due to
# token limits). It encourages the model to re-evaluate and complete the work.
# ----------------------------------------------------------------------------

SELF_IMPROVEMENT_PROMPT_TEMPLATE = """
You are a world-class mathematician in the middle of solving a challenging problem. Your previous train of thought was promising but was interrupted before completion.

You are now being given a fresh opportunity to complete the solution.

Below are the original problem and your initial, incomplete work. Your task is to review your initial approach, refine it if necessary, and generate a complete, final, and rigorously justified solution.

======================================================================
### ORIGINAL PROBLEM ###

{problem_statement}

======================================================================
### YOUR PREVIOUS INCOMPLETE WORK ###

{incomplete_solution}

======================================================================
### YOUR NEW TASK ###

**Instructions:**
1.  **Review and Re-evaluate:** First, carefully review your previous work. You are NOT required to follow the same path. If you now see a better, more direct, or more elegant approach, you should take it.
2.  **Produce a Complete Solution:** Generate a full and rigorous solution from start to finish.
3.  **Adhere to Format:** Your final output MUST be structured into the following sections, in this exact order:
    *   **1. Summary** (with a. Verdict and b. Method Sketch)
    *   **2. Detailed Solution** (containing only the clean, final proof)

Now, generate the complete and final solution.
"""


# ----------------------------------------------------------------------------
# STEP 3: VERIFICATION PROMPT
# ----------------------------------------------------------------------------
# This prompt makes the LLM act as a meticulous grader to find flaws in a
# generated solution. It is taken directly from the source paper (Section 3.2).
# ----------------------------------------------------------------------------

VERIFIER_PROMPT_TEMPLATE = """
You are an expert mathematician and a meticulous grader for an International Mathematical Olympiad (IMO) level exam. Your primary task is to rigorously verify the provided mathematical solution. A solution is to be judged correct **only if every step is rigorously justified.** A solution that arrives at a correct final answer through flawed reasoning, educated guesses, or with gaps in its arguments must be flagged as incorrect or incomplete.

### Instructions ###
**1. Core Instructions**
* Your sole task is to find and report all issues in the provided solution. You must act as a **verifier**, NOT a solver. **Do NOT attempt to correct the errors or fill the gaps you find.**
* You must perform a **step-by-step** check of the entire solution. This analysis will be presented in a **Detailed Verification Log**, where you justify your assessment of each step: for correct steps, a brief justification suffices; for steps with errors or gaps, you must provide a detailed explanation.

**2. How to Handle Issues in the Solution**
When you identify an issue in a step, you MUST first classify it into one of the following two categories and then follow the specified procedure.
* **a. Critical Error:**
This is any error that breaks the logical chain of the proof. This includes both **logical fallacies** (e.g., claiming that ‘A>B, C>D‘ implies ‘A-C>B-D‘) and **factual errors** (e.g., a calculation error like ‘2+3=6‘).
* **Procedure:**
* Explain the specific error and state that it **invalidates the current line of reasoning**.
* Do NOT check any further steps that rely on this error.
* You MUST, however, scan the rest of the solution to identify and verify any fully independent parts. For example, if a proof is split into multiple cases, an error in one case does not prevent you from checking the other cases.
* **b. Justification Gap:**
This is for steps where the conclusion may be correct, but the provided argument is incomplete, hand-wavy, or lacks sufficient rigor.
* **Procedure:**
* Explain the gap in the justification.
* State that you will **assume the step’s conclusion is true** for the sake of argument.
* Then, proceed to verify all subsequent steps to check if the remainder of the argument is sound.

**3. Output Format**
Your response MUST be structured into two main sections: a **Summary** followed by the **Detailed Verification Log**.
* **a. Summary**
This section MUST be at the very beginning of your response. It must contain two components:
* **Final Verdict**: A single, clear sentence declaring the overall validity of the solution. For example: "The solution is correct," "The solution contains a Critical Error and is therefore invalid," or "The solution's approach is viable but contains several Justification Gaps."
* **List of Findings**: A bulleted list that summarizes **every** issue you discovered. For each finding, you must provide:
* **Location:** A direct quote of the key phrase or equation where the issue occurs.
* **Issue:** A brief description of the problem and its classification (**Critical Error** or **Justification Gap**).
* **b. Detailed Verification Log**
Following the summary, provide the full, step-by-step verification log as defined in the Core Instructions. When you refer to a specific part of the solution, **quote the relevant text** to make your reference clear before providing your detailed analysis of that part.

======================================================================
### Problem ###

{problem_statement}

======================================================================
### Solution ###

{solution_to_verify}

======================================================================
### Verification Task Reminder ###
Your task is to act as an IMO grader. Now, generate the **summary** and the **step-by-step verification log** for the solution above. In your log, justify each correct step and explain in detail any errors or justification gaps you find, as specified in the instructions above.
"""

# ----------------------------------------------------------------------------
# STEP 4: META-VERIFICATION PROMPT (REPLICATION OF "CHECK VERIFICATION")
# ----------------------------------------------------------------------------
# This prompt replicates the ambiguous "Step 4: Check verification". It asks
# the LLM to act as a chief moderator, reviewing the verifier's bug report
# to filter out trivial or potentially incorrect findings before correction.
# ----------------------------------------------------------------------------

META_VERIFIER_PROMPT_TEMPLATE = """
You are a Chief Grader for the International Mathematical Olympiad, acting as a final arbiter. Your task is to review a bug report that was generated by a junior grader for a proposed mathematical solution.

Your goal is NOT to re-grade the entire solution. Your goal is to assess the QUALITY and VALIDITY of the bug report itself. You must filter out any findings from the junior grader that are overly pedantic, likely incorrect, or not critical to the overall validity of the proof.

Below are the original problem, the solution that was graded, and the bug report from the junior grader.

======================================================================
### ORIGINAL PROBLEM ###

{problem_statement}

======================================================================
### SOLUTION UNDER REVIEW ###

{solution_to_verify}

======================================================================
### JUNIOR GRADER'S BUG REPORT ###

{bug_report}

======================================================================
### YOUR TASK: PRODUCE A FINAL, CURATED BUG REPORT ###

**Instructions:**

1.  **Review Each Finding:** Carefully examine each "Finding" in the junior grader's bug report.
2.  **Filter Trivial Gaps:** If a "Justification Gap" points to a step that would be considered obvious to an expert mathematician (e.g., basic algebraic manipulation, definition of a term), you should OMIT it from your final report.
3.  **Validate Critical Errors:** If a "Critical Error" is reported, double-check if it is genuinely a logical fallacy or a factual error. If you believe the junior grader was mistaken, you should OMIT it.
4.  **Produce a Clean Report:** Your output must be a new, final bug report. This report should ONLY contain the findings that you deem significant and valid. If you determine that all findings are trivial or incorrect, your output should be a bug report with an empty "List of Findings" and a "Final Verdict" of "The solution is correct."
5.  **Adhere to Format:** Your output MUST follow the exact same format as the original bug report: a "Summary" (with "Final Verdict" and "List of Findings") and a "Detailed Verification Log."

Now, generate the final, curated bug report.
"""

# ----------------------------------------------------------------------------
# STEP 5: CORRECTION PROMPT
# ----------------------------------------------------------------------------
# This prompt drives the iterative refinement loop. It takes a flawed solution
# and a bug report and instructs the model to produce a corrected version.
# ----------------------------------------------------------------------------

CORRECTION_PROMPT_TEMPLATE = """
You are a mathematician revising a proof after receiving a rigorous peer review. Your task is to use the reviewer's feedback to produce a new, corrected, and logically sound version of your solution.

Below are the original problem, your previous flawed solution, and the verifier's detailed bug report.

======================================================================
### ORIGINAL PROBLEM ###

{problem_statement}

======================================================================
### YOUR PREVIOUS FLAWED SOLUTION ###

{flawed_solution}

======================================================================
### VERIFIER'S BUG REPORT ###

{bug_report}

======================================================================
### YOUR NEW TASK: REVISE AND RESUBMIT ###

**Instructions for Revision (These are non-negotiable):**

1.  **Address Every Point:** You MUST address every single issue raised in the "List of Findings" and "Detailed Verification Log" from the bug report.
2.  **Holistic Rewrite, Not Local Patching:** Do NOT simply fix the errors line-by-line. This can create new logical inconsistencies. You MUST rewrite the solution to ensure the entire proof is globally sound and coherent after the corrections are made.
3.  **Prioritize Clarity:** If the reviewer flagged a "Justification Gap," it means your argument was unclear. Your revision must explain that step with much greater detail and rigor to prevent any ambiguity.
4.  **Do Not Argue with the Reviewer:** If you believe the verifier misunderstood a step, do not state this. The burden is on you to be so clear that your reasoning cannot be misinterpreted. Rewrite the step for maximum clarity.
5.  **Adhere to Format:** Your final, corrected output MUST be structured into the following sections, in this exact order:
    *   **1. Summary** (with a. Verdict and b. Method Sketch)
    *   **2. Detailed Solution** (containing only the clean, final proof)

Now, generate the revised, complete, and correct solution based on the feedback.
"""