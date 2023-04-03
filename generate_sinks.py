import os

### table_name,primary_key_column
data = """
"active_rule_parameters,uuid"
"active_rules,uuid"
"alm_pats,uuid"
"alm_settings,uuid"
"project_alm_settings,uuid"
"analysis_properties,uuid"
"app_branch_project_branch,uuid"
"app_projects,uuid"
"ce_activity,uuid"
"ce_queue,uuid"
"ce_scanner_context,task_uuid"
"ce_task_characteristics,uuid"
"ce_task_input,task_uuid"
"ce_task_message,uuid"
"default_qprofiles,language"
"deprecated_rule_keys,uuid"
"duplications_index,uuid"
"es_queue,uuid"
"event_component_changes,uuid"
"events,uuid"
"file_sources,uuid"
"group_roles,uuid"
"groups,uuid"
"internal_component_props,uuid"
"internal_properties,kee"
"issue_changes,uuid"
"issues,kee"
"live_measures,uuid"
"metrics,uuid"
"new_code_periods,uuid"
"notifications,uuid"
"org_qprofiles,uuid"
"perm_templates_groups,uuid"
"perm_templates_users,uuid"
"perm_tpl_characteristics,uuid"
"permission_templates,uuid"
"plugins,uuid"
"project_branches,uuid"
"project_links,uuid"
"project_mappings,uuid"
"project_measures,uuid"
"project_qprofiles,uuid"
"projects,uuid"
"project_qgates,project_uuid"
"properties,uuid"
"qprofile_changes,kee"
"qprofile_edit_groups,uuid"
"qprofile_edit_users,uuid"
"quality_gate_conditions,uuid"
"quality_gates,uuid"
"session_tokens,uuid"
"rule_repositories,kee"
"rules,uuid"
"rules_parameters,uuid"
"rules_profiles,uuid"
"saml_message_ids,uuid"
"snapshots,uuid"
"user_roles,uuid"
"user_dismissed_messages,uuid"
"user_tokens,uuid"
"users,uuid"
"webhook_deliveries,uuid"
"webhooks,uuid"
"audits,uuid"
"portfolios,uuid"
"portfolio_references,uuid"
"portfolio_projects,uuid"
"qgate_user_permissions,uuid"
"qgate_group_permissions,uuid"
"portfolio_proj_branches,uuid"
"project_badge_token,uuid"
"new_code_reference_issues,uuid"
"scanner_analysis_cache,branch_uuid"
"rule_desc_sections,uuid"
"push_events,uuid"
"scim_users,scim_uuid"
"""

output_folder = "jdbc_sinks"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

with open('postgres-sink-template.json') as f:
    template_text = f.read()

    table_list = data.strip().replace("\"", "").split("\n")
    for line in table_list:
        table = line.split(',')[0]
        pk = line.split(',')[1].upper()

        with open(os.path.join(output_folder, table) + ".json", "w") as output_file:
            output_file.write(template_text.replace("TABLE_NAME_UPPER", table.upper()).replace("TABLE_NAME_PK", pk).replace("TABLE_NAME", table))

            print(f"""
                curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/{table}/config -d @{table}.json
            """.strip())


