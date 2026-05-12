"""
AISSM_BH 的主 MD 代理类
"""

import os
import json
导入logging
导入requests
from typing import List, Dict, Any, Optional, Union

导入time

from AISSM_BH.core.skill_router import SkillRouter
from AISSM_BH.utils.terminal import print_message, prompt_user
从AISSM_BH.config导入SYSTEM_MESSAGE_ADVISOR, SYSTEM_MESSAGE_AGENT


类BHMDAgent:
    “基于大语言模型的代理，用于使用GROMACS运行分子动力学模拟”
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o",
                workspace: str = "./md_workspace",
                url: str = "https://api.openai.com/v1/chat/completions", mode: str = "copilot", gmx_bin: str = "gmx"):
        """
初始化BH MD代理。

参数
        ----------
api_key : 字符串，可选
用于LLM服务的API密钥。如果未提供，则从环境变量中读取。
模型：字符串，可选
要使用的模型名称。默认值为“gpt-4o”。
工作区：字符串，可选
工作区目录。默认为“./md_workspace”。
url：字符串，可选
LLM服务URL。默认为OpenAI端点。
mode : 字符串，可选
操作模式：“副驾驶”或“代理”。默认为“副驾驶”。
gmx_bin : 字符串，可选
GROMACS 二进制文件的路径。默认值为“gmx”。 
        """
self.api_key= api_key或os.environ.get("OPENAI_API_KEY")
        self.url = url
        如果 未self.api_key:
            引发 ValueError("API密钥是必需的。请作为参数提供或设置OPENAI_API_KEY环境变量")
        
        self.model = model
        self.conversation_history = []
        self.workspace = workspace
        self.gmx_bin = gmx_bin
        
        self.mode = mode
        
        self.skill_router = SkillRouter(self.workspace, self.gmx_bin)
self.= 自我.skill_router.skill_classes["蛋白"
            self.workspace, self.gmx_bin
        )
        
logging.info(f"BH MD 代理已使用模型初始化：{model}")

    def switch_to_mmpbsa_skill(self) -> Dict[str, Any]:
        """
        Switch to MM-PBSA skill for binding free energy calculations.

        Returns
        -------
        dict
            Result indicating success or failure.
        """
        try:
            old_skill = self.current_skill
            self.current_skill, prev = self.skill_router.switch_to("mmpbsa", old_skill)
            return {
                "success": True,
                "message": "Switched to MM-PBSA skill successfully",
                "previous_skill": prev,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to switch to MM-PBSA skill: {str(e)}",
            }
        
    def switch_to_protein_ligand_skill(self) -> Dict[str, Any]:
        """
        Switch to Protein-Ligand skill.

        Returns
        -------
        dict
            Result indicating success or failure.
        """
        try:
            old_skill = self.current_skill
            self.current_skill, prev = self.skill_router.switch_to("protein_ligand", old_skill)
            return {
                "success": True,
                "message": "Switched to Protein-Ligand skill successfully",
                "previous_skill": prev,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to switch to Protein-Ligand skill: {str(e)}",
            }
        
    def switch_to_analysis_skill(self) -> Dict[str, Any]:
        """
        Switch to Analysis skill.

        Returns
        -------
        dict
            Result indicating success or failure.
        """
        try:
            old_skill = self.current_skill
            self.current_skill, prev = self.skill_router.switch_to("analysis", old_skill)
            return {
                "success": True,
                "message": "Switched to Analysis skill successfully",
                "previous_skill": prev,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to switch to Analysis skill: {str(e)}",
            }

    def _build_context(self) -> Dict[str, Any]:
        """
        Build context dict for skill evaluation.

        Returns
        -------
        dict
            Context with phase, has_ligand, workspace.
        """
        return {
            "phase": getattr(self.current_skill, 'stage', None).name if hasattr(self.current_skill, 'stage') else None,
            "has_ligand": getattr(self.current_skill, 'has_ligand', False),
            "workspace": self.workspace,
        }

    def _evaluate_skill(self, user_input: str) -> str:
        """
        Evaluate which skill applies to the given user input.

        Returns the skill *name* (e.g. "protein", "mmpbsa").

        Parameters
        ----------
        user_input : str
            The user's input text.

        Returns
        -------
        str
            Skill key.
        """
        return self.skill_router.evaluate(user_input, self._build_context())
    
    def get_tool_schema(self) -> List[Dict[str, Any]]:
        """
        Get combined tool schema from current skill plus global tools.

        Returns
        -------
        list of dict
            List of tool definitions.
        """
        global_tools = [
            {
                "type": "function",
                "function": {
                    "name": "run_shell_command",
                    "description": "Run a shell command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to run"
                            },
                            "capture_output": {
                                "type": "boolean",
                                "description": "Whether to capture stdout/stderr"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_workspace_info",
                    "description": "Get information about the current workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_gromacs_installation",
                    "description": "Check if GROMACS is installed and available",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "switch_to_mmpbsa_skill",
                    "description": "Switch to MM-PBSA skill for binding free energy calculations",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
        
        return global_tools + self.current_skill.get_tool_schema()
    
    def call_llm(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call the LLM API.

        Parameters
        ----------
        messages : list of dict
            Conversation messages.
        tools : list of dict, optional
            Tool definitions. Gets current schema if omitted.

        Returns
        -------
        dict
            Response JSON from the LLM.
        """
        start_time = time.time()
        tools = tools or self.get_tool_schema()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "tools": tools
        }
        
        response = requests.post(
            self.url,
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            logging.error(f"LLM API error: {response.status_code} - {response.text}")
            raise Exception(f"LLM API error: {response.status_code} - {response.text}")
        
        response_json = response.json()
        
        elapsed = time.time() - start_time
        usage = response_json.get('usage', {})
        print(f"\n[Record] LLM call took {elapsed:.2f}s, "
              f"prompt tokens: {usage.get('prompt_tokens', 'N/A')}, "
              f"completion tokens: {usage.get('completion_tokens', 'N/A')}, "
              f"total tokens: {usage.get('total_tokens', 'N/A')}\n", flush=True)

        return response_json

    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call from the LLM.

        Parameters
        ----------
        tool_call : dict
            Tool call object with function name and arguments.

        Returns
        -------
        dict
            Result of the tool execution.
        """
        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])
        
        if function_name == "switch_to_mmpbsa_skill":
            return self.switch_to_mmpbsa_skill()
        
        if hasattr(self.current_skill, function_name):
            method = getattr(self.current_skill, function_name)
            result = method(**arguments)
            return result
        else:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}"
            }
    
    def run(self, starting_prompt: str = None) -> None:
        """
        Main agent loop.

        Parameters
        ----------
        starting_prompt : str, optional
            Initial prompt from user.
        """
        from AISSM_BH.core.enums import MessageType
        
        if self.mode == "copilot":
            system_message = {
                "role": "system",
                "content": SYSTEM_MESSAGE_ADVISOR
            }
        else:
            system_message = {
                "role": "system",
                "content": SYSTEM_MESSAGE_AGENT
            }
        
        self.conversation_history = [system_message]
        
        if starting_prompt:
            self.conversation_history.append({
                "role": "user",
                "content": starting_prompt
            })
        
        response = self.call_llm(self.conversation_history)
        
        if starting_prompt:
            target_name = self._evaluate_skill(starting_prompt)
            current_name = self.skill_router.class_to_name.get(
                self.current_skill.__class__
            )
            if target_name != current_name:
                self.current_skill, _ = self.skill_router.switch_to(
                    target_name, self.current_skill
                )
                self.conversation_history.append({
                    "role": "system",
                    "content": f"Automatically switched to {self.current_skill.__class__.__name__}."
                })
                print(
                    f"\n[Record] Skill switched to: {self.current_skill.__class__.__name__}\n",
                    flush=True,
                )
        
        while True:
            assistant_message = response["choices"][0]["message"]
            self.conversation_history.append(assistant_message)
            
            if "tool_calls" in assistant_message:
                for tool_call in assistant_message["tool_calls"]:
                    print_message(f"Executing: {tool_call['function']['name']}", MessageType.TOOL)
                    result = self.execute_tool_call(tool_call)
                    
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "content": json.dumps(result)
                    })
                
                response = self.call_llm(self.conversation_history)
                continue
            
            content = assistant_message["content"]
            
            if "This is the final answer at this stage." in content:
                parts = content.split("This is the final answer at this stage.")
                
                print_message(parts[0].strip(), MessageType.INFO)
                
                final_part = "This is the final answer at this stage." + parts[1]
                print_message(final_part.strip(), MessageType.FINAL, style="box")
            else:
                print_message(content, MessageType.INFO)
            
            if "This is the final answer at this stage." in content:
                user_input = prompt_user("Do you want to continue with the next stage?", default="yes")
                if user_input.lower() not in ["yes", "y", "continue", ""]:
                    print_message("Exiting the BH MD agent. Thank you for using AISSM_BH!", MessageType.SUCCESS, style="box")
                    break
                
                user_input = prompt_user("What would you like to do next?")
            else:
                user_input = prompt_user("Your response")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print_message("Exiting the BH MD agent. Thank you for using AISSM_BH!", MessageType.SUCCESS, style="box")
                break
            
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            target_name = self._evaluate_skill(user_input)
            current_name = self.skill_router.class_to_name.get(
                self.current_skill.__class__
            )
            if target_name != current_name:
                self.current_skill, _ = self.skill_router.switch_to(
                    target_name, self.current_skill
                )
                self.conversation_history.append({
                    "role": "system",
                    "content": f"Automatically switched to {self.current_skill.__class__.__name__}."
                })
                print(
                    f"\n[Record] Skill switched to: {self.current_skill.__class__.__name__}\n",
                    flush=True,
                )
            
            response = self.call_llm(self.conversation_history)
