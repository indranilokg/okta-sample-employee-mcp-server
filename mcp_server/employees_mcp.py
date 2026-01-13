"""
Employee MCP Server - Standalone HTTP Server for Okta-Secured Employee Data Access

This is a standalone HTTP server version of the Employee MCP server.
It validates incoming Okta tokens before granting access to employee tools.

Features:
- FastAPI-based HTTP MCP server
- Okta token validation on every tool call
- Scope-based permission checking
- Complete audit trail with token claims
- Deployable to cloud (Render, Heroku, etc.)

MCP Tools Available:
1. list_employees - List all active employees
2. get_employee_info - Get detailed info about specific employee
3. get_department_info - Get department overview
4. get_benefits_info - List available benefits
5. get_salary_info - Get salary band distribution (requires mcp:read scope)
6. get_onboarding_info - Get onboarding process
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class EmployeesMCP:
    """
    Standalone MCP Server for Employee Data Management
    
    Validates Okta tokens and enforces scope-based permissions
    """
    
    def __init__(self):
        self.employees_data = self._initialize_mock_data()
        self.tools = self._define_tools()
        logger.info("EmployeesMCP initialized with mock data and tools")
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define available MCP tools for employee management"""
        return [
            {
                "name": "list_employees",
                "description": "List all active employees with their basic information (department, title, manager). Requires mcp:read scope.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status_filter": {
                            "type": "string",
                            "enum": ["Active", "Inactive", "All"],
                            "description": "Filter employees by status. Default: Active",
                            "default": "Active"
                        }
                    }
                }
            },
            {
                "name": "get_employee_info",
                "description": "Get detailed information about a specific employee by name or employee ID. Requires mcp:read scope.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "employee_identifier": {
                            "type": "string",
                            "description": "Employee name (e.g., 'John Smith') or employee ID (e.g., 'EMP001')"
                        }
                    },
                    "required": ["employee_identifier"]
                }
            },
            {
                "name": "get_department_info",
                "description": "Get overview information about all departments including head, employee count, budget, and location.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "department_name": {
                            "type": "string",
                            "description": "Optional: Specific department name. If not provided, returns all departments.",
                            "enum": ["Engineering", "Finance", "HR", "Legal", "Product", "Marketing", "Sales", None]
                        }
                    }
                }
            },
            {
                "name": "get_benefits_info",
                "description": "Get information about available employee benefits and enrollment statistics.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_salary_info",
                "description": "Get salary band distribution information. Requires mcp:read scope.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_onboarding_info",
                "description": "Get information about the employee onboarding process and steps.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def _initialize_mock_data(self) -> Dict[str, Any]:
        """Initialize mock employee data"""
        return {
            "employees": {
                # Engineering Department
                "emp-001": {
                    "id": "emp-001",
                    "employee_id": "EMP001",
                    "name": "Jane Doe",
                    "email": "jane.doe@streamward.com",
                    "department": "Engineering",
                    "title": "VP of Engineering",
                    "manager": None,
                    "hire_date": "2019-06-01",
                    "status": "Active",
                    "location": "San Francisco, CA",
                    "phone": "+1-555-0101",
                    "salary_band": "L7",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Executive Bonus"],
                    "access_level": "Admin",
                    "last_login": "2025-11-09T14:30:00Z",
                    "reports_count": 8,
                    "team": "Engineering Leadership"
                },
                "emp-002": {
                    "id": "emp-002",
                    "employee_id": "EMP002",
                    "name": "John Smith",
                    "email": "john.smith@streamward.com",
                    "department": "Engineering",
                    "title": "Senior Software Engineer",
                    "manager": "Jane Doe",
                    "hire_date": "2022-03-15",
                    "status": "Active",
                    "location": "San Francisco, CA",
                    "phone": "+1-555-0102",
                    "salary_band": "L5",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Gym Membership"],
                    "access_level": "Standard",
                    "last_login": "2025-11-09T09:30:00Z",
                    "reports_count": 0,
                    "team": "Backend Platform"
                },
                "emp-003": {
                    "id": "emp-003",
                    "employee_id": "EMP003",
                    "name": "Alice Kumar",
                    "email": "alice.kumar@streamward.com",
                    "department": "Engineering",
                    "title": "Software Engineer (Backend)",
                    "manager": "John Smith",
                    "hire_date": "2023-07-20",
                    "status": "Active",
                    "location": "San Francisco, CA",
                    "phone": "+1-555-0103",
                    "salary_band": "L4",
                    "benefits": ["Health Insurance", "401k", "Stock Options"],
                    "access_level": "Standard",
                    "last_login": "2025-11-09T10:15:00Z",
                    "reports_count": 0,
                    "team": "Backend Platform"
                },
                "emp-004": {
                    "id": "emp-004",
                    "employee_id": "EMP004",
                    "name": "Marcus Thompson",
                    "email": "marcus.thompson@streamward.com",
                    "department": "Engineering",
                    "title": "DevOps Engineer",
                    "manager": "Jane Doe",
                    "hire_date": "2021-11-01",
                    "status": "Active",
                    "location": "Seattle, WA",
                    "phone": "+1-555-0104",
                    "salary_band": "L5",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Remote Work"],
                    "access_level": "Admin",
                    "last_login": "2025-11-09T08:45:00Z",
                    "reports_count": 2,
                    "team": "Infrastructure"
                },
                # Finance Department
                "emp-005": {
                    "id": "emp-005",
                    "employee_id": "EMP005",
                    "name": "Mike Wilson",
                    "email": "mike.wilson@streamward.com",
                    "department": "Finance",
                    "title": "CFO",
                    "manager": None,
                    "hire_date": "2020-01-15",
                    "status": "Active",
                    "location": "New York, NY",
                    "phone": "+1-555-0105",
                    "salary_band": "L7",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Executive Bonus", "Company Car"],
                    "access_level": "Admin",
                    "last_login": "2025-11-09T15:00:00Z",
                    "reports_count": 5,
                    "team": "Finance Leadership"
                },
                "emp-006": {
                    "id": "emp-006",
                    "employee_id": "EMP006",
                    "name": "Sarah Johnson",
                    "email": "sarah.johnson@streamward.com",
                    "department": "Finance",
                    "title": "Senior Financial Analyst",
                    "manager": "Mike Wilson",
                    "hire_date": "2021-08-20",
                    "status": "Active",
                    "location": "New York, NY",
                    "phone": "+1-555-0106",
                    "salary_band": "L5",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Tuition Reimbursement"],
                    "access_level": "Standard",
                    "last_login": "2025-11-09T09:00:00Z",
                    "reports_count": 0,
                    "team": "Financial Planning"
                },
                "emp-007": {
                    "id": "emp-007",
                    "employee_id": "EMP007",
                    "name": "Priya Patel",
                    "email": "priya.patel@streamward.com",
                    "department": "Finance",
                    "title": "Controller",
                    "manager": "Mike Wilson",
                    "hire_date": "2019-03-10",
                    "status": "Active",
                    "location": "New York, NY",
                    "phone": "+1-555-0107",
                    "salary_band": "L6",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Executive Bonus"],
                    "access_level": "Admin",
                    "last_login": "2025-11-09T11:30:00Z",
                    "reports_count": 3,
                    "team": "Accounting"
                },
                # HR Department
                "emp-008": {
                    "id": "emp-008",
                    "employee_id": "EMP008",
                    "name": "Lisa Brown",
                    "email": "lisa.brown@streamward.com",
                    "department": "HR",
                    "title": "Chief People Officer",
                    "manager": None,
                    "hire_date": "2018-09-05",
                    "status": "Active",
                    "location": "Austin, TX",
                    "phone": "+1-555-0108",
                    "salary_band": "L7",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Executive Bonus"],
                    "access_level": "Admin",
                    "last_login": "2025-11-09T13:45:00Z",
                    "reports_count": 4,
                    "team": "HR Leadership"
                },
                "emp-009": {
                    "id": "emp-009",
                    "employee_id": "EMP009",
                    "name": "David Chen",
                    "email": "david.chen@streamward.com",
                    "department": "HR",
                    "title": "HR Business Partner",
                    "manager": "Lisa Brown",
                    "hire_date": "2020-11-10",
                    "status": "Active",
                    "location": "Austin, TX",
                    "phone": "+1-555-0109",
                    "salary_band": "L5",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Flexible PTO"],
                    "access_level": "Elevated",
                    "last_login": "2025-11-09T10:20:00Z",
                    "reports_count": 0,
                    "team": "Talent Management"
                },
                "emp-010": {
                    "id": "emp-010",
                    "employee_id": "EMP010",
                    "name": "Jessica Martinez",
                    "email": "jessica.martinez@streamward.com",
                    "department": "HR",
                    "title": "Recruiting Manager",
                    "manager": "Lisa Brown",
                    "hire_date": "2022-02-14",
                    "status": "Active",
                    "location": "Austin, TX",
                    "phone": "+1-555-0110",
                    "salary_band": "L5",
                    "benefits": ["Health Insurance", "401k", "Stock Options"],
                    "access_level": "Elevated",
                    "last_login": "2025-11-09T09:45:00Z",
                    "reports_count": 2,
                    "team": "Talent Acquisition"
                },
                # Legal Department
                "emp-011": {
                    "id": "emp-011",
                    "employee_id": "EMP011",
                    "name": "Robert Taylor",
                    "email": "robert.taylor@streamward.com",
                    "department": "Legal",
                    "title": "General Counsel",
                    "manager": None,
                    "hire_date": "2017-05-20",
                    "status": "Active",
                    "location": "Chicago, IL",
                    "phone": "+1-555-0111",
                    "salary_band": "L7",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Executive Bonus", "Legal Services"],
                    "access_level": "Admin",
                    "last_login": "2025-11-09T14:00:00Z",
                    "reports_count": 3,
                    "team": "Legal Leadership"
                },
                "emp-012": {
                    "id": "emp-012",
                    "employee_id": "EMP012",
                    "name": "Emily Davis",
                    "email": "emily.davis@streamward.com",
                    "department": "Legal",
                    "title": "Senior Legal Counsel",
                    "manager": "Robert Taylor",
                    "hire_date": "2023-01-05",
                    "status": "Active",
                    "location": "Chicago, IL",
                    "phone": "+1-555-0112",
                    "salary_band": "L6",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Legal Insurance"],
                    "access_level": "Elevated",
                    "last_login": "2025-11-09T12:30:00Z",
                    "reports_count": 0,
                    "team": "Corporate Law"
                },
                # Product & Marketing
                "emp-013": {
                    "id": "emp-013",
                    "employee_id": "EMP013",
                    "name": "Rachel Green",
                    "email": "rachel.green@streamward.com",
                    "department": "Product",
                    "title": "Head of Product",
                    "manager": None,
                    "hire_date": "2020-09-01",
                    "status": "Active",
                    "location": "San Francisco, CA",
                    "phone": "+1-555-0113",
                    "salary_band": "L6",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Executive Bonus"],
                    "access_level": "Elevated",
                    "last_login": "2025-11-09T13:15:00Z",
                    "reports_count": 4,
                    "team": "Product Management"
                },
                "emp-014": {
                    "id": "emp-014",
                    "employee_id": "EMP014",
                    "name": "Kevin Lopez",
                    "email": "kevin.lopez@streamward.com",
                    "department": "Marketing",
                    "title": "Marketing Manager",
                    "manager": None,
                    "hire_date": "2021-05-15",
                    "status": "Active",
                    "location": "New York, NY",
                    "phone": "+1-555-0114",
                    "salary_band": "L5",
                    "benefits": ["Health Insurance", "401k", "Stock Options"],
                    "access_level": "Standard",
                    "last_login": "2025-11-09T10:00:00Z",
                    "reports_count": 3,
                    "team": "Digital Marketing"
                },
                "emp-015": {
                    "id": "emp-015",
                    "employee_id": "EMP015",
                    "name": "Sophia Rodriguez",
                    "email": "sophia.rodriguez@streamward.com",
                    "department": "Sales",
                    "title": "VP of Sales",
                    "manager": None,
                    "hire_date": "2019-08-10",
                    "status": "Active",
                    "location": "New York, NY",
                    "phone": "+1-555-0115",
                    "salary_band": "L7",
                    "benefits": ["Health Insurance", "401k", "Stock Options", "Executive Bonus", "Car Allowance"],
                    "access_level": "Elevated",
                    "last_login": "2025-11-09T15:30:00Z",
                    "reports_count": 6,
                    "team": "Sales Leadership"
                }
            },
            "departments": {
                "Engineering": {
                    "name": "Engineering",
                    "head": "Jane Doe",
                    "employee_count": 45,
                    "budget": 5000000,
                    "budget_used": 4200000,
                    "location": "San Francisco, CA",
                    "description": "Software Development, Infrastructure, DevOps",
                    "teams": 5,
                    "hiring_plan": 8,
                    "avg_tenure_years": 3.2
                },
                "Finance": {
                    "name": "Finance",
                    "head": "Mike Wilson",
                    "employee_count": 12,
                    "budget": 800000,
                    "budget_used": 750000,
                    "location": "New York, NY",
                    "description": "Accounting, Financial Planning, Treasury",
                    "teams": 3,
                    "hiring_plan": 2,
                    "avg_tenure_years": 4.1
                },
                "HR": {
                    "name": "Human Resources",
                    "head": "Lisa Brown",
                    "employee_count": 8,
                    "budget": 400000,
                    "budget_used": 380000,
                    "location": "Austin, TX",
                    "description": "Talent Acquisition, Employee Relations, Compensation & Benefits",
                    "teams": 3,
                    "hiring_plan": 3,
                    "avg_tenure_years": 2.8
                },
                "Legal": {
                    "name": "Legal",
                    "head": "Robert Taylor",
                    "employee_count": 5,
                    "budget": 300000,
                    "budget_used": 290000,
                    "location": "Chicago, IL",
                    "description": "Corporate Law, Compliance, Contracts",
                    "teams": 2,
                    "hiring_plan": 1,
                    "avg_tenure_years": 5.3
                },
                "Product": {
                    "name": "Product",
                    "head": "Rachel Green",
                    "employee_count": 12,
                    "budget": 900000,
                    "budget_used": 850000,
                    "location": "San Francisco, CA",
                    "description": "Product Management, Product Strategy, UX Research",
                    "teams": 2,
                    "hiring_plan": 3,
                    "avg_tenure_years": 2.5
                },
                "Marketing": {
                    "name": "Marketing",
                    "head": "Kevin Lopez",
                    "employee_count": 15,
                    "budget": 1200000,
                    "budget_used": 1050000,
                    "location": "New York, NY",
                    "description": "Digital Marketing, Content, Brand, Demand Gen",
                    "teams": 4,
                    "hiring_plan": 2,
                    "avg_tenure_years": 2.1
                },
                "Sales": {
                    "name": "Sales",
                    "head": "Sophia Rodriguez",
                    "employee_count": 28,
                    "budget": 3500000,
                    "budget_used": 3200000,
                    "location": "New York, NY",
                    "description": "Enterprise Sales, Mid-Market, Sales Engineering",
                    "teams": 3,
                    "hiring_plan": 6,
                    "avg_tenure_years": 3.4
                }
            }
        }
    
    def _has_permission(self, token_claims: Dict[str, Any], permission: str) -> bool:
        """Check if user has specific permission based on OAuth scope"""
        if not token_claims:
            logger.warning(f"Permission '{permission}' denied: no token claims")
            return False
        
        scope = token_claims.get("scope", "")
        
        permission_scope_map = {
            "view_employee_list": ["read_data", "mcp:read"],
            "view_employee_details": ["read_data", "mcp:read"],
            "view_salary_info": ["read_data", "mcp:read"],
            "edit_employee": ["write_data", "mcp:write"],
            "delete_employee": ["write_data", "mcp:write"]
        }
        
        required_scopes = permission_scope_map.get(permission, [])
        
        # Handle scope as either space-separated string or array
        if isinstance(scope, list):
            scope_list = scope
        elif isinstance(scope, str):
            scope_list = scope.split() if scope else []
        else:
            scope_list = []
        
        # Check if any required scope is in the token's scopes
        has_permission = any(
            req_scope in scope_list or req_scope in scope 
            for req_scope in required_scopes
        )
        
        if has_permission:
            logger.info(f"Permission '{permission}' GRANTED (scopes: {scope_list}, required: {required_scopes})")
        else:
            logger.warning(f"Permission '{permission}' DENIED (scopes: {scope_list}, required: {required_scopes})")
            logger.debug(f"Full token claims keys: {list(token_claims.keys())}")
        
        return has_permission
    
    def _find_employee_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find employee by name or ID"""
        employees = self.employees_data["employees"]
        
        # Check by employee ID first
        for employee in employees.values():
            if employee['employee_id'].lower() == identifier.lower():
                return employee
        
        # Check by name
        for employee in employees.values():
            if identifier.lower() in employee['name'].lower():
                return employee
        
        return None
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools"""
        return self.tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool by name with arguments.
        
        Token validation must be done by the HTTP handler before calling this.
        Token claims are passed for permission checking.
        """
        try:
            if tool_name == "list_employees":
                status_filter = arguments.get("status_filter", "Active")
                return await self._tool_list_employees(status_filter, token_claims)
            elif tool_name == "get_employee_info":
                employee_identifier = arguments.get("employee_identifier")
                if not employee_identifier:
                    return {"error": "employee_identifier is required"}
                return await self._tool_get_employee_info(employee_identifier, token_claims)
            elif tool_name == "get_department_info":
                department_name = arguments.get("department_name")
                return await self._tool_get_department_info(department_name, token_claims)
            elif tool_name == "get_benefits_info":
                return await self._tool_get_benefits_info(token_claims)
            elif tool_name == "get_salary_info":
                return await self._tool_get_salary_info(token_claims)
            elif tool_name == "get_onboarding_info":
                return await self._tool_get_onboarding_info(token_claims)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def _tool_list_employees(self, status_filter: str, token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for list_employees"""
        if not self._has_permission(token_claims, "view_employee_list"):
            return {
                "error": "insufficient_permissions",
                "message": "You don't have permission to view the employee list. Please contact HR for access."
            }
        
        employees = self.employees_data["employees"]
        filtered_employees = []
        
        for emp_id, employee in employees.items():
            if status_filter == "All" or employee['status'] == status_filter:
                filtered_employees.append({
                    "employee_id": employee['employee_id'],
                    "name": employee['name'],
                    "department": employee['department'],
                    "title": employee['title'],
                    "manager": employee['manager'],
                    "status": employee['status']
                })
        
        return {
            "employees": filtered_employees,
            "total_count": len(filtered_employees),
            "status_filter": status_filter
        }
    
    async def _tool_get_employee_info(self, employee_identifier: str, token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for get_employee_info"""
        if not self._has_permission(token_claims, "view_employee_details"):
            return {
                "error": "insufficient_permissions",
                "message": "You don't have permission to view detailed employee information."
            }
        
        employee = self._find_employee_by_identifier(employee_identifier)
        if not employee:
            return {
                "error": "employee_not_found",
                "message": f"Employee '{employee_identifier}' not found."
            }
        
        return {
            "employee": {
                "id": employee['id'],
                "employee_id": employee['employee_id'],
                "name": employee['name'],
                "email": employee['email'],
                "department": employee['department'],
                "title": employee['title'],
                "manager": employee['manager'],
                "hire_date": employee['hire_date'],
                "status": employee['status'],
                "location": employee['location'],
                "phone": employee['phone'],
                "salary_band": employee['salary_band'],
                "benefits": employee['benefits'],
                "access_level": employee['access_level'],
                "last_login": employee['last_login']
            }
        }
    
    async def _tool_get_department_info(self, department_name: Optional[str], token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for get_department_info"""
        departments = self.employees_data["departments"]
        
        if department_name:
            if department_name in departments:
                return {
                    "department": {
                        "name": department_name,
                        **departments[department_name]
                    }
                }
            else:
                return {
                    "error": "department_not_found",
                    "message": f"Department '{department_name}' not found."
                }
        else:
            return {
                "departments": [
                    {"name": name, **info} 
                    for name, info in departments.items()
                ],
                "total_count": len(departments)
            }
    
    async def _tool_get_benefits_info(self, token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for get_benefits_info"""
        employees = self.employees_data["employees"]
        
        all_benefits = set()
        benefit_enrollments = {}
        
        for employee in employees.values():
            for benefit in employee['benefits']:
                all_benefits.add(benefit)
                if benefit not in benefit_enrollments:
                    benefit_enrollments[benefit] = 0
                benefit_enrollments[benefit] += 1
        
        return {
            "benefits": [
                {
                    "name": benefit,
                    "enrollment_count": benefit_enrollments[benefit]
                }
                for benefit in sorted(all_benefits)
            ],
            "total_unique_benefits": len(all_benefits),
            "total_employees": len(employees)
        }
    
    async def _tool_get_salary_info(self, token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for get_salary_info"""
        if not self._has_permission(token_claims, "view_salary_info"):
            return {
                "error": "insufficient_permissions",
                "message": "You don't have permission to view salary information. Please contact HR for access."
            }
        
        employees = self.employees_data["employees"]
        salary_bands = {}
        
        for employee in employees.values():
            band = employee['salary_band']
            if band not in salary_bands:
                salary_bands[band] = []
            salary_bands[band].append(employee['name'])
        
        return {
            "salary_bands": {
                band: {
                    "employees": names,
                    "count": len(names)
                }
                for band, names in salary_bands.items()
            }
        }
    
    async def _tool_get_onboarding_info(self, token_claims: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for get_onboarding_info"""
        return {
            "onboarding_process": {
                "pre_boarding": {
                    "timeline": "1 week before start date",
                    "steps": [
                        "Send welcome email with company information",
                        "Set up IT accounts and access",
                        "Schedule orientation session"
                    ]
                },
                "first_day": {
                    "steps": [
                        "Complete HR paperwork",
                        "IT setup and equipment assignment",
                        "Department introduction"
                    ]
                },
                "first_week": {
                    "steps": [
                        "Training sessions",
                        "Buddy assignment",
                        "Goal setting meeting"
                    ]
                },
                "first_month": {
                    "steps": [
                        "Regular check-ins",
                        "Performance review setup",
                        "Benefits enrollment"
                    ]
                }
            }
        }
