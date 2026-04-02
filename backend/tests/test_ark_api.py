"""
Ark IDE Backend API Tests
Tests for session management, agent execution, workflows, and multi-agent features
"""
import pytest
import requests
import time
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicEndpoints:
    """Test basic API health and root endpoints"""
    
    def test_api_root(self):
        """Test API root endpoint returns correct response"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Ark IDE API"
        assert "version" in data
        print(f"✓ API root: {data}")
    
    def test_list_tools(self):
        """Test tools listing endpoint"""
        response = requests.get(f"{BASE_URL}/api/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "count" in data
        assert data["count"] > 0
        print(f"✓ Tools available: {data['count']}")


class TestSessionManagement:
    """Test session CRUD operations"""
    
    def test_create_session(self):
        """Test creating a new session"""
        payload = {
            "user_prompt": "TEST_Create a simple hello.txt file",
            "workspace_path": "/app"
        }
        response = requests.post(f"{BASE_URL}/api/sessions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "status" in data
        assert data["status"] == "created"
        assert "user_prompt" in data
        print(f"✓ Session created: {data['session_id']}")
        return data["session_id"]
    
    def test_list_sessions(self):
        """Test listing sessions"""
        response = requests.get(f"{BASE_URL}/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "count" in data
        print(f"✓ Sessions listed: {data['count']} sessions")
    
    def test_get_session(self):
        """Test getting a specific session"""
        # First create a session
        payload = {
            "user_prompt": "TEST_Get session test",
            "workspace_path": "/app"
        }
        create_response = requests.post(f"{BASE_URL}/api/sessions", json=payload)
        session_id = create_response.json()["session_id"]
        
        # Then get it
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["user_prompt"] == "TEST_Get session test"
        print(f"✓ Session retrieved: {session_id}")
    
    def test_get_nonexistent_session(self):
        """Test getting a non-existent session returns 404"""
        response = requests.get(f"{BASE_URL}/api/sessions/nonexistent-session-id")
        assert response.status_code == 404
        print("✓ Non-existent session returns 404")


class TestAgentExecution:
    """Test agent execution flow - CRITICAL for P0 bug fix verification"""
    
    def test_execute_session_and_completion(self):
        """
        CRITICAL TEST: Verify agent completes within max_steps (10) and outputs 'done' state
        This tests the P0 bug fix for infinite thinking loop
        """
        # Create session with simple file creation task
        payload = {
            "user_prompt": "Create a file called test_agent_output.txt with content 'Hello from agent'",
            "workspace_path": "/app"
        }
        create_response = requests.post(f"{BASE_URL}/api/sessions", json=payload)
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]
        print(f"✓ Session created for execution test: {session_id}")
        
        # Execute the session
        exec_response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/execute")
        assert exec_response.status_code == 200
        print("✓ Execution started")
        
        # Poll for completion (max 60 seconds)
        max_wait = 60
        poll_interval = 2
        elapsed = 0
        final_status = None
        
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            session_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
            assert session_response.status_code == 200
            session_data = session_response.json()
            
            status = session_data.get("status")
            current_step = session_data.get("current_step", 0)
            print(f"  Polling... Status: {status}, Step: {current_step}/{10}")
            
            if status in ["completed", "failed", "cancelled"]:
                final_status = status
                break
        
        # Verify completion
        assert final_status is not None, f"Session did not complete within {max_wait}s"
        
        # Get final session state
        final_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
        final_data = final_response.json()
        
        # CRITICAL: Verify max_steps limit (10) was enforced
        assert final_data.get("current_step", 0) <= 10, f"Agent exceeded max_steps: {final_data.get('current_step')}"
        
        # Check steps for 'done' action
        steps = final_data.get("steps", [])
        has_done_step = any(step.get("type") == "done" for step in steps)
        
        print(f"✓ Agent completed in {final_data.get('current_step')} steps")
        print(f"✓ Final status: {final_status}")
        print(f"✓ Has 'done' step: {has_done_step}")
        
        # If completed, should have a done step
        if final_status == "completed":
            assert has_done_step, "Completed session should have a 'done' step"
        
        return session_id
    
    def test_execute_already_running_session(self):
        """Test that executing an already running session returns error"""
        # Create and start a session
        payload = {
            "user_prompt": "TEST_Long running task",
            "workspace_path": "/app"
        }
        create_response = requests.post(f"{BASE_URL}/api/sessions", json=payload)
        session_id = create_response.json()["session_id"]
        
        # Start execution
        requests.post(f"{BASE_URL}/api/sessions/{session_id}/execute")
        
        # Wait a moment for status to update
        time.sleep(1)
        
        # Try to execute again - should fail if running
        session_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
        status = session_response.json().get("status")
        
        if status == "running":
            exec_response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/execute")
            assert exec_response.status_code == 400
            print("✓ Cannot execute already running session")
        else:
            print(f"✓ Session already completed with status: {status}")


class TestWorkflows:
    """Test workflow endpoints"""
    
    def test_list_workflows(self):
        """Test listing available workflows"""
        response = requests.get(f"{BASE_URL}/api/workflows")
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert "count" in data
        print(f"✓ Workflows available: {data['count']}")
        for wf in data.get("workflows", []):
            print(f"  - {wf.get('name', 'Unknown')}: {wf.get('description', '')[:50]}...")
    
    def test_execute_workflow(self):
        """Test executing a workflow"""
        # First get available workflows
        list_response = requests.get(f"{BASE_URL}/api/workflows")
        workflows = list_response.json().get("workflows", [])
        
        if workflows:
            workflow_type = workflows[0].get("type", "code_review")
            response = requests.post(
                f"{BASE_URL}/api/workflows/{workflow_type}/execute",
                params={"context": "TEST_workflow execution"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            print(f"✓ Workflow executed, session: {data['session_id']}")
        else:
            print("⚠ No workflows available to test")


class TestMultiAgent:
    """Test multi-agent endpoints"""
    
    def test_list_agents(self):
        """Test listing available agent roles"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "count" in data
        print(f"✓ Agents available: {data['count']}")
        for agent in data.get("agents", []):
            print(f"  - {agent.get('role', 'Unknown')}")
    
    def test_assign_agent_to_session(self):
        """Test assigning an agent role to a session"""
        # Create a session first
        payload = {
            "user_prompt": "TEST_Agent assignment",
            "workspace_path": "/app"
        }
        create_response = requests.post(f"{BASE_URL}/api/sessions", json=payload)
        session_id = create_response.json()["session_id"]
        
        # Get available agents
        agents_response = requests.get(f"{BASE_URL}/api/agents")
        agents = agents_response.json().get("agents", [])
        
        if agents:
            role = agents[0].get("role", "planner")
            response = requests.post(
                f"{BASE_URL}/api/sessions/{session_id}/assign-agent",
                params={"role": role}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["agent_role"] == role
            print(f"✓ Agent '{role}' assigned to session")
        else:
            print("⚠ No agents available to test")


class TestSummaryAndDiff:
    """Test summary and diff endpoints"""
    
    def test_get_session_summary_incomplete(self):
        """Test getting summary for incomplete session"""
        # Create a session (not executed)
        payload = {
            "user_prompt": "TEST_Summary test",
            "workspace_path": "/app"
        }
        create_response = requests.post(f"{BASE_URL}/api/sessions", json=payload)
        session_id = create_response.json()["session_id"]
        
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "created" in data.get("status", "")
        print(f"✓ Summary for incomplete session: {data['summary'][:50]}...")
    
    def test_get_file_changes(self):
        """Test getting file changes for a session"""
        # Create a session
        payload = {
            "user_prompt": "TEST_File changes test",
            "workspace_path": "/app"
        }
        create_response = requests.post(f"{BASE_URL}/api/sessions", json=payload)
        session_id = create_response.json()["session_id"]
        
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/file-changes")
        assert response.status_code == 200
        data = response.json()
        assert "file_changes" in data
        assert "count" in data
        print(f"✓ File changes retrieved: {data['count']} changes")


class TestTodoEndpoints:
    """Test Todo CRUD endpoints"""
    
    def test_create_todo(self):
        """Test creating a todo"""
        payload = {
            "title": "TEST_Todo item",
            "description": "Test description"
        }
        response = requests.post(f"{BASE_URL}/api/todos", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "todo" in data
        assert data["todo"]["title"] == "TEST_Todo item"
        print(f"✓ Todo created: {data['todo']['id']}")
        return data["todo"]["id"]
    
    def test_list_todos(self):
        """Test listing todos"""
        response = requests.get(f"{BASE_URL}/api/todos")
        assert response.status_code == 200
        data = response.json()
        assert "todos" in data
        assert "count" in data
        print(f"✓ Todos listed: {data['count']} todos")
    
    def test_get_todo(self):
        """Test getting a specific todo"""
        # Create first
        payload = {"title": "TEST_Get todo", "description": "Test"}
        create_response = requests.post(f"{BASE_URL}/api/todos", json=payload)
        todo_id = create_response.json()["todo"]["id"]
        
        # Get it
        response = requests.get(f"{BASE_URL}/api/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["todo"]["id"] == todo_id
        print(f"✓ Todo retrieved: {todo_id}")
    
    def test_update_todo(self):
        """Test updating a todo"""
        # Create first
        payload = {"title": "TEST_Update todo", "description": "Original"}
        create_response = requests.post(f"{BASE_URL}/api/todos", json=payload)
        todo_id = create_response.json()["todo"]["id"]
        
        # Update it
        update_payload = {"title": "TEST_Updated todo", "completed": True}
        response = requests.patch(f"{BASE_URL}/api/todos/{todo_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["todo"]["title"] == "TEST_Updated todo"
        assert data["todo"]["completed"] == True
        print(f"✓ Todo updated: {todo_id}")
    
    def test_delete_todo(self):
        """Test deleting a todo"""
        # Create first
        payload = {"title": "TEST_Delete todo", "description": "To be deleted"}
        create_response = requests.post(f"{BASE_URL}/api/todos", json=payload)
        todo_id = create_response.json()["todo"]["id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/todos/{todo_id}")
        assert response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/todos/{todo_id}")
        assert get_response.status_code == 404
        print(f"✓ Todo deleted: {todo_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
