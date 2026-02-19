from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import py_compile
import tempfile


# ---------------------------------------------------------------------------
# FileWriterTool
# Writes content to a file inside the output/ directory.
# Use this when an agent needs to persist content that is NOT covered by an
# explicit output_file in tasks.yaml (e.g. auxiliary artifacts).
# ---------------------------------------------------------------------------

class FileWriterInput(BaseModel):
    """Input schema for FileWriterTool."""
    filename: str = Field(
        ...,
        description="Relative filename inside the output/ directory, e.g. 'report.md'.",
    )
    content: str = Field(..., description="Full content to write to the file.")


class FileWriterTool(BaseTool):
    name: str = "file_writer"
    description: str = (
        "Writes content to a file inside the output/ directory. "
        "Provide the filename (relative to output/) and the full content to write."
    )
    args_schema: Type[BaseModel] = FileWriterInput

    def _run(self, filename: str, content: str) -> str:
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written successfully: {filepath}"


# ---------------------------------------------------------------------------
# CodeValidatorTool
# Validates Python source code for syntax errors using py_compile.
# Useful for the test_engineer or backend_engineer to verify generated code
# before marking a task as done.
# ---------------------------------------------------------------------------

class CodeValidatorInput(BaseModel):
    """Input schema for CodeValidatorTool."""
    code: str = Field(..., description="Python source code to validate for syntax errors.")


class CodeValidatorTool(BaseTool):
    name: str = "code_validator"
    description: str = (
        "Validates Python source code for syntax errors. "
        "Pass the raw Python code as a string. Returns 'OK' if valid, "
        "or an error message describing the syntax problem."
    )
    args_schema: Type[BaseModel] = CodeValidatorInput

    def _run(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        try:
            py_compile.compile(tmp_path, doraise=True)
            return "OK — no syntax errors found."
        except py_compile.PyCompileError as e:
            return f"Syntax error: {e}"
        finally:
            os.unlink(tmp_path)
