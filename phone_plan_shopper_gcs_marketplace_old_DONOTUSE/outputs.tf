output "agent_engine_id" {
  description = "The ID of the created Agent Engine."
  value       = google_vertex_ai_reasoning_engine.managed.name
}

output "agent_name" {
  description = "The name of the deployed agent."
  value       = var.agent_engine_name
}


