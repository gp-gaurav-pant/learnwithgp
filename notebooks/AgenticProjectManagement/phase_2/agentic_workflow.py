# agentic_workflow.py

# 1 - Import the following agents: ActionPlanningAgent, KnowledgeAugmentedPromptAgent, EvaluationAgent, RoutingAgent from the workflow_agents.base_agents module

import os
from dotenv import load_dotenv
from workflow_agents.base_agents import ActionPlanningAgent, KnowledgeAugmentedPromptAgent, EvaluationAgent, RoutingAgent


# 2 - Load the OpenAI key into a variable called openai_api_key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# load the product spec
# 3 - Load the product spec document Product-Spec-Email-Router.txt into a variable called product_spec
with open("Product-Spec-Email-Router.txt") as f:
    product_spec = "".join(f.readlines())

# Instantiate all the agents

# Action Planning Agent
knowledge_action_planning = (
    "Stories are defined from a product spec by identifying a "
    "persona, an action, and a desired outcome for each story. "
    "Each story represents a specific functionality of the product "
    "described in the specification. \n"
    "Features are defined by grouping related user stories. \n"
    "Tasks are defined for each story and represent the engineering "
    "work required to develop the product. \n"
    "A development Plan for a product contains all these components. \n"
    "The steps to create it are exactly: define user stories for every type of user of the product, "
    "group related user stories into features, define the engineering tasks for each user story."
)
# 4 - Instantiate an action_planning_agent using the 'knowledge_action_planning'
action_planning_agent = ActionPlanningAgent(openai_api_key, knowledge_action_planning)

# Product Manager - Knowledge Augmented Prompt Agent
persona_product_manager = "You are a Product Manager, you are responsible for defining the user stories for a product."
knowledge_product_manager = (
    "Stories are defined by writing sentences with a persona, an action, and a desired outcome. "
    "The sentences always start with: As a "
    "Write as many stories as needed for each type of user described in the product spec below, "
    "so that every product feature, functional requirement and non-functional requirement in the spec is covered by at least one story. "
    f"#Product specs:\n{product_spec}"
)
# 6 - Instantiate a product_manager_knowledge_agent using 'persona_product_manager' and the completed 'knowledge_product_manager'
product_manager_knowledge_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona_product_manager, knowledge_product_manager)

# Product Manager - Evaluation Agent
# 7 - Define the persona and evaluation criteria for a Product Manager evaluation agent and instantiate it as product_manager_evaluation_agent. This agent will evaluate the product_manager_knowledge_agent.
# The evaluation_criteria should specify the expected structure for user stories (e.g., "As a [type of user], I want [an action or feature] so that [benefit/value].").
persona_product_manager_evaluator = "You are an evaluation agent that checks the answers of other worker agents"

evaluation_criteria = (
    "The answer should be a list of user stories covering the different users of the product. "
    "Each user story must follow this structure: "
    "As a [type of user], I want [an action or feature] so that [benefit/value]."
)
product_manager_evaluation_agent = EvaluationAgent(openai_api_key, persona_product_manager_evaluator, evaluation_criteria, product_manager_knowledge_agent, max_interactions=10)

# Program Manager - Knowledge Augmented Prompt Agent
persona_program_manager = "You are a Program Manager, you are responsible for defining the features for a product."
knowledge_program_manager = (
    "Features of a product are defined by organizing similar user stories into cohesive groups. "
    "Define the features for the product spec below, using the user stories provided in the prompt. "
    "Make sure every user story provided in the prompt belongs to a feature. "
    "Write every feature with these labeled fields, each on its own line:\n"
    "Feature Name: <clear, concise title>\n"
    "Description: <what the feature does and its purpose>\n"
    "Key Functionality: <specific capabilities or actions the feature provides>\n"
    "User Benefit: <how the feature creates value for the user>\n"
    f"#Product specs:\n{product_spec}"
)

# Instantiate a program_manager_knowledge_agent using 'persona_program_manager' and 'knowledge_program_manager'
# (This is a necessary step before 8. Students should add the instantiation code here.)
program_manager_knowledge_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona_program_manager, knowledge_program_manager)

# Program Manager - Evaluation Agent
persona_program_manager_eval = "You are an evaluation agent that checks the answers of other worker agents."

# 8 - Instantiate a program_manager_evaluation_agent using 'persona_program_manager_eval' and the evaluation criteria below.
#                      "The answer should be product features that follow the following structure: " \
#                      "Feature Name: A clear, concise title that identifies the capability\n" \
#                      "Description: A brief explanation of what the feature does and its purpose\n" \
#                      "Key Functionality: The specific capabilities or actions the feature provides\n" \
#                      "User Benefit: How this feature creates value for the user"
# For the 'agent_to_evaluate' parameter, refer to the provided solution code's pattern.
evaluation_criteria = """The answer should be product features that follow the following structure:
    # Feature Name: A clear, concise title that identifies the capability
    # Description: A brief explanation of what the feature does and its purpose
    # Key Functionality: The specific capabilities or actions the feature provides
    # User Benefit: How this feature creates value for the user"""

program_manager_evaluation_agent = EvaluationAgent(openai_api_key, persona_program_manager_eval, evaluation_criteria, program_manager_knowledge_agent, max_interactions=10)

# Development Engineer - Knowledge Augmented Prompt Agent
persona_dev_engineer = "You are a Development Engineer, you are responsible for defining the development tasks for a product."
knowledge_dev_engineer = (
    "Development tasks are defined by identifying what needs to be built to implement each user story. "
    "Define the development tasks for the product spec below, using the user stories and features provided in the prompt. "
    "Define as many tasks as needed for every user story provided in the prompt, so that every user story is covered. "
    "Write every task with these seven labeled fields, each on its own line. "
    "Task ID and Task Title are separate fields; never put the title on the Task ID line:\n"
    "Task ID: <unique identifier, e.g. DEV-001>\n"
    "Task Title: <brief description of the development work>\n"
    "Related User Story: <the full user story this task implements>\n"
    "Description: <detailed explanation of the technical work>\n"
    "Acceptance Criteria: <specific requirements for completion>\n"
    "Estimated Effort: <time or complexity estimate>\n"
    "Dependencies: <Task IDs that must be completed first, or None>\n"
    f"#Product specs:\n{product_spec}"
)
# Instantiate a development_engineer_knowledge_agent using 'persona_dev_engineer' and 'knowledge_dev_engineer'
# (This is a necessary step before 9. Students should add the instantiation code here.)
development_engineer_knowledge_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona_dev_engineer, knowledge_dev_engineer)

# Development Engineer - Evaluation Agent
persona_dev_engineer_eval = "You are an evaluation agent that checks the answers of other worker agents."
# 9 - Instantiate a development_engineer_evaluation_agent using 'persona_dev_engineer_eval' and the evaluation criteria below.
#                      "The answer should be tasks following this exact structure: " \
#                      "Task ID: A unique identifier for tracking purposes\n" \
#                      "Task Title: Brief description of the specific development work\n" \
#                      "Related User Story: Reference to the parent user story\n" \
#                      "Description: Detailed explanation of the technical work required\n" \
#                      "Acceptance Criteria: Specific requirements that must be met for completion\n" \
#                      "Estimated Effort: Time or complexity estimation\n" \
#                      "Dependencies: Any tasks that must be completed first"
# For the 'agent_to_evaluate' parameter, refer to the provided solution code's pattern.
evaluation_criteria= """The answer should be a list of tasks. Every task must have all of the following fields as separate labeled lines.
Task ID and Task Title must be two separate fields; a title written on the Task ID line does not meet the criteria.
  # Task ID: A unique identifier for tracking purposes
  # Task Title: Brief description of the specific development work
  # Related User Story: Reference to the parent user story
  # Description: Detailed explanation of the technical work required
  # Acceptance Criteria: Specific requirements that must be met for completion
  # Estimated Effort: Time or complexity estimation
  # Dependencies: Any tasks that must be completed first
  """
development_engineer_evaluation_agent = EvaluationAgent(openai_api_key, persona_dev_engineer_eval, evaluation_criteria, development_engineer_knowledge_agent, max_interactions=10)

# Routing Agent
# 10 - Instantiate a routing_agent. You will need to define a list of agent dictionaries (routes) for Product Manager, Program Manager, and Development Engineer. Each dictionary should contain 'name', 'description', and 'func' (linking to a support function). Assign this list to the routing_agent's 'agents' attribute.
routing_agent = RoutingAgent(openai_api_key, {})


# Job function persona support functions
# 11 - Define the support functions for the routes of the routing agent (e.g., product_manager_support_function, program_manager_support_function, development_engineer_support_function).
# Each support function should:
#   1. Take the input query (e.g., a step from the action plan).
#   2. Get a response from the respective Knowledge Augmented Prompt Agent.
#   3. Have the response evaluated by the corresponding Evaluation Agent.
#   4. Return the final validated response.

def product_manager_support_function(query):
    # Step 1: Get response from Knowledge Augmented Prompt Agent
    response = product_manager_knowledge_agent.respond(query)
    
    # Step 2: Have the response evaluated by the corresponding Evaluation Agent
    evaluation_result = product_manager_evaluation_agent.evaluate(response)

    # Step 3: Return final validated response
    return "Product Manager", evaluation_result["response"]

def program_manager_support_function(query):
    # Step 1: Get response from Knowledge Augmented Prompt Agent
    response = program_manager_knowledge_agent.respond(query)
    
    # Step 2: Have the response evaluated by the corresponding Evaluation Agent
    evaluation_result = program_manager_evaluation_agent.evaluate(response)

    # Step 3: Return final validated response
    return "Program Manager", evaluation_result["response"]

def development_engineer_support_function(query):
    # Step 1: Get response from Knowledge Augmented Prompt Agent
    response = development_engineer_knowledge_agent.respond(query)
    
    # Step 2: Have the response evaluated by the corresponding Evaluation Agent
    evaluation_result = development_engineer_evaluation_agent.evaluate(response)

    # Step 3: Return final validated response
    return "Development Engineer", evaluation_result["response"]

agent_routes = [
        {
            'name': 'Product Manager',
            'description': 'Defines user stories from the product spec, each with a persona, an action and a desired outcome',
            'func': product_manager_support_function
        },
        {
            'name': 'Program Manager',
            'description': 'Groups related user stories to define product features with feature name, description, key functionality and user benefit',
            'func': program_manager_support_function
        },
        {
            'name': 'Development Engineer',
            'description': 'Defines engineering development tasks for each user story with task ID, title, acceptance criteria, estimated effort and dependencies',
            'func': development_engineer_support_function
        }
    ]
routing_agent.agents = agent_routes

# Run the workflow

print("\n*** Workflow execution started ***\n")
# Workflow Prompt
# ****
workflow_prompt = "What would the development tasks for this product be?"
# ****
print(f"Task to complete in this workflow, workflow prompt = {workflow_prompt}")

print("\nDefining workflow steps from the workflow prompt")
# 12 - Implement the workflow.
#   1. Use the 'action_planning_agent' to extract steps from the 'workflow_prompt'.
#   2. Initialize an empty list to store 'completed_steps'.
#   3. Loop through the extracted workflow steps:
#      a. For each step, use the 'routing_agent' to route the step to the appropriate support function.
#      b. Append the result to 'completed_steps'.
#      c. Print information about the step being executed and its result.
#   4. After the loop, print the final output of the workflow (the last completed step).

# Section of the final plan that each role's output belongs to
section_titles = {"Product Manager": "User Stories",
                  "Program Manager": "Product Features",
                  "Development Engineer": "Engineering Tasks"}

def main_workflow(workflow_prompt):
    # 1. Use the 'action_planning_agent' to extract steps from the 'workflow_prompt'.
    workflow_steps = action_planning_agent.extract_steps_from_prompt(workflow_prompt)

    # 2. Initialize an empty list to store 'completed_steps'.
    completed_steps = []
    role_outputs = {}  # validated output of each role, keyed by role name

    for each_step in workflow_steps:
        print(f"-----Executing step: {each_step}-------")
        context = "\n\n".join(completed_steps)
        agent_name, response = routing_agent.route(each_step, context=context)
        role_outputs[agent_name] = response
        completed_steps.append(response)
        print(f"Response:: {response}")

    # 4. Consolidate the three role outputs into a single project plan
    divider = "----------------------------------"
    final_response = ""
    # Python dicts keep insertion order, so sections follow the order the steps ran
    for agent_name, agent_output in role_outputs.items():
        output = f"{divider}\n {section_titles.get(agent_name, agent_name)} \n\n {agent_output}"
        final_response += output+"\n\n\n"
    return final_response


final_response = main_workflow(workflow_prompt)
print("\n\n\nFINAL DELIVERABLE: Email Router Project Plan")
print(final_response)