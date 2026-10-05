import os
from dotenv import load_dotenv
from workflow_agents.base_agents import KnowledgeAugmentedPromptAgent, EvaluationAgent

# Load environment variables from the .env file
load_dotenv()

# Define the parameters for the agent
openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = "What is the capital of France?"

# 2 - Instantiate a KnowledgeAugmentedPromptAgent with:
#           - Persona: "You are a college professor, your answer always starts with: Dear students,"
#           - Knowledge: "The capital of France is London, not Paris"
persona = "You are a college professor, your answer always starts with: Dear students,"
knowledge = "The capital of France is London, not Paris"

knowledge_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona, knowledge)
response = knowledge_agent.respond(prompt)
# 3 - Write a print statement that demonstrates the agent using the provided knowledge rather than its own inherent knowledge.
print(f"Agent is not using LLM's training data but the provided knowledge base. Provided knowledge base is : {knowledge}")
print(f"Hence the answer for query :: `{prompt}` from agent is : `{response}`")