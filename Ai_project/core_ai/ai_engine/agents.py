from .llm_client import LLMClient

class BaseAgent:
    """Base class for all AI Agents"""
    def ask_ai(self, system_prompt, user_prompt):
        return LLMClient.call_model(system_prompt, user_prompt)
class HighLevelAgent(BaseAgent):
    def process(self, code_content, class_name=None, analysis_summary=None, **kwargs):
        system = (
            "You are a Senior Software Architect. Provide a HIGH-LEVEL overview.\n"
            "IMPORTANT: Focus on WHAT the code does, not HOW. NO technical jargon.\n\n"
            
            "MANDATORY FORMATTING RULES:\n"
            "1. Start with 'File: [Actual FileName]'.\n"
            "2. Use '---' EXACTLY ONCE, only after the Executive Summary section.\n"
            "3. For each Class, list its methods in a simple bullet points format.\n"
            "4. CRITICAL: For methods, ONLY list the name and parameters. \n"
            "5. DO NOT include 'Logic Flow', 'Purpose', or any descriptions inside the Class section.\n"
            "6. Use '### Method:' or '### Constructor:' for each method to ensure PDF compatibility.\n\n"
            "Structure:\n"
            "File: [FILENAME]\n\n"
            "## Executive Summary\n"
            "[2-3 sentences overview]\n\n"
            "--- \n\n"
            "## Application Lifecycle\n"
            "[1–2 sentences describing how the app initializes, configures dependencies, and serves requests]\n\n"
            "## Dependencies\n"
            "- [Dependency 1]\n"
            "- [Dependency 2]\n"
            "- [Dependency 3]\n"
            "## API Routes Overview\n"
            "- [METHOD] /path — short description\n"
            "- [METHOD] /path — short description\n"
            "## Purpose & Responsibility\n"
            "[Goal of this code]\n\n"
            "## Key Capabilities\n"
            "- Feature 1\n\n"
            "## Class: [ClassName]\n"
            "### Constructor: [Constructor Name with params]\n"
            "### Method: [Method Name with params]\n"
            "### Method: [Next Method Name]\n\n"
            "DO NOT add any text or explanation under the method names."
        )
        
        
        context = ""
        if class_name: context += f"Class: {class_name}\n"
        if analysis_summary: context += f"Analysis Summary (Stats & Components):\n{analysis_summary}\n"  

        user = f"{context}Code:\n{code_content}\n\nProvide the high-level report."
        return self.ask_ai(system, user)

class LowLevelAgent(BaseAgent):
    def process(self, code_content, detailed_analysis=None, **kwargs):
        system = (
         "You are a Senior Technical Architect. Perform a DEEP LOGIC ANALYSIS.\n\n"
         "CRITICAL: Use the provided 'Detailed Context' to fill in Relationships and Patterns.\n"
            "If the context says 'No inheritance', write 'None'. If it lists relationships, list them all.\n\n"
            "--- FILE NAMING RULE ---\n"
            "1. Your first line MUST be 'File: [GeneratedName]'.\n"
            "2. Replace [GeneratedName] with a descriptive name based on the code's purpose (e.g., VehicleManager, AuthController, SystemEngine).\n\n"

            "STRICT FORMATTING RULES:\n"
            "1. Every Class MUST start with '## Class: Name'.\n"
            "2. Every Method MUST start with '### Method: name()'.\n"
            "3. IMPORTANT: Use double new lines (Enter twice) between every section and every method to avoid text clumping.\n"
            "4. Every Class section MUST end with the separator '---' on a new line by itself.\n"
            "5. NO TABLES. Use bold keys (e.g., **Purpose:**).\n"
            "6. Use Numbered lists for 'Logic Flow'.\n\n"
            "7. Do NOT use '---' inside the method description, only use it between classes."
            "8. CRITICAL: Wrap any code-related names (variables, internal calls) with single quotes (e.g., 'variable_name') WITHIN your descriptions. DO NOT use quotes in main headers (## Class or ### Method)."
            "10. Explain EVERY 'Constructor' and 'Method' listed in the context. Do not skip any element."
            "11. TECHNICAL QUOTES: Use single quotes for names only inside the 'Description', 'Logic Flow', etc. The headers MUST be clean (e.g., ### Method: calculate_total)."
            "12. TERMINOLOGY & HEADERS: \n"
            "    - For class constructors, use the header: '### Constructor: [name]'.\n"
            "    - For all other class functions, use the header: '### Method: [name]'.\n"
            "    - NEVER use the word 'Function' or 'Routine' in any header. \n"
            "    - If you are unsure, default to '### Method:'."
            "13. ORDER: Always list the 'Constructor' first at the top of the class, followed by all other 'Methods' in sequential order."
            "DETAILED APPLICATION CONTEXT (IF APPLICABLE):"
            "If the code represents a web/API application, you MUST include:"
            "Structure:\n"
            "## Application Lifecycle"
            "Explain how the application initializes, configures dependencies, sets up the database, registers routes, and handles requests."

            "## Dependencies & External Services"
            "List all imported frameworks and libraries (e.g., Flask, SQLAlchemy, datetime) and explain their role in the system."

            "## API Routes (Full Technical Breakdown)"
            "For each route:"
            "- Show the HTTP method (GET, POST, PUT, DELETE)"
            "- Show the path (/tasks, /tasks/<id>, etc.)"
            "- Explain what the route does"
            "- Explain how it interacts with the underlying classes or database"
            "- Mention validation, error handling, and response structure"

            "Structure per Class:\n"
            "## Class: [ClassName]\n\n"
            "**Purpose:** [Description]\n\n"
            "**Patterns:** [Mention what was found in context]\n"
            "**Relationships:** [List all relationships in ONE line, e.g., Inherits from 'Animal', Composition with 'Engine', Association with 'Flyable',Aggregation with 'Vehicle', Dependency with 'Logger'. If none, write 'None']\n\n"
            "**Complexity Level:** Rate the logic complexity for each class/method as (Low, Medium, or High) based on its cyclomatic complexity and depth.\n"
            "**Security Note:** Identify any potential security risks, such as insecure communication (HTTP), hardcoded credentials, or lack of input validation.\n"
            "**Impact Analysis:** Briefly explain the side effects of modifying this method and which other components might be affected.\n"
            "**Best Practices:** Provide a brief comparison between the current implementation and industry standards like PEP 8 for Python or SOLID principles.\n"
            
            "### Constructor: [name]\n" 
            "[Same fields as method: Description, Logic Flow, Parameters, Returns, Error Handling]\n\n"
            "### Method: [name]\n\n"
            "**Description:** [Text]\n\n"
            "**Logic Flow:**\n"
            "1. Step One\n"
            "2. Step Two\n\n"
            "**Parameters:**\n"
            "- **p1**: description\n\n"
            "**Returns:** [Text]\n\n"
            "**Error Handling:** [Analyze how the method handles exceptions, edge cases, or invalid inputs. If none, suggest what's missing.]\n\n" 
            "STRICT STRUCTURE PER CLASS ENDING:\n"
            "At the end of EACH Class (before the '---' separator), you MUST add:\n"
            "**Architectual Recommendations:** [Provide a brief expert advice: e.g., 'Class is too large, consider splitting' or 'Use an Interface to improve decoupling'.]\n" 
            
            "---\n"
        )
        user = f"--- DETAILED ANALYSIS CONTEXT ---\n{detailed_analysis}\n\n--- ACTUAL CODE ---\n{code_content}"
        return self.ask_ai(system, user)

class VerifierAgent(BaseAgent):
    def verify(self, code, explanation, force_verification=False, **kwargs):
        """
        Verify explanation accuracy with smart handling of large sizes to avoid breaking the process
        """
        code_size = len(str(code)) + len(str(explanation))
        
        if code_size > 50000 and not force_verification:
            print(f"Warning: Code size too large ({code_size}). Skipping AI Verification.")
            return explanation 

        system = (
            "You are a QA Lead and Technical Reviewer. Your task is to verify the accuracy of the technical explanation against the actual code.\n\n"
            "STRICT FORMATTING RULES:\n"
            "1. DO NOT change the structure of the explanation. Keep all tags like 'File:', '## Class:', '### Method:', and '---' exactly as they are.\n"
            "2. Correct ONLY the technical content (logic, parameter names, return values) if they are wrong.\n"
            "3. Ensure that the 'Logic Flow' numbers and 'Bold Keys' (e.g., **Purpose:**) are preserved.\n"
            "4. Return ONLY the corrected explanation text.\n"
            "5. NO meta-commentary (e.g., don't say 'I have corrected the text').\n"
            "6. Maintain the 'File: [FileName]' line at the very beginning.\n"
            "7. CRITICAL: Do NOT use '---' inside method descriptions. Only use it between classes or sections.\n\n"
            "Your goal is to ensure 100% technical accuracy while maintaining the EXACT visual formatting provided."
        )
        
        user = (
            f"Original Code:\n{code}\n\n"
            f"Explanation to Verify:\n{explanation}\n\n"
            "Please verify and correct the content above while keeping all formatting tags intact."
        )
        
        try:
            return self.ask_ai(system, user)
        except Exception as e:
            print(f"AI Verification failed: {e}")
            return explanation # Return to original explanation in case AI fails

    def verify_async(self, code, explanation, **kwargs):
        """Direct call version with forced verification enabled"""
        return self.verify(code, explanation, force_verification=True, **kwargs)