from pylib_0xe.config.config import Config
import openai
import logging
import json
from typing import List, Dict, Any, Tuple

# Pydantic for data validation
from pydantic import BaseModel, Field, ValidationError

LOGGER = logging.getLogger(__name__)

# --- Configuration ---
OPENAI_API_KEY = Config.read_env("openai_api_key")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. Please set it in a .env file or directly."
    )

BASE_URL = Config.read_env("base_url")
if not BASE_URL:
    raise ValueError(
        "BASE_URL not found in environment variables. Please set it in a .env file or directly."
    )

LLM_MODEL = "gpt-4o-mini"  # Or a more capable model like "gpt-4o" or "gpt-4-turbo" for complex flows
TEMPERATURE = (
    0.3  # Lower temperature for more deterministic and instruction-following behavior
)


# --- Pydantic Models ---
class StackDetail(BaseModel):
    stack_field: str = Field(
        ...,
        description="The field of technology (e.g., 'Frontend', 'Backend', 'DevOps').",
    )
    stack_name: str = Field(
        ..., description="The name of the technology or stack component."
    )
    deep_requirements: List[str] = Field(
        default_factory=list,
        description="Specific details, versions, libraries, or type (e.g., 'Relational', 'Version 3.9+').",
    )


class JobPostingOutput(BaseModel):
    company_name: str = Field(..., description="The name of the company.")
    company_industry: str = Field(..., description="The industry of the company.")
    job_position: str = Field(..., description="The title of the job position.")
    requirements: List[StackDetail] = Field(
        default_factory=list,
        description="A list of detailed technology stack requirements.",
    )


# --- System Prompt for Stack-Focused Job Posting Agent ---
SYSTEM_PROMPT_STACK_FOCUS = f"""
Respond to the user in 'persian' language ('farsi') but keep the data storage in english.
The assistant's role is to help define technical requirements for a job posting through a structured, conversational process.

First, the assistant asks for the company name, and then the job position. These two pieces of information (company_name, job_position) WILL BE INCLUDED in the final JSON output.
Next, the assistant may ask about the job position fields, and a list of general job responsibilities or keywords related to the role. This additional information  (general responsibilities) is used only for background context for the LLM and is NOT included in the final structured JSON output.

Then, the assistant asks about the main technical fields or areas of expertise required for the role (e.g., Frontend Development, Backend Development, DevOps, Data Science).

For each technical field identified, the assistant shifts focus to identifying the key technologies, languages, tools, or stacks required. Assistant must provide examples for clarity when asking about technologies within a field (e.g., "For Frontend Development, what key technologies are required? For example, React, Vue, Angular, JavaScript, TypeScript..."). You should ask about each field one by one.

After a technology/stack is named by the user for a given field, you MUST ask at least two deeper, specific questions about that technology/stack to gather its 'deep_requirements'. For example:
- If 'Python' is mentioned for 'Backend Development', ask: "Are there any specific Python libraries or frameworks crucial for this role, like Django, Flask, or FastAPI?"
- If 'PostgreSQL' is mentioned for 'Databases', ask: "Is this for a relational database requirement?" and then "Are there specific version requirements or any essential extensions?"
- If 'AWS' is mentioned for 'Cloud', ask: "Which specific AWS services are key for this role (e.g., EC2, S3, Lambda, RDS)?" and then "Is experience with IaC tools like CloudFormation or Terraform for AWS needed?"

This process of identifying a technology and then asking deep questions is repeated for all technologies within a field, and then for all identified fields.

Again emphasize that assistant must ask about all fields identified.

Once all necessary information is collected, the assistant outputs ONLY a single JSON object. This object must conform to the following structure:
- "company_name": (string) The name of the company collected.
- "company_industry": (string) The field of the company industry
- "job_position": (string) The job position collected.
- "requirements": (array of objects) A list of technology stack details. Each object in this array must have:
    - "stack_field": (string) The field of technology (e.g., "Frontend Development", "DevOps").
    - "stack_name": (string) The name of the specific technology or stack component.
    - "deep_requirements": (array of strings) Specific details, versions, libraries, or type collected from the deep questions.

If no technologies are listed by the user after prompting for all fields, the "requirements" array in the final JSON object should be empty.
There must be no conversational text, pleasantries, or any other characters before or after this JSON object. The output must be *only* the JSON object.

Final JSON format example:
{{
    "company_name": "ZimboTech",
    "company_industry": "Information Technology",
    "job_position": "Senior AI Engineer",
    "requirements": [
        {{
            "stack_field": "Programming Language",
            "stack_name": "Python",
            "deep_requirements": ["Version 3.9+", "Experience with TensorFlow or PyTorch", "Familiarity with Scikit-learn"]
        }},
        {{
            "stack_field": "DevOps",
            "stack_name": "Docker",
            "deep_requirements": ["Experience writing Dockerfiles", "Understanding of container orchestration (e.g., Kubernetes basics)"]
        }},
        {{
            "stack_field": "Cloud Platform",
            "stack_name": "AWS",
            "deep_requirements": ["S3 for data storage", "SageMaker for model training", "EC2 for deployment if needed"]
        }}
    ]
}}

Assistant must ask questions one by one and wait for user answers before proceeding to the next question.
When the assistant believes it has gathered all necessary details for all fields and their technologies, it should directly output the final JSON object and must tell "FINISHED".
"""


class Agent:
    """
    An AI agent that interactively collects job posting information,
    focusing on detailed stack requirements, and outputs a JSON object.
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        api_key: str = OPENAI_API_KEY,
        model: str = LLM_MODEL,
        temperature: float = TEMPERATURE,
    ):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT_STACK_FOCUS}
        ]
        # Internal storage for all collected data
        self.collected_data: Dict[str, Any] = {
            "company_name": None,  # Will be filled by LLM in final JSON
            "job_position": None,  # Will be filled by LLM in final JSON
            "company_industry": None,  # Will be filled by the LLM in the final JSON
            "general_job_requirements_context": None,  # For context, not in final JSON
            "final_job_posting_output": None,  # This will store the LLM's final JSON object (as Pydantic model)
        }

    def history(self) -> str:
        return json.dumps(self.messages)

    def get_initial_greeting(self) -> str:
        """
        Gets the initial greeting/first question from the LLM.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,  # type:ignore
                temperature=self.temperature,
            )
            assistant_reply = response.choices[0].message.content
            if assistant_reply:
                self.messages.append({"role": "assistant", "content": assistant_reply})
                return assistant_reply
            else:
                return "Error: LLM returned an empty initial response."
        except openai.APIError as e:
            print(f"OpenAI API Error: {e}")
            return "Error: Could not connect to the AI. Please check your API key and network."
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "Error: An unexpected error occurred."

    def load_messages(self, messages: str) -> None:
        self.messages = json.loads(messages)

    def shot(self, messages: str, user_message: str) -> Tuple[str, str, str]:
        """
        response, messages, built_data
        """
        self.load_messages(messages)

        try:
            assistant_reply = self.process_user_response(user_message)
            if assistant_reply:
                self.messages.append({"role": "assistant", "content": assistant_reply})
                return (
                    assistant_reply,
                    json.dumps(self.messages),
                    (
                        self.collected_data["final_job_posting_output"].model_dump_json(
                            indent=2
                        )
                        if self.collected_data["final_job_posting_output"]
                        else None
                    ),  # type:ignore
                )
            else:
                raise Exception("Error: LLM returned an empty response.")
        except openai.APIError as e:
            print(f"OpenAI API Error: {e}")
            raise Exception(
                "Error: Could not process your response. Please check your API key and network."
            )
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise Exception("Error: An unexpected error occurred.")

        return "", "", ""

    def process_user_response(self, user_input: str) -> str:
        """
        Sends user input to the LLM, gets the next question or final JSON object,
        and updates conversation history.
        """
        if not user_input.strip():
            return "Please provide a response."

        self.messages.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,  # type:ignore
                temperature=self.temperature,
            )
            assistant_reply = response.choices[0].message.content
            if not assistant_reply:
                raise Exception("Invalid output from LLM")

            extracted = extract_json(assistant_reply)
            if is_potential_json_object(extracted):  # Check for JSON object
                LOGGER.info(
                    "\n🔄 Validating collected job posting information against schema..."
                )
                try:
                    # The LLM should output ONLY the JSON object string.
                    raw_json_data = json.loads(extracted)

                    # Validate the entire structure against JobPostingOutput
                    validated_job_output = JobPostingOutput(**raw_json_data)
                    self.collected_data["final_job_posting_output"] = (
                        validated_job_output
                    )

                    print("\n✅ Successfully collected and validated job posting data!")
                    print("\n--- Parsed Job Posting Data (Pydantic Model) ---")
                    # Use Pydantic's model_dump_json for clean output
                    output_json_str = validated_job_output.model_dump_json(indent=2)
                    print(output_json_str)
                    print("------------------------------------")
                    # The agent's collected_data also holds the Pydantic model now.
                    # agent.collected_data["company_name"] etc. are not directly updated here
                    # as the final JSON from LLM is the source of truth for those.
                except json.JSONDecodeError:
                    print("\n❌ Error: Agent's final response was not valid JSON.")
                    print(f"LLM Output: \n{assistant_reply}")
                    print(
                        "Agent: The final output was not valid JSON. Please ensure the AI is configured correctly or try again."
                    )
                except ValidationError as e:
                    print(
                        "\n❌ Error: Agent's final JSON object did not match the required JobPostingOutput schema."
                    )
                    print("Pydantic Validation Errors:")
                    print(e)
                    print(f"LLM Output: \n{assistant_reply}")
                    print(
                        "Agent: The final output's structure was incorrect. Please ensure the AI is configured correctly or try again."
                    )
                except (
                    Exception
                ) as e:  # Catch any other unexpected errors during validation
                    print(f"\n❌ An unexpected error occurred during validation: {e}")
                    print(f"LLM Output: \n{assistant_reply}")

            return assistant_reply
        except openai.APIError as e:
            print(f"OpenAI API Error: {e}")
            return "Error: Could not process your response. Please check your API key and network."
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "Error: An unexpected error occurred."


def is_potential_json_object(text: str) -> bool:
    """Quick check if a string looks like it might be a JSON object."""
    stripped_text = text.strip()
    return stripped_text.startswith("{") and stripped_text.endswith("}")


def extract_json(text: str) -> str:
    s, e = 0, len(text) - 1
    while s < e and text[s] != "{":
        s += 1
    while e > s and text[e] != "}":
        e -= 1
    if s < e:
        return text[s : e + 1]
    return ""


def main():
    print("🤖 AI Job Stacks Agent Initializing...\n")
    # For this complex flow, a more capable model like "gpt-4o" or "gpt-4-turbo" is recommended.
    print(BASE_URL)
    print(OPENAI_API_KEY)
    agent = Agent(
        base_url=BASE_URL,
        api_key=OPENAI_API_KEY,
        model=LLM_MODEL,
        temperature=TEMPERATURE,
    )

    assistant_reply = agent.get_initial_greeting()
    print(f"Agent: {assistant_reply}")

    if "Error:" in assistant_reply:
        return

    turn_count = 0
    # Max turns needs to be generous due to iterative stack questioning.
    # e.g., 2 initial Qs (company, position) + 1 context Q (industry) + 1 context Q (responsibilities)
    # + 1 Q for fields + (e.g., 3 fields * (1 Q for stacks in field + 2 stacks * 2 deep Qs per stack))
    # = 4 + 1 + (3 * (1 + 2*2)) = 5 + (3 * 5) = 20 AI questions.
    # So, ~20 user answers. Total ~40 message pairs.
    max_turns = 60  # Adjust as needed based on expected max number of fields/stacks

    while turn_count < max_turns:
        user_input = input("You: ").strip()
        if not user_input:
            print("Agent: Please provide a response.")
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("Agent: Exiting conversation. Goodbye!")
            break

        assistant_reply = agent.process_user_response(user_input)
        print(f"\nAgent: {assistant_reply}")

        if "Error:" in assistant_reply:
            print("Agent: Encountered an error processing the response. Exiting.")
            break

        if is_potential_json_object(assistant_reply):  # Check for JSON object
            print("\n🔄 Validating collected job posting information against schema...")
            try:
                # The LLM should output ONLY the JSON object string.
                raw_json_data = json.loads(assistant_reply.strip())

                # Validate the entire structure against JobPostingOutput
                validated_job_output = JobPostingOutput(**raw_json_data)
                agent.collected_data["final_job_posting_output"] = validated_job_output

                print("\n✅ Successfully collected and validated job posting data!")
                print("\n--- Parsed Job Posting Data (Pydantic Model) ---")
                # Use Pydantic's model_dump_json for clean output
                output_json_str = validated_job_output.model_dump_json(indent=2)
                print(output_json_str)
                print("------------------------------------")
                # The agent's collected_data also holds the Pydantic model now.
                # agent.collected_data["company_name"] etc. are not directly updated here
                # as the final JSON from LLM is the source of truth for those.
                break
            except json.JSONDecodeError:
                print("\n❌ Error: Agent's final response was not valid JSON.")
                print(f"LLM Output: \n{assistant_reply}")
                print(
                    "Agent: The final output was not valid JSON. Please ensure the AI is configured correctly or try again."
                )
                break
            except ValidationError as e:
                print(
                    "\n❌ Error: Agent's final JSON object did not match the required JobPostingOutput schema."
                )
                print("Pydantic Validation Errors:")
                print(e)
                print(f"LLM Output: \n{assistant_reply}")
                print(
                    "Agent: The final output's structure was incorrect. Please ensure the AI is configured correctly or try again."
                )
                break
            except (
                Exception
            ) as e:  # Catch any other unexpected errors during validation
                print(f"\n❌ An unexpected error occurred during validation: {e}")
                print(f"LLM Output: \n{assistant_reply}")
                break

        turn_count += 1
        if turn_count >= max_turns:
            print("\nAgent: Reached maximum conversation turns.")
            if not is_potential_json_object(
                assistant_reply
            ):  # Check if final output was not JSON object
                print(
                    "Agent: I wasn't able to collect all the information and provide the final JSON object in the allotted turns."
                )
            break


if __name__ == "__main__":
    main()
