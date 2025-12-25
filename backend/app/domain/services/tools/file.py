from typing import Optional, Dict, Any
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult
import os

class FileTool(BaseTool):
    """File tool class, providing file operation functions
    
    Enhanced with:
    - Excel/CSV analysis using pandas
    - PDF text and table extraction
    - Smart file detection and processing
    """

    name: str = "file"
    
    def __init__(self, sandbox: Sandbox):
        """Initialize file tool class
        
        Args:
            sandbox: Sandbox service
        """
        super().__init__()
        self.sandbox = sandbox
        
    @tool(
        name="file_read",
        description="Read file content. Use for checking file contents, analyzing logs, or reading configuration files.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the file to read"
            },
            "start_line": {
                "type": "integer",
                "description": "(Optional) Starting line to read from, 0-based"
            },
            "end_line": {
                "type": "integer",
                "description": "(Optional) Ending line number (exclusive)"
            },
            "sudo": {
                "type": "boolean",
                "description": "(Optional) Whether to use sudo privileges"
            }
        },
        required=["file"]
    )
    async def file_read(
        self,
        file: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Read file content
        
        Args:
            file: Absolute path of the file to read
            start_line: (Optional) Starting line, 0-based
            end_line: (Optional) Ending line (exclusive)
            sudo: (Optional) Whether to use sudo privileges
            
        Returns:
            File content
        """
        # Directly call sandbox's file_read method
        return await self.sandbox.file_read(
            file=file,
            start_line=start_line,
            end_line=end_line,
            sudo=sudo
        )
    
    @tool(
        name="file_write",
        description="Overwrite or append content to a file. Use for creating new files, appending content, or modifying existing files.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the file to write to"
            },
            "content": {
                "type": "string",
                "description": "Text content to write"
            },
            "append": {
                "type": "boolean",
                "description": "(Optional) Whether to use append mode"
            },
            "leading_newline": {
                "type": "boolean",
                "description": "(Optional) Whether to add a leading newline"
            },
            "trailing_newline": {
                "type": "boolean",
                "description": "(Optional) Whether to add a trailing newline"
            },
            "sudo": {
                "type": "boolean",
                "description": "(Optional) Whether to use sudo privileges"
            }
        },
        required=["file", "content"]
    )
    async def file_write(
        self,
        file: str,
        content: str,
        append: Optional[bool] = False,
        leading_newline: Optional[bool] = False,
        trailing_newline: Optional[bool] = False,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Write content to file
        
        Args:
            file: Absolute path of the file to write to
            content: Text content to write
            append: (Optional) Whether to use append mode
            leading_newline: (Optional) Whether to add a leading newline
            trailing_newline: (Optional) Whether to add a trailing newline
            sudo: (Optional) Whether to use sudo privileges
            
        Returns:
            Write result
        """
        # Prepare content
        final_content = content
        if leading_newline:
            final_content = "\n" + final_content
        if trailing_newline:
            final_content = final_content + "\n"
            
        # Directly call sandbox's file_write method, pass all parameters
        return await self.sandbox.file_write(
            file=file, 
            content=final_content,
            append=append,
            leading_newline=False,  # Already handled in final_content
            trailing_newline=False,  # Already handled in final_content
            sudo=sudo
        )
    
    @tool(
        name="file_str_replace",
        description="Replace specified string in a file. Use for updating specific content in files or fixing errors in code.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the file to perform replacement on"
            },
            "old_str": {
                "type": "string",
                "description": "Original string to be replaced"
            },
            "new_str": {
                "type": "string",
                "description": "New string to replace with"
            },
            "sudo": {
                "type": "boolean",
                "description": "(Optional) Whether to use sudo privileges"
            }
        },
        required=["file", "old_str", "new_str"]
    )
    async def file_str_replace(
        self,
        file: str,
        old_str: str,
        new_str: str,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Replace specified string in file
        
        Args:
            file: Absolute path of the file to perform replacement on
            old_str: Original string to be replaced
            new_str: New string to replace with
            sudo: (Optional) Whether to use sudo privileges
            
        Returns:
            Replacement result
        """
        # Directly call sandbox's file_replace method
        return await self.sandbox.file_replace(
            file=file,
            old_str=old_str,
            new_str=new_str,
            sudo=sudo
        )
    
    @tool(
        name="file_find_in_content",
        description="Search for matching text within file content. Use for finding specific content or patterns in files.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the file to search within"
            },
            "regex": {
                "type": "string",
                "description": "Regular expression pattern to match"
            },
            "sudo": {
                "type": "boolean",
                "description": "(Optional) Whether to use sudo privileges"
            }
        },
        required=["file", "regex"]
    )
    async def file_find_in_content(
        self,
        file: str,
        regex: str,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Search for matching text in file content
        
        Args:
            file: Absolute path of the file to search
            regex: Regular expression pattern for matching
            sudo: (Optional) Whether to use sudo privileges
            
        Returns:
            Search results
        """
        # Directly call sandbox's file_search method
        return await self.sandbox.file_search(
            file=file,
            regex=regex,
            sudo=sudo
        )
    
    @tool(
        name="file_find_by_name",
        description="Find files by name pattern in specified directory. Use for locating files with specific naming patterns.",
        parameters={
            "path": {
                "type": "string",
                "description": "Absolute path of directory to search"
            },
            "glob": {
                "type": "string",
                "description": "Filename pattern using glob syntax wildcards"
            }
        },
        required=["path", "glob"]
    )
    async def file_find_by_name(
        self,
        path: str,
        glob: str
    ) -> ToolResult:
        """Find files by name pattern in specified directory
        
        Args:
            path: Absolute path of directory to search
            glob: Filename pattern using glob syntax wildcards
            
        Returns:
            Search results
        """
        # Directly call sandbox's file_find method
        return await self.sandbox.file_find(
            path=path,
            glob_pattern=glob
        )
    
    @tool(
        name="file_analyze_excel",
        description="Analyze Excel or CSV file with pandas. Supports data queries like 'get average of column X' or 'count rows where Y > 100'.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the Excel (.xlsx, .xls) or CSV file"
            },
            "query": {
                "type": "string",
                "description": "(Optional) Analysis query: 'average column_name', 'sum column_name', 'count', 'max', 'min', 'unique values'"
            }
        },
        required=["file"]
    )
    async def file_analyze_excel(
        self,
        file: str,
        query: Optional[str] = None
    ) -> ToolResult:
        """Analyze Excel or CSV file using pandas
        
        Args:
            file: Absolute path of Excel/CSV file
            query: Optional analysis query
            
        Returns:
            File analysis with statistics and query results
        """
        try:
            # Import the processor
            from app.domain.services.tools.file_processors import DataFileProcessor
            
            # Read file from sandbox
            file_result = await self.sandbox.file_read(file)
            if not file_result.success:
                return ToolResult(
                    success=False,
                    message=f"Failed to read file: {file_result.message}"
                )
            
            # Get file extension
            _, ext = os.path.splitext(file)
            
            # Process file
            # Note: file_result.data is text content, we need binary
            # For now, let's download it properly
            try:
                file_stream = await self.sandbox.file_download(file)
                file_content = file_stream.read()
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Failed to download file for processing: {str(e)}"
                )
            
            # Process with pandas
            analysis_result = DataFileProcessor.process_excel_csv(
                file_content=file_content,
                file_extension=ext,
                query=query
            )
            
            if not analysis_result.get("success"):
                return ToolResult(
                    success=False,
                    message=analysis_result.get("error", "Analysis failed")
                )
            
            # Format result message
            summary = analysis_result["summary"]
            message = f"Excel/CSV Analysis:\n"
            message += f"- Rows: {summary['rows']}\n"
            message += f"- Columns: {summary['columns']}\n"
            message += f"- Column names: {', '.join(summary['column_names'])}\n"
            
            if analysis_result.get("query_result"):
                query_res = analysis_result["query_result"]
                if query_res.get("result"):
                    message += f"\nQuery Result: {query_res['result']}"
                elif query_res.get("error"):
                    message += f"\nQuery Error: {query_res['error']}"
            
            return ToolResult(
                success=True,
                message=message,
                data=analysis_result
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to analyze file: {str(e)}"
            )
    
    @tool(
        name="file_extract_pdf",
        description="Extract text and tables from PDF files. Maintains document structure and extracts tables in structured format.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the PDF file"
            },
            "extract_tables": {
                "type": "boolean",
                "description": "(Optional) Whether to extract tables. Default is True."
            },
            "start_page": {
                "type": "integer",
                "description": "(Optional) Starting page number (0-indexed)"
            },
            "end_page": {
                "type": "integer",
                "description": "(Optional) Ending page number (exclusive)"
            }
        },
        required=["file"]
    )
    async def file_extract_pdf(
        self,
        file: str,
        extract_tables: Optional[bool] = True,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None
    ) -> ToolResult:
        """Extract text and tables from PDF file
        
        Args:
            file: Absolute path of PDF file
            extract_tables: Whether to extract tables
            start_page: Optional starting page
            end_page: Optional ending page
            
        Returns:
            Extracted text and tables
        """
        try:
            # Import the processor
            from app.domain.services.tools.file_processors import PDFProcessor
            
            # Download file from sandbox
            try:
                file_stream = await self.sandbox.file_download(file)
                file_content = file_stream.read()
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Failed to download PDF file: {str(e)}"
                )
            
            # Prepare page range
            page_range = None
            if start_page is not None and end_page is not None:
                page_range = (start_page, end_page)
            
            # Process PDF
            extraction_result = PDFProcessor.process_pdf(
                file_content=file_content,
                extract_tables=extract_tables,
                page_range=page_range
            )
            
            if not extraction_result.get("success"):
                return ToolResult(
                    success=False,
                    message=extraction_result.get("error", "PDF extraction failed")
                )
            
            # Format result message
            message = f"PDF Extraction:\n"
            message += f"- Total pages: {extraction_result['total_pages']}\n"
            message += f"- Pages processed: {len(extraction_result['pages'])}\n"
            message += f"- Tables found: {len(extraction_result['tables'])}\n"
            message += f"\nExtracted text preview:\n{extraction_result['text'][:500]}..."
            
            return ToolResult(
                success=True,
                message=message,
                data=extraction_result
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to extract PDF: {str(e)}"
            ) 