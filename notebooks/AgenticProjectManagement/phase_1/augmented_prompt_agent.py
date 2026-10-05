import os
from dotenv import load_dotenv
from workflow_agents.base_agents import AugmentedPromptAgent

# Load environment variables from .env file
load_dotenv()

# Retrieve OpenAI API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = "What is the capital of France?"
persona = "You are a college professor; your answers always start with: 'Dear students,'"

# 2 - Instantiate an object of AugmentedPromptAgent with the required parameters
augmented_agent = AugmentedPromptAgent(openai_api_key, persona)

# 3 - Send the 'prompt' to the agent and store the response in a variable named 'augmented_agent_response'
augmented_agent_response = augmented_agent.respond(prompt)

# Print the agent's response
print(augmented_agent_response)

# 4 - Add a comment explaining:
# - What knowledge the agent likely used to answer the prompt.
# Ans: Agent will use its training data as no explicit instructions provided.
# - How the system prompt specifying the persona affected the agent's response.
# Ans: The persona helps the agent adapt its tone, grammar, and domain-specific knowledge to better answer the question.
