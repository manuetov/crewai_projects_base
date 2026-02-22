import unittest
from datetime import datetime
from task_distribution import TaskDistributionAssistant

class TestTaskDistributionAssistant(unittest.TestCase):

    def setUp(self):
        self.assistant = TaskDistributionAssistant(api_key="test_key")

    def test_process_task_data(self):
        tasks = [
            {"name": "Task 1", "priority": "high", "complexity": "medium"},
            {"name": "Task 2", "priority": "low", "complexity": "high"}
        ]
        processed = self.assistant.process_task_data(tasks)
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0]['priority'], 3)
        self.assertEqual(processed[1]['priority'], 1)
        
    def test_calculate_workload(self):
        team_availability = {
            "Alice": {"available_hours": 20, "current_tasks": ["task_1"], "skills": ["python"]},
            "Bob": {"available_hours": 15, "current_tasks": ["task_2"], "skills": ["javascript"]}
        }
        tasks = [
            {"id": "task_1", "estimated_hours": 5},
            {"id": "task_2", "estimated_hours": 10}
        ]
        self.assistant.process_task_data(tasks)
        workload = self.assistant.calculate_workload(team_availability)
        self.assertEqual(workload["Alice"]["remaining_capacity"], 15)
        self.assertEqual(workload["Bob"]["remaining_capacity"], 5)

    def test_generate_prompt(self):
        tasks = [
            {"id": "task_1", "name": "Task 1", "priority": 3, "complexity": 2, "estimated_hours": 6, "deadline": "2023-12-01", "required_skills": ["python"]}
        ]
        team_availability = {
            "Alice": {"available_hours": 10, "current_tasks": ["task_2"], "skills": ["python"]}
        }
        self.assistant.process_task_data(tasks)
        prompt = self.assistant.generate_prompt(tasks, team_availability)
        self.assertIn("TAREAS A ASIGNAR", prompt)
        self.assertIn("DISPONIBILIDAD DEL EQUIPO", prompt)

    def test_call_llm(self):
        prompt = "Test prompt"
        response = self.assistant.call_llm(prompt)
        self.assertIn("assignments", response)
        self.assertIn("risks", response)

    def test_parse_llm_response(self):
        llm_response = {
            "assignments": [
                {"task_id": "task_1", "assigned_to": "Alice", "rationale": "Fits skills"}
            ],
            "risks": []
        }
        self.assistant.process_task_data([{ "id": "task_1", "name": "Task 1", "estimated_hours": 6 }])
        parsed = self.assistant.parse_llm_response(llm_response)
        self.assertEqual(len(parsed["assignments"]), 1)
        self.assertEqual(parsed["assignments"][0]["task_name"], "Task 1")

    # Additional tests for database operations can be added here

if __name__ == '__main__':
    unittest.main()