from planner.schemas import Targets
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=1)
def subtarget_creator(target: str):
    """creates sub targets for a target
    
    Args:
        target (str): the main target
    """
    sys_msg = SystemMessage(content=f"""You are an expert problem solver.
                            Your role is to break down a complex problem into smaller, manageable sub-problems.
                            You will be provided with the main target.
                            Your task is to create sub-targets that are specific, measurable, achievable, relevant, and time-bound (SMART).
                            Each sub-target should be a step towards achieving the main target.
                            Make sure the sub-targets are in a logical order.
                            Make sure the sub-targets are not to narrow or too broad.
                            The sub-targets is used as an subtopic so make sure they can be covered with a few paragraphs.
                            Final Output:
                            - Return a list of sub-targets using the Targets tool.

                            Main Target: {target}
    """)
    llm_with_tool = llm.bind_tools([Targets])
    response = llm_with_tool.invoke([sys_msg])
    tool_calls = getattr(response, "tool_calls", [])
    if tool_calls:
        args = tool_calls[0]["args"]
        return args["targets"]
    return []